# n8n Pipeline Pattern (Pattern B)

Full setup guide for RSS monitoring using an existing n8n instance with
LibreTranslate and Hermes API curation, then a Hermes cron for filtering
and Telegram notification.

## Prerequisites

- n8n container running (e.g. `n8n-n8n-1` on `127.0.0.1:5678`)
- LibreTranslate container running (e.g. `libretranslate` on `127.0.0.1:5000`)
- Hermes API accessible (e.g. `hermes.jefe.al/api/v1/responses`)

## n8n Workflow Structure

The n8n workflow ("RSS Curation par Hermes") has two branches:

### Schedule branch (runs every 30 min)

```
Schedule Trigger (30 min)
  ├── RSS Read LoKan (https://lokan.fr/feed/)
  ├── RSS Read Korben (https://korben.info/feed)
  └── RSS Read HN (https://news.ycombinator.com/rss)
        │
        ├── LoKan → Tag LoKan (source=lokan) ─────────────┐
        ├── Korben → Tag Korben (source=korben) ──────────┼── Merge Feeds (3 inputs)
        └── HN → Tag HN → Translate HN (LibreTranslate)  │
              → Rebuild HN (title=translated, link, content) ┘
                                                           │
                                                  Aggregate (all items → articles array)
                                                           │
                                                  Prepare Hermes Input (builds prompt)
                                                           │
                                                  Hermes Curation (POST hermes.jefe.al/api/v1/responses)
                                                           │
                                                  Generate RSS XML (parses Hermes response → RSS XML)
                                                  → stores in $getWorkflowStaticData('global').rssXml
```

### Webhook branch (on-demand)

```
RSS Webhook (GET /webhook/rss-curation)
  → Read Stored XML (reads staticData.rssXml)
  → Responds with RSS XML
```

## LibreTranslate Configuration

LibreTranslate is configured with API key auth. Key details:

- **API key is passed in the JSON body**, NOT as a header
- Endpoint: `POST http://localhost:5000/translate`
- Body: `{"q":"text to translate","source":"en","target":"fr","api_key":"<key>"}`
- The `Authorization: Bearer <key>` header does NOT work — returns "Please contact the server operator"
- To find the API key: `docker exec libretranslate python3 -c "import sqlite3; conn=sqlite3.connect('/app/db/api_keys.db'); c=conn.cursor(); c.execute('SELECT * FROM api_keys'); print(c.fetchall())"`

### ⚠️ n8n Node Configuration (KNOWN BUG + FIX)

The Translate node must use `authentication: "none"` with `api_key` in the JSON
body. The `httpQueryAuth` credential type is the BUG, not the correct config —
it sends the key as `?apiKey=...` query param which LibreTranslate rejects
silently (no error, translation just doesn't happen).

**Correct node configuration:**
```json
{
  "parameters": {
    "method": "POST",
    "url": "https://translate.jefe.ovh/translate",
    "authentication": "none",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ { q: $json.title, source: \"en\", target: \"fr\", format: \"text\", api_key: \"<API_KEY>\" } }}",
    "options": { "batching": { "batch": { "batchSize": 5, "batchInterval": 500 } }, "timeout": 30000 }
  }
}
```

**Do NOT use**: `authentication: "genericCredentialType"`, `genericAuthType: "httpQueryAuth"`,
or a `credentials.httpQueryAuth` reference — these send the key as a query param
and LibreTranslate returns `{"error":"Please contact the server operator to get an API key"}`.

### ⚠️ Node Disabled / Disconnected (SILENT FAILURE)

A Translate node can be `"disabled": true` (skipped silently) and/or
disconnected from the flow (e.g. `Tag HN → Rebuild HN` bypasses `Translate HN`).
Both produce workflow status "success" with NO error — articles just pass
through untranslated. Always check:
1. `node.disabled` is `false` or absent
2. The connection chain goes through the Translate node
3. See `references/n8n-db-modification.md` for how to fix both via SQLite

### ⚠️ HTTP Request Node Discards Input Data (Rebuild HN Bug)

After an HTTP Request node (e.g. Translate HN → LibreTranslate API), the
output `$json` contains **only the API response fields**. For LibreTranslate,
that's `{ "translatedText": "..." }`. The original input fields (title, link,
content, pubDate) are NOT carried through.

A downstream Set node (e.g. Rebuild HN) that references `$json.title` or
`$json.link` will get **empty values** — another silent failure. The workflow
succeeds, articles appear in the RSS feed, but with missing titles/links/dates.

**Fix**: Use the API response field for the translated value, and recover
original fields from the upstream node using n8n's `$("NodeName").item.json`
syntax:

```javascript
// In Rebuild HN (Set node after Translate HN)
// title: use the translated text from LibreTranslate response
"={{ $json.translatedText || $json.title }}"

// link: recover from the Tag HN node (before the HTTP Request)
"={{ $json.link || $(\"Tag HN\").item.json.link }}"

// content: recover from Tag HN
"={{ $json.content || $(\"Tag HN\").item.json.contentSnippet || $(\"Tag HN\").item.json.content || \"\" }}"

// pubDate: recover from Tag HN
"={{ $json.pubDate || $(\"Tag HN\").item.json.pubDate || $(\"Tag HN\").item.json.isoDate || \"\" }}"
```

**Key pattern**: `$("UpstreamNodeName").item.json.fieldName` accesses data
from any earlier node in the workflow, even after an HTTP Request that
discarded the original fields. This is n8n's cross-node data access syntax.

## Hermes Cron: Reading the n8n RSS Feed

The Hermes cron reads the n8n-generated RSS XML and pushes new articles to Telegram.

### Scan script (`~/.hermes/scripts/rss-n8n-scan.sh`)

```bash
#!/bin/bash
# Reads the RSS XML feed generated by n8n, extracts new articles
SEEN_FILE="$HOME/.hermes/rss-seen.txt"
RSS_URL="http://localhost:5678/webhook/rss-curation"

touch "$SEEN_FILE"
RSS_XML=$(curl -s --max-time 15 "$RSS_URL")

python3 -c "
import sys, re

xml = sys.stdin.read()
seen_file = '$SEEN_FILE'

with open(seen_file, 'r') as f:
    seen = set(line.strip() for line in f if line.strip())

items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
new_items = []

for item in items:
    title_m = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
    link_m = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
    desc_m = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
    date_m = re.search(r'<pubDate>(.*?)</pubDate>', item, re.DOTALL)
    author_m = re.search(r'<author>(.*?)</author>', item, re.DOTALL)
    
    title = title_m.group(1).strip() if title_m else ''
    link = link_m.group(1).strip() if link_m else ''
    desc = desc_m.group(1).strip() if desc_m else ''
    date = date_m.group(1).strip() if date_m else ''
    author = author_m.group(1).strip() if author_m else ''
    
    if link and link not in seen:
        new_items.append((title, link, desc, date, author))

if not new_items:
    sys.exit(0)

print(f'---NEW_ARTICLES_START---')
for title, link, desc, date, author in new_items:
    print(f'TITLE: {title}')
    print(f'LINK: {link}')
    print(f'DESC: {desc[:300]}')
    print(f'DATE: {date}')
    print(f'SOURCE: {author}')
    print('---')
print(f'---NEW_ARTICLES_END---')

with open(seen_file, 'a') as f:
    for _, link, _, _, _ in new_items:
        f.write(link + '\n')
" <<< "$RSS_XML"
```

### Cron job creation

Create two cron jobs (morning 8h, evening 20h):

```
cronjob create:
  name: veille-rss-matin
  schedule: "0 8 * * *"
  script: rss-n8n-scan.sh
  deliver: telegram
  enabled_toolsets: ["terminal"]
  prompt: <see references/rss-filter-prompt.md, Pattern B variant>
```

### Key differences from Pattern A

| Aspect | Pattern A (blogwatcher) | Pattern B (n8n pipeline) |
|--------|------------------------|--------------------------|
| Feed sources | blogwatcher-cli DB | n8n RSS Feed Read nodes |
| Translation | None (agent translates) | LibreTranslate in n8n |
| Curation | Agent only | Hermes API in n8n + agent |
| Storage | SQLite DB | n8n workflow staticData |
| Seen tracking | blogwatcher read/unread | `~/.hermes/rss-seen.txt` file |
| Script | `rss-scan.sh` | `rss-n8n-scan.sh` |

## Inspecting Existing n8n Workflows

When the n8n REST API key is not available in env vars:

```bash
# List all workflows
docker exec n8n-n8n-1 npx n8n list:workflow 2>&1

# Export all workflows to JSON
docker exec n8n-n8n-1 npx n8n export:workflow --all --output=/tmp/all_workflows.json
docker cp n8n-n8n-1:/tmp/all_workflows.json /tmp/all_workflows.json

# Parse to find RSS/translate/curation workflows
python3 -c "
import json
with open('/tmp/all_workflows.json') as f:
    wfs = json.load(f)
for wf in wfs:
    name = wf.get('name','')
    if any(k in name.lower() for k in ['rss','translate','curat','feed']):
        print(f'ID: {wf[\"id\"]} | Name: {name} | Active: {wf.get(\"active\")}')
        for n in wf.get('nodes',[]):
            print(f'  - {n[\"type\"]} : {n.get(\"name\",\"?\")}')
"
```

## Adding Feeds to the n8n Workflow

To add a new RSS source to the existing n8n workflow, edit the workflow in the n8n UI:

1. Add a new "RSS Feed Read" node with the feed URL
2. Add a "Set" node to tag the source (e.g. `source=verge`)
3. Connect the Set node to the Merge Feeds node (add an input)
4. If the feed is in English, add a Translate node before the Merge
5. Update the Merge Feeds node `numberInputs` to match
6. Save and activate

No changes needed to the Hermes cron — it reads whatever the n8n workflow produces.