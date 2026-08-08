# Mem0 Self-Hosted Deployment Reference

## Overview
- **Path**: `/srv/docker/mem0/mem0/server/` (double `mem0/` because `mv` into existing dir)
- **Containers**: `mem0-dev-mem0-1` (API :8888), `mem0-dev-postgres-1` (pgvector :8432), `mem0-dev-mem0-dashboard-1` (:3101)
- **LLM**: `mistral-small-latest` via LiteLLM (EU sovereign)
- **Embeddings**: `mistral/mistral-embed` via LiteLLM (must match model_name in LiteLLM config exactly)

## Docker Compose Modifications
1. **Port bindings**: All bound to `127.0.0.1`
2. **Volume `.:/app`**: DELETE — overwrites built package with source, breaks pip install
3. **Volume `init-db.sh`**: DELETE — create DB manually instead:
   ```bash
   docker exec mem0-dev-postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE mem0_app;"
   ```
4. **Dashboard port**: 3000 → 3101 (3000 taken by DockHand)
5. **Networks**: Add `litellm_default` as external network so Mem0 can reach LiteLLM

## Environment Variables (.env)
```
OPENAI_API_KEY=<LiteLLM virtual key>
OPENAI_BASE_URL=http://litellm:4000/v1    # NOT OPENAI_API_BASE_URL
MEM0_DEFAULT_LLM_MODEL=mistral-small-latest
MEM0_DEFAULT_EMBEDDER_MODEL=mistral/mistral-embed
AUTH_DISABLED=false
JWT_SECRET=<random string>
APP_DB_NAME=mem0_app
DASHBOARD_URL=http://localhost:3101
```

## Critical Pitfalls

### OPENAI_BASE_URL vs OPENAI_API_BASE_URL
Mem0 uses the Python `openai` SDK which reads `OPENAI_BASE_URL`, NOT `OPENAI_API_BASE_URL`.
Wrong variable → falls back to `https://api.openai.com/v1/embeddings` → `401 Unauthorized`.

### AUTH_DISABLED=true Rejection Pattern
When `AUTH_DISABLED=true`, Mem0 STILL rejects `Authorization: Bearer <token>` with
"Invalid or expired token". It only accepts no-header requests OR `X-API-Key` header.
Set `AUTH_DISABLED=false` and use `X-API-Key` consistently.

### LiteLLM Model Names Must Match Exactly
- LiteLLM model `id` must match `MEM0_DEFAULT_EMBEDDER_MODEL` in `.env`
- If LiteLLM registers as `mistral/mistral-embed`, env var must be `mistral/mistral-embed`
- Verify: `curl -s http://localhost:4000/v1/models -H "Authorization: Bearer <key>" | python3 -m json.tool | grep embed`

### mistral-embed Must Be Declared as Embedding in LiteLLM
LiteLLM must recognize it as embedding model (prefix `mistral/`), not chat model.
Wrong declaration → sent to `/v1/chat/completions` → "Invalid model" error.

### --force-recreate Required for .env Changes
`docker compose down && docker compose up -d` does NOT reload env_file.
Use `docker compose down && docker compose up -d --force-recreate`.
Verify: `docker exec mem0-dev-mem0-1 sh -c "python3 -c \"import os; print(os.environ.get('OPENAI_API_KEY','NOT SET')[:20])\""`

## Admin Account Creation (CLI — dashboard may show "Network Error" via browser)
```bash
docker exec mem0-dev-mem0-1 sh -c 'python3 -c "
import requests
r = requests.post(\"http://localhost:8000/auth/register\", json={
    \"name\":\"Jefe\", \"email\":\"jefe@jefe.al\",
    \"password\":\"<password>\", \"confirm_password\":\"<password>\"
})
print(r.status_code, r.text[:500])
"'
```

## API Key Generation
```bash
docker exec mem0-dev-mem0-1 sh -c 'python3 -c "
import requests
r = requests.post(\"http://localhost:8000/auth/login\", json={
    \"email\":\"jefe@jefe.al\", \"password\":\"<password>\"
})
token = r.json()[\"access_token\"]
r2 = requests.post(\"http://localhost:8000/api-keys\",
    headers={\"Authorization\": f\"Bearer {token}\"},
    json={\"label\":\"n8n\"})
print(r2.status_code, r2.text[:500])
"'
```
Returns key format `m0sk_...` — use as `X-API-Key` header value.

## API Endpoints (Mem0 v0.x)
Discovered via `/openapi.json`:
- `POST /memories` — add memories (body: `{"messages": [...], "user_id": "..."}`)
- `GET /memories?user_id=...` — list all memories for a user
- `POST /search` — semantic search (body: `{"query": "...", "user_id": "...", "limit": N}`)
- `GET /memories/{memory_id}` — get specific memory
- `DELETE /memories/{memory_id}` — delete memory
- `POST /reset` — reset all memories

**IMPORTANT**: Search endpoint is `/search`, NOT `/memories/search`.

## Postgres Chat Memory for n8n AI Agent
1. Create DB: `docker exec mem0-dev-postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE n8n_chat_memory;"`
2. n8n Postgres credential: host=`mem0-dev-postgres-1`, port=5432, DB=`n8n_chat_memory`, user/pass=`postgres`
3. n8n must be on `mem0-dev_mem0_network` (add as external network in n8n's compose.yaml)
4. Session ID: `={{ $json.message.chat.id }}` (stable per Telegram chat)