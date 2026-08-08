#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Hermes Agent — Live sync to GitHub
# Watches /opt/data for changes and pushes to GitHub in near-real-time.
# Replaces the 12h batch backup cron job.
#
# Strategy:
#   - Poll git status every POLL_INTERVAL seconds
#   - When changes detected, wait DEBOUNCE seconds to group bursts
#   - Commit + push with timeout
#   - Silent on success (no output = nothing happened)
#   - Only prints when something is pushed or on error
#
# Designed to run as a background process (terminal background=true).
# ============================================================

export PATH="$HOME/.local/bin:$PATH"
cd /opt/data

POLL_INTERVAL=10      # seconds between status checks
DEBOUNCE=15           # seconds to wait after first change before committing
PUSH_TIMEOUT=120      # max seconds for git push
MIN_INTERVAL=30       # minimum seconds between pushes (rate limit safety)

LAST_PUSH_EPOCH=0

log() {
    # Only log to stderr so stdout stays clean
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] $*" >&2
}

do_sync() {
    # Stage all changes (respect .gitignore)
    git add -A 2>/dev/null || true

    # Check if there are staged changes
    if git diff --cached --quiet 2>/dev/null; then
        return 0  # no changes
    fi

    local changed
    changed=$(git diff --cached --name-only | wc -l)
    local timestamp
    timestamp=$(date -u +'%Y-%m-%d %H:%M:%S UTC')

    # Commit
    git commit -m "Live sync ${timestamp}" 2>/dev/null || return 0

    # Push with timeout
    local push_output push_exit=0
    push_output=$(timeout "$PUSH_TIMEOUT" git push origin main 2>&1) || push_exit=$?

    if [ "$push_exit" -eq 124 ]; then
        log "ERROR: push timed out after ${PUSH_TIMEOUT}s"
        return 1
    elif [ "$push_exit" -ne 0 ]; then
        log "ERROR: push failed (exit $push_exit)"
        log "$push_output"
        return 1
    fi

    log "Pushed $changed files — ${timestamp}"
    return 0
}

log "Live sync started — polling every ${POLL_INTERVAL}s, debounce ${DEBOUNCE}s"

while true; do
    # Check for changes
    if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
        # Also check for untracked files (not in .gitignore)
        if [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
            sleep "$POLL_INTERVAL"
            continue
        fi
    fi

    # Changes detected — debounce: wait for more changes to settle
    log "Changes detected, waiting ${DEBOUNCE}s to settle..."
    sleep "$DEBOUNCE"

    # Rate limit: ensure minimum interval between pushes
    now=$(date +%s)
    elapsed=$((now - LAST_PUSH_EPOCH))
    if [ "$elapsed" -lt "$MIN_INTERVAL" ]; then
        wait_time=$((MIN_INTERVAL - elapsed))
        log "Rate limit: waiting ${wait_time}s..."
        sleep "$wait_time"
    fi

    # Do the sync
    if do_sync; then
        LAST_PUSH_EPOCH=$(date +%s)
    else
        # On error, wait longer before retrying
        log "Sync failed, waiting 60s before retry..."
        sleep 60
    fi
done