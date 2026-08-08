#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
TMP_DIR="/tmp/ha-docs-sync"
REPO_URL="https://github.com/home-assistant/home-assistant.io.git"
CHANGED=0

echo "=== HA Docs Sync ==="

# Clone shallow
echo "Cloning repo..."
git clone --depth 1 "$REPO_URL" "$TMP_DIR" 2>&1 | tail -3

# Define what to sync
declare -A SOURCES
SOURCES["_docs"]="docs__"
SOURCES["getting-started"]="getting-started__"
SOURCES["installation"]="installation__"
SOURCES["common-tasks"]="common-tasks__"
SOURCES["faq"]="faq__"
SOURCES["_faq"]="faq__"
SOURCES["dashboards"]="dashboards__"
SOURCES["_dashboards"]="dashboards__"
SOURCES["voice_control"]="voice__"
SOURCES["_triggers"]="triggers__"
SOURCES["_conditions"]="conditions__"
SOURCES["_includes"]="includes__"
SOURCES["more-info"]="more-info__"

# Sync each source dir
for src_dir in "${!SOURCES[@]}"; do
  prefix="${SOURCES[$src_dir]}"
  full_src="$TMP_DIR/source/$src_dir"
  [ -d "$full_src" ] || continue

  find "$full_src" -name "*.markdown" -o -name "*.md" | while IFS= read -r f; do
    rel="${f#$full_src/}"
    out="$REF_DIR/${prefix}${rel//\//__}"
    if [ ! -f "$out" ]; then
      mkdir -p "$(dirname "$out")"
      cp "$f" "$out"
      echo "[NEW] $out"
      CHANGED=1
    elif ! cmp -s "$f" "$out"; then
      cp "$f" "$out"
      echo "[CHANGED] $out"
      CHANGED=1
    fi
  done
done

# Sync core domain actions only
CORE_DOMAINS="light switch climate cover media_player vacuum lock alarm_control_panel scene script automation input_boolean input_number input_select input_text input_button input_datetime counter timer todo calendar button number select text sensor binary_sensor device_tracker person zone sun weather homeassistant group template fan humidifier water_heater camera siren lawn_mower"

for domain in $CORE_DOMAINS; do
  for f in "$TMP_DIR/source/_actions/${domain}."*.markdown; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    out="$REF_DIR/actions__$base"
    if [ ! -f "$out" ]; then
      cp "$f" "$out"
      echo "[NEW] actions__$base"
      CHANGED=1
    elif ! cmp -s "$f" "$out"; then
      cp "$f" "$out"
      echo "[CHANGED] actions__$base"
      CHANGED=1
    fi
  done
done

# Clean up
rm -rf "$TMP_DIR"

# Skip gotchas file (not from upstream)
echo "[SKIP] 00-gotchas-jefe.md (local file)"

if [ "$CHANGED" -eq 0 ]; then
  echo "=== All files up to date ==="
  exit 0
else
  echo "=== Files changed — review and commit ==="
  exit 1
fi