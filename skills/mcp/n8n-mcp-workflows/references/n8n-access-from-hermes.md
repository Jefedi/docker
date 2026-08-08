# Accessing n8n from Inside the Hermes Container

## Problem: MCP Token Truncated

The n8n MCP server token in `config.yaml` under `mcp.servers.n8n-mcp.headers.Authorization`
may be stored truncated with literal `...` (e.g. `Bearer eyJhbG...6Jgs`). When this happens,
MCP tools (`mcp_n8n_mcp_*`) cannot authenticate and all calls fail.

### Detection

```bash
# Read the raw config line — if you see literal "..." the token is truncated
grep "Authorization" /opt/data/config.yaml | grep n8n
# Output: Authorization: Bearer eyJhbG...6Jgs  ← truncated
```

The `.env` file in the n8n profile may also have a truncated token:
```bash
grep N8N_MCP_TOKEN /opt/data/profiles/n8n/.env
# Output: N8N_MCP_TOKEN=eyJhbG...mKk4  ← also truncated
```

## Fallback: Direct REST API

n8n exposes a REST API at `/api/v1/` on the n8n instance. It requires
an `X-N8N-API-KEY` header that is separate from the MCP token.

### Finding the API key

The n8n API key is NOT stored in Hermes config or `.env` by default.
Options to get it:

1. **Vaultwarden** (automated) — the key may be stored as "Api n8n" item in
   Jefe's Vaultwarden (`vault.jefe.al`, account `hermesagent@jefe.ovh`).
   See `references/vaultwarden-access.md` for the full Vaultwarden API
   authentication and decryption flow. Note: items may have item-level
   encryption keys (must decrypt `item["key"]` first).
2. **n8n UI** → Settings → n8n API → create or copy the key
3. **User provides it directly** in chat — simplest fallback

⚠️ **Vaultwarden token truncation**: JWT tokens stored via the Bitwarden
mobile app may be truncated with literal `...`. If the retrieved key
contains `...`, it's truncated — ask the user to re-save via desktop or
provide it in chat directly.

### Using the REST API

```bash
# List all workflows
curl -sk "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: <key>" \
  -H "Accept: application/json"

# Get a specific workflow
curl -sk "http://localhost:5678/api/v1/workflows/<id>" \
  -H "X-N8N-API-KEY: <key>"

# Get executions for a workflow
curl -sk "http://localhost:5678/api/v1/executions?workflowId=<id>&status=error&limit=5" \
  -H "X-N8N-API-KEY: <key>"
```

## Connectivity Check

From inside the Hermes container, n8n is typically reachable via:

```bash
# Local Docker port mapping (most common)
curl -sk --max-time 5 "http://localhost:5678" -o /dev/null -w "%{http_code}"

# Via Pangolin proxy
curl -sk --max-time 5 "https://n8n.jefe.ovh" -o /dev/null -w "%{http_code}"
```

Both should return 200 if n8n is running.

## Docker Socket Available

The Hermes environment has access to the Docker socket (`/var/run/docker.sock`).
This means `docker ps`, `docker cp`, and `docker exec` all work from inside Hermes:

```bash
# List containers
docker ps --format '{{.Names}} {{.Ports}}'

# Copy n8n DB out for read-only inspection
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_db.sqlite

# Exec into the n8n container (CAUTION — see destructive command warning below)
docker exec n8n-n8n-1 env | grep -i api
```

This provides a third access path alongside the REST API and MCP tools.
The DB copy + Python `sqlite3` inspection pattern is the most reliable fallback
when the REST API key is unavailable and MCP tools are non-functional.

⚠️ **Earlier versions of this document claimed Docker was NOT accessible.**
As of 2026-08-01, Docker commands work fine from the Hermes environment.
If `docker ps` ever returns "Cannot connect to the Docker daemon", it means
the Docker socket mount was removed — check the Hermes container compose file.