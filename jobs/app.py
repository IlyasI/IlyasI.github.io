#!/usr/bin/env python3
"""
Job Dashboard - Flask backend that integrates the search engine.

Runs the search on a background schedule and serves results via API.
No cron, no LaunchAgent, no static JSON files - this IS the backend.

Usage:
    python3 jobs/app.py                  # Start on port 5001
    python3 jobs/app.py --port 8080      # Custom port
    python3 jobs/app.py --interval 2     # Search every 2 hours
"""

import argparse
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from search import (
    load_config, load_seen, save_seen, mark_seen, is_new_job,
    deduplicate, filter_jobs, score_job, notify_macos,
    SOURCE_FETCHERS, ALERT_THRESHOLD, _log,
)
from digest import generate_digest, send_digest

app = Flask(__name__, static_folder=str(Path(__file__).parent.parent))

TRACKED_FILE = Path(__file__).parent / ".tracked.json"

# ---------------------------------------------------------------------------
# Tracking helpers
# ---------------------------------------------------------------------------

def _load_tracked() -> dict:
    """Load tracked applications from disk."""
    if TRACKED_FILE.exists():
        try:
            return json.loads(TRACKED_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_tracked(data: dict):
    """Persist tracked applications to disk."""
    TRACKED_FILE.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_state = {
    "jobs": [],
    "generated_at": None,
    "total": 0,
    "new_count": 0,
    "status": "starting",
    "last_error": None,
    "search_count": 0,
}
_lock = threading.Lock()


def _run_search():
    """Execute a full search cycle and update in-memory state."""
    config = load_config()
    max_age = config["search"]["max_age_hours"]
    min_score = config["search"]["min_score"]
    max_results = config["search"]["max_results"]

    _log(f"[{datetime.now().strftime('%H:%M')}] Running search...")

    all_jobs = []
    for source_name, fetcher in SOURCE_FETCHERS.items():
        if not config["sources"].get(source_name, {}).get("enabled", False):
            continue
        _log(f"  Querying {source_name}...")
        for query in config["profile"]["title_queries"]:
            try:
                jobs = fetcher(config, query, max_age)
                all_jobs.extend(jobs)
            except Exception as e:
                _log(f"  [{source_name}] Error for '{query}': {e}")

    _log(f"  Raw results: {len(all_jobs)}")
    all_jobs = deduplicate(all_jobs)
    _log(f"  After dedup: {len(all_jobs)}")
    all_jobs = filter_jobs(all_jobs, config, max_age)
    _log(f"  After filters: {len(all_jobs)}")

    all_jobs = [score_job(j, config) for j in all_jobs]
    all_jobs = [j for j in all_jobs if j.score >= min_score]
    all_jobs.sort(
        key=lambda j: (j.score, j.posted_at or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )
    all_jobs = all_jobs[:max_results]

    seen = load_seen()

    now = datetime.now(timezone.utc)
    job_list = []
    for j in all_jobs:
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
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "salary": j.salary_display,
            "posted": j.age_display,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "score": j.score,
            "url": j.url,
            "source": j.source,
            "new": is_new_job(j, seen),
            "freshness": freshness,
            "score_breakdown": j.score_breakdown,
            "matched_skills": j.matched_skills,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None,
        })

    # Notify on new high-score matches
    new_high = [j for j in all_jobs if is_new_job(j, seen) and j.score >= ALERT_THRESHOLD]
    if new_high:
        count = len(new_high)
        top = new_high[0]
        if count == 1:
            notify_macos(f"Job Match ({top.score}/100)",
                         f"{top.title} at {top.company}\n{top.salary_display}")
        else:
            notify_macos(f"{count} New Job Matches",
                         f"Top: {top.title} at {top.company} ({top.score}/100)")

    # Update seen tracker
    mark_seen(all_jobs, seen)
    save_seen(seen)

    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        _state["jobs"] = job_list
        _state["generated_at"] = now
        _state["total"] = len(job_list)
        _state["new_count"] = sum(1 for j in job_list if j["new"])
        _state["status"] = "ok"
        _state["last_error"] = None
        _state["search_count"] += 1

    _log(f"  Done: {len(job_list)} results, {_state['new_count']} new")


def _search_loop(interval_hours: float):
    """Background thread: run search immediately, then on interval."""
    while True:
        try:
            _run_search()
        except Exception as e:
            _log(f"  Search failed: {e}")
            with _lock:
                _state["status"] = "error"
                _state["last_error"] = str(e)
        time.sleep(interval_hours * 3600)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    return send_from_directory(app.static_folder, "jobs.html")


@app.route("/api/jobs")
def api_jobs():
    with _lock:
        return jsonify(_state)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Trigger an immediate search (non-blocking)."""
    threading.Thread(target=_run_search, daemon=True).start()
    return jsonify({"status": "refresh started"})


@app.route("/api/health")
def api_health():
    with _lock:
        return jsonify({
            "status": _state["status"],
            "last_updated": _state["generated_at"],
            "search_count": _state["search_count"],
            "job_count": _state["total"],
        })


# ---------------------------------------------------------------------------
# Tracking routes
# ---------------------------------------------------------------------------

@app.route("/api/track", methods=["POST"])
def api_track():
    """Track a job application."""
    body = request.get_json(force=True)
    job_id = body.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id required"}), 400

    status = body.get("status", "applied")
    valid_statuses = {"applied", "interviewing", "rejected", "offer"}
    if status not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    now = datetime.now(timezone.utc)
    tracked = _load_tracked()

    if job_id in tracked:
        # Update existing entry
        tracked[job_id]["status"] = status
        tracked[job_id]["notes"] = body.get("notes", tracked[job_id].get("notes", ""))
    else:
        # New entry
        applied_at = now.isoformat()
        follow_up_at = (now + timedelta(days=7)).isoformat()
        tracked[job_id] = {
            "status": status,
            "company": body.get("company", ""),
            "title": body.get("title", ""),
            "url": body.get("url", ""),
            "applied_at": applied_at,
            "notes": body.get("notes", ""),
            "follow_up_at": follow_up_at,
        }

    _save_tracked(tracked)
    return jsonify({"ok": True, "tracked": tracked[job_id]})


@app.route("/api/tracked")
def api_tracked():
    """Get all tracked applications."""
    return jsonify(_load_tracked())


@app.route("/api/track/<path:job_id>", methods=["DELETE"])
def api_track_delete(job_id):
    """Remove tracking for a job."""
    tracked = _load_tracked()
    if job_id not in tracked:
        return jsonify({"error": "not found"}), 404
    del tracked[job_id]
    _save_tracked(tracked)
    return jsonify({"ok": True})


@app.route("/api/tracked/followups")
def api_tracked_followups():
    """Return jobs where follow_up_at is in the past and status is still 'applied'."""
    tracked = _load_tracked()
    now = datetime.now(timezone.utc)
    followups = {}
    for job_id, entry in tracked.items():
        if entry.get("status") != "applied":
            continue
        follow_up_at = entry.get("follow_up_at")
        if not follow_up_at:
            continue
        try:
            fut = datetime.fromisoformat(follow_up_at)
            if fut <= now:
                followups[job_id] = entry
        except (ValueError, TypeError):
            continue
    return jsonify(followups)


# ---------------------------------------------------------------------------
# Digest routes
# ---------------------------------------------------------------------------

@app.route("/api/digest/preview")
def api_digest_preview():
    """Return the HTML digest for preview."""
    include_all = request.args.get("all", "").lower() in ("1", "true", "yes")
    subject, html, jobs = generate_digest(include_all=include_all)
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/digest/send", methods=["POST"])
def api_digest_send():
    """Trigger sending the digest email."""
    body = request.get_json(silent=True) or {}
    include_all = body.get("all", False)
    result = send_digest(include_all=include_all)
    status_code = 200 if result["status"] in ("sent", "saved_locally", "skipped") else 500
    return jsonify(result), status_code


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Job Dashboard Server")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--interval", type=float, default=4.0,
                        help="Hours between searches (default: 4)")
    parser.add_argument("--no-search", action="store_true",
                        help="Start server without running search")
    args = parser.parse_args()

    # Start background search thread
    if not args.no_search:
        t = threading.Thread(target=_search_loop, args=(args.interval,), daemon=True)
        t.start()

    print(f"\n  Job Dashboard running at http://localhost:{args.port}")
    print(f"  Search interval: every {args.interval}h")
    print(f"  API: /api/jobs  /api/health  POST /api/refresh")
    print(f"       /api/tracked  /api/tracked/followups")
    print(f"       POST /api/track  DELETE /api/track/<job_id>")
    print(f"       /api/digest/preview  POST /api/digest/send\n")

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
