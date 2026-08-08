#!/usr/bin/env bash
set -euo pipefail

# Hermes backup script — sync /opt/data to GitHub private repo
# Exits 0 if no changes, 1 if changes pushed, 2 on error.

export PATH="$HOME/.local/bin:$PATH"

cd /opt/data

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "ERROR: gh CLI not authenticated" >&2
    exit 2
fi

# Stage all changes (respect .gitignore)
git add -A 2>/dev/null || true

# Check if there are changes
if git diff --cached --quiet; then
    echo "No changes to backup."
    exit 0
fi

# Show what changed
CHANGED=$(git diff --cached --name-only | wc -l)
echo "$CHANGED files changed"

# Commit
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
git commit -m "Auto backup ${TIMESTAMP}" 2>/dev/null

# Push with timeout (5 minutes max) and proper error detection
PUSH_OUTPUT=$(timeout 300 git push origin main 2>&1) || PUSH_EXIT=$?
PUSH_EXIT=${PUSH_EXIT:-0}

if [ "$PUSH_EXIT" -eq 124 ]; then
    echo "ERROR: push timed out after 5 minutes" >&2
    exit 2
elif [ "$PUSH_EXIT" -ne 0 ]; then
    echo "ERROR: push failed (exit $PUSH_EXIT)" >&2
    echo "$PUSH_OUTPUT" >&2
    exit 2
fi

# Verify push actually succeeded by checking remote tracking
git fetch origin main 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "none")

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "ERROR: local and remote diverge after push (local=$LOCAL remote=$REMOTE)" >&2
    exit 2
fi

echo "Backup pushed: $CHANGED files at ${TIMESTAMP}"
exit 1