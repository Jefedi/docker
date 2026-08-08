#!/bin/bash
# ntfy notification sender for Hermes Agent
# Usage: notify.sh "Title" "Message" [priority]
# Priority: urgent, high, default, low, min
#
# Reads credentials from Vaultwarden (self-hosted) or falls back to public ntfy.sh
# Configure by setting NTFY_TOPIC, NTFY_URL, and NTFY_BW_ITEM_ID in environment or script.

# Config — override these per user
NTFY_TOPIC="${NTFY_TOPIC:-hermes-agent-jefe}"
NTFY_URL="${NTFY_URL:-https://ntfy.sh}"
NTFY_BW_ITEM_ID="${NTFY_BW_ITEM_ID:-}"

TITLE="${1:-Hermes Agent}"
MESSAGE="${2:-Notification}"
PRIORITY="${3:-default}"
TAGS=""

case "$PRIORITY" in
  urgent|high) TAGS="warning" ;;
  low|min)     TAGS="information_source" ;;
  *)           TAGS="" ;;
esac

# Build notification headers
HEADERS=(-H "Title: $TITLE" -H "Priority: $PRIORITY")
if [ -n "$TAGS" ]; then HEADERS+=(-H "Tags: $TAGS"); fi

# Auth: Bearer token from cache file, or Vaultwarden fallback
AUTH_ARGS=()
# Priority 1: Bearer token cache file (works in no_agent cron context)
TOKEN_FILE="${NTFY_TOKEN_FILE:-/opt/data/.ntfy_token}"
if [ -f "$TOKEN_FILE" ]; then
  TOKEN=$(cat "$TOKEN_FILE" 2>/dev/null)
  if [ -n "$TOKEN" ]; then
    AUTH_ARGS=(-H "Authorization: Bearer $TOKEN")
  fi
# Priority 2: Vaultwarden dynamic fetch (interactive context only)
elif [ -n "$NTFY_BW_ITEM_ID" ] && command -v bw &>/dev/null; then
  CACHE_FILE="/root/.hermes/.ntfy_pass.txt"
  if [ -f "$CACHE_FILE" ]; then
    PASSWORD=$(cat "$CACHE_FILE" 2>/dev/null)
  else
    PASSWORD=$(bw get password "$NTFY_BW_ITEM_ID" 2>/dev/null)
  fi
  if [ -n "$PASSWORD" ]; then
    AUTH_ARGS=(-u "hermes-agent:$PASSWORD")
  fi
fi
if [ ${#AUTH_ARGS[@]} -gt 0 ]; then HEADERS+=("${AUTH_ARGS[@]}"); fi

# Send notification
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
  "${HEADERS[@]}" \
  -d "$MESSAGE" \
  "$NTFY_URL/$NTFY_TOPIC" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
  exit 0
fi
echo "FATAL: ntfy notification failed (HTTP $HTTP_CODE, URL=$NTFY_URL/$NTFY_TOPIC)"
exit 1