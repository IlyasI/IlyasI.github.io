#!/usr/bin/env python3
"""
Email digest for job search results.

Generates a professional HTML email with top job matches and sends
via Gmail SMTP. Falls back to saving HTML locally if no credentials.

Usage:
    python3 jobs/digest.py              # Send digest of new jobs
    python3 jobs/digest.py --preview    # Save HTML locally, don't send
    python3 jobs/digest.py --all        # Include all jobs, not just new
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yaml


JOBS_DIR = Path(__file__).parent
DATA_DIR = JOBS_DIR / "data"
RESULTS_FILE = DATA_DIR / "results.json"
DIGEST_FILE = JOBS_DIR / ".last-digest.html"
SENT_FILE = JOBS_DIR / ".digest-sent.json"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    config_path = JOBS_DIR / "config.yaml"
    if not config_path.exists():
        print(f"Error: config not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def _get_email(config: dict) -> str:
    """Get email address from env var or config."""
    email = os.environ.get("EMAIL_FROM", "")
    if not email:
        email = config.get("profile", {}).get("email", "")
    return email


# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------

def load_results() -> dict:
    """Load results from the JSON file, or return empty structure."""
    if not RESULTS_FILE.exists():
        return {"generated_at": None, "total": 0, "new_count": 0, "jobs": []}
    try:
        return json.loads(RESULTS_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading results: {e}", file=sys.stderr)
        return {"generated_at": None, "total": 0, "new_count": 0, "jobs": []}


def load_sent_ids() -> set:
    """Load IDs of jobs already included in a previous digest."""
    if not SENT_FILE.exists():
        return set()
    try:
        data = json.loads(SENT_FILE.read_text())
        return set(data.get("sent_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_sent_ids(ids: set):
    """Persist the set of job IDs we've already digested."""
    SENT_FILE.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sent_ids": list(ids),
    }, indent=2))


def _job_id(job: dict) -> str:
    """Deterministic ID matching search.py's Job.job_id logic."""
    import hashlib
    raw = f"{job.get('company', '')}|{job.get('title', '')}|{job.get('location', '')}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def filter_new_jobs(jobs: list[dict], sent_ids: set) -> list[dict]:
    """Return only jobs not previously sent in a digest."""
    return [j for j in jobs if _job_id(j) not in sent_ids]


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _score_color(score: int) -> str:
    if score >= 60:
        return "#4ade80"  # green
    elif score >= 40:
        return "#38bdf8"  # blue
    elif score >= 25:
        return "#facc15"  # yellow
    return "#94a3b8"      # gray


def _escape(text: str) -> str:
    """Basic HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_html(jobs: list[dict], is_new_only: bool = True) -> str:
    """Build the full HTML email body."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")

    # Sort by score descending
    jobs = sorted(jobs, key=lambda j: j.get("score", 0), reverse=True)
    top_10 = jobs[:10]

    # Summary stats
    total = len(jobs)
    avg_score = int(sum(j.get("score", 0) for j in jobs) / total) if total else 0

    # Most common company
    company_counts: dict[str, int] = {}
    for j in jobs:
        c = j.get("company", "Unknown")
        company_counts[c] = company_counts.get(c, 0) + 1
    top_company = max(company_counts, key=company_counts.get) if company_counts else "N/A"

    label = "new" if is_new_only else "total"

    # Build job rows
    job_rows = ""
    for job in top_10:
        score = job.get("score", 0)
        color = _score_color(score)
        title = _escape(job.get("title", "Untitled"))
        company = _escape(job.get("company", "Unknown"))
        location = _escape(job.get("location", ""))
        salary = _escape(job.get("salary", "Not listed"))
        url = job.get("url", "#")
        posted = _escape(job.get("posted", ""))
        source = _escape(job.get("source", ""))
        matched = job.get("matched_skills", []) or []

        # Skill tags
        skill_tags = ""
        for skill in matched[:8]:
            skill_tags += (
                f'<span style="display:inline-block;background:#1e293b;color:#94a3b8;'
                f'padding:2px 8px;border-radius:10px;font-size:11px;margin:2px 3px 2px 0;'
                f'border:1px solid #334155;">{_escape(skill)}</span>'
            )

        job_rows += f"""
        <tr>
          <td style="padding:16px 20px;border-bottom:1px solid #1e293b;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td width="50" valign="top" style="padding-right:14px;">
                  <div style="background:{color}22;border:2px solid {color};border-radius:8px;
                              width:44px;height:44px;text-align:center;line-height:44px;
                              font-size:16px;font-weight:700;color:{color};">
                    {score}
                  </div>
                </td>
                <td valign="top">
                  <a href="{url}" style="color:#e2e8f0;font-size:15px;font-weight:600;
                     text-decoration:none;">{title}</a>
                  <div style="color:#94a3b8;font-size:13px;margin-top:4px;">
                    {company} &middot; {location}
                  </div>
                  <div style="color:#64748b;font-size:12px;margin-top:3px;">
                    {salary} &middot; {posted} &middot; via {source}
                  </div>
                  {"<div style='margin-top:6px;'>" + skill_tags + "</div>" if skill_tags else ""}
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    # Remaining count
    remaining = total - len(top_10)
    remaining_row = ""
    if remaining > 0:
        remaining_row = f"""
        <tr>
          <td style="padding:14px 20px;text-align:center;color:#64748b;font-size:13px;
                     border-bottom:1px solid #1e293b;">
            + {remaining} more job{"s" if remaining != 1 else ""} below the top 10
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#050810;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background-color:#050810;padding:20px 0;">
    <tr>
      <td align="center">
        <table cellpadding="0" cellspacing="0" border="0" width="600"
               style="max-width:600px;background-color:#0a0e18;border-radius:12px;
                      border:1px solid #1e293b;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0f172a,#1e293b);padding:28px 24px;
                       text-align:center;">
              <div style="font-size:22px;font-weight:700;color:#e2e8f0;">
                Job Alert
              </div>
              <div style="font-size:13px;color:#64748b;margin-top:4px;">
                {date_str}
              </div>
            </td>
          </tr>

          <!-- Stats bar -->
          <tr>
            <td style="padding:0;">
              <table cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="33%" style="text-align:center;padding:16px 8px;
                                         border-bottom:1px solid #1e293b;">
                    <div style="font-size:24px;font-weight:700;color:#38bdf8;">{total}</div>
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                                letter-spacing:1px;margin-top:2px;">{label} matches</div>
                  </td>
                  <td width="34%" style="text-align:center;padding:16px 8px;
                                         border-bottom:1px solid #1e293b;
                                         border-left:1px solid #1e293b;
                                         border-right:1px solid #1e293b;">
                    <div style="font-size:24px;font-weight:700;color:#4ade80;">{avg_score}</div>
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                                letter-spacing:1px;margin-top:2px;">avg score</div>
                  </td>
                  <td width="33%" style="text-align:center;padding:16px 8px;
                                         border-bottom:1px solid #1e293b;">
                    <div style="font-size:14px;font-weight:600;color:#e2e8f0;
                                line-height:1.3;">{_escape(top_company)}</div>
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                                letter-spacing:1px;margin-top:2px;">top company</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Section header -->
          <tr>
            <td style="padding:18px 20px 8px;color:#94a3b8;font-size:12px;
                       text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">
              Top matches
            </td>
          </tr>

          <!-- Job list -->
{job_rows}
{remaining_row}

          <!-- Footer -->
          <tr>
            <td style="padding:20px 24px;text-align:center;border-top:1px solid #1e293b;">
              <div style="color:#475569;font-size:12px;">
                Configure search criteria in config.yaml
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return html


def build_subject(jobs: list[dict], is_new_only: bool = True) -> str:
    """Build the email subject line."""
    total = len(jobs)
    label = "new match" if total == 1 else "new matches"
    if not is_new_only:
        label = "match" if total == 1 else "matches"
    top = sorted(jobs, key=lambda j: j.get("score", 0), reverse=True)
    if top:
        best = top[0]
        return f"Job Alert: {total} {label} (top: {best.get('company', '?')} - {best.get('title', '?')})"
    return f"Job Alert: {total} {label}"


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

def send_email(subject: str, html: str, to_email: str):
    """Send an HTML email via Gmail SMTP."""
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not password:
        raise RuntimeError("GMAIL_APP_PASSWORD env var not set")
    if not to_email:
        raise RuntimeError("No email address configured (set EMAIL_FROM or add email to config.yaml)")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = to_email
    msg["To"] = to_email

    # Plain text fallback
    plain = f"{subject}\n\nView the full digest in your email client (HTML required)."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(to_email, password)
        server.sendmail(to_email, to_email, msg.as_string())


# ---------------------------------------------------------------------------
# Public API (used by app.py)
# ---------------------------------------------------------------------------

def generate_digest(include_all: bool = False) -> tuple[str, str, list[dict]]:
    """Generate digest and return (subject, html, jobs_included).

    If include_all is False, only new (not previously digested) jobs
    are included.  Returns the jobs that made it into the digest.
    """
    results = load_results()
    all_jobs = results.get("jobs", [])

    if not all_jobs:
        return ("Job Alert: 0 new matches", "<p>No results found. Run a search first.</p>", [])

    if include_all:
        jobs = all_jobs
        is_new_only = False
    else:
        sent_ids = load_sent_ids()
        jobs = filter_new_jobs(all_jobs, sent_ids)
        is_new_only = True

    if not jobs:
        return ("Job Alert: 0 new matches", "<p>No new jobs since the last digest.</p>", [])

    subject = build_subject(jobs, is_new_only=is_new_only)
    html = generate_html(jobs, is_new_only=is_new_only)
    return subject, html, jobs


def send_digest(include_all: bool = False) -> dict:
    """Generate and send the digest email. Returns a status dict."""
    config = _load_config()
    email = _get_email(config)

    subject, html, jobs = generate_digest(include_all=include_all)

    if not jobs:
        return {"status": "skipped", "reason": "no new jobs", "count": 0}

    password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not password or not email:
        # Fallback: save locally
        DIGEST_FILE.write_text(html)
        reason = "no GMAIL_APP_PASSWORD" if not password else "no email configured"
        print(f"No email credentials ({reason}). Saved digest to {DIGEST_FILE}")
        return {
            "status": "saved_locally",
            "file": str(DIGEST_FILE),
            "count": len(jobs),
            "subject": subject,
        }

    try:
        send_email(subject, html, email)
    except Exception as e:
        # On failure, still save locally
        DIGEST_FILE.write_text(html)
        return {"status": "error", "error": str(e), "file": str(DIGEST_FILE), "count": len(jobs)}

    # Mark jobs as sent
    sent_ids = load_sent_ids()
    for job in jobs:
        sent_ids.add(_job_id(job))
    save_sent_ids(sent_ids)

    return {"status": "sent", "to": email, "count": len(jobs), "subject": subject}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Job search email digest")
    parser.add_argument("--preview", action="store_true",
                        help="Save HTML locally instead of sending")
    parser.add_argument("--all", action="store_true", dest="include_all",
                        help="Include all jobs, not just new ones")
    args = parser.parse_args()

    if args.preview:
        subject, html, jobs = generate_digest(include_all=args.include_all)
        if not jobs:
            print("No jobs to include in digest.")
            return
        DIGEST_FILE.write_text(html)
        print(f"Subject: {subject}")
        print(f"Jobs: {len(jobs)}")
        print(f"Saved to: {DIGEST_FILE}")
        return

    result = send_digest(include_all=args.include_all)
    status = result.get("status", "unknown")

    if status == "sent":
        print(f"Digest sent to {result['to']} ({result['count']} jobs)")
        print(f"Subject: {result['subject']}")
    elif status == "saved_locally":
        print(f"Digest saved to {result['file']} ({result['count']} jobs)")
        print(f"Subject: {result['subject']}")
    elif status == "skipped":
        print(f"Skipped: {result['reason']}")
    elif status == "error":
        print(f"Send failed: {result['error']}", file=sys.stderr)
        print(f"HTML saved to: {result['file']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
