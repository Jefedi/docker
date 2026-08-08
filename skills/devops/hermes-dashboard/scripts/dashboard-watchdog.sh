#!/bin/bash
# Dashboard watchdog — checks if the Hermes dashboard is alive on its port
# and relaunches it via start-dashboard.sh if it's down.
# Designed to be called by a Hermes cron job every 2 minutes.
# Silent on success (no stdout) — only outputs when it had to restart something.
#
# Usage:
#   bash /opt/data/scripts/dashboard-watchdog.sh
#
# Requirements:
#   - /opt/data/scripts/start-dashboard.sh must exist and be executable
#   - curl available
#   - The dashboard should listen on the port configured below
#
# Setup:
#   1. Place this script at /opt/data/scripts/dashboard-watchdog.sh
#   2. chmod +x it
#   3. Create a Hermes cron job with schedule=2m that runs:
#      bash /opt/data/scripts/dashboard-watchdog.sh
#   4. The cron job should deliver to origin (so restart notifications reach the user)

DASH_PORT="${HERMES_DASHBOARD_PORT:-9120}"
START_SCRIPT="/opt/data/scripts/start-dashboard.sh"
LOG_FILE="/opt/data/logs/dashboard-watchdog.log"

# Check if dashboard is responding
if curl -sS -o /dev/null -m 5 "http://127.0.0.1:${DASH_PORT}/api/status" 2>/dev/null; then
    # Dashboard is alive, nothing to do
    exit 0
fi

# Dashboard is down — kill any stale process on the port, then restart
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dashboard down on port ${DASH_PORT}, restarting..." >> "$LOG_FILE"

# Kill any stale dashboard process (match the exact port to avoid killing wrong processes)
pkill -f "hermes dashboard.*--port ${DASH_PORT}" 2>/dev/null
sleep 1

# Relaunch
export HOME=/opt/data
nohup bash "$START_SCRIPT" >> "$LOG_FILE" 2>&1 &

# Wait and verify
sleep 5
if curl -sS -o /dev/null -m 5 "http://127.0.0.1:${DASH_PORT}/api/status" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dashboard restarted successfully" >> "$LOG_FILE"
    echo "Dashboard was down — restarted OK on port ${DASH_PORT}"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Dashboard failed to restart" >> "$LOG_FILE"
    echo "WARNING: Dashboard failed to restart on port ${DASH_PORT}"
fi