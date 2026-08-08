#!/usr/bin/env bash
set -euo pipefail

# Sync Jellyfin/Jellyseerr/Bazarr docs from GitHub repos
# Exit 0 if unchanged, 1 if changed, 2 on error.
# Sources: jellyfin/jellyfin.org (docs), seerr-team/seerr (develop), morpheus65535/bazarr.wiki

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
mkdir -p "$REF_DIR"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

CHANGED=0
FAILED=0

# ── Jellyfin docs (jellyfin/jellyfin.org) ──────────────────────────────────

echo "=== Cloning jellyfin/jellyfin.org ==="
if ! git clone --depth 1 https://github.com/jellyfin/jellyfin.org.git "$TMP_DIR/jellyfin-org" 2>/dev/null; then
    echo "  [FAIL] Could not clone jellyfin/jellyfin.org" >&2
    FAILED=1
else
    echo "  Copying docs/general/**/*.md..."
    while IFS= read -r -d '' src; do
        rel="${src#$TMP_DIR/jellyfin-org/docs/general/}"
        flat="${rel//\//__}"
        flat="${flat%.md}"
        dst="$REF_DIR/jellyfin__${flat}.md"
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
            cp "$src" "$dst"
            echo "  [CHANGED] jellyfin__${flat}.md"
            CHANGED=1
        fi
    done < <(find "$TMP_DIR/jellyfin-org/docs/general" -name '*.md' -print0)

    echo "  Copying docs/project/**/*.md..."
    while IFS= read -r -d '' src; do
        rel="${src#$TMP_DIR/jellyfin-org/docs/project/}"
        flat="${rel//\//__}"
        flat="${flat%.md}"
        dst="$REF_DIR/jellyfin__project__${flat}.md"
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
            cp "$src" "$dst"
            echo "  [CHANGED] jellyfin__project__${flat}.md"
            CHANGED=1
        fi
    done < <(find "$TMP_DIR/jellyfin-org/docs/project" -name '*.md' -print0)
fi

# ── Jellyseerr docs (seerr-team/seerr, branch develop) ─────────────────────

echo "=== Cloning seerr-team/seerr (develop) ==="
if ! git clone --depth 1 --branch develop https://github.com/seerr-team/seerr.git "$TMP_DIR/jellyseerr" 2>/dev/null; then
    echo "  [FAIL] Could not clone seerr-team/seerr" >&2
    FAILED=1
else
    echo "  Copying docs/**/*.md and *.mdx..."
    while IFS= read -r -d '' src; do
        rel="${src#$TMP_DIR/jellyseerr/docs/}"
        flat="${rel//\//__}"
        # Normalize .mdx → .md
        flat="${flat%.md}"
        flat="${flat%.mdx}"
        dst="$REF_DIR/jellyseerr__${flat}.md"
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
            cp "$src" "$dst"
            echo "  [CHANGED] jellyseerr__${flat}.md"
            CHANGED=1
        fi
    done < <(find "$TMP_DIR/jellyseerr/docs" \( -name '*.md' -o -name '*.mdx' \) -print0)

    echo "  Copying gen-docs/**/*.md..."
    while IFS= read -r -d '' src; do
        rel="${src#$TMP_DIR/jellyseerr/gen-docs/}"
        flat="${rel//\//__}"
        flat="${flat// /-}"
        flat="${flat%.md}"
        dst="$REF_DIR/jellyseerr__gen-docs__${flat}.md"
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
            cp "$src" "$dst"
            echo "  [CHANGED] jellyseerr__gen-docs__${flat}.md"
            CHANGED=1
        fi
    done < <(find "$TMP_DIR/jellyseerr/gen-docs" -name '*.md' -print0)
fi

# ── Bazarr wiki (morpheus65535/bazarr.wiki) ───────────────────────────────

echo "=== Cloning morpheus65535/bazarr.wiki ==="
if ! git clone --depth 1 https://github.com/morpheus65535/bazarr.wiki.git "$TMP_DIR/bazarr-wiki" 2>/dev/null; then
    echo "  [FAIL] Could not clone morpheus65535/bazarr.wiki" >&2
    FAILED=1
else
    echo "  Copying *.md (lowercase, spaces→dashes)..."
    while IFS= read -r -d '' src; do
        fname="$(basename "$src")"
        flat="${fname,,}"            # lowercase
        flat="${flat// /-}"          # spaces to dashes
        flat="${flat%.md}"
        dst="$REF_DIR/bazarr__${flat}.md"
        if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
            cp "$src" "$dst"
            echo "  [CHANGED] bazarr__${flat}.md"
            CHANGED=1
        fi
    done < <(find "$TMP_DIR/bazarr-wiki" -maxdepth 1 -name '*.md' -print0)
fi

# ── Summary ───────────────────────────────────────────────────────────────

echo ""
echo "Done. Changed=$CHANGED Failed=$FAILED"

if [ "$FAILED" -ne 0 ]; then
    exit 2
fi
if [ "$CHANGED" -ne 0 ]; then
    exit 1
fi
exit 0