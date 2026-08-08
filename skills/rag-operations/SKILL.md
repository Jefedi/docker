---
name: rag-operations
description: "Build RAG pipelines with Qdrant, LiteLLM embeddings, and n8n."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [rag, qdrant, fastembed, n8n, embeddings, vector-search, litellm, openrouter]
---

# RAG Operations — Building and Running RAG Pipelines

## When to use

Use this skill when:
- Building a RAG (Retrieval Augmented Generation) knowledge base
- Setting up FastEmbed embedding services
- Configuring Qdrant vector stores
- Creating n8n workflows for document ingestion and semantic search
- Debugging RAG hallucination or retrieval quality issues
- Ingesting documentation sites into a vector database

## Architecture pattern

The canonical RAG pipeline in this environment:

1. **Embedding**: Qwen3-Embedding-8B via LiteLLM→OpenRouter (4096-dim, multilingual FR/EN, $0.01/M tokens)
2. **Vector store**: Qdrant (Docker on host, port 6333)
3. **LLM**: Hermes Agent API (OpenAI-compatible, port 9119)
4. **Orchestration**: n8n workflows (Docker container, port 5678)

### Data flow

```
Ingest:  URL/doc → fetch → chunk (1000 chars, 200 overlap) → embed via LiteLLM → store in Qdrant
Query:   question → embed via LiteLLM → search Qdrant (top-5) → [guard-rail chunks] → LLM with context → answer
```

### Embedding model — current and legacy

| Époque | Modèle | Dim | Provider | Langues | MTEB Multi |
|--------|--------|-----|----------|---------|------------|
| **Actuel (2026-07)** | Qwen3-Embedding-8B | 4096 | OpenRouter via LiteLLM | 100+ (FR natif) | 70.58 (#1) |
| Legacy (initial) | all-MiniLM-L6-v2 | 384 | FastEmbed local (s6, port 9200) | English only | ❌ |

**Sélection**: Qwen3-Embedding-8B choisi après comparatif exhaustif (OpenRouter, Mistral, Cohere,
OpenAI, Gemini, BGE-M3, self-hosted FastEmbed). Critères: multilingual FR/EN, perf MTEB, prix.
Résultat: $0.01/M tokens (même prix que BGE-M3, 10x moins que Mistral Embed).
Voir `references/embedding-model-comparison.md` pour le comparatif complet.

**Migration vers un nouveau modèle d'embedding** — quand on change de modèle, il faut:
1. Ajouter le modèle dans LiteLLM config (`/srv/docker/litellm/config.yaml` sur l'hôte AX42)
2. Redémarrer LiteLLM: `docker restart litellm` (sur l'hôte)
3. Créer une **nouvelle collection Qdrant** avec la bonne dimension (4096 pour Qwen3-8B)
4. Modifier l'embed service (ou les workflows n8n) pour appeler LiteLLM au lieu de FastEmbed local
5. **Ré-ingérer** tous les docs (les vecteurs d'un modèle ne sont pas compatibles avec un autre)
6. Mettre à jour les workflows n8n (query + ingest) avec le nouveau nom de collection
7. Optionnel: supprimer l'ancienne collection après validation

## Setting up the embedding service

### Current: LiteLLM as embedding provider (recommended)

Embeddings now go through LiteLLM (port 4000), which routes to OpenRouter's
Qwen3-Embedding-8B. No local model to run — just an API call.

**LiteLLM config** (on AX42 host, `/srv/docker/litellm/config.yaml`):
```yaml
model_list:
  - model_name: qwen3-embedding
    litellm_params:
      model: openrouter/qwen/qwen3-embedding-8b
      api_key: os.environ/OPENROUTER_API_KEY
```

**Usage from n8n or embed service**:
```
POST http://172.17.0.1:4000/v1/embeddings  (from n8n container)
POST http://127.0.0.1:4000/v1/embeddings   (from Hermes container)
Headers: Authorization: Bearer <LITELLM_KEY>
Body: {"model": "qwen3-embedding", "input": "text to embed"}
```

Response: standard OpenAI embeddings format, `data[0].embedding` is a 4096-dim float array.

**n8n credential**: use the native OpenAI node with custom base URL
`http://172.17.0.1:4000/v1` and a LiteLLM API key. This gives access to all
LiteLLM models (LLMs + embeddings) from n8n.

### Legacy: FastEmbed local service (English-only, 384-dim)

The original FastEmbed service runs at port 9200 as an s6-supervised process.
It uses `all-MiniLM-L6-v2` (English-only, 384-dim). Still functional but
**should not be used for new collections** — Qwen3-Embedding-8B via LiteLLM
is the standard for all multilingual RAG work.

Install FastEmbed (only if needed for legacy compatibility):

```bash
uv venv /opt/data/rag-venv --python 3.13
uv pip install --python /opt/data/rag-venv/bin/python "qdrant-client[fastembed]"
```

### Create the HTTP service

A minimal embedding service (`embedding_service.py`):
- POST `/embed` `{"texts": ["text1", ...]}` → `{"embeddings": [[...], ...], "dim": 384, "count": N}`
- GET `/health` → `{"status": "ok", "model": "...", "dim": 384}`
- Model: `sentence-transformers/all-MiniLM-L6-v2` (90MB, 384-dim)
- First run downloads model weights from HuggingFace (~2s)

### Make it s6-persistent

`/etc/s6-overlay/s6-rc.d/` is **read-only**. Create a runtime service under `/run/service/`:

```
/run/service/embed-service/
├── run         (#!/bin/sh — exec /opt/data/rag-venv/bin/python3 embedding_service.py)
├── type        ("longrun")
├── finish      (exit 125 on code 78, else 0)
└── log/
    └── run     (s6-log → $HERMES_HOME/logs/embed-service/)
```

**CRITICAL**: Use `#!/bin/sh` as shebang, NOT `#!/command/with-contenv sh`. The latter
fails with "execlineb: fatal: unable to exec ifelse" for manually created runtime services.

Start supervision: `/command/s6-supervise /run/service/embed-service` (background process).
The service auto-restarts on crash and survives container restarts.

## Qdrant collection setup

**Current (Qwen3-Embedding-8B, 4096-dim)**:
```bash
curl -X PUT http://localhost:6333/collections/<name> \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 4096, "distance": "Cosine"}, "optimizers_config": {"default_segment_number": 2}}'
```

**Legacy (all-MiniLM-L6-v2, 384-dim)** — only for existing `ha-docs` collection:
```bash
curl -X PUT http://localhost:6333/collections/<name> \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}, "optimizers_config": {"default_segment_number": 2}}'
```

⚠️ **Dimension must match the embedding model exactly.** You cannot mix models
in the same collection. When upgrading the embedding model, create a new
collection and re-ingest everything.

Payload schema for points:
```json
{
  "id": "<unix_millis_int>",
  "vector": [0.01, "..."],
  "payload": {
    "title": "page title",
    "content": "chunk text",
    "source": "URL or manual",
    "category": "automation|configuration|templates|...",
    "chunk_index": 0,
    "ingested_at": "2026-07-27T17:00:00Z"
  }
}
```

## n8n workflow patterns

### Ingestion workflow

```
Webhook POST → Fetch page (HTTP Request) → Extract & Chunk (Code node) → Embed (HTTP Request) → Store in Qdrant (HTTP Request) → Respond
```

Chunking code (in Code node): strip HTML tags, split into 1000-char chunks with 200-char
overlap, limit to 10 chunks per page. See `references/n8n-workflows.md` for the full JSON.

### Query workflow

```
Webhook POST → Embed query (HTTP Request) → Search Qdrant (HTTP Request) → Merge Context (Code node with inline guard-rail fetch) → LLM (HTTP Request to Hermes API) → Respond
```

The Merge Context node does an inline `fetch()` to Qdrant for guard-rail chunks
(filtered by `category: "templates-guard"`) instead of using a parallel branch.

### n8n API management

```bash
N8N_KEY=$(cat /opt/data/.n8n_api_key)
# Create
curl -X POST http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" -d @workflow.json
# Activate (required for production webhooks)
curl -X POST http://localhost:5678/api/v1/workflows/<ID>/activate -H "X-N8N-API-KEY: $N8N_KEY"
# Update
curl -X PUT http://localhost:5678/api/v1/workflows/<ID> -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" -d @workflow.json
```

## Pitfalls

### n8n networking — CRITICAL
n8n runs in a **separate Docker container**. It CANNOT reach Hermes services via `localhost`.
All HTTP nodes in n8n workflows MUST use `172.17.0.1` (Docker bridge gateway IP) instead.
Using `localhost` → "The service refused the connection - perhaps it is offline" error
on the target HTTP Request node.

### LiteLLM Docker port binding — CRITICAL
LiteLLM runs as a Docker container on AX42. If its port mapping is `127.0.0.1:4000:4000`
(localhost-only), n8n **cannot** reach it via `172.17.0.1:4000` — it will get
"connection refused". The port must be mapped as `0.0.0.0:4000:4000` (or just `4000:4000`)
in the docker-compose so it's accessible from the Docker bridge gateway.

**To check on AX42**: `docker inspect litellm --format '{{json .HostConfig.PortBindings}}'`
**To fix**: edit `/srv/docker/litellm/docker-compose.yml`, change `127.0.0.1:4000:4000` to
`4000:4000`, then `docker compose down && docker compose up -d`.

**Working setup**: n8n uses the Pangolin external URL (`https://litelllm.jefe.al/v1/...`).
This is the **primary** path, not a fallback — the user intentionally keeps LiteLLM
bound to `127.0.0.1` for security (no public IP exposure). The Pangolin tunnel routes
n8n traffic to LiteLLM via the VPS. Timeout must be set to 60000ms in n8n nodes (the
default 30s is too short for the external round-trip).

### n8n credential type mismatch for embeddings — CRITICAL
The n8n `openAiApi` credential type (used for the native OpenAI node) does **NOT** work
reliably when applied to a generic HTTP Request node via `authentication: predefinedCredentialType`.
It can cause silent failures or empty error data. **Use manual headers instead**:

```json
{
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {"name": "Authorization", "value": "Bearer <LITELLM_KEY>"},
      {"name": "Content-Type", "value": "application/json"}
    ]
  }
}
```

This is the same pattern used by the Hermes LLM node in the query workflow.

### Embedding API format difference — FastEmbed vs LiteLLM
When migrating from FastEmbed local service to LiteLLM, the request AND response formats change:

| | FastEmbed (legacy, port 9200) | LiteLLM (current, port 4000) |
|--|-------------------------------|------------------------------|
| **Request body** | `{"texts": ["text1", ...]}` | `{"model": "qwen3-embedding", "input": "text"}` |
| **Response vector path** | `$json.embeddings[0]` | `$json.data[0].embedding` |
| **Auth** | None | `Authorization: Bearer <key>` header |
| **Dimension** | 384 | 4096 |

Every n8n node that calls the embed service AND every node that reads the embedding
from the response (Qdrant store, Qdrant search) must be updated with the new paths.

### n8n workflow update via API — deactivate/update/activate
When modifying workflows programmatically via the n8n REST API:

```bash
N8N_KEY=$(cat /opt/data/.n8n_api_key)
# 1. Deactivate (required before update)
curl -X POST http://localhost:5678/api/v1/workflows/<ID>/deactivate -H "X-N8N-API-KEY: $N8N_KEY"
# 2. Update with new nodes/connections
curl -X PUT http://localhost:5678/api/v1/workflows/<ID> -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" -d @patched.json
# 3. Reactivate
curl -X POST http://localhost:5678/api/v1/workflows/<ID>/activate -H "X-N8N-API-KEY: $N8N_KEY"
# 4. Wait 2-3s before testing
```

### n8n execution error inspection
The n8n API's `GET /api/v1/executions/<ID>` returns empty `data` by default. To get
error details (including the failing node, request context, and error message), use:

```bash
curl -s "http://localhost:5678/api/v1/executions/<ID>?includeData=true" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

The error is at `data.resultData.error` with `message`, `context.request` (shows the
actual URL/headers/body that were sent), and `context.response` (status code/body).

### n8n parallel branches — CRITICAL
`executionOrder: v1` does NOT support fan-out to parallel branches reliably. Two HTTP Request
nodes fed from one node → "Node 'X' hasn't been executed" error in the downstream merge node.
**Workaround**: use a single Code node with inline `fetch()` calls. Do NOT create a second
HTTP Request branch — do the second HTTP call from JavaScript inside a Code node instead.

### n8n webhook registration
After creating or updating a workflow, the webhook may not register immediately. If
`POST /webhook/<path>` returns empty body with 200 OK but the execution shows as error:
1. Deactivate: `POST /api/v1/workflows/<ID>/deactivate`
2. Update: `PUT /api/v1/workflows/<ID>` with the workflow JSON
3. Activate: `POST /api/v1/workflows/<ID>/activate`
4. Wait 2-3 seconds before testing

### RAG hallucination prevention
LLMs will "complete" answers with generic knowledge when retrieved context doesn't cover
a sub-topic. This is especially dangerous for domain-specific gotchas (e.g., HA's
`states.sensor.xxx` raising `UndefinedError` before `is defined` is evaluated).

**Prevention stack (all three required)**:
1. **Guard-rail chunks**: manually authored chunks covering domain-specific gotchas,
   tagged with a distinguishable category (e.g., `templates-guard`). Injected via filtered
   Qdrant search on every query (lower score_threshold, e.g., 0.2).
2. **Strict system prompt**: temperature 0.1, explicit "NE JAMAIS completer avec des
   connaissances externes" and "NE JAMAIS inventer de syntaxe, parametres ou fonctions".
3. **Source citation requirement**: prompt must require citing sources with URLs for
   verification.

### Documentation site crawling
Doc sites change URL structure over time. **Always pull URLs from the sitemap**
(`https://<site>/sitemap.xml`) rather than guessing or using cached URL lists. Old URLs
may 404. Filter sitemap URLs by path prefix (`/docs/`, `/integrations/`, etc.) and
ingest with a 0.3s delay between requests to avoid overwhelming n8n.

### Batch re-ingestion when migrating embedding models
When changing the embedding model (e.g., MiniLM→Qwen3), all documents must be re-embedded
because vectors from different models are not compatible. Key lessons from migrating 2324 docs:

- **Batch size 5, not 10**: large models (8B) via API are slow per request (~10-15s for 5 texts).
  Batches of 10 can timeout or hang indefinitely on certain batches.
- **Timeout 45-60s per embed call**: the Pangolin round-trip + 8B model inference can take 10-20s.
  The n8n default 30s timeout is too short. For Python scripts, use 45s.
- **Retry with backoff**: some batches fail transiently (rate limit, network blip). 3 retries
  with exponential backoff (3s, 6s, 9s) handles most cases.
- **Resume capability**: check `points_count` in the target collection before starting, skip
  already-processed docs. Prevents starting over after a hang or kill.
- **0.5s delay between batches**: avoids rate limiting on OpenRouter.
- **A batch can hang indefinitely**: if a batch gets stuck (no response, no timeout), the script
  appears to make no progress. Kill and restart — the resume logic picks up where it left off.

See `scripts/reingest_batch.py` for a ready-to-run script with all these features.

### Qdrant indexing lag
After bulk point insertion, `indexed_vectors_count` may show 0 — Qdrant indexes
asynchronously. `points_count` is the reliable count immediately after insertion.

## See also

- `references/n8n-workflows.md` — full workflow JSON templates for ingestion, query, and auto-ingest
- `references/embedding-model-comparison.md` — comparatif complet des modèles d'embedding multilingues (OpenRouter, Mistral, Cohere, OpenAI, Gemini, BGE-M3, FastEmbed) avec benchmarks MTEB, prix, et dimensions
- `scripts/reingest_batch.py` — batch re-embedding script with resume, retry, and progress reporting (for embedding model migrations)
- The `ha-rag` skill (user-owned) for the specific Home Assistant RAG instance