#!/bin/bash
# Uninstall JobWatch LaunchAgent
PLIST_PATH="$HOME/Library/LaunchAgents/com.ilyas.jobwatch.plist"
launchctl unload "$PLIST_PATH" 2>/dev/null
rm -f "$PLIST_PATH"
echo "JobWatch uninstalled."
