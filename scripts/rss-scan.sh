#!/bin/bash
# RSS Scan Script — scanne les feeds, extrait les nouveaux articles
# Déclenche un run agent Hermes pour filtrage et notification Telegram
set -euo pipefail

export PATH="/opt/data/home/.local/bin:$PATH"
export BLOGWATCHER_DB="/opt/data/home/.blogwatcher-cli/blogwatcher-cli.db"

# Scan tous les blogs
SCAN_OUTPUT=$(blogwatcher-cli scan --silent 2>&1)

# Récupère les articles non-lus
ARTICLES=$(blogwatcher-cli articles 2>&1)

# Si pas d'articles, on sort silencieusement
if echo "$ARTICLES" | grep -q "Unread articles (0)"; then
    exit 0
fi

# Si on a des articles, on les passe à l'agent
NEW_COUNT=$(echo "$ARTICLES" | grep -oP "Unread articles \(\d+\)" | grep -oP "\d+")
echo "$NEW_COUNT nouveaux article(s) RSS à filtrer."
echo "---ARTICLES_START---"
echo "$ARTICLES"
echo "---ARTICLES_END---"

# Marquer comme lus après extraction
blogwatcher-cli read-all --yes 2>/dev/null