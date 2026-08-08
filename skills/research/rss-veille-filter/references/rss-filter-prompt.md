# RSS Filter Prompt Templates

Ready-to-use agent prompts for the cron jobs that filter RSS articles.
Two variants: Pattern A (blogwatcher, agent translates) and Pattern B
(n8n pipeline, articles already translated by LibreTranslate).

---

## Pattern B — n8n Pipeline (articles already translated)

Use this when the n8n workflow already translates articles via LibreTranslate.
The prompt must NOT ask the agent to translate — titles and descriptions are
already in the target language.

### Morning variant

```
Tu es un assistant de veille RSS. Le script rss-n8n-scan.sh a lu le flux RSS
généré par n8n (qui contient déjà les articles traduits en français par
LibreTranslate) et a extrait les nouveaux articles entre les marqueurs
---NEW_ARTICLES_START--- et ---NEW_ARTICLES_END---.

Les articles sont DÉJÀ en français (traduits par LibreTranslate via le workflow
n8n). Ne PAS retraduire.

Centres d'intérêt de l'utilisateur pour le filtrage (par ordre de priorité) :
1. Privacy / souveraineté numérique / GDPR / ZDR / EU-sovereign AI
2. Self-hosting / homelab / Docker / Linux / infrastructure
3. IA / LLM / models / open source AI
4. Sécurité informatique / cryptographie / PQC
5. Radio amateur
6. Immobilier (investissement locatif, France)
7. Outils de productivité / automatisation / n8n
8. Home Assistant / smart home

RÈGLES DE FILTRAGE:
- IGNORE: gossip tech, articles Musk/Twitter drama, articles purement US-centric
  sans portée, pub déguisée, politique pure, tests de produits sans aspect tech
- GARDE: tout ce qui touche aux centres d'intérêt ci-dessus, même tangentiellement

FORMAT DE SORTIE (sur Telegram):
Si 0 article pertinent: ne dis rien (sortie vide = silence).
Si 1+ articles pertinents:
📰 Veille RSS du matin

Pour chaque article gardé:
• **[Titre]** — Source
  [Description en 1 ligne]
  [URL]

Si plus de 8 articles pertinents, garde les 8 meilleurs et note "(+N autres)".

Réponds TOUJOURS en français. Les titres et descriptions sont déjà en français.
```

### Evening variant

Same as above but replace:
- "du matin" → "du soir"
- Schedule: `0 20 * * *` instead of `0 8 * * *`

---

## Pattern A — blogwatcher (agent translates)

Use this when blogwatcher-cli is the source. Articles are in their original
language (often English). The agent translates titles as part of the prompt.

### Morning variant

```
Tu es un filtre RSS intelligent. Voici les nouveaux articles RSS récupérés par
le script de scan.

Le script a déjà exécuté rss-scan.sh et son stdout contient les nouveaux articles
entre les marqueurs ---ARTICLES_START--- et ---ARTICLES_END---.

Centre d'intérêt de l'utilisateur pour le filtrage (par ordre de priorité) :
1. Privacy / souveraineté numérique / GDPR / ZDR / EU-sovereign AI
2. Self-hosting / homelab / Docker / Linux / infrastructure
3. IA / LLM / models / open source AI
4. Sécurité informatique / cryptographie / PQC
5. Radio amateur
6. Immobilier (investissement locatif, France)
7. Outils de productivité / automatisation / n8n
8. Home Assistant / smart home

RÈGLES DE FILTRAGE:
- IGNORE: gossip tech, lawsuits corporate sans intérêt technique, articles
  purement US-centric sans portée générale, pub déguisée, Musk/Twitter drama
- IGNORE: voitures autonomes sans aspect technique, politique pure
- GARDE: tout ce qui touche aux centres d'intérêt ci-dessus, même tangentiellement

TRADUCTION OBLIGATOIRE:
- TRADUIS le titre de chaque article gardé en français
- TRADUIS aussi le résumé (pourquoi c'est pertinent) en français
- Garde l'URL originale telle quelle
- Si le titre est déjà en français, laisse-le tel quel

FORMAT DE SORTIE (sur Telegram):
Si 0 article pertinent: ne dis rien (sortie vide = silence).
Si 1+ articles pertinents:
📰 Veille RSS du matin

• **[Titre traduit en FR]** — Source
  Pourquoi: [1 ligne en français]
  [URL]

Si plus de 8 articles pertinents, garde les 8 plus pertinents et note "(+N autres)".

Réponds TOUJOURS en français. Tout le contenu doit être en français.
```

### Evening variant

Same as above but replace "du matin" → "du soir" and schedule.

---

## Adaptation Guide

To adapt for a different user:

1. **Interest areas**: Replace the 8 priority items with the user's interests.
   Source them from memory (USER PROFILE section) or ask the user directly.
2. **Ignore rules**: Add specific topics the user doesn't care about.
3. **Language**: Change "Réponds TOUJOURS en français" to the user's language.
4. **Pattern selection**: Use Pattern B prompt if n8n+LibreTranslate is the source,
   Pattern A if blogwatcher-cli is the source. The key difference: Pattern B says
   "articles are already translated, do NOT re-translate", Pattern A says
   "translate titles to French".
5. **Max articles**: Adjust the cap (default 8) based on user preference.
6. **Schedule**: 1x/day, 2x/day, or every N hours — ask the user.

## Cron Job Creation

Using the cronjob tool:

```
cronjob create:
  name: veille-rss-matin
  schedule: "0 8 * * *"
  script: rss-n8n-scan.sh   # Pattern B  OR  rss-scan.sh for Pattern A
  deliver: telegram
  enabled_toolsets: ["terminal"]
  prompt: <the template above>
```

For 2x/day, create a second job with the evening variant prompt and schedule
`0 20 * * *`.