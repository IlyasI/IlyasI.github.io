#!/usr/bin/env python3
"""
Fetch a job description and prepare for application.

Usage:
    python3 jobs/apply.py "Stripe" "https://stripe.com/careers/123"

This script:
1. Fetches the job description from the URL
2. Saves it to jobs/jd-{slug}.txt
3. Adds the company to the tracker (if scripts/tracker.py exists)
4. Opens the URL in the default browser
5. Prints next steps for resume/cover letter generation
"""

import sys
import os
import re
import subprocess
import webbrowser
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 is required. Run: pip3 install beautifulsoup4")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = REPO_ROOT / "jobs"
TRACKER_SCRIPT = REPO_ROOT / "scripts" / "tracker.py"


def slugify(company: str) -> str:
    """Convert company name to a lowercase slug for filenames."""
    return re.sub(r"[^a-z0-9]+", "", company.lower())


def fetch_jd(url: str) -> str:
    """Fetch the job description text from a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    req = Request(url, headers=headers)
    resp = urlopen(req, timeout=30)
    html = resp.read().decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Clean up whitespace: collapse blank lines, strip trailing spaces
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    # Collapse 3+ consecutive newlines into 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def add_to_tracker(company: str, url: str):
    """Try to add the company to the application tracker."""
    if not TRACKER_SCRIPT.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(TRACKER_SCRIPT), "add", company, "Software Engineer", url],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"  Added '{company}' to application tracker.")
    except Exception:
        # Fail gracefully — tracker is optional
        pass


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 jobs/apply.py <company> <url>")
        print('  Example: python3 jobs/apply.py "Stripe" "https://stripe.com/careers/123"')
        sys.exit(1)

    company = sys.argv[1]
    url = sys.argv[2]
    slug = slugify(company)

    print(f"\n=== Applying to {company} ===\n")

    # 1. Fetch and save the job description
    jd_path = JOBS_DIR / f"jd-{slug}.txt"
    print(f"  Fetching job description from {url} ...")
    try:
        jd_text = fetch_jd(url)
        jd_path.write_text(jd_text, encoding="utf-8")
        print(f"  Saved job description to {jd_path.relative_to(REPO_ROOT)}")
    except (URLError, HTTPError) as e:
        print(f"  Warning: Could not fetch JD: {e}")
        print(f"  You can manually save the JD to {jd_path.relative_to(REPO_ROOT)}")

    # 2. Add to tracker
    add_to_tracker(company, url)

    # 3. Open the URL in the browser
    print(f"  Opening {url} in browser ...")
    webbrowser.open(url)

    # 4. Print next steps
    print(f"""
=== Next Steps ===

1. Review the job description in {jd_path.relative_to(REPO_ROOT)}

2. Generate a tailored resume with Claude:
   - Read the JD and resume-clear.tex
   - Create resume-{slug}.tex tailored to this role

3. Build and verify the resume:
   make resume-{slug}
   make verify-ats PDF=Ilyas_Ibragimov_Resume_{company}.pdf TEX=resume-{slug}.tex

4. (Optional) Generate a cover letter:
   - Create cover-{slug}.tex
   make cover-{slug}
   make verify-cover PDF=Ilyas_Ibragimov_Cover_Letter_{company}.pdf TEX=cover-{slug}.tex

5. Update tracker status after applying:
   make tracker-update COMPANY="{company}" STATUS=applied
""")


if __name__ == "__main__":
    main()
