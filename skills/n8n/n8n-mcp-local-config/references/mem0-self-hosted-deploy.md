# Mem0 Self-Hosted Deployment

## Overview
Mem0 = memory layer for AI agents. Self-hosted = 3 Docker containers :
- **mem0** (FastAPI REST API + dashboard) — port 8888
- **Postgres pgvector** (embeddings) — port 8432
- **Neo4j** (entity graph) — ports 8474/8687 (optional, for graph memory)

## Prerequisites
- Docker + Docker Compose
- `OPENAI_API_KEY` (default LLM + embedder) — can be replaced by LiteLLM
- n8n community node `@mem0/n8n-nodes-mem0` installed

## Deployment (official repo)

```bash
git clone https://github.com/mem0ai/mem0.git /opt/data/mem0
cd /opt/data/mem0/server
cp .env.example .env
# Edit .env:
#   OPENAI_API_KEY=sk-...
#   POSTGRES_PASSWORD=<strong password>
#   JWT_SECRET=<openssl rand -base64 48>
#   AUTH_DISABLED=true  (for local dev only)
#   MEM0_TELEMETRY=false
docker compose up -d --build
```

## Port binding — localhost only

The official docker-compose.yaml binds on `0.0.0.0` by default. Patch ALL port mappings to `127.0.0.1`:

```yaml
# mem0 API
ports:
  - "127.0.0.1:8888:8000"

# dashboard
ports:
  - "127.0.0.1:3000:3000"

# postgres pgvector
ports:
  - "127.0.0.1:8432:5432"

# neo4j (if used)
ports:
  - "127.0.0.1:8474:7474"
  - "127.0.0.1:8687:7687"
```

## Connecting n8n to Mem0

The containers run on their own Docker network (`mem0_network`). To let n8n reach Mem0:

```bash
docker network connect mem0-dev_mem0_network n8n-n8n-1
```

In n8n, the Mem0 node points to `http://mem0:8888` (service name on the shared network).

## Architecture in n8n

```
n8n AI Agent
  ├── Postgres Chat Memory (slot Memory — contexte conversation)
  ├── Mem0 (slot Tool — mémoires long-terme, extraction de faits)
  │     ├── Postgres pgvector (embeddings)
  │     └── Neo4j (graphe d'entités)
  ├── Get News (tool)
  └── Get Weather (tool)
```

**Important :** Mem0 est un TOOL, pas un MEMORY backend. Il ne remplace pas Postgres Chat Memory. Les deux coexistent :
- Postgres = fenêtre de conversation récente
- Mem0 = faits persistants extraits par LLM, retrieval sémantique

## Souveraineté EU — remplacer OpenAI

Mem0 utilise OpenAI par défaut (gpt-5-mini pour extraction, text-embedding-3-small pour embeddings). Pour rester souverain :

Option 1 — LiteLLM (port 4000) :
```env
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=<litellm key>
MEM0_DEFAULT_LLM_MODEL=glm-5.2
MEM0_DEFAULT_EMBEDDER_MODEL=text-embedding-3-small
```

Option 2 — Ollama local pour embeddings :
- Requires `sentence-transformers` in the container (heavy, ~2GB PyTorch)
- Add to Dockerfile: `RUN pip install sentence-transformers`
- Extend `BUNDLED_EMBEDDER_PROVIDERS` in `server/main.py`

## Verification

```bash
# Containers running
docker compose ps

# API responds
curl -s http://127.0.0.1:8888/
# → 307 redirect to /docs

# Add a memory
curl -s -X POST http://127.0.0.1:8888/memories \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Je vis au Havre"}],"user_id":"jefe"}'

# Search memories
curl -s -X POST http://127.0.0.1:8888/search \
  -H "Content-Type: application/json" \
  -d '{"query":"où habite l utilisateur","user_id":"jefe"}'
```

## Gotchas

- **Neo4j start_period**: 90s on first boot. If mem0 crashes on startup, it's usually Neo4j not being ready yet. Retry.
- **`docker compose restart` does NOT re-read `.env`**: use `docker compose up -d --force-recreate mem0` after `.env` changes.
- **`AUTH_DISABLED=true`**: local dev only. The server logs a warning on every boot.
- **`JWT_SECRET` required**: server returns 500 on auth endpoints if unset.
- **pgvector image**: official compose uses `pgvector/pgvector:pg17` (not `ankane/pgvector` as some blog posts show).