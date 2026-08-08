#!/usr/bin/env bash
set -euo pipefail

# Sync Pangolin docs from https://docs.pangolin.net/llms.txt
# Exit code 1 if any file changed (for cron + notif), 0 if unchanged.
# Exit code 2 on fetch errors.

REF_DIR="$(dirname "$0")/../references"
mkdir -p "$REF_DIR"

INDEX_URL="https://docs.pangolin.net/llms.txt"
TMP_INDEX="$(mktemp)"
TMP_NEW="$(mktemp)"
trap 'rm -f "$TMP_INDEX" "$TMP_NEW"' EXIT

# Fetch index
if ! curl -sf -o "$TMP_INDEX" -H "User-Agent: Hermes-Agent/1.0" "$INDEX_URL"; then
    echo "ERROR: Failed to fetch llms.txt" >&2
    exit 2
fi

# Extract all .md URLs
URLS=$(grep -oP 'https://docs\.pangolin\.net/[^\s)]+\.md' "$TMP_INDEX" | sort -u)
TOTAL=$(echo "$URLS" | wc -l)

echo "Found $TOTAL pages."

CHANGED=0
FAILED=0

while IFS= read -r url; do
    [ -z "$url" ] && continue
    path="${url#https://docs.pangolin.net/}"
    filename="${path//\//__}"
    filepath="$REF_DIR/$filename"

    if ! curl -sf -o "$TMP_NEW" -H "User-Agent: Hermes-Agent/1.0" "$url"; then
        echo "  [FAIL] $url" >&2
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check if content changed (or file is new)
    if [ ! -f "$filepath" ] || ! cmp -s "$TMP_NEW" "$filepath"; then
        cp "$TMP_NEW" "$filepath"
        echo "  [CHANGED] $filename"
        CHANGED=1
    fi

    sleep 0.3
done <<< "$URLS"

echo "Done. Changed=$CHANGED Failed=$FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 2
fi
if [ "$CHANGED" -eq 1 ]; then
    exit 1
fi
exit 0