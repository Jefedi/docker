#!/bin/bash
# ntfy notification sender for Hermes Agent
# Usage: notify.sh "Title" "Message" [priority]
# Priority: urgent, high, default, low, min
# URLs in the message are automatically converted to ntfy action buttons

# Read config
TOPIC="hermes-agent-jefe"
NTFY_URL="https://ntfy.jefe.ovh"
PASSWORD_FILE="/opt/data/.ntfy_token"

# Get password from Vaultwarden if not cached
if [ ! -f "$PASSWORD_FILE" ]; then
  bw get password 15936e06-d49b-48d1-8768-7435af4ae15f > "$PASSWORD_FILE" 2>/dev/null || {
    echo "FATAL: ntfy password not found in Vaultwarden"
    exit 1
  }
  chmod 600 "$PASSWORD_FILE"
fi
PASSWORD=$(cat "$PASSWORD_FILE")

TITLE="${1:-Hermes Agent}"
MESSAGE="${2:-Notification}"
PRIORITY="${3:-default}"
TAGS=""

case "$PRIORITY" in
  urgent|high) TAGS="warning" ;;
  low|min)     TAGS="information_source" ;;
  *)           TAGS="" ;;
esac

# --- Auto-convert URLs to ntfy action buttons ---
# Extract unique URLs from message, build Actions header, strip URLs from body
ACTIONS=""
URLS=$(echo "$MESSAGE" | grep -oE 'https?://[^[:space:]]+' | sed 's/[.,;:)]*$//g' | awk '!seen[$0]++')
if [ -n "$URLS" ]; then
  ACTION_LIST=""
  COUNT=0
  while IFS= read -r url; do
    [ $COUNT -ge 5 ] && break  # ntfy max 5 action buttons
    DOMAIN=$(echo "$url" | sed -E 's|https?://([^/]+).*|\1|')
    if [ -z "$ACTION_LIST" ]; then
      ACTION_LIST="view, $DOMAIN, $url"
    else
      ACTION_LIST="$ACTION_LIST; view, $DOMAIN, $url"
    fi
    COUNT=$((COUNT + 1))
  done <<< "$URLS"
  ACTIONS="$ACTION_LIST"
  # Remove converted URLs from message body for cleaner notification
  MESSAGE=$(echo "$MESSAGE" | sed -E 's|https?://[^[:space:]]+[.,;:)]*||g' | sed 's/[[:space:]]*$//' | sed '/^[[:space:]]*$/d')
fi

# Send notification
RESP=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $PASSWORD" \
  -H "Title: $TITLE" \
  -H "Priority: $PRIORITY" \
  ${TAGS:+-H "Tags: $TAGS"} \
  ${ACTIONS:+-H "Actions: $ACTIONS"} \
  -d "$MESSAGE" \
  "$NTFY_URL/$TOPIC" 2>/dev/null)

HTTP_CODE=$(echo "$RESP" | tail -1)
[ "$HTTP_CODE" = "200" ] && exit 0 || { echo "FATAL: ntfy notification failed (HTTP $HTTP_CODE)"; exit 1; }