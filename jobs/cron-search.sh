#!/bin/bash
# Cron wrapper for job search - runs every 4 hours, sends macOS alerts for matches.
# Also updates the dashboard JSON so jobs.html stays fresh.
# All sources are free, no API keys needed.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR/.." || exit 1

PYTHON="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"

# Alert mode: notify on new high-score jobs
$PYTHON jobs/search.py \
    --alert \
    --max-age 6 \
    2>> jobs/.search.log

# Update dashboard JSON (full 7-day window)
$PYTHON jobs/search.py \
    --json \
    --no-track \
    --output jobs/data/results.json \
    2>> jobs/.search.log
