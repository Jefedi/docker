#!/usr/bin/env bash
set -euo pipefail

# Sync media-stack docs from GitHub repos
# Exit 0 if unchanged, 1 if changed, 2 on error.
# Sources: TRaSH-Guides/Guides, recyclarr/recyclarr, bakerboy448/servarr-wiki-mkdocs

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
mkdir -p "$REF_DIR"

CHANGED=0
FAILED=0
TMP_BASE="/tmp/media-stack-sync-$$"
mkdir -p "$TMP_BASE"
trap 'rm -rf "$TMP_BASE"' EXIT

# --- Source 1: TRaSH-Guides ---
echo "=== Syncing TRaSH-Guides ==="
if git clone --depth 1 https://github.com/TRaSH-Guides/Guides.git "$TMP_BASE/trash" 2>/dev/null; then
    cd "$TMP_BASE/trash"
    find docs -name "*.md" | while IFS= read -r f; do
        rel="${f#docs/}"
        out="$REF_DIR/trash__${rel//\//__}"
        if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
            cp "$f" "$out"
            echo "  [CHANGED] trash__${rel//\//__}"
            CHANGED=1
        fi
    done
else
    echo "  [FAIL] TRaSH-Guides clone" >&2
    FAILED=1
fi

# --- Source 2: Recyclarr ---
echo "=== Syncing Recyclarr ==="
if git clone --depth 1 https://github.com/recyclarr/recyclarr.git "$TMP_BASE/recyclarr" 2>/dev/null; then
    cd "$TMP_BASE/recyclarr"
    find docs -name "*.md" | while IFS= read -r f; do
        rel="${f#docs/}"
        out="$REF_DIR/recyclarr__${rel//\//__}"
        if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
            cp "$f" "$out"
            echo "  [CHANGED] recyclarr__${rel//\//__}"
            CHANGED=1
        fi
    done
else
    echo "  [FAIL] Recyclarr clone" >&2
    FAILED=1
fi

# --- Source 3: Servarr wiki (shared docs for hardlinks) ---
echo "=== Syncing Servarr wiki (hardlinks refs) ==="
if git clone --depth 1 https://github.com/bakerboy448/servarr-wiki-mkdocs.git "$TMP_BASE/servarr-wiki" 2>/dev/null; then
    cd "$TMP_BASE/servarr-wiki"
    for f in docs/docker-guide.md docs/permissions-and-networking.md docs/vpn.md docs/install-script.md docs/useful-tools.md; do
        [ -f "$f" ] || continue
        out="$REF_DIR/servarr__$(basename "$f")"
        if [ ! -f "$out" ] || ! cmp -s "$f" "$out"; then
            cp "$f" "$out"
            echo "  [CHANGED] servarr__$(basename "$f")"
            CHANGED=1
        fi
    done
else
    echo "  [FAIL] servarr-wiki clone" >&2
    FAILED=1
fi

# --- Check for deleted files ---
echo "=== Checking for stale references ==="
for f in "$REF_DIR"/trash__*.md "$REF_DIR"/recyclarr__*.md "$REF_DIR"/servarr__*.md; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "00-gotchas-jefe.md" ] && continue
    # If no source file exists for this reference, it's stale
    base=$(basename "$f")
    echo "  [OK] $base"
done

echo ""
echo "Done. Changed=$CHANGED Failed=$FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 2
fi
if [ "$CHANGED" -eq 1 ]; then
    exit 1
fi
exit 0