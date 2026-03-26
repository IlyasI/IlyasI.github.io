#!/bin/bash
# Install Job Dashboard as a macOS LaunchAgent (auto-starts on login).
# Runs the Flask backend which searches every 4 hours and serves the dashboard.
#
# Run: bash jobs/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="com.ilyas.jobdashboard"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
LOG_DIR="$SCRIPT_DIR"
PORT=5001

echo "Installing Job Dashboard..."

# Install dependencies
$PYTHON -m pip install -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Stop old agents
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.ilyas.jobwatch.plist" 2>/dev/null || true

# Create LaunchAgent plist
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>${SCRIPT_DIR}/app.py</string>
        <string>--port</string>
        <string>${PORT}</string>
        <string>--interval</string>
        <string>4</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/.jobdashboard.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/.jobdashboard.stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin</string>
    </dict>
</dict>
</plist>
PLIST

# Load the agent
launchctl load "$PLIST_PATH"

echo ""
echo "Job Dashboard installed and running at http://localhost:${PORT}"
echo "Searches every 4 hours. Sends macOS notifications for high-score matches."
echo ""
echo "Commands:"
echo "  open http://localhost:${PORT}                # Open dashboard"
echo "  curl localhost:${PORT}/api/health            # Health check"
echo "  curl -X POST localhost:${PORT}/api/refresh   # Force refresh"
echo "  launchctl unload $PLIST_PATH                 # Stop"
echo "  bash jobs/uninstall.sh                       # Uninstall"
echo ""
