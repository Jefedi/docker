#!/bin/bash
# Sync Hermes Agent files to Obsidian vault - silent on success, ntfy on failure
VAULT="/root/Documents/Obsidian Vault"
HERMES_DIR="/root/.hermes"
OUTDIR="$VAULT/Mémoire AI/Hermes Agent"
NOTIFY="/root/.hermes/scripts/notify.sh"

mkdir -p "$OUTDIR/memories" "$OUTDIR/skills" || {
  $NOTIFY "🚨 Sync vault échoué" "mkdir a échoué sur $OUTDIR" urgent
  exit 0
}

# 1. Sync memory files
cp "$HERMES_DIR/memories/MEMORY.md" "$OUTDIR/memories/MEMORY.md" 2>/dev/null || true
cp "$HERMES_DIR/memories/USER.md" "$OUTDIR/memories/USER.md" 2>/dev/null || true

# 2. Generate skills inventory
SKILL_LIST=$(find "$HERMES_DIR/skills" -name "SKILL.md" -maxdepth 3 2>/dev/null | sort | while read f; do
  skill_dir=$(dirname "$f")
  name=$(basename "$skill_dir")
  parent=$(basename "$(dirname "$skill_dir")")
  desc=$(grep -m1 "^description:" "$f" | sed 's/description: *//' | head -c 120)
  echo "- **$name** ($parent): $desc"
done)

cat > "$OUTDIR/skills/_inventory.md" << EOF
---
title: Skills Inventory
generated: $(date -Iseconds)
---

# Skills Inventory

Skills actives chez Hermes Agent :

$SKILL_LIST
EOF

# 3. Config summary
grep -E "^model:|^provider:|^  backend:" "$HERMES_DIR/config.yaml" 2>/dev/null | sed 's/^/    /' > "$OUTDIR/config_snippet.txt" 2>/dev/null || true

# Silent exit on success — rien n'est envoyé
exit 0