#!/usr/bin/env python3
"""
Job search aggregator - pulls from LinkedIn, Indeed, Greenhouse boards, and Lever boards.

All sources are 100% free, no API keys needed.

Usage:
    python3 jobs/search.py                    # Default search
    python3 jobs/search.py --max-age 24       # Only last 24 hours
    python3 jobs/search.py --min-score 40     # Higher quality threshold
    python3 jobs/search.py --source linkedin  # Single source only
    python3 jobs/search.py --alert            # Notify on new high-score jobs
    python3 jobs/search.py --json             # JSON output
"""

import html as html_mod
import os
import sys
import json
import hashlib
import argparse
import subprocess
import math
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependency: pip3 install beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: str = ""
    job_type: str = ""
    remote: bool = False
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    matched_skills: list = field(default_factory=list)

    @property
    def job_id(self) -> str:
        raw = f"{self.company}|{self.title}|{self.location}".lower().strip()
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @property
    def salary_display(self) -> str:
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} - ${self.salary_max:,}"
        elif self.salary_min:
            return f"${self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,}"
        return "Not listed"

    @property
    def age_display(self) -> str:
        if not self.posted_at:
            return "Unknown"
        now = datetime.now(timezone.utc)
        delta = now - self.posted_at
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return "< 1 hour ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        elif hours < 48:
            return "1 day ago"
        else:
            return f"{int(hours / 24)} days ago"


# ---------------------------------------------------------------------------
# HTTP + logging
# ---------------------------------------------------------------------------

def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _get(url: str, headers: Optional[dict] = None, timeout: int = 20) -> bytes:
    """Raw GET request, returns bytes."""
    ctx = _ssl_context()
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/json,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    default_headers.update(headers or {})
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200] if e.fp else ""
        _log(f"  HTTP {e.code} from {url[:80]}... {body}")
        return b""
    except Exception as e:
        _log(f"  Error fetching {url[:80]}...: {e}")
        return b""


def _api_get(url: str, headers: Optional[dict] = None, timeout: int = 20) -> dict:
    """GET request, returns parsed JSON."""
    raw = _get(url, headers=headers, timeout=timeout)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _log(msg: str):
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

LOG_FILE = Path(__file__).parent / ".search.log"


def notify_macos(title: str, message: str, url: str = ""):
    # Sanitize for AppleScript: escape backslashes first, then quotes
    for s in (title, message):
        s = s.replace("\\", "\\\\").replace('"', '\\"')
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_msg = message.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass


def notify_jobs(new_high_score_jobs: list["Job"], alert_threshold: int):
    if not new_high_score_jobs:
        return
    count = len(new_high_score_jobs)
    if count == 1:
        job = new_high_score_jobs[0]
        notify_macos(
            f"Job Match ({job.score}/100)",
            f"{job.title} at {job.company}\n{job.salary_display}",
        )
    else:
        top = new_high_score_jobs[0]
        notify_macos(
            f"{count} New Job Matches",
            f"Top: {top.title} at {top.company} ({top.score}/100)",
        )
    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n")
        for job in new_high_score_jobs:
            f.write(f"  [{job.score}] {job.title} @ {job.company} | {job.salary_display}\n")
            f.write(f"       {job.url}\n")


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def _parse_date(val) -> Optional[datetime]:
    """Try to parse various date formats into a timezone-aware datetime."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        # Unix timestamp (milliseconds or seconds)
        ts = val / 1000 if val > 1e12 else val
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    if isinstance(val, str):
        val = val.strip()
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        # Try fromisoformat as fallback
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass
    return None


def _parse_salary(val) -> Optional[int]:
    if val is None:
        return None
    try:
        v = int(float(val))
        if v < 500:
            v = v * 2080
        return v if v > 10000 else None
    except (ValueError, TypeError):
        return None


# -- LinkedIn --

def fetch_linkedin(config: dict, query: str, max_age_hours: int) -> list[Job]:
    """Scrape LinkedIn's public job search page."""
    location = config["profile"]["location"]
    seconds = max_age_hours * 3600

    params = {
        "keywords": query,
        "location": location,
        "f_TPR": f"r{seconds}",
        "position": "1",
        "pageNum": "0",
        "sortBy": "DD",  # sort by date
    }
    url = f"https://www.linkedin.com/jobs/search?{urllib.parse.urlencode(params)}"
    raw = _get(url)
    if not raw:
        return []

    soup = BeautifulSoup(raw, "html.parser")
    jobs = []

    for card in soup.select("div.base-card, li.result-card, div.job-search-card"):
        title_el = card.select_one(
            "h3.base-search-card__title, h3.result-card__title, "
            "h3.job-search-card__title, span.sr-only"
        )
        company_el = card.select_one(
            "h4.base-search-card__subtitle, h4.result-card__subtitle, "
            "a.job-search-card__subtitle-link"
        )
        location_el = card.select_one(
            "span.job-search-card__location, span.result-card__location"
        )
        link_el = card.select_one("a.base-card__full-link, a.result-card__full-link, a[href]")
        time_el = card.select_one("time")
        salary_el = card.select_one(
            "span.job-search-card__salary-info, div.salary-snippet-container, "
            "span.result-card__salary"
        )

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        job_url = ""
        if link_el and link_el.get("href"):
            job_url = link_el["href"].split("?")[0]  # clean tracking params

        posted = None
        if time_el and time_el.get("datetime"):
            posted = _parse_date(time_el["datetime"])

        # Extract salary from card if present
        sal_min, sal_max = None, None
        if salary_el:
            sal_text = salary_el.get_text(strip=True)
            sal_match = re.search(
                r'\$(\d{2,3}(?:,\d{3})+)\s*(?:[-–—to/]+|and)\s*\$?(\d{2,3}(?:,\d{3})+)',
                sal_text
            )
            if sal_match:
                lo = int(sal_match.group(1).replace(",", ""))
                hi = int(sal_match.group(2).replace(",", ""))
                if lo >= 50000 and hi >= 50000:
                    sal_min, sal_max = lo, hi

        if not title or not company:
            continue

        jobs.append(Job(
            title=title,
            company=company,
            location=loc,
            url=job_url,
            source="linkedin",
            posted_at=posted,
            created_at=posted,
            salary_min=sal_min,
            salary_max=sal_max,
            remote="remote" in loc.lower(),
        ))

    return jobs


# -- Indeed --

def _parse_indeed_date(text: str) -> Optional[datetime]:
    """Parse Indeed's relative date strings like 'Just posted', '1 day ago', '3 days ago'."""
    if not text:
        return None
    text = text.strip().lower()
    now = datetime.now(timezone.utc)
    if "just" in text or "today" in text or "moment" in text:
        return now
    m = re.search(r'(\d+)\s*day', text)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r'(\d+)\s*hour', text)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r'(\d+)\s*minute', text)
    if m:
        return now - timedelta(minutes=int(m.group(1)))
    # "30+ days ago" etc.
    if "30+" in text:
        return now - timedelta(days=30)
    return None


def fetch_indeed(config: dict, query: str, max_age_hours: int) -> list[Job]:
    """Scrape Indeed's public job search page."""
    location = config["profile"]["location"]
    fromage = math.ceil(max_age_hours / 24)

    params = {
        "q": query,
        "l": location,
        "sort": "date",
        "fromage": str(fromage),
    }
    url = f"https://www.indeed.com/jobs?{urllib.parse.urlencode(params)}"
    raw = _get(url, headers={"Referer": "https://www.indeed.com/"})
    if not raw:
        return []

    soup = BeautifulSoup(raw, "html.parser")
    jobs = []

    # Indeed job cards use various container selectors
    for card in soup.select(
        'div.job_seen_beacon, div.cardOutline, div.result, '
        'div[data-jk], li[data-jk], td.resultContent'
    ):
        # Title
        title_el = card.select_one(
            'h2.jobTitle a span, h2.jobTitle span, h2.jobTitle a, '
            'a[data-jk] span, a.jcs-JobTitle span'
        )
        # Company name
        company_el = card.select_one(
            'span[data-testid="company-name"], span.company, '
            'span.companyName, a.companyName, '
            'a[data-tn-element="companyName"]'
        )
        # Location
        location_el = card.select_one(
            'div[data-testid="text-location"], div.companyLocation, '
            'span.companyLocation, div.location, span.location'
        )
        # Salary
        salary_el = card.select_one(
            'div.salary-snippet, span.salary-snippet, '
            'div[data-testid="attribute_snippet_testid"], '
            'div.metadata.salary-snippet-container, '
            'span.estimated-salary, div.salaryOnly'
        )
        # Date
        date_el = card.select_one(
            'span.date, span[data-testid="myJobsStateDate"], '
            'span.visually-hidden'
        )
        # Link
        link_el = card.select_one(
            'h2.jobTitle a, a[data-jk], a.jcs-JobTitle, a[id^="job_"]'
        )

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""

        job_url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            if href.startswith("/"):
                job_url = f"https://www.indeed.com{href}"
            elif href.startswith("http"):
                job_url = href
            else:
                job_url = f"https://www.indeed.com/{href}"
            # Clean tracking params but keep the job key
            job_url = job_url.split("&")[0] if "&" in job_url else job_url

        posted = None
        if date_el:
            posted = _parse_indeed_date(date_el.get_text())

        # Parse salary from snippet using the same regex pattern
        sal_min, sal_max = None, None
        if salary_el:
            salary_text = salary_el.get_text(strip=True)
            sal_match = re.search(
                r'\$(\d{2,3}(?:,\d{3})+)\s*(?:[-\u2013\u2014to]+|and)\s*\$?(\d{2,3}(?:,\d{3})+)',
                salary_text
            )
            if sal_match:
                lo = int(sal_match.group(1).replace(",", ""))
                hi = int(sal_match.group(2).replace(",", ""))
                if lo >= 50000 and hi >= 50000:
                    sal_min, sal_max = lo, hi

        if not title or not company:
            continue

        jobs.append(Job(
            title=title,
            company=company,
            location=loc,
            url=job_url,
            source="indeed",
            posted_at=posted,
            salary_min=sal_min,
            salary_max=sal_max,
            remote="remote" in loc.lower(),
        ))

    time.sleep(1.0)  # Indeed is stricter about rate limiting
    return jobs


# -- Greenhouse boards --

def fetch_greenhouse(config: dict, query: str, max_age_hours: int) -> list[Job]:
    """Fetch from Greenhouse board APIs - public JSON, no auth.

    Boards are fetched once and cached to avoid redundant API calls across
    multiple title queries.  The relevance filter uses ALL title_queries
    (not just the current one) so every call returns the same superset.
    """
    companies = config["sources"]["greenhouse"].get("companies", [])
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    # Build keyword set from ALL title queries so every invocation returns
    # the same result.  This lets the main loop call us N times without
    # wasting N-1 redundant HTTP requests (dedup catches the duplicates).
    all_queries = config["profile"].get("title_queries", [query])
    kw_set = set()
    for q in all_queries:
        for w in q.lower().split():
            if len(w) > 3:
                kw_set.add(w)

    # Use module-level cache so repeated calls within the same process
    # skip the network entirely.
    cache = getattr(fetch_greenhouse, "_cache", {})

    all_jobs = []
    for company_slug in companies:
        if company_slug in cache:
            data = cache[company_slug]
        else:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
            data = _api_get(url)
            cache[company_slug] = data
            time.sleep(0.3)  # Be polite

        if not data:
            continue

        company_name = data.get("meta", {}).get("name") or company_slug.replace("-", " ").title()

        for item in data.get("jobs", []):
            title = item.get("title", "")
            title_lower = title.lower()

            # Basic relevance filter
            if not any(w in title_lower for w in kw_set):
                continue

            created = _parse_date(item.get("first_published") or item.get("created_at"))
            updated = _parse_date(item.get("updated_at"))
            posted = created or updated
            if posted and posted < cutoff:
                continue

            loc = ""
            loc_data = item.get("location", {})
            if isinstance(loc_data, dict):
                loc = loc_data.get("name", "")
            elif isinstance(loc_data, str):
                loc = loc_data

            job_url = item.get("absolute_url", "")

            # Extract description text from HTML content field
            desc = ""
            sal_min, sal_max = None, None
            content_html = item.get("content", "")
            if content_html:
                # Greenhouse content may be double-encoded HTML entities;
                # first parse decodes &lt; -> <, second parse extracts text.
                decoded = html_mod.unescape(content_html)
                full_text = BeautifulSoup(decoded, "html.parser").get_text(separator=" ", strip=True)
                desc = full_text[:2000]
                # Extract salary from full text (salary is often at the end)
                sal_match = re.search(
                    r'\$(\d{2,3}(?:,\d{3})+)\s*(?:[-–—to]+|and)\s*\$?(\d{2,3}(?:,\d{3})+)',
                    full_text
                )
                if sal_match:
                    lo = int(sal_match.group(1).replace(",", ""))
                    hi = int(sal_match.group(2).replace(",", ""))
                    if lo >= 50000 and hi >= 50000:
                        sal_min, sal_max = lo, hi

            all_jobs.append(Job(
                title=title,
                company=company_name,
                location=loc,
                url=job_url,
                source="greenhouse",
                posted_at=posted,
                created_at=created,
                updated_at=updated,
                salary_min=sal_min,
                salary_max=sal_max,
                description=desc,
                remote="remote" in loc.lower(),
            ))

    fetch_greenhouse._cache = cache
    return all_jobs


# -- Lever boards --

def fetch_lever(config: dict, query: str, max_age_hours: int) -> list[Job]:
    """Fetch from Lever posting APIs - public JSON, no auth."""
    companies = config["sources"]["lever"].get("companies", [])
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    query_words = [w.lower() for w in query.split() if len(w) > 3]
    all_jobs = []

    for company_slug in companies:
        url = f"https://api.lever.co/v0/postings/{company_slug}"
        data = _api_get(url)
        if not data or not isinstance(data, list):
            continue

        for item in data:
            title = item.get("text", "")
            title_lower = title.lower()

            if not any(w in title_lower for w in query_words):
                continue

            posted = _parse_date(item.get("createdAt"))
            if posted and posted < cutoff:
                continue

            categories = item.get("categories", {})
            loc = categories.get("location", "")
            team = categories.get("team", "")
            commitment = categories.get("commitment", "")
            company_name = item.get("company", company_slug.replace("-", " ").title())

            desc = item.get("descriptionPlain", "")
            lists_text = ""
            for lst in item.get("lists", []):
                lists_text += " ".join(lst.get("content", ""))

            all_jobs.append(Job(
                title=title,
                company=company_name,
                location=loc,
                url=item.get("hostedUrl", ""),
                source="lever",
                posted_at=posted,
                description=(desc + " " + lists_text)[:2000],
                job_type=commitment,
                remote="remote" in loc.lower(),
            ))

        time.sleep(0.3)

    return all_jobs


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_job(job: Job, config: dict) -> Job:
    profile = config["profile"]
    search = config["search"]
    breakdown = {}

    title_lower = job.title.lower()
    desc_lower = (job.description + " " + job.title).lower()

    # Title relevance (0-35)
    title_score = 0
    for q in profile["title_queries"]:
        words = q.lower().split()
        matches = sum(1 for w in words if w in title_lower)
        ratio = matches / len(words) if words else 0
        title_score = max(title_score, int(ratio * 35))
    breakdown["title"] = title_score

    # Skills match (0-35)
    skills_score = 0
    strong = profile["skills"]["strong"]
    moderate = profile["skills"]["moderate"]
    familiar = profile["skills"]["familiar"]
    matched_skills = []
    for s in strong:
        if s.lower() in desc_lower:
            matched_skills.append(s)
    for s in moderate:
        if s.lower() in desc_lower:
            matched_skills.append(s)
    for s in familiar:
        if s.lower() in desc_lower:
            matched_skills.append(s)
    strong_matches = sum(1 for s in strong if s.lower() in desc_lower)
    moderate_matches = sum(1 for s in moderate if s.lower() in desc_lower)
    familiar_matches = sum(1 for s in familiar if s.lower() in desc_lower)
    if strong:
        skills_score += int((strong_matches / len(strong)) * 20)
    if moderate:
        skills_score += int((moderate_matches / len(moderate)) * 10)
    if familiar:
        skills_score += int((familiar_matches / len(familiar)) * 5)
    breakdown["skills"] = min(35, skills_score)
    job.matched_skills = matched_skills

    # Salary (0-15)
    salary_score = 0
    min_sal = profile.get("min_salary", 0)
    max_sal = profile.get("max_salary", 999999)
    if job.salary_min and job.salary_max:
        mid = (job.salary_min + job.salary_max) / 2
        if min_sal <= mid <= max_sal:
            salary_score = 15
        elif job.salary_max >= min_sal:
            salary_score = 8
    elif job.salary_min and job.salary_min >= min_sal:
        salary_score = 10
    elif not job.salary_min and not job.salary_max:
        salary_score = 5
    breakdown["salary"] = salary_score

    # Recency (0-10)
    recency_score = 5
    if job.posted_at:
        hours_old = (datetime.now(timezone.utc) - job.posted_at).total_seconds() / 3600
        if hours_old < 6:
            recency_score = 10
        elif hours_old < 12:
            recency_score = 9
        elif hours_old < 24:
            recency_score = 8
        elif hours_old < 48:
            recency_score = 6
        elif hours_old < 72:
            recency_score = 4
        else:
            recency_score = 2
    breakdown["recency"] = recency_score

    # Boost keywords (0-5)
    boost = 0
    for kw in search.get("boost_keywords", []):
        if kw.lower() in desc_lower:
            boost += 1
    breakdown["boost"] = min(5, boost)

    job.score = sum(breakdown.values())
    job.score_breakdown = breakdown
    return job


# ---------------------------------------------------------------------------
# Filtering & dedup
# ---------------------------------------------------------------------------

def filter_jobs(jobs: list[Job], config: dict, max_age_hours: int) -> list[Job]:
    search = config["search"]
    exclude_companies = [c.lower() for c in search.get("exclude_companies", [])]
    exclude_keywords = [k.lower() for k in search.get("exclude_keywords", [])]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    accepted_locations = [p.lower() for p in search.get("accepted_locations", [])]
    rejected_countries = [c.lower() for c in search.get("rejected_countries", [])]

    filtered = []
    for job in jobs:
        if job.company.lower() in exclude_companies:
            continue
        title_lower = job.title.lower()
        if any(kw in title_lower for kw in exclude_keywords):
            continue
        if job.posted_at and job.posted_at < cutoff:
            continue
        min_sal = config["profile"].get("min_salary", 0)
        if job.salary_max and job.salary_max < min_sal * 0.8:
            continue
        # Location filter: keep jobs matching accepted patterns, or with no location
        if accepted_locations and job.location:
            loc_lower = job.location.lower()
            if not any(pattern in loc_lower for pattern in accepted_locations):
                continue
            # Reject locations containing foreign country names
            if rejected_countries and any(c in loc_lower for c in rejected_countries):
                continue
        filtered.append(job)
    return filtered


def _normalize_for_dedup(title: str, company: str, location: str) -> tuple[str, str, str]:
    """Normalize title, company, and location for fuzzy deduplication.

    Returns (norm_title, norm_company, norm_location) all lowercased and stripped.
    """
    # --- Title normalization ---
    t = title.lower().strip()
    # Expand common abbreviations (use lookahead instead of \b after optional period)
    title_abbrevs = {
        r'\bsr\.?(?=\s|$)': 'senior',
        r'\bjr\.?(?=\s|$)': 'junior',
        r'\beng\.?(?=\s|$)': 'engineer',
        r'\bmgr\.?(?=\s|$)': 'manager',
        r'\bdev\.?(?=\s|$)': 'developer',
        r'\bswe(?=\s|$)': 'software engineer',
        r'\bml(?=\s|$)': 'machine learning',
    }
    for pattern, replacement in title_abbrevs.items():
        t = re.sub(pattern, replacement, t)
    # Strip parenthetical suffixes like (Remote), (NYC), (Hybrid)
    t = re.sub(r'\s*\([^)]*\)\s*$', '', t)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    # --- Company normalization ---
    c = company.lower().strip()
    # Strip corporate suffixes (use lookahead instead of \b after optional period)
    c = re.sub(r',?\s*\b(inc\.?|corp\.?|llc\.?|ltd\.?|co\.?|incorporated|corporation|limited|l\.?p\.?|plc)(?=\s|$)', '', c)
    # Strip country/region suffixes like "USA", "US", "Global"
    c = re.sub(r'\s+(usa|u\.s\.a\.?|us|global|international|worldwide)\s*$', '', c)
    c = re.sub(r'\s+', ' ', c).strip()

    # --- Location normalization ---
    loc = location.lower().strip()
    # US state name -> abbreviation mapping
    state_abbrevs = {
        'alabama': 'al', 'alaska': 'ak', 'arizona': 'az', 'arkansas': 'ar',
        'california': 'ca', 'colorado': 'co', 'connecticut': 'ct', 'delaware': 'de',
        'florida': 'fl', 'georgia': 'ga', 'hawaii': 'hi', 'idaho': 'id',
        'illinois': 'il', 'indiana': 'in', 'iowa': 'ia', 'kansas': 'ks',
        'kentucky': 'ky', 'louisiana': 'la', 'maine': 'me', 'maryland': 'md',
        'massachusetts': 'ma', 'michigan': 'mi', 'minnesota': 'mn',
        'mississippi': 'ms', 'missouri': 'mo', 'montana': 'mt', 'nebraska': 'ne',
        'nevada': 'nv', 'new hampshire': 'nh', 'new jersey': 'nj',
        'new mexico': 'nm', 'new york': 'ny', 'north carolina': 'nc',
        'north dakota': 'nd', 'ohio': 'oh', 'oklahoma': 'ok', 'oregon': 'or',
        'pennsylvania': 'pa', 'rhode island': 'ri', 'south carolina': 'sc',
        'south dakota': 'sd', 'tennessee': 'tn', 'texas': 'tx', 'utah': 'ut',
        'vermont': 'vt', 'virginia': 'va', 'washington': 'wa',
        'west virginia': 'wv', 'wisconsin': 'wi', 'wyoming': 'wy',
        'district of columbia': 'dc',
    }
    # Strip country suffixes (", USA", ", United States", etc.)
    loc = re.sub(r',?\s*(usa|u\.s\.a\.?|united states of america|united states|us)\s*$', '', loc)
    # Replace full state names with abbreviations: "New York, New York" -> "New York, NY"
    # Split on comma, normalize the state part
    parts = [p.strip() for p in loc.split(',')]
    if len(parts) >= 2:
        # Try to match the last part as a state name
        last = parts[-1].strip()
        if last in state_abbrevs:
            parts[-1] = state_abbrevs[last]
        loc = ', '.join(parts)
    # Strip parenthetical suffixes from location too
    loc = re.sub(r'\s*\([^)]*\)\s*', ' ', loc)
    loc = re.sub(r'\s+', ' ', loc).strip()

    return t, c, loc


def _dedup_key(title: str, company: str, location: str) -> str:
    """Generate a dedup hash from normalized title/company/location."""
    t, c, loc = _normalize_for_dedup(title, company, location)
    raw = f"{c}|{t}|{loc}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _job_richness(job: Job) -> int:
    """Score how much data a job listing has (higher = more info)."""
    score = 0
    score += len(job.description)
    if job.salary_min:
        score += 500
    if job.salary_max:
        score += 500
    if job.posted_at:
        score += 200
    if job.job_type:
        score += 100
    if job.matched_skills:
        score += len(job.matched_skills) * 50
    return score


def deduplicate(jobs: list[Job]) -> list[Job]:
    seen = {}
    for job in jobs:
        jid = _dedup_key(job.title, job.company, job.location)
        if jid in seen:
            existing = seen[jid]
            if _job_richness(job) > _job_richness(existing):
                seen[jid] = job
        else:
            seen[jid] = job
    return list(seen.values())


# ---------------------------------------------------------------------------
# Seen jobs tracker
# ---------------------------------------------------------------------------

SEEN_FILE = Path(__file__).parent / ".seen_jobs.json"


def load_seen() -> dict:
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_seen(seen: dict):
    import fcntl
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    pruned = {k: v for k, v in seen.items() if v.get("first_seen", "") > cutoff}
    # Atomic write: write to temp file, then rename (prevents corruption on crash)
    tmp = SEEN_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(pruned, f, indent=2)
    tmp.rename(SEEN_FILE)


def mark_seen(jobs: list[Job], seen: dict) -> list[Job]:
    now = datetime.now(timezone.utc).isoformat()
    for job in jobs:
        jid = job.job_id
        if jid not in seen:
            seen[jid] = {"first_seen": now, "title": job.title, "company": job.company}
    return jobs


def is_new_job(job: Job, seen: dict) -> bool:
    return job.job_id not in seen


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(jobs: list[Job], seen: dict, show_json: bool = False,
                   output_file: str = ""):
    if show_json:
        now = datetime.now(timezone.utc)
        job_list = []
        for j in jobs:
            # Compute freshness tag
            freshness = ""
            if j.posted_at:
                age_h = (now - j.posted_at).total_seconds() / 3600
                if age_h < 1:
                    freshness = "just_posted"
                elif age_h < 6:
                    freshness = "hot"
                elif age_h < 24:
                    freshness = "today"
                elif age_h < 48:
                    freshness = "yesterday"

            job_list.append({
                "title": j.title, "company": j.company, "location": j.location,
                "salary": j.salary_display, "posted": j.age_display,
                "salary_min": j.salary_min, "salary_max": j.salary_max,
                "score": j.score, "url": j.url, "source": j.source,
                "new": is_new_job(j, seen),
                "freshness": freshness,
                "score_breakdown": j.score_breakdown,
                "matched_skills": j.matched_skills,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "updated_at": j.updated_at.isoformat() if j.updated_at else None,
                "posted_at": j.posted_at.isoformat() if j.posted_at else None,
            })
        if output_file:
            output = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total": len(job_list),
                "new_count": sum(1 for j in job_list if j["new"]),
                "jobs": job_list,
            }
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(json.dumps(output, indent=2))
            _log(f"  Wrote {len(job_list)} jobs to {output_file}")
        else:
            print(json.dumps(job_list, indent=2))
        return

    if not jobs:
        print("\nNo matching jobs found. Try increasing --max-age or lowering --min-score.")
        return

    new_count = sum(1 for j in jobs if is_new_job(j, seen))
    print(f"\n{'=' * 80}")
    print(f" Found {len(jobs)} matching jobs ({new_count} new)")
    print(f"{'=' * 80}\n")

    for i, job in enumerate(jobs, 1):
        new_tag = " [NEW]" if is_new_job(job, seen) else ""
        print(f"  {i:2d}. [{job.score:3d}/100]{new_tag} {job.title}")
        print(f"      {job.company} | {job.location}")
        print(f"      Salary: {job.salary_display} | Posted: {job.age_display} | Via: {job.source}")
        print(f"      {job.url}")
        bd = job.score_breakdown
        print(f"      Score: title={bd.get('title', 0)} skills={bd.get('skills', 0)} "
              f"salary={bd.get('salary', 0)} recency={bd.get('recency', 0)} "
              f"boost={bd.get('boost', 0)}")
        print()

    print(f"{'=' * 80}")
    print(f"  Tip: Apply to [NEW] jobs ASAP for the best chance.")
    print(f"{'=' * 80}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SOURCE_FETCHERS = {
    "linkedin": fetch_linkedin,
    "indeed": fetch_indeed,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
}

ALERT_THRESHOLD = 50


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"Error: config not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Search for matching jobs")
    parser.add_argument("--max-age", type=int, help="Max job age in hours")
    parser.add_argument("--min-score", type=int, help="Min match score 0-100")
    parser.add_argument("--max-results", type=int, help="Max results to show")
    parser.add_argument("--source", choices=list(SOURCE_FETCHERS.keys()), help="Single source")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--output", type=str, help="Write JSON to file (with metadata)")
    parser.add_argument("--no-track", action="store_true", help="Don't update seen tracker")
    parser.add_argument("--alert", action="store_true", help="Alert mode")
    parser.add_argument("--alert-threshold", type=int, default=ALERT_THRESHOLD)
    args = parser.parse_args()

    config = load_config()
    max_age = args.max_age or config["search"]["max_age_hours"]
    min_score = args.min_score if args.min_score is not None else config["search"]["min_score"]
    max_results = args.max_results or config["search"]["max_results"]
    quiet = args.alert

    if not quiet and not args.json:
        print(f"\nSearching for jobs (posted within {max_age}h, score >= {min_score})...")

    all_jobs = []
    for source_name, fetcher in SOURCE_FETCHERS.items():
        if args.source and source_name != args.source:
            continue
        if not config["sources"].get(source_name, {}).get("enabled", False):
            continue
        if not quiet and not args.json:
            print(f"  Querying {source_name}...")

        for query in config["profile"]["title_queries"]:
            try:
                jobs = fetcher(config, query, max_age)
                all_jobs.extend(jobs)
            except Exception as e:
                _log(f"  [{source_name}] Error for '{query}': {e}")

    if not quiet and not args.json:
        print(f"  Raw results: {len(all_jobs)}")

    all_jobs = deduplicate(all_jobs)
    if not quiet and not args.json:
        print(f"  After dedup: {len(all_jobs)}")

    all_jobs = filter_jobs(all_jobs, config, max_age)
    if not quiet and not args.json:
        print(f"  After filters: {len(all_jobs)}")

    all_jobs = [score_job(j, config) for j in all_jobs]
    all_jobs = [j for j in all_jobs if j.score >= min_score]
    all_jobs.sort(
        key=lambda j: (j.score, j.posted_at or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )
    all_jobs = all_jobs[:max_results]

    seen = load_seen()
    new_high = [j for j in all_jobs if is_new_job(j, seen) and j.score >= args.alert_threshold]

    out = args.output or ""
    if args.alert:
        if new_high:
            notify_jobs(new_high, args.alert_threshold)
            print_results(new_high, seen, show_json=args.json, output_file=out)
    else:
        print_results(all_jobs, seen, show_json=args.json, output_file=out)
        if new_high:
            notify_jobs(new_high, args.alert_threshold)

    if not args.no_track:
        mark_seen(all_jobs, seen)
        save_seen(seen)


if __name__ == "__main__":
    main()
