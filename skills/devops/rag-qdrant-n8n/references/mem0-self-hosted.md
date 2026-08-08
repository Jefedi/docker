# Mem0 Self-Hosted — Long-Term AI Memory

Mem0 = long-term semantic memory for AI agents. Self-hosted via Docker, integrated with LiteLLM (sovereign EU routing) and n8n AI Agent tools.

## Architecture

- **3 containers**: mem0 API (8888→8000), Postgres pgvector (8432→5432), mem0-dashboard (3101→3000)
- **Compose path**: `/srv/docker/mem0/server/docker-compose.yaml`
- **Networks**: `mem0-dev_mem0_network` (internal) + `litellm_default` (external, for LiteLLM)
- **LLM**: `mistral-small-latest` via LiteLLM (fact extraction from messages)
- **Embeddings**: `mistral/mistral-embed` via LiteLLM (vector search)
- **Auth**: API key (`m0sk_...` format), `AUTH_DISABLED=false`

## Key Env Variables

```env
OPENAI_API_KEY=<LiteLLM virtual key>
OPENAI_BASE_URL=http://litellm:4000/v1     # NOT OPENAI_API_BASE_URL — SDK reads OPENAI_BASE_URL
MEM0_DEFAULT_LLM_MODEL=mistral-small-latest   # must match LiteLLM model name exactly
MEM0_DEFAULT_EMBEDDER_MODEL=mistral/mistral-embed  # must match LiteLLM model name exactly
AUTH_DISABLED=false
```

## Docker Compose — External Network for LiteLLM

```yaml
services:
  mem0:
    networks:
      - mem0_network
      - litellm_default    # external, for LiteLLM API access

networks:
  mem0_network:
    driver: bridge
  litellm_default:
    external: true
```

Same pattern for n8n — add `mem0-dev_mem0_network` as external network in n8n's compose.yaml so n8n can reach `http://mem0:8000` without manual `docker network connect` after each restart.

## Critical Pitfalls

### 1. OPENAI_BASE_URL vs OPENAI_API_BASE_URL
The OpenAI Python SDK reads `OPENAI_BASE_URL`, NOT `OPENAI_API_BASE_URL`. Wrong variable → Mem0 falls back to `https://api.openai.com/v1/embeddings` → 401 Unauthorized. Logs show `POST https://api.openai.com/v1/embeddings "HTTP/1.1 401 Unauthorized"`.

### 2. Model names must match LiteLLM exactly
Check with: `curl -s http://localhost:4000/v1/models -H "Authorization: Bearer <key>" | python3 -m json.tool | grep id`. If LiteLLM lists `mistral/mistral-embed`, the `.env` must say `mistral/mistral-embed`, not `mistral-embed`.

### 3. AUTH_DISABLED=true still rejects Authorization: Bearer with API keys
When `AUTH_DISABLED=true`, Mem0 ignores auth headers BUT if it receives `Authorization: Bearer m0sk_...`, it tries to parse as JWT and rejects with `"Invalid or expired token."`. API keys work only with `X-API-Key` header. Set `AUTH_DISABLED=false` and use `X-API-Key` for proper auth.

### 4. n8n native Mem0 node incompatible
`@mem0/n8n-nodes-mem0.mem0Tool` sends `Authorization: Bearer <key>` which Mem0 rejects. Use `@n8n/n8n-nodes-langchain.toolHttpRequest` (typeVersion 1.1) with `X-API-Key` header instead.

### 5. Docker network lost on compose down/up
`docker network connect litellm_default mem0-dev-mem0-1` is lost after `docker compose down && up`. Must declare `litellm_default` as external network in compose.yaml.

### 6. mistral-embed in LiteLLM must be embedding model
LiteLLM config must use `model: mistral/mistral-embed` (the `mistral/` prefix tells LiteLLM it's an embedding model). If declared wrong, LiteLLM sends to `/v1/chat/completions` instead of `/v1/embeddings`.

### 7. `docker compose up -d` doesn't reload .env
After editing `.env`, must use `docker compose down && docker compose up -d --force-recreate` to pick up new env vars. Plain `up -d` reuses cached container config.

## Admin Account & API Key (CLI)

```bash
# Register admin
docker exec mem0-dev-mem0-1 sh -c 'python3 -c "
import requests
r = requests.post(\"http://localhost:8000/auth/register\", json={\"name\":\"Jefe\",\"email\":\"jefe@jefe.al\",\"password\":\"<pass>\",\"confirm_password\":\"<pass>\"})
print(r.status_code, r.text[:500])
"'

# Login + create API key
docker exec mem0-dev-mem0-1 sh -c 'python3 -c "
import requests
r = requests.post(\"http://localhost:8000/auth/login\", json={\"email\":\"jefe@jefe.al\",\"password\":\"<pass>\"})
token = r.json()[\"access_token\"]
r2 = requests.post(\"http://localhost:8000/api-keys\", headers={\"Authorization\":f\"Bearer {token}\"}, json={\"label\":\"n8n\"})
print(r2.status_code, r2.text[:500])
"'
```

## n8n AI Agent Integration

### Correct node type for AI tools
Use `@n8n/n8n-nodes-langchain.toolHttpRequest` (typeVersion **1.1**) — this is the only HTTP tool type that:
- Produces `ai_tool` output (required by AI Agent node)
- Is available in n8n 2.32.x

**Do NOT use:**
- `n8n-nodes-base.httpRequest` — no `ai_tool` output, connection rejected
- `n8n-nodes-base.httpRequestTool` v4.4 — may not be installed, shows "Install this node"
- `@n8n/n8n-nodes-langchain.toolHttpRequest` v1.6 — not available in n8n 2.32.x

### Mem0 Search tool config
- URL: `http://mem0:8000/memories/search` (Docker network name, NOT localhost)
- Method: POST
- Headers: `X-API-Key: m0sk_...`, `Content-Type: application/json`
- Body: `={"query": "{{ $fromAI('query', 'Search query', 'string') }}", "user_id": "jefe", "limit": 10}`
- Connection: `ai_tool` → AI Agent

### Mem0 Add tool config
- URL: `http://mem0:8000/memories`
- Body: `={"messages": [{"role": "user", "content": "{{ $fromAI('content', 'Info to remember', 'string') }}"}], "user_id": "jefe"}`
- Connection: `ai_tool` → AI Agent

### Memory architecture distinction
- **Postgres Chat Memory** (`ai_memory`): session-level conversation history (short-term, per chat)
- **Mem0 tools** (`ai_tool`): long-term semantic memory (persists across sessions, agent decides when to search/add)

## API Testing

```bash
# Search
curl -s -X POST http://localhost:8888/memories/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: m0sk_..." \
  -d '{"query": "où habite Jefe", "user_id": "jefe", "limit": 5}'

# Add
curl -s -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -H "X-API-Key: m0sk_..." \
  -d '{"messages": [{"role": "user", "content": "Je suis Jefe"}], "user_id": "jefe"}'

# List
curl -s http://localhost:8888/memories -H "X-API-Key: m0sk_..."
```