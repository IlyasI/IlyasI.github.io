#!/usr/bin/env python3
"""
JobWatch - macOS menu bar app that monitors job boards and alerts you.

Runs in the background, checks every 4 hours, sends native macOS notifications
when high-scoring jobs appear. Click the menu bar icon to see recent results
or trigger a manual search.

Usage:
    python3 jobs/jobwatch.py          # Launch menu bar app
    python3 jobs/jobwatch.py --once   # Run once and exit (for testing)
"""

import sys
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

# Import the search engine
sys.path.insert(0, str(Path(__file__).parent))
from search import (
    load_config, load_seen, save_seen, mark_seen, is_new_job,
    deduplicate, filter_jobs, score_job, notify_macos, print_results,
    SOURCE_FETCHERS, ALERT_THRESHOLD, _log,
)


SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / ".jobwatch_state.json"
CHECK_INTERVAL = 4 * 60 * 60  # 4 hours in seconds


def run_search(max_age: int = 6, min_score: int = 30, alert_threshold: int = ALERT_THRESHOLD):
    """Run a job search cycle. Returns (all_jobs, new_high_score_jobs)."""
    config = load_config()
    seen = load_seen()

    all_jobs = []
    for source_name, fetcher in SOURCE_FETCHERS.items():
        if not config["sources"].get(source_name, {}).get("enabled", False):
            continue
        for query in config["profile"]["title_queries"]:
            try:
                jobs = fetcher(config, query, max_age)
                all_jobs.extend(jobs)
            except Exception as e:
                _log(f"[{source_name}] Error: {e}")

    all_jobs = deduplicate(all_jobs)
    all_jobs = filter_jobs(all_jobs, config, max_age)
    all_jobs = [score_job(j, config) for j in all_jobs]
    all_jobs = [j for j in all_jobs if j.score >= min_score]
    all_jobs.sort(key=lambda j: j.score, reverse=True)
    all_jobs = all_jobs[:50]

    new_high = [j for j in all_jobs if is_new_job(j, seen) and j.score >= alert_threshold]

    # Capture new-status BEFORE marking seen (otherwise is_new_job returns False for all)
    new_flags = {j.job_id: is_new_job(j, seen) for j in all_jobs}

    # Notify
    if new_high:
        count = len(new_high)
        top = new_high[0]
        if count == 1:
            notify_macos(
                f"Job Match ({top.score}/100)",
                f"{top.title} at {top.company}\n{top.salary_display}",
            )
        else:
            notify_macos(
                f"{count} New Job Matches",
                f"Top: {top.title} at {top.company} ({top.score}/100)",
            )

    # Save state for menu bar display (using pre-mark new flags)
    state = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "total_found": len(all_jobs),
        "new_high_count": len(new_high),
        "top_jobs": [
            {
                "title": j.title,
                "company": j.company,
                "score": j.score,
                "salary": j.salary_display,
                "url": j.url,
                "posted": j.age_display,
                "new": new_flags.get(j.job_id, False),
            }
            for j in all_jobs[:10]
        ],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))

    # Update dashboard JSON (using pre-mark seen dict)
    dashboard_file = str(SCRIPT_DIR / "data" / "results.json")
    try:
        print_results(all_jobs, seen, show_json=True, output_file=dashboard_file)
    except Exception as e:
        _log(f"  Failed to write dashboard JSON: {e}")

    # NOW update tracker (after dashboard/state are written)
    mark_seen(all_jobs, seen)
    save_seen(seen)

    return all_jobs, new_high


def scheduled_loop():
    """Run search on a schedule forever."""
    import time
    while True:
        try:
            _log(f"[{datetime.now().strftime('%H:%M')}] Running scheduled search...")
            all_jobs, new_high = run_search()
            _log(f"  Found {len(all_jobs)} jobs, {len(new_high)} new high-score matches")
        except Exception as e:
            _log(f"  Search error: {e}")
        time.sleep(CHECK_INTERVAL)


def open_url(url: str):
    subprocess.run(["open", url], capture_output=True)


def build_menu_bar_app():
    """Build and run a macOS menu bar app using rumps (if available) or fallback to simple loop."""
    try:
        import rumps
    except ImportError:
        _log("rumps not installed. Running in background-only mode (no menu bar icon).")
        _log("Install with: pip3 install rumps")
        _log("Notifications will still work.")
        scheduled_loop()
        return

    class JobWatchApp(rumps.App):
        def __init__(self):
            super().__init__("JobWatch", icon=None, title="JW")
            self.menu = [
                rumps.MenuItem("Search Now", callback=self.search_now),
                rumps.MenuItem("View All Results", callback=self.view_results),
                None,  # separator
                rumps.MenuItem("Last check: never"),
                rumps.MenuItem("Status: starting..."),
            ]
            # Run first search after a short delay
            self.timer = rumps.Timer(self._scheduled_check, CHECK_INTERVAL)
            self.timer.start()
            # Also run once immediately in background
            threading.Thread(target=self._do_search, daemon=True).start()

        def _scheduled_check(self, _):
            threading.Thread(target=self._do_search, daemon=True).start()

        def _do_search(self):
            try:
                all_jobs, new_high = run_search()
                now = datetime.now().strftime("%I:%M %p")
                self.title = f"JW ({len(new_high)})" if new_high else "JW"
                # Update menu items
                for item in self.menu.values():
                    if hasattr(item, "title"):
                        if item.title.startswith("Last check"):
                            item.title = f"Last check: {now}"
                        elif item.title.startswith("Status"):
                            item.title = f"Status: {len(all_jobs)} jobs found"
            except Exception as e:
                _log(f"Search error: {e}")

        def search_now(self, _):
            self.title = "JW..."
            threading.Thread(target=self._do_search, daemon=True).start()

        def view_results(self, _):
            # Open the terminal with full results
            subprocess.Popen([
                "osascript", "-e",
                f'tell application "Terminal" to do script '
                f'"cd {SCRIPT_DIR.parent} && python3 jobs/search.py --max-age 72"'
            ])

    app = JobWatchApp()
    app.run()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JobWatch - macOS job monitoring app")
    parser.add_argument("--once", action="store_true", help="Run one search and exit")
    parser.add_argument("--no-menubar", action="store_true", help="Run without menu bar (background only)")
    args = parser.parse_args()

    if args.once:
        all_jobs, new_high = run_search()
        print(f"Found {len(all_jobs)} jobs, {len(new_high)} new high-score matches")
        if new_high:
            for j in new_high:
                print(f"  [{j.score}] {j.title} @ {j.company} - {j.url}")
        return

    if args.no_menubar:
        scheduled_loop()
    else:
        build_menu_bar_app()


if __name__ == "__main__":
    main()
