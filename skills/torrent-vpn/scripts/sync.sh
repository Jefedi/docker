#!/usr/bin/env bash
set -euo pipefail

# Sync torrent-vpn docs from GitHub repos
# Exit 0 if unchanged, 1 if changed, 2 on error.
# Sources: qbittorrent/qBittorrent.wiki, qdm12/gluetun-wiki, cross-seed/cross-seed

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
mkdir -p "$REF_DIR"

CHANGED=0
FAILED=0

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "=== Cloning repos ==="

# Clone qBittorrent wiki
if ! git clone --depth 1 https://github.com/qbittorrent/qBittorrent.wiki.git "$TMP_DIR/qbt-wiki" 2>/dev/null; then
    echo "ERROR: Failed to clone qBittorrent wiki" >&2
    exit 2
fi

# Clone Gluetun wiki
if ! git clone --depth 1 https://github.com/qdm12/gluetun-wiki.git "$TMP_DIR/gluetun-wiki" 2>/dev/null; then
    echo "ERROR: Failed to clone Gluetun wiki" >&2
    exit 2
fi

# Clone cross-seed
if ! git clone --depth 1 https://github.com/cross-seed/cross-seed.git "$TMP_DIR/crossseed" 2>/dev/null; then
    echo "ERROR: Failed to clone cross-seed" >&2
    exit 2
fi

echo "=== Syncing qBittorrent wiki ==="

for f in "$TMP_DIR"/qbt-wiki/*.md; do
    [ -f "$f" ] || continue
    base=$(basename "$f" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    dest="$REF_DIR/qbt__${base}"
    if [ ! -f "$dest" ] || ! cmp -s "$f" "$dest"; then
        cp "$f" "$dest"
        echo "  [CHANGED] qbt__${base}"
        CHANGED=1
    fi
done

echo "=== Syncing Gluetun wiki ==="

copy_gluetun_subdir() {
    local src_dir="$1"
    local prefix="$2"
    for f in "$src_dir"/*.md; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        dest="$REF_DIR/${prefix}__${base}"
        if [ ! -f "$dest" ] || ! cmp -s "$f" "$dest"; then
            cp "$f" "$dest"
            echo "  [CHANGED] ${prefix}__${base}"
            CHANGED=1
        fi
    done
}

# Top-level README
if [ -f "$TMP_DIR/gluetun-wiki/README.md" ]; then
    dest="$REF_DIR/gluetun__readme.md"
    if [ ! -f "$dest" ] || ! cmp -s "$TMP_DIR/gluetun-wiki/README.md" "$dest"; then
        cp "$TMP_DIR/gluetun-wiki/README.md" "$dest"
        echo "  [CHANGED] gluetun__readme.md"
        CHANGED=1
    fi
fi

copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/setup" "gluetun__setup"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/setup/advanced" "gluetun__setup__advanced"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/setup/options" "gluetun__setup__options"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/setup/providers" "gluetun__setup__providers"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/setup/prerequisites" "gluetun__setup__prerequisites"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/errors" "gluetun__errors"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/faq" "gluetun__faq"
copy_gluetun_subdir "$TMP_DIR/gluetun-wiki/contributing" "gluetun__contributing"

echo "=== Syncing cross-seed docs ==="

copy_crossseed_subdir() {
    local src_dir="$1"
    local prefix="$2"
    for f in "$src_dir"/*.md; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        dest="$REF_DIR/${prefix}__${base}"
        if [ ! -f "$dest" ] || ! cmp -s "$f" "$dest"; then
            cp "$f" "$dest"
            echo "  [CHANGED] ${prefix}__${base}"
            CHANGED=1
        fi
    done
}

copy_crossseed_subdir "$TMP_DIR/crossseed/cross-seed.org/docs/basics" "crossseed__basics"
copy_crossseed_subdir "$TMP_DIR/crossseed/cross-seed.org/docs/tutorials" "crossseed__tutorials"
copy_crossseed_subdir "$TMP_DIR/crossseed/cross-seed.org/docs/reference" "crossseed__reference"
copy_crossseed_subdir "$TMP_DIR/crossseed/cross-seed.org/docs/legacy" "crossseed__legacy"

# v6-migration.md (top-level in docs/)
if [ -f "$TMP_DIR/crossseed/cross-seed.org/docs/v6-migration.md" ]; then
    dest="$REF_DIR/crossseed__v6-migration.md"
    if [ ! -f "$dest" ] || ! cmp -s "$TMP_DIR/crossseed/cross-seed.org/docs/v6-migration.md" "$dest"; then
        cp "$TMP_DIR/crossseed/cross-seed.org/docs/v6-migration.md" "$dest"
        echo "  [CHANGED] crossseed__v6-migration.md"
        CHANGED=1
    fi
fi

echo "=== Done. Changed=$CHANGED Failed=$FAILED ==="

if [ "$FAILED" -gt 0 ]; then
    exit 2
fi
if [ "$CHANGED" -eq 1 ]; then
    exit 1
fi
exit 0