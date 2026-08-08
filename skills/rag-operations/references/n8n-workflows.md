# n8n Workflow Templates for RAG Pipelines

## Ingestion workflow (single document)

Webhook: `POST /webhook/rag-ingest`

```json
{
  "name": "RAG - Docs Ingestion",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "rag-ingest",
        "responseMode": "responseNode",
        "options": {}
      },
      "name": "Webhook Ingest",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [240, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://172.17.0.1:9200/embed",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ { \"texts\": [$json.body.content] } }}",
        "options": {"timeout": 30000}
      },
      "name": "Generate Embedding",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [460, 300]
    },
    {
      "parameters": {
        "method": "PUT",
        "url": "http://172.17.0.1:6333/collections/<collection>/points",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ { \"points\": [ { \"id\": $now.toMillis(), \"vector\": $json.embeddings[0], \"payload\": { \"title\": $('Webhook Ingest').item.json.body.title, \"content\": $('Webhook Ingest').item.json.body.content, \"source\": $('Webhook Ingest').item.json.body.source || 'manual', \"category\": $('Webhook Ingest').item.json.body.category || 'general', \"ingested_at\": $now.toISO() } } ] } }}",
        "options": {}
      },
      "name": "Store in Qdrant",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [680, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"status\": \"ok\", \"message\": \"Document ingested\", \"title\": $('Webhook Ingest').item.json.body.title, \"vector_dim\": $json.dim || 384 } }}",
        "options": {"responseCode": 200}
      },
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [900, 300]
    }
  ],
  "connections": {
    "Webhook Ingest": {"main": [[{"node": "Generate Embedding", "type": "main", "index": 0}]]},
    "Generate Embedding": {"main": [[{"node": "Store in Qdrant", "type": "main", "index": 0}]]},
    "Store in Qdrant": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
  },
  "settings": {"executionOrder": "v1"}
}
```

## Auto-ingest workflow (from URL)

Webhook: `POST /webhook/rag-ha-ingest-url`

Fetches a URL, extracts text from HTML, chunks it (1000 chars, 200 overlap, max 10 chunks),
embeds each chunk, and stores in Qdrant.

Key Code node (Extract & Chunk):
```javascript
function htmlToText(html) {
  html = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  html = html.replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '');
  html = html.replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '');
  html = html.replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '');
  html = html.replace(/<br\s*\/?>/gi, '\n');
  html = html.replace(/<\/(p|div|h[1-6]|li|tr)>/gi, '\n');
  html = html.replace(/<[^>]+>/g, '');
  html = html.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
           .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ');
  html = html.replace(/\n{3,}/g, '\n\n').replace(/^[\s]+/gm, '').trim();
  return html;
}

const chunkSize = 1000;
const overlap = 200;
const chunks = [];
for (let i = 0; i < text.length; i += chunkSize - overlap) {
  const chunk = text.substring(i, i + chunkSize).trim();
  if (chunk.length > 50) chunks.push({json: {title, content: chunk, source: url, category, chunk_index: chunks.length}});
  if (i + chunkSize >= text.length) break;
}
return chunks.slice(0, 10);
```

## Query workflow (with guard-rail chunks)

Webhook: `POST /webhook/rag-query`

The query workflow has 6 nodes in a sequential chain (NOT parallel branches):
1. Webhook Query → 2. Embed Query → 3. Search Qdrant → 4. Merge Context (Code node) → 5. Hermes LLM → 6. Respond

The Merge Context Code node does an inline `fetch()` for guard-rail chunks:
```javascript
const embed = $('Embed Query').item.json.embeddings[0];
const searchResults = $('Search Qdrant').item.json.result || [];

// Guard-rail search via inline fetch (NOT a parallel HTTP Request node)
const guardBody = JSON.stringify({
  vector: embed,
  limit: 2,
  with_payload: true,
  score_threshold: 0.2,
  filter: { must: [{ key: 'category', match: { value: 'templates-guard' } }] }
});

let guardResults = [];
try {
  const resp = await fetch('http://172.17.0.1:6333/collections/<collection>/points/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: guardBody
  });
  const data = await resp.json();
  guardResults = data.result || [];
} catch(e) { /* continue without guard */ }

// Build context
let contextParts = searchResults.map(item => {
  const p = item.payload;
  return `[${p.title}] (${p.source})\n${p.content}`;
});
if (guardResults.length > 0) {
  contextParts.push(guardResults.map(item => `[BONNES PRATIQUES] ${item.payload.content}`).join('\n\n'));
}
```

## System prompt for LLM (anti-hallucination)

```
Tu es un assistant expert Home Assistant. Reponds en francais.

REGLES ABSOLUES:
1. Tu ne peux repondre QUE avec les informations presentes dans le contexte fourni.
2. Si le contexte ne contient pas la reponse, dis-le explicitement.
3. NE JAMAIS completer avec des connaissances externes.
4. NE JAMAIS inventer de syntaxe, de parametres ou de fonctions.
5. Si le contexte mentionne des bonnes pratiques (sections [BONNES PRATIQUES]), inclus-les.
6. Cite les sources utilisees avec leur URL.
7. Si tu identifies une contradiction, signale-la.
```

Temperature: 0.1

## Batch sitemap ingestion script

```python
import json, urllib.request, time

# Read URLs from sitemap
with open("/tmp/ha_urls.txt") as f:
    urls = [line.strip() for line in f if line.strip()]

for i, url in enumerate(urls):
    payload = json.dumps({"url": url, "category": category}).encode()
    req = urllib.request.Request(
        "http://localhost:5678/webhook/rag-ha-ingest-url",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=90)
        result = json.loads(resp.read())
        print(f"[{i+1}/{len(urls)}] OK ({result.get('chunks_stored', 0)} chunks): {url}")
    except Exception as e:
        print(f"[{i+1}/{len(urls)}] FAIL: {url} - {e}")
    time.sleep(0.3)  # avoid overwhelming n8n
```

## s6 service setup for embedding service

### run script
```sh
#!/bin/sh
set -e
export HOME=/opt/data
cd /opt/data/rag
exec /opt/data/rag-venv/bin/python3 embedding_service.py
```

### log/run script
```sh
#!/bin/sh
: "${HERMES_HOME:=/opt/data}"
log_dir="$HERMES_HOME/logs/embed-service"
mkdir -p "$log_dir"
rm -f "$log_dir/lock"
exec s6-log 1 n10 s1000000 T "$log_dir"
```

### finish script
```sh
#!/bin/sh
if [ "$1" = "78" ]; then exit 125; fi
exit 0
```

### type file
```
longrun
```

### Setup commands
```bash
mkdir -p /run/service/embed-service/log
cp run.sh /run/service/embed-service/run
cp log.sh /run/service/embed-service/log/run
cp finish.sh /run/service/embed-service/finish
echo "longrun" > /run/service/embed-service/type
chmod +x /run/service/embed-service/run /run/service/embed-service/log/run /run/service/embed-service/finish
# Start supervision (background)
/command/s6-supervise /run/service/embed-service &
# Verify
sleep 5 && /command/s6-svstat /run/service/embed-service
```

## Key ports and endpoints

| Service | Address from Hermes | Address from n8n | Endpoint |
|---------|-------------------|-------------------|----------|
| LiteLLM (embeddings) | localhost:4000 | https://litelllm.jefe.al/v1 | POST /v1/embeddings |
| FastEmbed (legacy) | localhost:9200 | 172.17.0.1:9200 | POST /embed, GET /health |
| Qdrant | localhost:6333 | 172.17.0.1:6333 | REST API |
| Hermes API | localhost:9119 | 172.17.0.1:9119 | POST /v1/chat/completions |
| n8n | localhost:5678 | — | Webhooks + REST API |

⚠️ **LiteLLM from n8n**: LiteLLM Docker is bound to `127.0.0.1:4000` only (intentional,
user does not want it on public IP). n8n cannot reach it via `172.17.0.1:4000`.
Use the Pangolin URL `https://litelllm.jefe.al/v1` instead. Timeout must be 60s+
due to external round-trip. See SKILL.md pitfall.

## LiteLLM embedding node config (current)

When using LiteLLM as embedding provider in n8n HTTP Request nodes:

**Request**:
- Method: POST
- URL: `https://litelllm.jefe.al/v1/embeddings` (Pangolin URL — works from n8n container)
- Headers: `Authorization: Bearer <key>`, `Content-Type: application/json`
- Body (n8n expression): `={{ { "model": "qwen3-embedding", "input": $json.content } }}`
- Timeout: 60000ms (Pangolin round-trip can be slow; 30s default is too short)

**Response parsing** (in downstream Qdrant nodes):
- Vector path: `$json.data[0].embedding` (NOT `$json.embeddings[0]` — that was FastEmbed)

**Auth**: use manual headers (`sendHeaders: true`), NOT predefined credential type.
The `openAiApi` credential type does not work reliably on HTTP Request nodes.

**Why Pangolin URL and not 172.17.0.1:4000**: LiteLLM Docker container is bound to
`127.0.0.1:4000` only (intentional — user does not want it on public IP). n8n runs in
a separate Docker container and cannot reach `127.0.0.1` of the host. The Pangolin
tunnel (`litelllm.jefe.al`) is the correct way for n8n to reach LiteLLM.
Note: `172.17.0.1:4000` also fails because LiteLLM is not bound to `0.0.0.0`.