#!/usr/bin/env bash
set -euo pipefail

# Sync Servarr docs from GitHub repos
# Exit 0 if unchanged, 1 if changed, 2 on error.
# Sources: bakerboy448/servarr-wiki-mkdocs (docs), Sonarr/Radarr/Lidarr/Prowlarr (openapi)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
mkdir -p "$REF_DIR"

CHANGED=0
FAILED=0
TMP_BASE="/tmp/servarr-sync-$$"
mkdir -p "$TMP_BASE"
trap 'rm -rf "$TMP_BASE"' EXIT

# --- Source 1: Servarr wiki (docs) ---
echo "=== Syncing servarr-wiki-mkdocs ==="
if git clone --depth 1 https://github.com/bakerboy448/servarr-wiki-mkdocs.git "$TMP_BASE/wiki" 2>/dev/null; then
    cd "$TMP_BASE/wiki/docs"
    
    # Copy per-app docs
    for app in sonarr radarr lidarr prowlarr; do
        for f in "$app"/*.md; do
            [ -f "$f" ] || continue
            out="$REF_DIR/${app}__$(basename "$f")"
            if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
                cp "$f" "$out"
                echo "  [CHANGED] ${app}__$(basename "$f")"
                CHANGED=1
            fi
        done
        # Subdirs (installation, etc.)
        for f in "$app"/installation/*.md; do
            [ -f "$f" ] || continue
            out="$REF_DIR/${app}__installation__$(basename "$f")"
            if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
                cp "$f" "$out"
                echo "  [CHANGED] ${app}__installation__$(basename "$f")"
                CHANGED=1
            fi
        done
    done
    
    # Shared docs
    for f in docker-guide.md permissions-and-networking.md vpn.md install-script.md useful-tools.md index.md; do
        [ -f "$f" ] || continue
        out="$REF_DIR/servarr__${f}"
        if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
            cp "$f" "$out"
            echo "  [CHANGED] servarr__${f}"
            CHANGED=1
        fi
    done
else
    echo "  [FAIL] servarr-wiki clone" >&2
    FAILED=1
fi

# --- Source 2: OpenAPI specs ---
echo "=== Syncing OpenAPI specs ==="

# Sonarr V5
if git clone --depth 1 --branch v5-develop https://github.com/Sonarr/Sonarr.git "$TMP_BASE/sonarr" 2>/dev/null; then
    src="$TMP_BASE/sonarr/src/Sonarr.Api.V5/openapi.json"
    out="$REF_DIR/sonarr-openapi.json"
    if [ ! -f "$out" ] || ! cmp -s "$src" "$out"; then
        cp "$src" "$out"
        echo "  [CHANGED] sonarr-openapi.json"
        CHANGED=1
    fi
else
    echo "  [FAIL] Sonarr clone" >&2
    FAILED=1
fi

# Radarr V3
if git clone --depth 1 --branch develop https://github.com/Radarr/Radarr.git "$TMP_BASE/radarr" 2>/dev/null; then
    src="$TMP_BASE/radarr/src/Radarr.Api.V3/openapi.json"
    out="$REF_DIR/radarr-openapi.json"
    if [ ! -f "$out" ] || ! cmp -s "$src" "$out"; then
        cp "$src" "$out"
        echo "  [CHANGED] radarr-openapi.json"
        CHANGED=1
    fi
else
    echo "  [FAIL] Radarr clone" >&2
    FAILED=1
fi

# Lidarr V1
if git clone --depth 1 --branch develop https://github.com/Lidarr/Lidarr.git "$TMP_BASE/lidarr" 2>/dev/null; then
    src="$TMP_BASE/lidarr/src/Lidarr.Api.V1/openapi.json"
    out="$REF_DIR/lidarr-openapi.json"
    if [ ! -f "$out" ] || ! cmp -s "$src" "$out"; then
        cp "$src" "$out"
        echo "  [CHANGED] lidarr-openapi.json"
        CHANGED=1
    fi
else
    echo "  [FAIL] Lidarr clone" >&2
    FAILED=1
fi

# Prowlarr V1
if git clone --depth 1 --branch develop https://github.com/Prowlarr/Prowlarr.git "$TMP_BASE/prowlarr" 2>/dev/null; then
    src="$TMP_BASE/prowlarr/src/Prowlarr.Api.V1/openapi.json"
    out="$REF_DIR/prowlarr-openapi.json"
    if [ ! -f "$out" ] || ! cmp -s "$src" "$out"; then
        cp "$src" "$out"
        echo "  [CHANGED] prowlarr-openapi.json"
        CHANGED=1
    fi
else
    echo "  [FAIL] Prowlarr clone" >&2
    FAILED=1
fi

# Note: api-index.md files are generated from openapi.json and need manual regeneration
# Run: python3 -c "import json; ..." to regenerate after openapi changes

echo ""
echo "Done. Changed=$CHANGED Failed=$FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 2
fi
if [ "$CHANGED" -eq 1 ]; then
    exit 1
fi
exit 0