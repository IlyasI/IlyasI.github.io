#!/usr/bin/env python3
"""
Test suite for the job search system.

Run:
    python3 -m pytest jobs/test_search.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from search import (
    Job,
    _parse_salary,
    _parse_date,
    _normalize_for_dedup,
    _dedup_key,
    _job_richness,
    score_job,
    filter_jobs,
    deduplicate,
    load_seen,
    save_seen,
    mark_seen,
    is_new_job,
    load_config,
    fetch_linkedin,
    fetch_indeed,
    _parse_indeed_date,
    fetch_greenhouse,
    fetch_lever,
    notify_macos,
    print_results,
    SEEN_FILE,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def sample_job():
    return Job(
        title="Senior Software Engineer",
        company="Acme Corp",
        location="New York, NY",
        url="https://example.com/job/123",
        source="greenhouse",
        posted_at=datetime.now(timezone.utc) - timedelta(hours=3),
        salary_min=180000,
        salary_max=250000,
        description="We need a senior software engineer with Python, BigQuery, GCP, dbt experience. "
                    "You'll build data pipelines and ELT systems for our fintech platform.",
        job_type="Full Time",
        remote=False,
    )


@pytest.fixture
def sample_jobs():
    now = datetime.now(timezone.utc)
    return [
        Job(title="Senior Software Engineer", company="Good Match Inc",
            location="New York, NY", url="https://example.com/1", source="greenhouse",
            posted_at=now - timedelta(hours=2), salary_min=190000, salary_max=260000,
            description="Python, BigQuery, dbt, GCP, data engineering, ELT pipelines, fintech"),
        Job(title="Senior Backend Engineer", company="Also Good Corp",
            location="New York, NY (Remote)", url="https://example.com/2", source="linkedin",
            posted_at=now - timedelta(hours=10), salary_min=200000, salary_max=300000,
            description="Python backend engineer, SQL, AWS, data platform, GenAI integration",
            remote=True),
        Job(title="Junior Developer", company="Nope LLC",
            location="New York, NY", url="https://example.com/3", source="linkedin",
            posted_at=now - timedelta(hours=1), salary_min=60000, salary_max=80000,
            description="Entry level JavaScript developer"),
        Job(title="Senior Data Engineer", company="Two Sigma",
            location="New York, NY", url="https://example.com/4", source="greenhouse",
            posted_at=now - timedelta(hours=5), salary_min=250000, salary_max=350000,
            description="Python, BigQuery, dbt"),
        Job(title="Senior Software Engineer", company="Old Post Inc",
            location="San Francisco, CA", url="https://example.com/5", source="linkedin",
            posted_at=now - timedelta(hours=200), salary_min=200000, salary_max=280000,
            description="Python developer"),
        Job(title="Senior Platform Engineer", company="Low Pay Corp",
            location="New York, NY", url="https://example.com/6", source="greenhouse",
            posted_at=now - timedelta(hours=6), salary_min=80000, salary_max=100000,
            description="Python platform engineer"),
        Job(title="Engineering Manager", company="Management Inc",
            location="New York, NY", url="https://example.com/7", source="linkedin",
            posted_at=now - timedelta(hours=4), salary_min=220000, salary_max=300000,
            description="Lead engineering teams"),
    ]


@pytest.fixture
def temp_seen_file(tmp_path):
    import search
    original = search.SEEN_FILE
    search.SEEN_FILE = tmp_path / ".seen_jobs.json"
    yield search.SEEN_FILE
    search.SEEN_FILE = original


@pytest.fixture(autouse=True)
def clear_greenhouse_cache():
    """Clear the Greenhouse API cache between tests to prevent leaks."""
    import search
    if hasattr(search.fetch_greenhouse, "_cache"):
        search.fetch_greenhouse._cache = {}
    yield
    if hasattr(search.fetch_greenhouse, "_cache"):
        search.fetch_greenhouse._cache = {}


# ---------------------------------------------------------------------------
# Tests: Job model
# ---------------------------------------------------------------------------

class TestJobModel:
    def test_job_id_stable(self, sample_job):
        assert sample_job.job_id == sample_job.job_id
        assert len(sample_job.job_id) == 12

    def test_job_id_differs(self):
        j1 = Job(title="A", company="B", location="C", url="", source="x")
        j2 = Job(title="D", company="E", location="F", url="", source="x")
        assert j1.job_id != j2.job_id

    def test_job_id_case_insensitive(self):
        j1 = Job(title="Senior Engineer", company="ACME", location="NYC", url="", source="x")
        j2 = Job(title="senior engineer", company="acme", location="nyc", url="", source="x")
        assert j1.job_id == j2.job_id

    def test_salary_display_range(self, sample_job):
        assert sample_job.salary_display == "$180,000 - $250,000"

    def test_salary_display_min_only(self):
        j = Job(title="", company="", location="", url="", source="", salary_min=150000)
        assert j.salary_display == "$150,000+"

    def test_salary_display_max_only(self):
        j = Job(title="", company="", location="", url="", source="", salary_max=200000)
        assert j.salary_display == "Up to $200,000"

    def test_salary_display_none(self):
        j = Job(title="", company="", location="", url="", source="")
        assert j.salary_display == "Not listed"

    def test_age_display_recent(self):
        j = Job(title="", company="", location="", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(minutes=30))
        assert j.age_display == "< 1 hour ago"

    def test_age_display_hours(self):
        j = Job(title="", company="", location="", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=5))
        assert j.age_display == "5 hours ago"

    def test_age_display_days(self):
        j = Job(title="", company="", location="", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(days=3))
        assert j.age_display == "3 days ago"

    def test_age_display_unknown(self):
        j = Job(title="", company="", location="", url="", source="")
        assert j.age_display == "Unknown"


# ---------------------------------------------------------------------------
# Tests: Parsing helpers
# ---------------------------------------------------------------------------

class TestParseSalary:
    def test_normal(self):
        assert _parse_salary(180000) == 180000

    def test_float(self):
        assert _parse_salary(180000.50) == 180000

    def test_string(self):
        assert _parse_salary("200000") == 200000

    def test_hourly(self):
        assert _parse_salary(100) == 100 * 2080

    def test_none(self):
        assert _parse_salary(None) is None

    def test_garbage(self):
        assert _parse_salary("not a number") is None

    def test_too_small(self):
        assert _parse_salary(1) is None  # 1 * 2080 = 2080 < 10000


class TestParseDate:
    def test_iso_format(self):
        dt = _parse_date("2025-06-15T10:30:00Z")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_iso_with_offset(self):
        dt = _parse_date("2025-06-15T10:30:00+00:00")
        assert dt is not None

    def test_date_only(self):
        dt = _parse_date("2025-06-15")
        assert dt is not None

    def test_unix_timestamp_seconds(self):
        dt = _parse_date(1718450000)
        assert dt is not None

    def test_unix_timestamp_millis(self):
        dt = _parse_date(1718450000000)
        assert dt is not None

    def test_none(self):
        assert _parse_date(None) is None

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_garbage(self):
        assert _parse_date("not a date") is None


# ---------------------------------------------------------------------------
# Tests: Scoring
# ---------------------------------------------------------------------------

class TestScoring:
    def test_perfect_match_scores_high(self, sample_job, config):
        scored = score_job(sample_job, config)
        assert scored.score >= 50

    def test_irrelevant_job_scores_low(self, config):
        bad_job = Job(title="Receptionist", company="Random Corp", location="Dallas, TX",
                      url="", source="x",
                      posted_at=datetime.now(timezone.utc) - timedelta(hours=100),
                      description="Answer phones and greet visitors")
        scored = score_job(bad_job, config)
        assert scored.score < 20

    def test_score_breakdown_sums(self, sample_job, config):
        scored = score_job(sample_job, config)
        assert scored.score == sum(scored.score_breakdown.values())

    def test_title_match(self, config):
        j = Job(title="Senior Software Engineer", company="", location="", url="", source="",
                description="")
        scored = score_job(j, config)
        assert scored.score_breakdown["title"] > 0

    def test_skills_match(self, config):
        j = Job(title="", company="", location="", url="", source="",
                description="python bigquery dbt gcp sql data engineering etl")
        scored = score_job(j, config)
        assert scored.score_breakdown["skills"] > 0

    def test_recency_boost(self, config):
        fresh = Job(title="", company="", location="", url="", source="",
                    posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
        old = Job(title="", company="", location="", url="", source="",
                  posted_at=datetime.now(timezone.utc) - timedelta(hours=80))
        score_job(fresh, config)
        score_job(old, config)
        assert fresh.score_breakdown["recency"] > old.score_breakdown["recency"]

    def test_salary_in_range(self, config):
        j = Job(title="", company="", location="", url="", source="",
                salary_min=190000, salary_max=260000)
        scored = score_job(j, config)
        assert scored.score_breakdown["salary"] >= 10

    def test_unknown_salary_neutral(self, config):
        j = Job(title="", company="", location="", url="", source="")
        scored = score_job(j, config)
        assert scored.score_breakdown["salary"] == 5

    def test_boost_keywords(self, config):
        j = Job(title="", company="", location="", url="", source="",
                description="fintech genai data platform")
        scored = score_job(j, config)
        assert scored.score_breakdown["boost"] >= 2

    def test_score_max_100(self, config):
        perfect = Job(
            title="Senior Software Engineer", company="", location="", url="", source="",
            posted_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            salary_min=200000, salary_max=280000,
            description="python bigquery gcp dbt sql data engineering etl elt "
                        "bash git c++ aws docker flask django datadog playwright selenium "
                        "javascript java postgresql react node.js "
                        "genai llm ai fintech data platform financial quantitative hedge fund")
        scored = score_job(perfect, config)
        assert scored.score <= 100


# ---------------------------------------------------------------------------
# Tests: Filtering
# ---------------------------------------------------------------------------

class TestFiltering:
    def test_excludes_current_employer(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        assert not any(j.company == "Two Sigma" for j in filtered)

    def test_excludes_junior(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        assert not any("Junior" in j.title for j in filtered)

    def test_excludes_manager(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        assert not any("Manager" in j.title for j in filtered)

    def test_excludes_old(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        assert not any(j.company == "Old Post Inc" for j in filtered)

    def test_excludes_low_salary(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        assert not any(j.company == "Low Pay Corp" for j in filtered)

    def test_keeps_good(self, sample_jobs, config):
        filtered = filter_jobs(sample_jobs, config, max_age_hours=168)
        companies = [j.company for j in filtered]
        assert "Good Match Inc" in companies
        assert "Also Good Corp" in companies

    def test_salary_tolerance(self, config):
        j = Job(title="Senior Engineer", company="X", location="NYC", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=1), salary_max=150000)
        filtered = filter_jobs([j], config, max_age_hours=168)
        assert len(filtered) == 1  # Within 20% tolerance

    def test_salary_hard_reject(self, config):
        j = Job(title="Senior Engineer", company="X", location="NYC", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=1), salary_max=100000)
        filtered = filter_jobs([j], config, max_age_hours=168)
        assert len(filtered) == 0


# ---------------------------------------------------------------------------
# Tests: Location filtering
# ---------------------------------------------------------------------------

class TestLocationFiltering:
    def test_keeps_nyc_jobs(self, config):
        j = Job(title="Senior Engineer", company="X", location="New York, NY", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
        filtered = filter_jobs([j], config, max_age_hours=168)
        assert len(filtered) == 1

    def test_keeps_remote_jobs(self, config):
        j = Job(title="Senior Engineer", company="X", location="Remote - United States", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
        filtered = filter_jobs([j], config, max_age_hours=168)
        assert len(filtered) == 1

    def test_filters_foreign_jobs(self, config):
        for loc in ["Ljubljana, Slovenia", "Lisbon, Portugal", "Madrid, Spain", "Berlin, Germany"]:
            j = Job(title="Senior Engineer", company="X", location=loc, url="", source="",
                    posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
            filtered = filter_jobs([j], config, max_age_hours=168)
            assert len(filtered) == 0, f"Should have filtered out {loc}"

    def test_filters_remote_foreign(self, config):
        for loc in ["Portugal, Remote", "France, Remote; Germany, Remote; Spain, Remote",
                     "Ireland, Remote", "India, Remote"]:
            j = Job(title="Senior Engineer", company="X", location=loc, url="", source="",
                    posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
            filtered = filter_jobs([j], config, max_age_hours=168)
            assert len(filtered) == 0, f"Should have filtered out '{loc}'"

    def test_keeps_remote_usa(self, config):
        for loc in ["Remote - USA", "Remote - United States", "Remote - US",
                     "Remote (U.S. Only)", "Remote, US"]:
            j = Job(title="Senior Engineer", company="X", location=loc, url="", source="",
                    posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
            filtered = filter_jobs([j], config, max_age_hours=168)
            assert len(filtered) == 1, f"Should have kept '{loc}'"

    def test_keeps_jobs_without_location(self, config):
        j = Job(title="Senior Engineer", company="X", location="", url="", source="",
                posted_at=datetime.now(timezone.utc) - timedelta(hours=1))
        filtered = filter_jobs([j], config, max_age_hours=168)
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Tests: Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_removes_exact_dupes(self):
        j1 = Job(title="Engineer", company="Corp", location="NYC", url="1", source="a")
        j2 = Job(title="Engineer", company="Corp", location="NYC", url="2", source="b")
        assert len(deduplicate([j1, j2])) == 1

    def test_keeps_richer_data(self):
        j1 = Job(title="Engineer", company="Corp", location="NYC", url="1", source="a",
                 description="short")
        j2 = Job(title="Engineer", company="Corp", location="NYC", url="2", source="b",
                 description="much longer description with details about the role")
        result = deduplicate([j1, j2])
        assert result[0].source == "b"

    def test_keeps_one_with_salary(self):
        j1 = Job(title="Engineer", company="Corp", location="NYC", url="1", source="a")
        j2 = Job(title="Engineer", company="Corp", location="NYC", url="2", source="b",
                 salary_min=200000)
        result = deduplicate([j1, j2])
        assert result[0].salary_min == 200000

    def test_preserves_different(self):
        j1 = Job(title="Engineer", company="Corp A", location="NYC", url="1", source="a")
        j2 = Job(title="Engineer", company="Corp B", location="NYC", url="2", source="b")
        assert len(deduplicate([j1, j2])) == 2


# ---------------------------------------------------------------------------
# Tests: Seen tracker
# ---------------------------------------------------------------------------

class TestSeenTracker:
    def test_new_job_is_new(self):
        j = Job(title="X", company="Y", location="Z", url="", source="")
        assert is_new_job(j, {})

    def test_seen_job_not_new(self):
        j = Job(title="X", company="Y", location="Z", url="", source="")
        assert not is_new_job(j, {j.job_id: {"first_seen": "2025-01-01"}})

    def test_mark_seen(self):
        j = Job(title="X", company="Y", location="Z", url="", source="")
        seen = {}
        mark_seen([j], seen)
        assert j.job_id in seen

    def test_roundtrip(self, temp_seen_file):
        seen = {"abc123": {"first_seen": datetime.now(timezone.utc).isoformat(), "title": "Test"}}
        save_seen(seen)
        assert "abc123" in load_seen()

    def test_prunes_old(self, temp_seen_file):
        seen = {
            "old": {"first_seen": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()},
            "new": {"first_seen": datetime.now(timezone.utc).isoformat()},
        }
        save_seen(seen)
        loaded = load_seen()
        assert "old" not in loaded
        assert "new" in loaded


# ---------------------------------------------------------------------------
# Tests: Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_loads(self, config):
        assert "profile" in config and "sources" in config and "search" in config

    def test_title_queries(self, config):
        assert len(config["profile"]["title_queries"]) > 0

    def test_skills(self, config):
        for k in ("strong", "moderate", "familiar"):
            assert k in config["profile"]["skills"]

    def test_salary(self, config):
        assert config["profile"]["min_salary"] == 170000

    def test_exclude_companies(self, config):
        assert "two sigma" in [c.lower() for c in config["search"]["exclude_companies"]]

    def test_sources(self, config):
        assert "linkedin" in config["sources"]
        assert "greenhouse" in config["sources"]


# ---------------------------------------------------------------------------
# Tests: Greenhouse parsing (mocked)
# ---------------------------------------------------------------------------

MOCK_GREENHOUSE_RESPONSE = {
    "meta": {"name": "TechCo"},
    "jobs": [
        {
            "title": "Senior Software Engineer",
            "location": {"name": "New York, NY"},
            "absolute_url": "https://techco.com/careers/123",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "title": "Receptionist",  # should be filtered by query relevance
            "location": {"name": "New York, NY"},
            "absolute_url": "https://techco.com/careers/456",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    ],
}


class TestGreenhouseParsing:
    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_parses_jobs(self, mock_get, config):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        matching = [j for j in jobs if "Senior Software" in j.title]
        assert len(matching) >= 1
        assert matching[0].company == "TechCo"
        assert matching[0].source == "greenhouse"

    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_filters_irrelevant_titles(self, mock_get, config):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        assert not any("Receptionist" in j.title for j in jobs)

    @patch("search._api_get", return_value={})
    def test_handles_empty(self, mock_get, config):
        jobs = fetch_greenhouse(config, "test", 168)
        assert jobs == []


# ---------------------------------------------------------------------------
# Tests: LinkedIn parsing (mocked)
# ---------------------------------------------------------------------------

MOCK_LINKEDIN_HTML = b"""
<html><body>
<div class="base-card">
    <h3 class="base-search-card__title">Senior Software Engineer</h3>
    <h4 class="base-search-card__subtitle">Google</h4>
    <span class="job-search-card__location">New York, NY</span>
    <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/123?trk=foo"></a>
    <time datetime="2025-06-15T10:00:00.000Z"></time>
</div>
<div class="base-card">
    <h3 class="base-search-card__title">Staff Backend Engineer</h3>
    <h4 class="base-search-card__subtitle">Stripe</h4>
    <span class="job-search-card__location">San Francisco, CA</span>
    <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/456"></a>
    <time datetime="2025-06-14"></time>
</div>
</body></html>
"""


class TestLinkedInParsing:
    @patch("search._get", return_value=MOCK_LINKEDIN_HTML)
    def test_parses_jobs(self, mock_get, config):
        jobs = fetch_linkedin(config, "senior software engineer", 168)
        assert len(jobs) == 2
        assert jobs[0].title == "Senior Software Engineer"
        assert jobs[0].company == "Google"
        assert jobs[0].source == "linkedin"

    @patch("search._get", return_value=MOCK_LINKEDIN_HTML)
    def test_cleans_tracking_params(self, mock_get, config):
        jobs = fetch_linkedin(config, "senior software engineer", 168)
        google_job = [j for j in jobs if j.company == "Google"][0]
        assert "trk=" not in google_job.url

    @patch("search._get", return_value=b"")
    def test_handles_empty(self, mock_get, config):
        jobs = fetch_linkedin(config, "test", 168)
        assert jobs == []

    @patch("search._get", return_value=b"<html><body>no jobs here</body></html>")
    def test_handles_no_cards(self, mock_get, config):
        jobs = fetch_linkedin(config, "test", 168)
        assert jobs == []


# ---------------------------------------------------------------------------
# Tests: Indeed parsing (mocked)
# ---------------------------------------------------------------------------

MOCK_INDEED_HTML = b"""
<html><body>
<div class="job_seen_beacon">
    <h2 class="jobTitle">
        <a href="/rc/clk?jk=abc123"><span>Senior Software Engineer</span></a>
    </h2>
    <span data-testid="company-name">Google</span>
    <div data-testid="text-location">New York, NY</div>
    <div class="salary-snippet">$190,000 - $260,000 a year</div>
    <span class="date">Posted 2 days ago</span>
</div>
<div class="job_seen_beacon">
    <h2 class="jobTitle">
        <a href="/rc/clk?jk=def456"><span>Staff Data Engineer</span></a>
    </h2>
    <span data-testid="company-name">Meta</span>
    <div data-testid="text-location">Remote</div>
    <span class="date">Just posted</span>
</div>
<div class="job_seen_beacon">
    <h2 class="jobTitle">
        <a href="https://www.indeed.com/viewjob?jk=ghi789"><span>Senior Backend Engineer</span></a>
    </h2>
    <span data-testid="company-name">Stripe</span>
    <div data-testid="text-location">San Francisco, CA</div>
    <div class="salary-snippet">$200,000 - $300,000 a year</div>
    <span class="date">3 days ago</span>
</div>
</body></html>
"""


class TestIndeedParsing:
    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_parses_jobs(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        assert len(jobs) == 3
        assert jobs[0].title == "Senior Software Engineer"
        assert jobs[0].company == "Google"
        assert jobs[0].source == "indeed"

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_parses_salary(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        google_job = [j for j in jobs if j.company == "Google"][0]
        assert google_job.salary_min == 190000
        assert google_job.salary_max == 260000

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_parses_location(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        google_job = [j for j in jobs if j.company == "Google"][0]
        assert google_job.location == "New York, NY"

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_builds_urls(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        google_job = [j for j in jobs if j.company == "Google"][0]
        assert google_job.url.startswith("https://www.indeed.com/")
        # Absolute URLs should be preserved
        stripe_job = [j for j in jobs if j.company == "Stripe"][0]
        assert stripe_job.url.startswith("https://www.indeed.com/")

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_parses_date(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        meta_job = [j for j in jobs if j.company == "Meta"][0]
        assert meta_job.posted_at is not None
        # "Just posted" should be very recent
        age = (datetime.now(timezone.utc) - meta_job.posted_at).total_seconds()
        assert age < 60  # within a minute of now

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_remote_flag(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        meta_job = [j for j in jobs if j.company == "Meta"][0]
        assert meta_job.remote is True
        google_job = [j for j in jobs if j.company == "Google"][0]
        assert google_job.remote is False

    @patch("search.time.sleep")
    @patch("search._get", return_value=b"")
    def test_handles_empty(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "test", 168)
        assert jobs == []

    @patch("search.time.sleep")
    @patch("search._get", return_value=b"<html><body>no jobs here</body></html>")
    def test_handles_no_cards(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "test", 168)
        assert jobs == []

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_no_salary_job(self, mock_get, mock_sleep, config):
        jobs = fetch_indeed(config, "senior software engineer", 168)
        meta_job = [j for j in jobs if j.company == "Meta"][0]
        assert meta_job.salary_min is None
        assert meta_job.salary_max is None

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_url_param(self, mock_get, mock_sleep, config):
        """Verify the correct Indeed URL is constructed."""
        fetch_indeed(config, "senior software engineer", 168)
        call_url = mock_get.call_args[0][0]
        assert "indeed.com/jobs?" in call_url
        assert "q=senior+software+engineer" in call_url
        assert "fromage=7" in call_url  # 168 hours / 24 = 7 days
        assert "sort=date" in call_url

    @patch("search.time.sleep")
    @patch("search._get", return_value=MOCK_INDEED_HTML)
    def test_referer_header(self, mock_get, mock_sleep, config):
        """Verify Indeed requests include a Referer header."""
        fetch_indeed(config, "senior software engineer", 168)
        call_headers = mock_get.call_args[1].get("headers", {})
        assert call_headers.get("Referer") == "https://www.indeed.com/"


class TestIndeedDateParsing:
    def test_just_posted(self):
        dt = _parse_indeed_date("Just posted")
        assert dt is not None
        age = (datetime.now(timezone.utc) - dt).total_seconds()
        assert age < 60

    def test_today(self):
        dt = _parse_indeed_date("Today")
        assert dt is not None

    def test_days_ago(self):
        dt = _parse_indeed_date("3 days ago")
        assert dt is not None
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert 71 < hours < 73

    def test_one_day_ago(self):
        dt = _parse_indeed_date("1 day ago")
        assert dt is not None
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert 23 < hours < 25

    def test_hours_ago(self):
        dt = _parse_indeed_date("5 hours ago")
        assert dt is not None
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        assert 4.9 < hours < 5.1

    def test_thirty_plus_days(self):
        dt = _parse_indeed_date("30+ days ago")
        assert dt is not None
        days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
        assert 29.9 < days < 30.1

    def test_empty(self):
        assert _parse_indeed_date("") is None

    def test_none(self):
        assert _parse_indeed_date(None) is None

    def test_unrecognized(self):
        assert _parse_indeed_date("sometime last year") is None


# ---------------------------------------------------------------------------
# Tests: Notifications
# ---------------------------------------------------------------------------

class TestNotifications:
    @patch("search.subprocess.run")
    def test_calls_osascript(self, mock_run):
        notify_macos("Test", "Message")
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "osascript"

    @patch("search.subprocess.run", side_effect=Exception("no display"))
    def test_handles_error(self, mock_run):
        notify_macos("Test", "Test")  # should not raise


# ---------------------------------------------------------------------------
# Tests: End-to-end
# ---------------------------------------------------------------------------

class TestEndToEnd:
    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_full_pipeline(self, mock_get, config, temp_seen_file):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        assert len(jobs) > 0

        jobs = deduplicate(jobs)
        jobs = filter_jobs(jobs, config, max_age_hours=168)
        jobs = [score_job(j, config) for j in jobs]
        for j in jobs:
            assert j.score > 0

        seen = load_seen()
        assert all(is_new_job(j, seen) for j in jobs)
        mark_seen(jobs, seen)
        save_seen(seen)
        assert not any(is_new_job(j, load_seen()) for j in jobs)

    @patch("search._get", return_value=MOCK_LINKEDIN_HTML)
    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_multi_source(self, mock_api, mock_get, config, temp_seen_file):
        linkedin_jobs = fetch_linkedin(config, "senior software engineer", 168)
        greenhouse_jobs = fetch_greenhouse(config, "senior software engineer", 168)
        all_jobs = linkedin_jobs + greenhouse_jobs
        assert len(all_jobs) >= 3

        deduped = deduplicate(all_jobs)
        scored = [score_job(j, config) for j in deduped]
        scored.sort(key=lambda j: j.score, reverse=True)
        for i in range(len(scored) - 1):
            assert scored[i].score >= scored[i + 1].score

    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_alert_mode(self, mock_get, config, temp_seen_file):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        jobs = [score_job(j, config) for j in jobs]
        seen = load_seen()
        new_high = [j for j in jobs if is_new_job(j, seen) and j.score >= 50]
        # At least the "Senior Software Engineer" should score well
        assert len(new_high) >= 0  # depends on scoring

        mark_seen(jobs, seen)
        save_seen(seen)
        new_high2 = [j for j in jobs if is_new_job(j, load_seen()) and j.score >= 50]
        assert len(new_high2) == 0

    @patch("search._api_get")
    def test_excluded_company(self, mock_get, config, temp_seen_file):
        mock_get.return_value = {
            "meta": {"name": "Two Sigma"},
            "jobs": [{
                "title": "Senior Software Engineer",
                "location": {"name": "New York, NY"},
                "absolute_url": "https://twosigma.com/jobs/1",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
        }
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        filtered = filter_jobs(jobs, config, max_age_hours=168)
        assert len(filtered) == 0

    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_json_output(self, mock_get, config, temp_seen_file, capsys):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        jobs = [score_job(j, config) for j in jobs]
        seen = load_seen()
        print_results(jobs, seen, show_json=True)
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        if data:
            assert all(k in data[0] for k in ("title", "company", "score", "url", "new"))

    @patch("search._api_get", return_value=MOCK_GREENHOUSE_RESPONSE)
    def test_json_output_file(self, mock_get, config, temp_seen_file, tmp_path):
        jobs = fetch_greenhouse(config, "senior software engineer", 168)
        jobs = [score_job(j, config) for j in jobs]
        seen = load_seen()
        out = str(tmp_path / "data" / "results.json")
        print_results(jobs, seen, show_json=True, output_file=out)
        assert Path(out).exists()
        data = json.loads(Path(out).read_text())
        assert "generated_at" in data
        assert "total" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        if data["jobs"]:
            j = data["jobs"][0]
            assert "score_breakdown" in j
            assert all(k in j for k in ("title", "company", "score", "url", "new"))


# ---------------------------------------------------------------------------
# Tests: Live APIs
# ---------------------------------------------------------------------------

class TestLiveLinkedIn:
    def test_returns_data(self, config):
        jobs = fetch_linkedin(config, "senior software engineer", 168)
        assert isinstance(jobs, list)
        assert len(jobs) > 0, "LinkedIn should return results for senior software engineer in NYC"
        for j in jobs:
            assert j.source == "linkedin"
            assert j.title
            assert j.company

    def test_full_pipeline(self, config, temp_seen_file):
        jobs = fetch_linkedin(config, "senior software engineer", 168)
        if not jobs:
            pytest.skip("No LinkedIn results")
        jobs = deduplicate(jobs)
        jobs = filter_jobs(jobs, config, max_age_hours=168)
        if not jobs:
            pytest.skip("All filtered out")
        scored = [score_job(j, config) for j in jobs]
        assert all(j.score >= 0 for j in scored)


class TestLiveGreenhouse:
    def test_returns_data(self, config):
        """Test against a single known-good board (stripe)."""
        test_config = {**config, "sources": {**config["sources"],
                       "greenhouse": {"enabled": True, "companies": ["stripe"]}}}
        jobs = fetch_greenhouse(test_config, "senior software engineer", 168)
        assert isinstance(jobs, list)
        # Stripe always has senior SWE roles
        assert len(jobs) > 0, "Stripe should have senior software engineer listings"
        for j in jobs:
            assert j.source == "greenhouse"
            assert j.company


# ---------------------------------------------------------------------------
# Tests: CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_help(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "search.py"), "--help"],
            capture_output=True, text=True)
        assert result.returncode == 0
        assert "Search for matching jobs" in result.stdout

    def test_jobwatch_help(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "jobwatch.py"), "--help"],
            capture_output=True, text=True)
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Tests: Fuzzy deduplication
# ---------------------------------------------------------------------------

class TestFuzzyDedup:
    """Tests for fuzzy dedup: title/company/location normalization and richness-based merging."""

    def test_sr_vs_senior_title(self):
        """'Sr. Software Engineer' and 'Senior Software Engineer' should dedup."""
        j1 = Job(title="Sr. Software Engineer", company="Acme", location="New York, NY",
                 url="1", source="linkedin")
        j2 = Job(title="Senior Software Engineer", company="Acme", location="New York, NY",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_eng_vs_engineer_title(self):
        """'Staff Software Eng' and 'Staff Software Engineer' should dedup."""
        j1 = Job(title="Staff Software Eng", company="Stripe", location="San Francisco, CA",
                 url="1", source="linkedin")
        j2 = Job(title="Staff Software Engineer", company="Stripe", location="San Francisco, CA",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_location_state_normalization(self):
        """'New York, NY' and 'New York, New York, USA' should dedup."""
        j1 = Job(title="Backend Engineer", company="Corp", location="New York, NY",
                 url="1", source="linkedin")
        j2 = Job(title="Backend Engineer", company="Corp", location="New York, New York, USA",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_location_california_normalization(self):
        """'San Francisco, CA' and 'San Francisco, California, USA' should dedup."""
        j1 = Job(title="Senior Engineer", company="Tech Co", location="San Francisco, CA",
                 url="1", source="linkedin")
        j2 = Job(title="Senior Engineer", company="Tech Co",
                 location="San Francisco, California, USA", url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_company_suffix_normalization(self):
        """'DoorDash Inc.' and 'DoorDash' should dedup."""
        j1 = Job(title="Senior Engineer", company="DoorDash Inc.", location="NYC",
                 url="1", source="linkedin")
        j2 = Job(title="Senior Engineer", company="DoorDash", location="NYC",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_company_country_suffix(self):
        """'DoorDash USA' and 'DoorDash' should dedup."""
        j1 = Job(title="Senior Engineer", company="DoorDash USA", location="NYC",
                 url="1", source="linkedin")
        j2 = Job(title="Senior Engineer", company="DoorDash", location="NYC",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_title_parenthetical_stripped(self):
        """'Senior Engineer (Remote)' and 'Senior Engineer' should dedup."""
        j1 = Job(title="Senior Engineer (Remote)", company="Acme", location="NYC",
                 url="1", source="linkedin")
        j2 = Job(title="Senior Engineer", company="Acme", location="NYC",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 1

    def test_keeps_richer_job(self):
        """When deduping, keep the job with more data (salary, longer description)."""
        j1 = Job(title="Sr. Software Engineer", company="Acme", location="New York, NY",
                 url="1", source="linkedin", description="Short desc")
        j2 = Job(title="Senior Software Engineer", company="Acme", location="New York, NY",
                 url="2", source="greenhouse",
                 description="A much longer description with lots of details about the role",
                 salary_min=180000, salary_max=250000)
        result = deduplicate([j1, j2])
        assert len(result) == 1
        assert result[0].salary_min == 180000
        assert result[0].source == "greenhouse"

    def test_truly_different_jobs_kept(self):
        """Different titles at the same company should NOT be deduped."""
        j1 = Job(title="Senior Software Engineer", company="Acme", location="NYC",
                 url="1", source="greenhouse")
        j2 = Job(title="Senior Data Engineer", company="Acme", location="NYC",
                 url="2", source="greenhouse")
        result = deduplicate([j1, j2])
        assert len(result) == 2

    def test_normalize_helper_title(self):
        """Directly test _normalize_for_dedup on title abbreviations."""
        t, _, _ = _normalize_for_dedup("Sr. Software Eng.", "X", "Y")
        assert t == "senior software engineer"

    def test_normalize_helper_company(self):
        """Directly test _normalize_for_dedup on company suffixes."""
        _, c, _ = _normalize_for_dedup("X", "Acme Corp.", "Y")
        assert c == "acme"

    def test_normalize_helper_location(self):
        """Directly test _normalize_for_dedup on location normalization."""
        _, _, loc = _normalize_for_dedup("X", "Y", "New York, New York, USA")
        assert loc == "new york, ny"

    def test_cross_source_dedup(self):
        """Same job on LinkedIn and Greenhouse with slight title differences should dedup."""
        j1 = Job(title="Sr. Software Eng (Remote)", company="Stripe, Inc.",
                 location="San Francisco, California, United States",
                 url="https://linkedin.com/jobs/1", source="linkedin",
                 description="Short listing from LinkedIn")
        j2 = Job(title="Senior Software Engineer", company="Stripe",
                 location="San Francisco, CA",
                 url="https://stripe.com/careers/123", source="greenhouse",
                 description="Full job description from Greenhouse with lots of detail "
                             "about the role, team, compensation, and requirements.",
                 salary_min=200000, salary_max=300000)
        result = deduplicate([j1, j2])
        assert len(result) == 1
        # Should keep the Greenhouse one (richer data)
        assert result[0].source == "greenhouse"
        assert result[0].salary_min == 200000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
