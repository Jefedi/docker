# Mem0 Self-Hosted Deployment Notes

## Architecture

Mem0 self-hosted = 3 Docker containers:
- **mem0** (FastAPI REST API, port 8888→8000)
- **postgres** (pgvector/pgvector:pg17, port 8432→5432)
- **mem0-dashboard** (Next.js UI, port 3101→3000)

Plus optionally Neo4j for graph memory (not in the official dev compose).

## Key Issues Encountered

### 1. Dev volume mount `.:/app` breaks production
The official `docker-compose.yaml` in `server/` has a dev mount `.:/app` that overwrites the Dockerfile build. Remove this line for production use.

### 2. `init-db.sh` file mount creates a directory
The compose mounts `./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh`. On first run, Docker creates a **directory** instead of a file if the host file doesn't exist at mount time. Remove the mount and create the DB manually:
```bash
docker compose up -d postgres
sleep 5
docker exec mem0-dev-postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE mem0_app;"
docker compose up -d
```

### 3. `OPENAI_BASE_URL` not `OPENAI_API_BASE_URL`
Mem0 uses the OpenAI Python SDK. The SDK reads `OPENAI_BASE_URL` for the custom endpoint. The `.env.example` may suggest `OPENAI_API_BASE_URL` — this is WRONG. The container will hit `api.openai.com` and get 401.

### 4. Hardcoded password in `alembic.ini`
`server/alembic.ini` has `sqlalchemy.url = postgresql+psycopg://postgres:postgres@postgres:5432/mem0_app`. The password is hardcoded as `postgres`. Set `POSTGRES_PASSWORD=postgres` in `.env` to match.

### 5. Network isolation — Mem0 can't reach LiteLLM
Mem0's compose creates its own bridge network. To route through LiteLLM (port 4000) for souverain AI:
```bash
docker network connect litellm_default mem0-dev-mem0-1
```
This must be re-run after every `docker compose down && up`.

### 6. LiteLLM virtual keys invalidated by config changes
Adding `mistral-embed` to LiteLLM via Web UI invalidated existing virtual API keys. Regenerate keys after model config changes.

### 7. Model name must match LiteLLM model_list
`mistral/mistral-small` → wrong. LiteLLM exposes it as `mistral-small-latest`. Check `curl http://localhost:4000/v1/models` for exact names.

### 8. Embeddings need a dedicated embedding model
LiteLLM must have `mistral-embed` declared as a model (not just a chat model). Mistral's `/v1/embeddings` endpoint is separate from `/v1/chat/completions`. Ensure the LiteLLM config routes `mistral-embed` to the embeddings endpoint, not chat.

## Working .env

```
OPENAI_API_KEY=<litellm-virtual-key>
OPENAI_BASE_URL=http://litellm:4000/v1
POSTGRES_PASSWORD=postgres
JWT_SECRET=<openssl rand -base64 48>
AUTH_DISABLED=true
MEM0_DEFAULT_LLM_MODEL=mistral-small-latest
MEM0_DEFAULT_EMBEDDER_MODEL=mistral-embed
MEM0_TELEMETRY=false
```

## Compose Modifications (sed one-liner)

```bash
sed -i \
  -e 's|"8888:8000"|"127.0.0.1:8888:8000"|' \
  -e '/- \.:\/app/d' \
  -e 's|"8432:5432"|"127.0.0.1:8432:5432"|' \
  -e '/- \.\/init-db.sh:\/docker-entrypoint-initdb.sh/d' \
  -e 's|"3000:3000"|"127.0.0.1:3101:3000"|' \
  -e 's|DASHBOARD_URL=http://localhost:3000|DASHBOARD_URL=http://localhost:3101|' \
  docker-compose.yaml
```

## n8n Integration

The `@mem0/n8n-nodes-mem0` community node is an **action/tool node**, NOT a LangChain memory backend. It connects as `ai_tool` to the AI Agent, not `ai_memory`. The agent decides when to call Mem0 (add/search memories). For conversation context retention, use Postgres Chat Memory in the `ai_memory` slot alongside Mem0 as a tool.

## Unresolved

- ASCII encoding error with Mistral Small generating Unicode characters (→ arrow) in fact extraction output. Mem0's `openai.py` embedder crashes with `'ascii' codec can't encode character`. This may require a Mem0 config to force UTF-8 or a different LLM model.