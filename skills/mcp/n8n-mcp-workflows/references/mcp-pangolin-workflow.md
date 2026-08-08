# MCP Pangolin Workflow — Diagnostics & Architecture

## Architecture

The MCP Pangolin is an n8n workflow (NOT a standalone MCP server):

| Field | Value |
|-------|-------|
| Workflow ID | `6HGntC63ycMMcAQo` |
| Name | `MCP - Pangolin` |
| MCP Trigger path | `pangolin` |
| SSE endpoint | `http://127.0.0.1:5678/mcp/pangolin/sse` |
| Tool node | `pangolin_api` (httpRequestTool) |
| Auth type | `predefinedCredentialType` → `pangolinApi` (NOT genericCredentialType) |
| Credential | "Pangolin account" (ID: `EWwPTFj2frDs75Yg`, type: `pangolinApi`) |
| API URL | `https://api.jefe.ovh/v1/{{ $fromAI("path", ...) }}` |

The workflow also has unused credentials attached: "Pangolin auth" (httpHeaderAuth,
ID: `SDoq2e9FW6f0zxjd`) and "Pangolin api key" (httpBearerAuth, ID: `GW571V3yFXtQN3q4`).
The active auth is `pangolinApi` via `authentication: "predefinedCredentialType"`.

Hermes config: `config.yaml` → `mcp_servers.pangolin-mcp.url: http://127.0.0.1:5678/mcp/pangolin/sse`

## API Key Expiration — Diagnostic Pattern

Pangolin API keys expire / lose permissions. The failure mode differs depending
on WHERE the request originates, which makes diagnosis confusing:

| Caller | HTTP | Body | Meaning |
|--------|------|------|---------|
| External curl (Hermes host → `api.jefe.ovh`) | 403 | empty | Traefik middleware blocks before Pangolin |
| Internal (n8n container → `api.jefe.ovh`) | 401 | `{"message":"Invalid API key"}` | Key is truly invalid/expired |
| Internal (n8n MCP workflow → Pangolin API) | 403 | `{"message":"Key does not have permission perform this action"}` | Key valid but missing scopes |
| Internal (n8n MCP workflow → Pangolin API) | 403 | `{"message":"Key does not have root access"}` | Key valid but not root |

### Diagnostic sequence

1. **Test from inside n8n container** (bypasses Traefik):
```bash
docker exec n8n-n8n-1 node -e "
const h=require('https');
h.get('https://api.jefe.ovh/v1/org/jorganisation', r => {
  let d=''; r.on('data', c => d+=c);
  r.on('end', () => console.log(r.statusCode, d));
}).end();
"
```
- 401 "Invalid API key" → key is dead, must regenerate
- 403 with JSON permission error → key alive but lacks scopes
- 200 → key works, problem is elsewhere

2. **If 403 empty body from external curl only** → Traefik is blocking external
   access to `api.jefe.ovh` — not an API key issue.

3. **Test MCP transport** (SSE handshake + tools/list + tools/call) to verify
   the n8n MCP workflow itself is functioning. See the "Full MCP Protocol
   Handshake Test" section in the main SKILL.md.

### Fix

Regenerate key from `https://pangolin.jefe.ovh` dashboard → API Keys,
with scopes Resource+Target R/W/U. Then update:
- `/opt/data/.env` `PANGOLIN_API_KEY`
- n8n credential "Pangolin account" (ID: `EWwPTFj2frDs75Yg`, type: `pangolinApi`)
  — must be done in n8n UI (predefined credential type, not assignable via API)

## Other Pangolin n8n Workflows

| Workflow ID | Name | Purpose |
|-------------|------|---------|
| `p080hRLP6L2hSv8Z` | Pangolin → Uptime Kuma Auto-Surveillance | Auto-monitor new Pangolin resources (inactive) |
| `IIqWZRSkKJfsdHdu` | Pangolin Events → Discord | Stream Pangolin events to Discord (active) |