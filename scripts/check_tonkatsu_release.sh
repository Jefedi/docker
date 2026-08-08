#!/usr/bin/env bash
# Check tonkatsu_box upstream releases, notify via ntfy on new ones.
# Silent on stdout = nothing to report. ntfy push on new release.

set -euo pipefail

NTFY_URL="https://ntfy.jefe.ovh/hermes-agent-jefe"
STATE_FILE="$HOME/.hermes/scripts/.tonkatsu_last_version"
UPSTREAM="hacan359/tonkatsu_box"

# Fetch latest release
DATA=$(curl -sf "https://api.github.com/repos/$UPSTREAM/releases/latest" 2>/dev/null || true)

if [ -z "$DATA" ]; then
  exit 0  # silent on failure
fi

TAG=$(echo "$DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])" 2>/dev/null || echo "")
DATE=$(echo "$DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['published_at'])" 2>/dev/null || echo "")
BODY=$(echo "$DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['body'][:500])" 2>/dev/null || echo "")

if [ -z "$TAG" ]; then
  exit 0
fi

# Read last known version
LAST=""
if [ -f "$STATE_FILE" ]; then
  LAST=$(cat "$STATE_FILE")
fi

if [ "$TAG" != "$LAST" ]; then
  echo "$TAG" > "$STATE_FILE"

  RELEASE_URL="https://github.com/$UPSTREAM/releases/tag/$TAG"
  MESSAGE="🎮 **Tonkatsu Box — Nouvelle release !**

**$TAG** — publiée le $(date -d "$DATE" '+%d/%m/%Y' 2>/dev/null || echo "$DATE")

**Changelog :**
\`\`\`
$BODY
\`\`\`"

  curl -sf -X POST "$NTFY_URL" \
    -H "Title: Tonkatsu Box $TAG" \
    -H "Tags: package" \
    -H "Priority: 3" \
    -H "Actions: view, Voir la release, $RELEASE_URL" \
    -d "$MESSAGE" > /dev/null 2>&1 || true
fi
