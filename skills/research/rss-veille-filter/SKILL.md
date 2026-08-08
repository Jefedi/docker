---
name: rss-veille-filter
description: "Use when setting up AI-filtered RSS monitoring pipelines."
version: 2.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [rss, veille, monitoring, cron, filtering, telegram, blogwatcher, n8n, libretranslate]
---

# RSS Veille with AI Filtering

Set up recurring RSS/Atom feed monitoring where an agent filters new articles by
relevance to the user's interests and pushes only the interesting ones to a chat
platform (Telegram, Discord). Silent when nothing is relevant.

This is the pattern: **scan → filter → notify**, with the agent as the intelligent
intermediary that curates what the user sees.

## Two Architectures

### Pattern A — blogwatcher-cli (standalone)

```
cron → rss-scan.sh → blogwatcher-cli scan → articles list
  → agent filters by user interests → Telegram/Discord notification
```

Use when: no n8n instance, or simple standalone setup needed.

See `references/blogwatcher-pattern.md` for full setup details.

### Pattern B — n8n pipeline (preferred when n8n is available)

```
n8n Schedule Trigger (e.g. every 30 min)
  ├── RSS Feed Read (multiple sources)
  ├── LibreTranslate (en → fr or other target language)
  ├── Hermes API /api/v1/responses (AI curation)
  └── Generate RSS XML → stored in workflow staticData
        ↓
  Webhook endpoint: /webhook/rss-curation (serves the RSS XML)

Hermes cron (2x/day)
  ├── rss-n8n-scan.sh reads the n8n RSS XML feed
  ├── Compares with seen-links file (~/.hermes/rss-seen.txt)
  ├── Outputs new articles between markers
  └── Agent filters by interests → Telegram notification
```

Use when: n8n is already running, LibreTranslate is available, or translation
is needed before the agent sees the articles. This is the preferred pattern for
users with an existing homelab stack.

See `references/n8n-pipeline-pattern.md` for full setup details.

## ⚠️ Before You Build: Check for Existing Infrastructure

**Critical pitfall**: Before creating any RSS monitoring infrastructure, check
whether the user already has an n8n workflow that handles RSS. Creating a parallel
system wastes time and creates maintenance burden.

```bash
# List n8n workflows (inside the container)
docker exec n8n-n8n-1 npx n8n list:workflow 2>&1 | grep -i -E "rss|feed|translate|curat"

# If workflows exist, inspect them
docker exec n8n-n8n-1 npx n8n export:workflow --all --output=/tmp/all_workflows.json
docker cp n8n-n8n-1:/tmp/all_workflows.json /tmp/all_workflows.json
# Then parse with python3 to find RSS-related workflows and their nodes
```

If an existing n8n workflow already does RSS → translate → curate → RSS XML,
use Pattern B and just create the Hermes cron that reads the existing feed.
Do NOT set up blogwatcher-cli in parallel.

## Prompt Design for Filtering

The agent prompt should contain:

1. **User's interest areas** (ordered by priority) — these define what "relevant" means.
2. **Explicit ignore rules** — topics to filter OUT (gossip, US-centric drama, ads).
3. **Output format** — compact, scannable format for chat (title, source, URL, 1-line why).
4. **Silence rule** — if 0 articles are relevant, produce empty output (no message sent).
5. **Max articles cap** — e.g. top 8 most relevant, note "(+N others)" if more.
6. **Translation awareness** — if using Pattern B (n8n + LibreTranslate), articles are
   ALREADY translated. The prompt must say "articles are already in French, do NOT
   re-translate." If using Pattern A, decide whether the agent should translate or not.

See `references/rss-filter-prompt.md` for complete, ready-to-use prompt templates
for both patterns.

## User Interest Profile

The filtering prompt should be tailored to the user. Common interest areas for this
user (Le Havre, solopreneur, privacy-focused, homelab operator):

1. Privacy / souveraineté numérique / GDPR / ZDR / EU-sovereign AI
2. Self-hosting / homelab / Docker / Linux / infrastructure
3. IA / LLM / models / open source AI
4. Sécurité informatique / cryptographie / PQC
5. Radio amateur
6. Immobilier (investissement locatif, France)
7. Outils de productivité / automatisation / n8n
8. Home Assistant / smart home

## Pitfalls

- **Check for existing n8n workflows FIRST**: before setting up blogwatcher-cli or
  any new RSS pipeline, inspect n8n for existing RSS/translate/curation workflows.
  Creating a parallel system that duplicates an existing n8n pipeline is the #1 mistake.
- **Script path**: cron `script` MUST be a bare filename in `~/.hermes/scripts/`.
  Absolute paths like `/opt/data/scripts/rss-scan.sh` are rejected with:
  "Script path must be relative to ~/.hermes/scripts/".
- **PATH in cron scripts**: cron runs with a minimal environment. Always export
  `PATH="$HOME/.local/bin:$PATH"` if blogwatcher-cli is installed there.
- **Backlog flood**: after adding feeds (Pattern A) or first run (Pattern B), the first
  scan pulls many articles. Always mark backlog as read / seed the seen-file before
  enabling the cron, or the first notification will be a flood.
- **read-all / seen-file timing**: the scan script must mark articles as read AFTER
  outputting them (not before), so the agent sees them but the next run doesn't
  re-process them.
- **Silent scan flag**: use `blogwatcher-cli scan --silent` (Pattern A) to suppress
  per-blog output; the script only needs the articles list, not the scan progress.
- **Two cron jobs, one script**: for 2x/day scheduling, create two separate cron jobs
  (e.g. `veille-rss-matin` at 8h, `veille-rss-soir` at 20h) both pointing to the same
  script but with different prompt headers ("du matin" / "du soir").
- **LibreTranslate API key**: passed as `api_key` in the JSON body, NOT as a header.
  Example: `{"q":"text","source":"en","target":"fr","api_key":"<key>"}`.
  The `Authorization: Bearer <key>` header does NOT work.
- **n8n API key may not be in env vars**: if `curl http://localhost:5678/api/v1/workflows`
  returns unauthorized, use the CLI inside the container instead:
  `docker exec n8n-n8n-1 npx n8n list:workflow`.
- **Articles already translated (Pattern B)**: when the n8n workflow includes a
  LibreTranslate step, the RSS XML feed already contains French titles/descriptions.
  The agent prompt must explicitly say "do NOT re-translate" to avoid wasted LLM effort
  and potential double-translation degradation.
- **HTTP Request node discards input fields**: after a Translate node (HTTP Request to
  LibreTranslate), `$json` contains only `{ translatedText: "..." }`. Original fields
  (title, link, content, pubDate) are lost. A downstream Set node (Rebuild HN) must use
  `$json.translatedText` for the title and `$("Tag HN").item.json.link` to recover other
  fields from the upstream node. If this is wrong, articles appear with empty titles/links
  — another silent failure. See `references/n8n-pipeline-pattern.md` for the fix.
- **WAL trap when modifying n8n DB**: always stop n8n, delete `database.sqlite-wal` and
  `database.sqlite-shm`, then copy the modified DB. If the WAL exists, n8n replays it on
  startup and overwrites your changes. See `references/n8n-db-modification.md`.
- **User expectation: test immediately**: the user expects you to trigger/verify the fix
  right away, not say "it'll work next cycle." Test the underlying API directly (curl to
  LibreTranslate) to prove the fix works, even if you can't trigger the n8n workflow.

## n8n Workflow Debugging (Pattern B)

When the n8n RSS workflow runs but articles are NOT translated (or a source
is missing from the feed), check these common silent-failure patterns:

### Translate node disabled or disconnected

The Translate HN node can be **disabled** (`"disabled": true` in the node JSON)
and/or **disconnected from the flow** (e.g. `Tag HN → Rebuild HN` bypasses
`Translate HN` entirely). Both produce a "success" status with no error —
articles just pass through untranslated.

**Diagnosis**: inspect the workflow's nodes and connections in the SQLite DB.
See `references/n8n-db-modification.md` for the full procedure.

### LibreTranslate auth: body key, NOT httpQueryAuth

The n8n `httpQueryAuth` credential type sends the API key as a query parameter
(`?apiKey=...`). LibreTranslate does NOT accept this — it requires `api_key`
in the JSON body. The node must use `authentication: "none"` and include
`api_key` directly in the `jsonBody` expression:

```
jsonBody: ={{ { q: $json.title, source: "en", target: "fr", api_key: "<KEY>" } }}
```

### Verifying the fix

After modifying the DB and restarting n8n, test LibreTranslate directly:
```bash
curl -s https://translate.jefe.ovh/translate -X POST \
  -H "Content-Type: application/json" \
  -d '{"q":"test","source":"en","target":"fr","api_key":"<key>"}'
```
Then wait for the next n8n schedule trigger cycle and check the RSS feed for
translated titles.

**User expectation**: test immediately, don't just configure and wait. The user
expects you to trigger/verify the workflow right away, not say "it'll work
next cycle." If you can't trigger the schedule, test the underlying API
directly (curl to LibreTranslate) to prove the fix works.

## Reference Files

- `references/rss-filter-prompt.md` — Prompt templates for both patterns (with and without translation)
- `references/n8n-pipeline-pattern.md` — Full setup guide for the n8n + LibreTranslate + Hermes API pattern
- `references/blogwatcher-pattern.md` — Full setup guide for the standalone blogwatcher-cli pattern
- `references/n8n-db-modification.md` — How to modify n8n workflows via SQLite when REST API is unavailable (WAL trap, node fixes, connection repair)
- `scripts/rss-scan.sh` — Scan script for Pattern A (blogwatcher-cli)
- `scripts/rss-n8n-scan.sh` — Scan script for Pattern B (reads n8n RSS XML feed)