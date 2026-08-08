---
name: rag-qdrant-n8n
description: "RAG with Qdrant + FastEmbed + n8n. Use for vector search."
version: 1.0.0
created_by: agent
tags: [rag, qdrant, fastembed, n8n, embeddings, vector-search, hermes-api]
---

# RAG Pipeline — Qdrant + FastEmbed + n8n + Hermes API

Build a Retrieval-Augmented Generation pipeline on Jefe's homelab using existing infrastructure: Qdrant vector DB, FastEmbed for embeddings, n8n for orchestration, and the Hermes API server as LLM.

## Architecture

```
Docs → n8n webhook → FastEmbed (:9200) → Qdrant (:6333)
                                                    ↓
Query → n8n webhook → FastEmbed (:9200) → Qdrant search → Hermes API (:9119) → Answer
```

**Components:**

| Component | Location | Port | Purpose |
|-----------|----------|------|---------|
| FastEmbed service | Hermes container (host network) | 9200 | Generate 384-dim embeddings via ONNX |
| Qdrant | Docker container on host | 6333 | Vector store with cosine similarity |
| n8n | Docker container on host | 5678 | Workflow orchestration (webhooks) |
| Hermes API | Hermes container (host network) | 9119 | LLM for answer generation (model: `hermes-agent`) |

## Step 1 — FastEmbed Embedding Service

FastEmbed runs inside the Hermes container (which uses `network_mode: host`). It uses a separate venv to avoid polluting the Hermes Python environment.

### Installation

```bash
uv venv /opt/data/rag-venv --python 3.13
uv pip install --python /opt/data/rag-venv/bin/python "qdrant-client[fastembed]"
```

### Service script

The service is at `/opt/data/rag/embedding_service.py`. Key points:
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 90MB, downloads from HuggingFace on first run)
- Endpoints: `POST /embed` (texts → embeddings), `GET /health`
- Listens on `0.0.0.0:9200`

### Starting the service

```bash
/opt/data/rag-venv/bin/python3 /opt/data/rag/embedding_service.py &
```

⚠️ **The service is NOT persistent** — it dies when the Hermes container restarts. To make it persistent, either create an s6 service or add a watchdog cron.

### s6-supervised (persistent, recommended)

The FastEmbed service can be registered as a runtime s6 service under `/run/service/embed-service/`. This makes it auto-restart on crash and survive Hermes container restarts (the s6 reconciler picks it up).

**Critical**: Runtime s6 services must use `#!/bin/sh` as the shebang — NOT `#!/command/with-contenv sh` (that binary is only available to static services built into the Docker image; runtime services get exit code 127). Use absolute paths to binaries (e.g. `/opt/data/rag-venv/bin/python3`) instead of venv activation.

```bash
# Create service directory
mkdir -p /run/service/embed-service/log
echo "longrun" > /run/service/embed-service/type

# run script — use #!/bin/sh, NOT #!/command/with-contenv sh
cat > /run/service/embed-service/run << 'EOF'
#!/bin/sh
set -e
export HOME=/opt/data
cd /opt/data/rag
exec /opt/data/rag-venv/bin/python3 embedding_service.py
EOF
chmod +x /run/service/embed-service/run

# log/run script
cat > /run/service/embed-service/log/run << 'EOF'
#!/bin/sh
: "${HERMES_HOME:=/opt/data}"
log_dir="$HERMES_HOME/logs/embed-service"
mkdir -p "$log_dir"
rm -f "$log_dir/lock"
exec s6-log 1 n10 s1000000 T "$log_dir"
EOF
chmod +x /run/service/embed-service/log/run

# finish script
cat > /run/service/embed-service/finish << 'EOF'
#!/bin/sh
if [ "$1" = "78" ]; then exit 125; fi
exit 0
EOF
chmod +x /run/service/embed-service/finish

chown -R hermes:hermes /run/service/embed-service/

# Start s6 supervision
/command/s6-supervise /run/service/embed-service &
# Verify
sleep 5
/command/s6-svstat /run/service/embed-service
# → "up (pid XXXX) N seconds"
```

See `references/s6-embed-service-setup.md` for the full walkthrough and troubleshooting.

### Available FastEmbed models

| Model | Dim | Size | Notes |
|-------|-----|------|-------|
| `BAAI/bge-small-en-v1.5` | 384 | 67MB | Smallest, English |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 90MB | Default, good balance |
| `nomic-ai/nomic-embed-text-v1.5-Q` | 768 | 130MB | Quantized, English |
| `BAAI/bge-base-en-v1.5` | 768 | 210MB | Better accuracy |
| `jinaai/jina-embeddings-v2-base-de` | 768 | 320MB | German |
| `mixedbread-ai/mxbai-embed-large-v1` | 1024 | 640MB | Best accuracy |

For multilingual docs, consider `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, 220MB).

### Upgrading to multilingual embeddings (FR/EN)

The default `all-MiniLM-L6-v2` is English-only. For RAG serving French queries on English docs,
upgrade to a multilingual model. See `references/embedding-model-comparison.md` for the full
benchmark and pricing comparison (Qwen3-Embedding-8B, BGE-M3, e5-large, etc.).

**Recommended upgrade path — route embeddings through LiteLLM:**

1. Add the embedding model to LiteLLM config (on the host, see `hermes-infra-config` skill →
   "LiteLLM Proxy" section for how to add providers)
2. Create a NEW Qdrant collection with the correct vector size (e.g. 4096 for Qwen3-8B, 1024 for
   BGE-M3 or e5-large — MUST match the model output dim)
3. Re-ingest all documents into the new collection
4. Update n8n workflows to point to the new collection and use the new embedding endpoint
5. Delete the old collection once verified

**⚠️ Dimension change = full re-ingestion.** You cannot change the embedding model on an existing
Qdrant collection — vector dimensions are fixed at creation time.

**Architecture when routing through LiteLLM:**

```
n8n / embed service → LiteLLM (:4000) → OpenRouter API → Qwen3-Embedding-8B
```

This centralizes all API keys and providers. Adding Mistral, OpenAI, or other providers later
only requires a LiteLLM config change — n8n workflows and embed service stay unchanged.

**Privacy tiering:** for sensitive docs (Paperless, emails), use a self-hosted model
(`multilingual-e5-large` via FastEmbed or `qwen3-embedding:0.6b` via Ollama) instead of API-based.

## Step 2 — Qdrant Collection

```bash
curl -X PUT http://localhost:6333/collections/ha-docs \
  -H "Content-Type: application/json" \
  -d '{"vectors":{"size":384,"distance":"Cosine"},"optimizers_config":{"default_segment_number":2}}'
```

**Key parameters:**
- `size` MUST match the embedding model dimension (384 for MiniLM)
- `distance`: `Cosine` for semantic similarity
- Collection name should describe the content domain

## Step 3 — n8n Workflows

### Critical: Docker Bridge Networking

n8n runs in a separate Docker container and CANNOT reach services on `localhost`. All HTTP Request nodes must use `172.17.0.1` (Docker bridge gateway):

| Service | n8n URL |
|---------|---------|
| FastEmbed | `http://172.17.0.1:9200` |
| Qdrant | `http://172.17.0.1:6333` |
| Hermes API | `http://172.17.0.1:9119` |

### Workflow 1 — Ingestion (`POST /webhook/rag-ingest`)

**Input:** `{"title":"...","content":"...","source":"...","category":"..."}`

**Flow:** Webhook → POST /embed → PUT /points (Qdrant) → Respond

Qdrant point IDs must be unique unsigned integers or UUIDs. `$now.toMillis()` works but can collide in batch ingestion.

### Workflow 2 — Query (`POST /webhook/rag-query`)

**Input:** `{"query":"..."}`

**Flow (sequential, 6 nodes):** Webhook → POST /embed → Search Qdrant (limit=5, score_threshold=0.3) → Search Guard (HTTP Request, threshold=0.0, category filter) → Merge Context (Code node) → POST /v1/chat/completions (Hermes API) → Respond

Hermes API auth: `Authorization: Bearer <API_SERVER_KEY from .env>`, model: `hermes-agent`, temperature: 0.1

#### Guard chunk injection — prevents hallucination on safety-critical knowledge

Safety-critical knowledge (e.g. "use `has_value()` not `is defined` for entity guards") can score below the main search threshold when the user's question is semantically distant. To guarantee this knowledge is always injected:

1. **Ingest guard-rail chunks** with a specific category (e.g. `category: "templates-guard"`)
2. **Add a dedicated Qdrant search node** (sequential HTTP Request, NOT async `fetch()` in a Code node) with `score_threshold: 0.0` and `filter.must` on the guard category
3. **Merge Context Code node** tags guard results as `[BONNES PRATIQUES]` in the prompt
4. **System prompt** instructs the LLM to include `[BONNES PRATIQUES]` sections obligatorily

**Anti-hallucination system prompt** (temperature 0.1):
- Only answer from provided context
- If context doesn't contain the answer, say so explicitly
- NEVER complete with external knowledge
- NEVER invent syntax/parameters/functions not in context
- Include [BONNES PRATIQUES] sections obligatorily
- Cite sources with URLs
- Flag contradictions between context and common practice

### Creating workflows via n8n REST API

```bash
N8N_KEY=$(cat /opt/data/.n8n_api_key)
# Create
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" -d @workflow.json
# Activate (separate call)
curl -X POST "http://localhost:5678/api/v1/workflows/<ID>/activate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

⚠️ **Webhook registration:** After creating a workflow, the webhook is NOT registered until activation. If 404 persists after activate, toggle deactivate→activate to force re-registration.

### n8n expression syntax for JSON body

```
={{ { "texts": [$json.body.content] } }}
```
- `$json` = current node input
- `$('NodeName').item.json` = access upstream node data
- `$now.toISO()` = timestamp

## Step 4 — Testing

```bash
curl -X POST http://localhost:5678/webhook/rag-ingest \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Some content","source":"test"}'

curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is this about?"}'
```

## Step 5 — Batch ingesting external documentation

To populate the RAG with an entire documentation site (e.g. Home Assistant):

1. **Fetch the sitemap** to get current URLs (don't hardcode paths — sites restructure):
```bash
curl -s https://www.home-assistant.io/sitemap.xml | grep -o '<loc>[^<]*</loc>' | sed 's/<loc>//;s|</loc>||' | grep '/docs/' > urls.txt
```

2. **POST each URL** to the auto-ingest webhook with a small delay:
```python
import json, urllib.request, time
for url in urls:
    payload = json.dumps({"url": url, "category": "docs"}).encode()
    req = urllib.request.Request("http://localhost:5678/webhook/rag-ha-ingest-url",
        data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=90)
    time.sleep(0.3)
```

3. **Verify** in Qdrant: `curl http://localhost:6333/collections/ha-docs | jq .result.points_count`

The auto-ingest workflow (ID: `a4MBBPRpVnwDRUd4`) fetches the page, strips HTML, chunks into 1000-char segments with 200-char overlap, embeds each chunk, and stores in Qdrant. Up to 10 chunks per page to avoid overload.

### Workflow 3 — Auto-ingest from URL (`POST /webhook/rag-ha-ingest-url`)

**Input:** `{"url":"https://...","category":"automation"}`

**Flow:** Webhook → HTTP GET (fetch page) → Code node (strip HTML, chunk text) → POST /embed → PUT /points (Qdrant)

This workflow has a Code node that:
- Removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` tags
- Converts HTML to plain text
- Chunks into 1000-char segments with 200-char overlap
- Limits to 10 chunks per page

## Pitfalls

- **`localhost` in n8n** → use `172.17.0.1`. #1 cause of "service refused connection" errors.
- **FastEmbed model download** → first run downloads ~90MB from HuggingFace. Needs internet.
- **Embedding dimension mismatch** → Qdrant collection `size` MUST match model output dim. Changing models = recreate collection.
- **Score threshold too low globally** → don't lower the main search threshold below 0.3 to make specific chunks pass — this injects noise into ALL queries. Use category-filtered guard chunk injection (threshold 0.0 + `filter.must`) for safety-critical knowledge that scores low.
- **`fetch()` in n8n Code node is async and silently fails** → `await fetch()` inside a Code node's `jsCode` does NOT work reliably in n8n CE. The call returns nothing (guard_count: 0) without throwing. Use a dedicated HTTP Request node in the sequential pipeline instead.
- **n8n parallel branches with v1 executionOrder** → splitting the flow into two branches (main search + guard search) that merge into a Code node causes "Node hasn't been executed" errors. Keep the pipeline strictly sequential: Embed → Search → Search Guard → Merge → LLM.
- **LLM hallucination on missing context** → when retrieval returns no results or low-relevance results, the LLM will "complete" with generic knowledge (e.g. suggesting `is defined` from Jinja2 docs when HA's `has_value()` is the correct guard). Mitigate with: (a) strict system prompt forbidding external knowledge, (b) temperature 0.1, (c) guard chunk injection.
- **n8n webhook 404** → always call `/activate` after create. Toggle if needed.
- **Hermes API key** → in `.env` as `API_SERVER_KEY`. Hermes masks `sk-*` in output — use `od -c` to read.
- **FastEmbed venv isolation** → separate venv, NOT Hermes venv. ONNX runtime can conflict.
- **Non-persistent service** → use s6 supervision (see Step 1 s6 section). Runtime s6 services must use `#!/bin/sh`, not `#!/command/with-contenv sh` (exit 127).
- **Ollama Cloud = no embeddings** → only LLMs. Use FastEmbed locally.
- **404 on HA doc URLs** → HA restructures docs frequently. Always use the sitemap, never hardcoded URLs (e.g. `/docs/automation/triggers/` → now `/docs/automation/trigger/`).
- **n8n webhook returns 200 but empty body** → workflow errored on a node. Check executions API for the error detail.
- **n8n workflow PUT silently fails** → the n8n REST API PUT `/workflows/<id>` may return 200 but not apply changes (especially node parameter edits). When updating a workflow, delete and recreate rather than PUT.
- **Verifying RAG answers** → don't trust the final answer alone. Check the n8n execution data (`/api/v1/executions/<id>?includeData=true`) to verify: (a) how many chunks were retrieved, (b) whether guard chunks were injected (`guard_count > 0`, `BONNES PRATIQUES in context`), (c) what was actually sent to the LLM. The LLM can reproduce correct-sounding text from conversation carry-over, not from the RAG.

## Mem0 — Long-Term AI Memory (alternative to Qdrant RAG)

Mem0 is a complementary long-term memory layer for AI agents (fact extraction + semantic search via Postgres pgvector). Unlike Qdrant RAG (document retrieval), Mem0 extracts discrete facts from conversations and stores them as searchable memory entries.

Self-hosted at `/srv/docker/mem0/server/`, integrated with LiteLLM (`mistral-small-latest` for extraction, `mistral/mistral-embed` for vectors) and n8n AI Agent via `toolHttpRequest` nodes.

**Key pitfall — n8n AI tool node type**: Only `@n8n/n8n-nodes-langchain.toolHttpRequest` (typeVersion **1.1**) produces `ai_tool` output AND is available in n8n 2.32.x. Other types (`n8n-nodes-base.httpRequest`, `n8n-nodes-base.httpRequestTool` v4.4, `toolHttpRequest` v1.6) either lack `ai_tool` output or aren't installed.

**Key pitfall — Mem0 auth**: Mem0 API keys use `X-API-Key` header, NOT `Authorization: Bearer`. The native n8n Mem0 node (`@mem0/n8n-nodes-mem0.mem0Tool`) sends `Authorization: Bearer` which Mem0 rejects. Use `toolHttpRequest` with `X-API-Key` header.

See `references/mem0-self-hosted.md` for full deployment guide, env vars, compose config, CLI admin setup, and n8n integration.

## References

- `references/s6-embed-service-setup.md` — full s6 service setup walkthrough (shebang gotcha, step-by-step, troubleshooting)
- `references/mem0-self-hosted.md` — Mem0 self-hosted deployment, LiteLLM integration, n8n AI Agent tools, pitfalls
- `references/guard-chunk-injection.md` — guard chunk injection pattern & RAG testing methodology (prevents hallucination on safety-critical knowledge)
- `references/embedding-model-comparison.md` — multilingual embedding model benchmark (MTEB scores, pricing, FR/EN comparison, self-hosted vs API)
- `scripts/batch-ingest-sitemap.py` — batch ingest URLs from a sitemap into the RAG
- `references/embedding-service.py` — full FastEmbed HTTP service script
- `references/rag-ingest-workflow.json` — n8n workflow JSON for ingestion
- `references/rag-query-workflow.json` — n8n workflow JSON for query

## Existing infrastructure (Jefe's homelab)

- Qdrant 1.18.3 on `:6333` (Docker, AX42) — collection `ha-docs`, ~2324 vectors
- n8n CE on `:5678` (Docker, API key at `/opt/data/.n8n_api_key`)
- Hermes API on `:9119` (key in `.env` → `API_SERVER_KEY`)
- FastEmbed service on `:9200` (s6-supervised, `/run/service/embed-service`, venv `/opt/data/rag-venv`) — ⚠️ s6 service dir can disappear after container restart; process may still run but unsupervised. Check with `ls /run/service/embed-service/` and `pgrep -f embedding_service`
- LiteLLM proxy on `:4000` (key in `.env` → `OPENROUTER_API_KEY` available) — can route embeddings too, not just LLMs
- Ollama Cloud — LLMs only (glm-5.2, minimax-m3, etc.) — NO embeddings
- n8n workflows: `rag-ingest` (JLbUk8sEKU7rKJ1p), `rag-query` (lNssKJlsXR9axFyR), `rag-ha-ingest-url` (a4MBBPRpVnwDRUd4)
- Guard-rail chunks: category `templates-guard`, injected via sequential HTTP Request node (threshold 0.0 + category filter)
- **OpenRouter API key** in `.env` → `OPENROUTER_API_KEY` (sk-or-...bb39) — for embedding model upgrades via LiteLLM