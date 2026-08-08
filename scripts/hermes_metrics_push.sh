#!/usr/bin/env bash
# Back up previous metrics before running the exporter, so we can diff.
set -euo pipefail
PREV="/opt/data/hermes_metrics.json.prev"
CURR="/opt/data/hermes_metrics.json"
[ -f "$CURR" ] && cp "$CURR" "$PREV"
python3 /opt/data/scripts/hermes_metrics.py
