# Mem0 + LiteLLM Integration Troubleshooting

## Architecture

```
n8n AI Agent (GLM-5.2) → decides when to call Mem0 (tool)
    ↓
Mem0 API (port 8888)
    ├── Internal LLM (mistral-small-latest via LiteLLM) → extracts facts from messages
    └── Internal Embedder (mistral-embed via LiteLLM) → vectorizes facts for search
        ↓
    LiteLLM (port 4000) → routes to Mistral API (EU sovereign)
```

Three separate LLM layers:
1. **n8n AI Agent LLM** (GLM-5.2) — decides WHEN to use Mem0
2. **Mem0 internal LLM** (mistral-small-latest) — extracts discrete facts
3. **Mem0 internal embedder** (mistral-embed) — vectorizes for semantic search

## Common errors and fixes

### `provider_auth_failed` (authentication)

**Cause 0: `OPENAI_API_BASE_URL` vs `OPENAI_BASE_URL` (SILENT FAILURE)**
- The openai Python SDK (used by Mem0 internally) reads `OPENAI_BASE_URL`, NOT `OPENAI_API_BASE_URL`.
- If the `.env` has `OPENAI_API_BASE_URL=http://litellm:4000/v1`, Mem0 IGNORES it and calls `https://api.openai.com/v1/embeddings` directly.
- Symptoms: logs show `POST https://api.openai.com/v1/embeddings "HTTP/1.1 401 Unauthorized"` even though the .env has a LiteLLM URL configured.
- Fix: rename the env var from `OPENAI_API_BASE_URL` to `OPENAI_BASE_URL` in `.env`.
- ⚠️ `docker compose down && up` does NOT reload env_file changes. Must use `--force-recreate`:
  ```bash
  docker compose down && docker compose up -d --force-recreate
  ```

**Cause 1: Wrong API key**
- Verify the LiteLLM virtual key is valid:
  ```bash
  curl -s http://localhost:4000/v1/models -H "Authorization: Bearer <key>"
  ```
- If 401/auth error, create a new virtual key in LiteLLM with `all_proxy_models` authorized.

**Cause 2: Container can't reach LiteLLM**
- Public URL (`https://litellm.jefe.al/v1`) returns 404 through Pangolin proxy
- Use internal Docker hostname: `http://litellm:4000/v1`
- Connect Mem0 to LiteLLM's network:
  ```bash
  docker network connect litellm_default mem0-dev-mem0-1
  ```
- ⚠️ Must re-run after every `docker compose down && up` cycle

**Cause 3: Typo in URL**
- `litelllm` (3 L's) vs `litellm` (2 L's) — check spelling carefully

### `Invalid model: mistral-embed` (400 Bad Request)

**Cause: LiteLLM treats mistral-embed as a chat model**

LiteLLM sends embedding requests to `/v1/chat/completions` instead of `/v1/embeddings` when the model is not properly configured.

**Fix**: In LiteLLM's `config.yaml`, declare the embedding model with the `mistral/` prefix:

```yaml
model_list:
  - model_name: mistral-embed
    litellm_params:
      model: mistral/mistral-embed
      api_key: <mistral-api-key>
```

The `mistral/` prefix tells LiteLLM this is a Mistral embedding model, routing requests to `/v1/embeddings`.

### `Invalid model: mistral/mistral-small` (model not found)

**Cause: Wrong model name in .env**

The `.env` field `MEM0_DEFAULT_LLM_MODEL` must use the exact `id` from LiteLLM's `/v1/models` response.

```bash
# Check available models
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer <key>" | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

Common mappings:
| Wrong (provider name) | Correct (LiteLLM id) |
|---|---|
| `mistral/mistral-small` | `mistral-small-latest` |
| `mistral-embed` | `mistral/mistral-embed` (must match the model_name in LiteLLM config.yaml) |

⚠️ The embedder model name in `MEM0_DEFAULT_EMBEDDER_MODEL` must match the `model_name` field in LiteLLM's config.yaml, NOT the `model:` field. If LiteLLM config has `model_name: mistral/mistral-embed`, then `.env` must use `mistral/mistral-embed`. Verify with `curl -s http://localhost:4000/v1/models` and use the exact `id` value.

### Network reconnection after `docker compose down`

`docker network connect` is NOT persisted across container recreation. After `docker compose down && up`, you must re-run:

```bash
docker network connect litellm_default mem0-dev-mem0-1
```

**Permanent fix**: Add the LiteLLM network to `docker-compose.yaml`:

```yaml
services:
  mem0:
    networks:
      - mem0_network
      - litellm_default   # Add this

networks:
  mem0_network:
    driver: bridge
  litellm_default:
    external: true         # Reference existing network
```

This way the connection survives container recreation.

### Mem0 API key auth: X-API-Key vs Authorization: Bearer (CRITICAL)

Mem0 API keys (`m0sk_...` format) MUST be sent via `X-API-Key` header, NOT `Authorization: ***`:

```bash
# ✅ Works
curl -s http://localhost:8888/memories -H "X-API-Key: m0sk_xxx"

# ❌ Fails — Mem0 treats it as JWT, returns "Invalid or expired token"
curl -s http://localhost:8888/memories -H "Authorization: Bearer m0sk_xxx"
```

The n8n Mem0 community node credential sends `Authorization: *** — which fails. Use HTTP Request Tool with `X-API-Key` header instead.

### AUTH_DISABLED=false required for clean API key auth

With `AUTH_DISABLED=true`, Mem0 accepts no-auth requests but REJECTS `Authorization: *** with API keys (treats as JWT). Set `AUTH_DISABLED=false` in `.env` for proper API key auth via `X-API-Key` header.

⚠️ Changing `.env` requires `--force-recreate`:
```bash
# sed fails with quotes in values — use nano for AUTH_DISABLED
nano .env  # Change AUTH_DISABLED=true to AUTH_DISABLED=***
docker compose down && docker compose up -d --force-recreate
```

### sed gotchas with .env values

`sed -i 's|AUTH_DISABLED=true|AUTH_DISABLED=*** ' .env` — FAILS with "unterminated `s' command" because the replacement value contains characters that confuse the sed delimiter. Use `nano` for values containing special characters, or use a different delimiter:
```bash
sed -i 's/AUTH_DISABLED=true/AUTH_DISABLED=*** ' .env  # also fails
# Just use nano for AUTH_DISABLED changes
```

### n8n Mem0 integration via HTTP Request Tool (verified working 2026-08-02)

Instead of the Mem0 community node (credential test fails), use two **HTTP Request Tool** nodes connected as `ai_tool` to the AI Agent:

**Mem0 Search tool**:
- Method: POST
- URL: `http://mem0:8000/memories/search`
- Headers: `X-API-Key: m0sk_xxx`, `Content-Type: application/json`
- Body: `{"query": "{{ $fromAI('query', 'Search query', 'string') }}", "user_id": "jefe", "limit": 10}`

**Mem0 Add tool**:
- Method: POST
- URL: `http://mem0:8000/memories`
- Headers: `X-API-Key: m0sk_xxx`, `Content-Type: application/json`
- Body: `{"messages": [{"role": "user", "content": "{{ $fromAI('content', 'Info to remember', 'string') }}"}], "user_id": "jefe"}`

The AI Agent calls these tools automatically when the user shares info or asks about past context.

## Verification commands

```bash
# 1. Check all containers running
docker compose ps

# 2. Check Mem0 API is up
curl -s http://localhost:8888/docs | head -5

# 3. Check LiteLLM is reachable from Mem0 container
docker exec mem0-dev-mem0-1 sh -c "curl -s http://litellm:4000/v1/models -H 'Authorization: Bearer <key>'"

# 4. Test memory creation
curl -s -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test memory"}], "user_id": "test"}'

# 5. Check Mem0 logs for errors
docker logs mem0-dev-mem0-1 --tail 30
```