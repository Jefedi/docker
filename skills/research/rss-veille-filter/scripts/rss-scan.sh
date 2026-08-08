#!/bin/bash
# RSS Scan Script — scans feeds, extracts new articles for agent filtering
# Place at ~/.hermes/scripts/rss-scan.sh and reference by bare filename in cron
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
export BLOGWATCHER_DB="$HOME/.blogwatcher-cli/blogwatcher-cli.db"

# Scan all tracked blogs (silent = suppress per-blog progress)
blogwatcher-cli scan --silent 2>&1

# Get unread articles
ARTICLES=$(blogwatcher-cli articles 2>&1)

# If no articles, exit silently (cron agent gets empty context = no message)
if echo "$ARTICLES" | grep -q "Unread articles (0)"; then
    exit 0
fi

# Output articles between markers for the agent to parse
echo "---ARTICLES_START---"
echo "$ARTICLES"
echo "---ARTICLES_END---"

# Mark all as read AFTER output so next run doesn't re-process
blogwatcher-cli read-all --yes 2>/dev/null