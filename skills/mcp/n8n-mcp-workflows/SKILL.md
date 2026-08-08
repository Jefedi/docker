---
name: n8n-mcp-workflows
description: "Design and refactor MCP tool workflows in n8n — single catch-all tool pattern with $fromAI() for dynamic API calls."
version: 1.1.0
author: agent
tags: [n8n, mcp, workflow, tool-design, http-request]
---

# n8n MCP Workflows

Guidelines for building and maintaining MCP (Model Context Protocol) tool servers in n8n.

## Core Pattern: Single Catch-All Tool

**Do NOT create one HTTP Request node per API endpoint.** Instead, create ONE HTTP Request Tool node using `$fromAI()` for dynamic parameters. This mirrors the MCP Discord pattern.

### Structure

A catch-all MCP workflow has two nodes:

```
[MCP Trigger] ──ai_tool──► [HTTP Request Tool (1 node)]
```

### MCP Trigger Node

```json
{
  "type": "@n8n/n8n-nodes-langchain.mcpTrigger",
  "version": 1.1,
  "parameters": {
    "path": "service-name",               // MCP server base path
    "authentication": "none"              // or bearerAuth/headerAuth if needed
  }
}
```

### HTTP Request Tool Node (the catch-all)

Use a single `n8n-nodes-base.httpRequestTool` (version 4.4+) with these parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `method` | `={{ $fromAI("method", "HTTP method: GET, POST, PUT, PATCH, or DELETE") }}` | AI infers the method |
| `url` | `=https://api.example.com/v1/{{ $fromAI("path", "Full API reference here...") }}` | AI infers the path — embed ALL available endpoints in the description |
| `authentication` | `genericCredentialType` | Use with `genericAuthType` |
| `genericAuthType` | `httpHeaderAuth` or `httpBearerAuth` | Match the API's auth scheme |
| `sendQuery` | `true` | Enable query params |
| `specifyQuery` | `json` | JSON format |
| `jsonQuery` | `={{ $fromAI("query", "Query params description...") }}` | AI generates query JSON |
| `sendBody` | `true` | Enable request body |
| `contentType` | `json` | JSON body |
| `specifyBody` | `json` | JSON format |
| `jsonBody` | `={{ $fromAI("body", "Body description with examples...") }}` | AI generates body JSON |
| `options.response.response.neverError` | `true` | Return non-2xx responses as data, not errors |
| `options.timeout` | `30000` | 30s timeout |

### Path Description Format

The `$fromAI("path", "...")` description is CRITICAL — it's the only documentation the LLM caller sees. Format:

```
Service name path AFTER /v1/ prefix. Universal tool covering full API.

RESOURCES BY CATEGORY:
CATEGORY1: path1 (GET description), path2/{id} (GET/POST/DELETE)
CATEGORY2: path3 (GET list, POST create), path3/{id} (GET/PATCH/DELETE)

Auth: Bearer token via [credential type]. All POST/PUT bodies are JSON.
Examples: example1, example2/{id}, example3/{id}/sub
```

### Multi-Tool MCP Workflow

A single MCP trigger can expose **multiple catch-all tools** (e.g. one for a main API, one for a tabular/data API). Each tool is a separate `httpRequestTool` node with its own `ai_tool` connection back to the MCP trigger:

```
[MCP Trigger] ◄──ai_tool── [HTTP Request Tool A (main API)]
                ◄──ai_tool── [HTTP Request Tool B (tabular API)]
```

Both connections use `ai_tool` type with the **tool as source** and **trigger as target** (same direction as single-tool). The MCP client discovers both tools from `tools/list`.

When to use: a platform has two distinct API surfaces with different base URLs (e.g. data.gouv.fr has `/api/1/` for metadata and `tabular-api.data.gouv.fr/api/resources/` for raw data). One tool per API surface keeps the `$fromAI("path")` description focused and prevents the LLM from confusing URL prefixes.

**Catch-all `jsonBody` on GET-heavy tools**: When a tool is primarily for GET requests but still has `sendBody: true` + `$fromAI("body")`, the LLM sends `""` for the body on GETs, causing `Unexpected end of JSON input`. Fix: append `|| "{}"` to the expression:
```
={{ $fromAI("body", "Request body as JSON for POST/PUT operations. Empty for GET requests.") || "{}" }}
```

### Credential Handling

Credentials must be assigned manually in the n8n UI after creating the catch-all node. The node uses:
- `authentication: "genericCredentialType"`
- `genericAuthType: "httpHeaderAuth"` (or the appropriate type like `httpBearerAuth`)
- The `update_workflow` tool will warn: "HTTP Request nodes (name) were skipped during credential auto-assignment."

**Fix:** Go to n8n UI → workflow → click the HTTP Request node → select the correct credential, then Save and republish.

**`hermes mcp add` interactive prompt:** When registering a direct Python MCP server, `hermes mcp add` detects tools and asks "Enable all N tools? [Y/n/select]" — this blocks non-interactive terminal calls. Pipe input to auto-confirm:

```bash
echo "Y" | hermes mcp add my-service --command python3 --args "/path/to/script.py"
```

Without this, the tool is saved but marked cancelled and no tools are enabled.

**API assignment limitation:** The `setNodeCredential` operation via `update_workflow` does NOT work with `n8n-nodes-base.httpRequestTool` nodes using generic credential types. It fails with:
```
node type 'n8n-nodes-base.httpRequestTool' does not accept credential 'httpHeaderAuth'
```
This affects ALL generic auth types (httpHeaderAuth, httpBearerAuth, httpQueryAuth, etc.). Only predefined credential types (like discordBotApi, slackApi) can be assigned via the API. Workaround: assign manually in the n8n UI, then republish the workflow.

**Alternative: hardcode auth in headers** (for testing or single-user setups):
Set `authentication: "none"` and add a static `Authorization` header via `sendHeaders: true`, `specifyHeaders: "json"`, `jsonHeaders: "={ \"Authorization\": \"Bearer YOUR_TOKEN\" }"`. This bypasses credential system entirely but exposes the token in node code — only use for dev/testing.

## Stale Parameter Cleanup

When switching a node's `authentication` type (e.g. `genericCredentialType` → `none`), old parameters like `genericAuthType` persist in the node's stored data and cause `INVALID_PARAMETER` warnings:

```
Field "parameters.genericAuthType": This field is only allowed when: authentication="genericCredentialType"
```

**Fix:** Use `replace: true` in `updateNodeParameters` to wipe ALL parameters and set fresh ones:

```json
{
  "type": "updateNodeParameters",
  "nodeName": "my_node",
  "replace": true,
  "parameters": { /* complete set of new parameters */ }
}
```

Without `replace: true`, the `updateNodeParameters` deep-merges, leaving stale fields in place.

## Refactoring: Many Tools → One Catch-All

When replacing many individual HTTP Request nodes with a single catch-all:

1. **Unpublish** the workflow first (so edits don't race with active execution)
2. **Remove all tool nodes** via `update_workflow` with `type: "removeNode"`
3. **Add the catch-all node** via `update_workflow` with `type: "addNode"`
4. **Add the connection** — the MCP trigger connects via `ai_tool` type:
   - `source`: the tool node name (e.g. `"service_api"`)
   - `target`: the MCP trigger node name (e.g. `"MCP Service"`)
   - `connectionType`: `"ai_tool"`
5. **Publish** the workflow
6. **Assign credential** manually in n8n UI

The connection direction for MCP tools is: **tool → ai_tool → trigger** (source=tool, target=trigger).

## Diagnostics: MCP Tool Returns Connection Error

When an MCP tool (especially SSE-bridged tools through n8n) returns:

```
NodeOperationError: The connection cannot be established,
this usually occurs due to an incorrect host (domain) value
```

**Diagnostic chain (in order):**

1. **Check the n8n workflow** — `get_workflow_details(workflowId)` to see what URL the HTTP Request node targets
2. **Identify the URL** — if it uses a Docker hostname like `http://service-name:port/...`, the hostname only resolves within Docker networks
3. **Check if the backend container is running** — on the Docker host: `docker ps | grep service-name`
4. **Ask the user** — they may have stopped the container ("j'ai coupé le bot", etc.)
5. **Check Docker network** — n8n must be on the same network as the backend container for Docker hostname resolution to work

**Root causes (most likely first):**
- **Container stopped** — the backend service was stopped/removed (most common with migrated stacks)
- **Docker network mismatch** — n8n not on the same Docker network as the backend (e.g. `discord-net`)
- **Host changed** — after a migration (e.g. jNas→AX42), the backend runs on a different host and the Docker hostname `service-name` isn't resolvable cross-host

**Fix:**
- If container is stopped: restart it
- If network mismatch: connect n8n to the backend's network: `docker network connect <network> n8n`
- If cross-host: replace Docker hostname with the IP address in the n8n node URL

## Scheduled Data Sync Patterns

For building recurring sync/backup workflows that fetch data from external APIs (Spotify, etc.) and store it in n8n internal Data Tables, see `references/scheduled-data-sync.md`. Covers parallel branches from a single trigger, OAuth2 service node integration, Data Table upsert with compound keys, Code-node transform patterns, **bidirectional sync (delete orphaned rows)**, and the inverse restore/import pattern.

Supporting sub-references:
- `references/parallel-schedule-branches.md` — SDK wiring for parallel branches from one trigger
- `references/spotify-backup-pattern.md` — Full Spotify backup workflow
- `references/spotify-backup-verification.md` — Verifying backup completeness against live Spotify data (track count, ID integrity, silent failure detection)
- `references/data-table-upsert.md` — Data Table upsert configuration details
- `references/restore-import-pattern.md` — Restore/import from Data Tables to external API

## Consolidated References

These files were absorbed from sibling skills covering related n8n workflow development topics:

- `references/sdk-pitfalls.md` — SDK parameter naming quirks, Discord embed formatting, publish-after-update requirement, webhook array handling, and `replace=true` parameter wipe prevention (absorbed from `n8n-workflow-sdk-pitfalls`)
- `references/bridge-maintenance.md` — Diagnosing and fixing n8n MCP bridges when backend IPs change, creating new MCP bridge workflows, cookie-based auth patterns (absorbed from `mcp-bridge-maintenance`)
- `references/mcp-pangolin-workflow.md` — MCP Pangolin workflow architecture (workflow ID, credentials, auth type) and API key expiration diagnostic pattern (401 vs 403-JSON vs 403-empty)

## Catch-All URL Bug: `$fromAI("method")` vs `$fromAI("path")`

The most common bug in single-catch-all MCP workflows: the URL uses `$fromAI("method")` instead of `$fromAI("path")`, causing every API call to route to `GET`/`POST` instead of the intended endpoint.

### Symptom

```
URL built:  http://service:port/api/v3/GET
Expected:   http://service:port/api/v3/actual-endpoint
```

All catch-all tool calls return `[{}]` or nonsense responses.

### Root Cause

The n8n HTTP Request Tool node has its URL expression set to:

```
{{ $fromAI("method", "HTTP method: GET, POST, PUT, or DELETE") }}
```

Instead of:

```
{{ $fromAI("path", "Service API path AFTER /v1/ prefix...") }}
```

The `$fromAI("method")` is used correctly for the HTTP method parameter, but was copy-pasted into the URL field instead of using `$fromAI("path")`.

### Debugging

1. **Inspect the workflow**:
   ```
   mcp_n8n_mcp_get_workflow_details({ workflowId })
   ```
   Find the catch-all HTTP Request Tool node and examine its `parameters.url` expression.

2. **Identify the broken expression** — look for `$fromAI("method")` in the `url` field where `$fromAI("path")` belongs.

### Fixing

**DO NOT use `setNodeParameter`** — it creates nested `parameters.parameters.url` instead of replacing `parameters.url`. Use `updateNodeParameters` with `replace: true`:

```javascript
mcp_n8n_mcp_update_workflow({
  workflowId: "...",
  operations: [{
    type: "updateNodeParameters",
    nodeName: "catch_all_node",
    replace: true,
    parameters: {
      // Replace ALL parameters — this is destructive, pass everything
      url: "=http://service:port/api/v1/{{ $fromAI(\"path\", \"Service API path AFTER /v1/ prefix. Full endpoint list here.\") }}",
      method: "={{ $fromAI(\"method\", \"HTTP method: GET, POST, PUT, or DELETE\") }}",
      authentication: "genericCredentialType",
      genericAuthType: "httpHeaderAuth",
      sendQuery: true,
      specifyQuery: "json",
      jsonQuery: "={{ $fromAI(\"query\", \"Query params as JSON object...\") }}",
      sendBody: true,
      specifyBody: "json",
      jsonBody: "={{ $fromAI(\"body\", \"Request body as JSON...\") }}",
      options: { timeout: 30000, response: { neverError: true } }
    }
  }]
})
```

### Publishing & Testing

After any mutation, publish the new version:

```javascript
mcp_n8n_mcp_publish_workflow({ workflowId })
```

Then test immediately with the fixed tool. If the MCP session still returns stale results (old tool signature), toggle the workflow off/on to force SSE session reconnection:

```javascript
mcp_n8n_mcp_unpublish_workflow({ workflowId })
mcp_n8n_mcp_publish_workflow({ workflowId })
```

### Prevention

When creating a new catch-all tool from scratch, ALWAYS use `$fromAI("path")` in the URL and `$fromAI("method")` for the HTTP method — never the same variable for both.

## Accessing n8n When MCP Token Is Truncated

The n8n MCP server token in `config.yaml` (`mcp.servers.n8n-mcp.headers.Authorization`) may be stored truncated with literal `...` (e.g. `Bearer eyJhbG...6Jgs`), making all `mcp_n8n_mcp_*` tools non-functional. The same truncation can appear in `/opt/data/profiles/n8n/.env` as `N8N_MCP_TOKEN`.

**Permanent fix (applied 2026-07-25):** Re-add the MCP server using `hermes mcp add --auth header`. This stores the token in `/opt/data/.env` as `MCP_N8N_MCP_API_KEY`, which is NOT subject to Hermes secret redaction. The token survives restarts and new sessions.

**Fallback:** use n8n's REST API at `http://localhost:5678/api/v1/` with an `X-N8N-API-KEY` header. This key is separate from the MCP token and must be obtained from n8n UI → Settings → API. Store it in `/opt/data/.n8n_api_key` for reuse. The Docker socket IS available (confirmed 2026-08-01), so `docker cp` + Python `sqlite3` on the n8n DB is also a viable fallback. See `references/n8n-access-from-hermes.md`.

**Finding the n8n API key:** The key may be in session history (use `session_search` with query "n8n API key"). It was NOT in Vaultwarden despite memory referencing an "Api n8n" item — that item did not exist. The `vault.py` script is read-only (lists items, cannot add). To create new vault items, use `scripts/vault_create.py` (full write support via Bitwarden API with encryption) — see `references/vaultwarden-access.md` for the complete write flow including the encryption helper and client sync requirement.

## Hermes-Side Registration: Direct SSE vs n8n-mcp Hub

After creating an n8n MCP workflow, it must be registered in Hermes to be discovered. Two approaches:

### Approach A: Via n8n-mcp Hub (Preferred)

The `n8n-mcp` server in `config.yaml` connects to `https://n8n.jefe.ovh/mcp-server/http` (HTTP Streamable). It auto-discovers ALL n8n workflows with `availableInMCP: true`. New workflows appear automatically — no Hermes config change needed.

**When it breaks:** The hub token can expire (403 Forbidden). The token in `.env` may also get truncated by Hermes secret redaction. Fix: regenerate the token from n8n UI → Settings → MCP, then `hermes mcp remove n8n-mcp` + `printf "Y\n<token>\ny\n" | hermes mcp add n8n-mcp --url ... --auth header`.

### Approach B: Direct SSE Bridge (Fallback)

When the n8n-mcp hub is down (expired token, 403), register individual MCP workflows directly:

```bash
hermes mcp remove data-gouv  # clean any old entry
printf "Y\n" | hermes mcp add data-gouv \
  --command /opt/data/hermes-agent/venv/bin/python \
  --args "/opt/data/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py" \
  --env "SSE_URL=http://127.0.0.1:5678/mcp/data-gouv/sse"
hermes config set mcp_servers.data-gouv.enabled true
hermes config set mcp_servers.data-gouv.connect_timeout 60
```

**CRITICAL: Use Hermes venv Python, not system python3.** The `mcp` module is only in `/opt/data/hermes-agent/venv/bin/python`. System `python3` lacks it.

**`hermes mcp test` false negative:** The test reports "Connection closed" after ~8s even when the bridge works. Verify manually:

```bash
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; sleep 1; echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'; sleep 1; echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'; sleep 3) | SSE_URL="http://127.0.0.1:5678/mcp/data-gouv/sse" timeout 15 /opt/data/hermes-agent/venv/bin/python /opt/data/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py 2>&1
```

If this returns valid JSON-RPC responses with tool definitions, the bridge works. Tools will be available after `hermes gateway restart` (from a separate terminal; the gateway cannot restart itself).

See `references/hermes-side-registration.md` for the full registration reference.

## Migration: Hermes-Native MCPs → n8n Central Hub

**Status: COMPLETED (2026-07-25).** All 22 Hermes-local MCP servers migrated to n8n.
Hermes now has a single `n8n-mcp` entry connecting to 24 n8n MCP workflows.

See `references/migration-from-hermes-to-n8n.md` for the complete inventory (all 24
workflows with IDs, auth types, SSE paths), the procedure actually used, and key file
locations (`/opt/data/.n8n_api_key`, `/opt/data/.env`).

**Key principle:** n8n-hosted MCPs work for ANY client that speaks MCP. Hermes-native
MCPs only work inside Hermes. Centralizing on n8n = one place to maintain all tools.

**Critical lesson — AUDIT BEFORE CREATING:** When asked to migrate MCPs to n8n, always
list existing n8n MCP workflows first (via REST API `GET /api/v1/workflows`). In this
case, 24 of 24 already existed — creating new ones caused webhook path conflicts
(`{"message":"There is a conflict with one of the webhooks."}`). The actual work was:
audit → delete duplicates → remove Hermes-local entries → re-add n8n-mcp with correct token.

**Token fix via `hermes mcp add --auth header`:**
The MCP token gets truncated by Hermes secret redaction. Use `hermes mcp add --auth header`
which saves it to `/opt/data/.env` as `MCP_N8N_MCP_API_KEY`, bypassing redaction. Pipe
the three interactive prompts: `printf "Y\n<token>\ny\n" | hermes mcp add n8n-mcp --url ... --auth header`.

## Testing MCP SSE Endpoints

After any change to MCP workflows (auth, parameters, nodes), **always test the SSE
endpoints** — not just the workflow active status. A workflow can be "active" but
return 500 on its SSE endpoint due to stale webhooks or parameter parsing errors.

### Test all endpoints at once

```bash
for name in bazarr crosswatch dockhand ha-mcp libretranslate metube myanimelist \
  portainer profilarr prowlarr searxng cineverse discord github jellyfin pangolin \
  paperless paymenter pterodactyl radarr seerr sonarr uptimekuma qbittorrent; do
  echo -n "$name: "
  timeout 5 curl -s -o /dev/null -w "%{http_code}" "http://localhost:5678/mcp/$name/sse" --max-time 3
  echo
done
```

Expected: all 200. If any return 403 or 500, see the pitfalls below.

**User expectation (CRITICAL):** When asked "did you test them?" or "tu les as testés?",
the user means "did you actually call each endpoint and verify it responds with 200",
NOT "did you check they're active in the UI" or "did you see they're ON".
**Always test end-to-end with `curl` to each SSE endpoint before reporting success.**
Reporting "they're active" without testing the actual HTTP response is a failure
the user will catch. This is non-negotiable.

### Full MCP Protocol Handshake Test (beyond status codes)

A 200 on the SSE endpoint only confirms the transport is up — it does NOT verify
that `initialize`, `tools/list`, or `tools/call` actually work. When a user says
"test the MCP" or when an MCP tool is reported broken, do a **full handshake test**:

**Step 1 — Start SSE connection in background** (terminal with `background=true`):
```bash
curl -s -N --max-time 60 "http://127.0.0.1:5678/mcp/SERVICE-NAME/sse" > /tmp/mcp_sse.txt 2>&1
```

**Step 2 — Extract session ID** from the SSE output:
```bash
sleep 2
SESSION_ID=$(grep -oP 'sessionId=\K[a-f0-9-]+' /tmp/mcp_sse.txt)
echo "Session: $SESSION_ID"
```

**Step 3 — Send MCP initialize** (POST to the messages endpoint, NOT the SSE endpoint):
```bash
curl -s -X POST "http://127.0.0.1:5678/mcp/SERVICE-NAME/messages?sessionId=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

**Step 4 — Send initialized notification:**
```bash
curl -s -X POST "http://127.0.0.1:5678/mcp/SERVICE-NAME/messages?sessionId=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
```

**Step 5 — List tools:**
```bash
curl -s -X POST "http://127.0.0.1:5678/mcp/SERVICE-NAME/messages?sessionId=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**Step 6 — Read responses from the SSE stream:**
```bash
sleep 3
cat /tmp/mcp_sse.txt
# or tail -20 /tmp/mcp_sse.txt for just the latest
```

The SSE stream accumulates `event: message` lines with `data:` containing JSON-RPC
responses. Each response has an `id` matching the request. Look for:
- `initialize` response → `serverInfo` with name + version
- `tools/list` response → `tools` array with names, descriptions, inputSchema
- `tools/call` response → `content` array with the actual tool output

**Step 7 — Call a tool** (optional, to verify end-to-end):
```bash
curl -s -X POST "http://127.0.0.1:5678/mcp/SERVICE-NAME/messages?sessionId=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{...}}}'
```

**Key details:**
- The SSE connection MUST stay open during the test — that's why it runs in background.
- POST requests go to `/mcp/SERVICE-NAME/messages?sessionId=...`, NOT to the SSE endpoint.
- Responses come back on the SSE stream (the background curl output), not in the POST response body (which just says "Accepted").
- Use `process(action='kill')` to clean up the background SSE connection after testing.
- This pattern works for ANY n8n-hosted MCP SSE server, not just Pangolin.

### Diagnosing 403 on SSE endpoints

403 means the MCP trigger has `authentication: "bearerAuth"` and the token you're
sending doesn't match the credential stored in n8n. Two fixes:

1. **Remove bearerAuth** (recommended when n8n is behind Pangolin/proxy):
   - PUT the workflow with `authentication: "none"` on the MCP trigger node
   - Remove the `credentials` block from the trigger node
   - Toggle: `POST .../deactivate` then `POST .../activate` to refresh the webhook

2. **Send the correct token**: The token is stored in an encrypted n8n credential
   (`httpBearerAuth` type) and cannot be read via the REST API. You'd need to
   check the n8n UI or know the token from when it was created.

### Diagnosing 500 on SSE endpoints

500 typically means either:
- **"Workflow could not be started"** — the webhook is stale after a PUT update.
  Fix: toggle `deactivate` → `activate` to refresh the webhook registration.
- **$fromAI parsing error** — the `$fromAI("query", "description")` string has
  escaped quotes or invalid characters that break the expression parser. Error
  looks like: `Failed to parse $fromAI arguments: "query", "...": Error: Invalid type: 2`.
  Fix: simplify the description string — remove nested quotes, use plain text.

## PUT /api/v1/workflows/{id} — Complete Field Restrictions

When updating workflows via PUT, strip ALL of these fields or get 400 errors:

**Forbidden fields (cause 400 "must NOT have additional properties"):**
`id`, `versionId`, `createdAt`, `updatedAt`, `active`, `activeVersionId`,
`triggerCount`, `shared`, `tags`, `sourceWorkflowId`, `parentFolder`,
`activeVersion`, `versionCounter`, `isArchived`, `pinData`, `staticData`,
`meta`, `nodeGroups`

**Settings restrictions:** Only `executionOrder` and `availableInMCP` are safe.
`binaryMode`, `timeSavedMode`, and other settings keys cause 400
"must NOT have additional properties". Use:
```python
wf['settings'] = {'executionOrder': 'v1', 'availableInMCP': True}
```

**Node-level:** Remove `webhookId` from each node — it's auto-generated and
including it can cause issues.

**`description` field:** n8n stores `description: null` on workflows created without a description. The GET response includes `description: null`. When you strip metadata fields for PUT but leave `description` as `null`, the API rejects it with `request/body/description must be string`. Always set `wf['description'] = ''` (or a real description) before PUT.

**After PUT:** Always toggle `deactivate` → `activate` to refresh the webhook.
PUT updates the workflow definition but doesn't re-register webhooks.

```bash
curl -s -X POST "http://localhost:5678/api/v1/workflows/$ID/deactivate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
curl -s -X POST "http://localhost:5678/api/v1/workflows/$ID/activate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

## RAG Workflows in n8n

For building Retrieval-Augmented Generation systems (vector store + embeddings
+ AI agent chat), see `references/rag-workflows.md`. Covers the 3-workflow
pattern (ingestion → chat → optional MCP server), infrastructure requirements
(Qdrant + Ollama embeddings in Docker on AX42), n8n node reference for Qdrant
Vector Store modes and embeddings nodes, LLM backend selection for RAG
(LiteLLM direct preferred over Hermes API server for tool-calling), and
pitfalls (embeddings model mismatch, localhost IPv6, LiteLLM lacks embeddings).

**⚠️ LiteLLM (port 4000) does NOT expose embedding models** — only chat models.
The Ollama API key is restricted to chat models. Embeddings require a local
Ollama instance (`nomic-embed-text` or `mxbai-embed-large`) or a dedicated
embeddings provider.

**Document source for HA RAG**: `home-assistant/home-assistant.io` repo (branch
`current`), files in `source/_docs/**/*.md` and `source/_integrations/**/*.md`.
~3000+ markdown files. Use `git clone --depth 1` for ingestion.

## RSS Curation Workflows (RSS → Translate → AI Curate → RSS Output)

For building RSS aggregation workflows that fetch multiple feeds, translate
non-French content via LibreTranslate, run AI curation via an LLM, and serve
the result as a single RSS feed via n8n webhook, see
`references/rss-curation-workflow.md`. Covers the parallel RSS Read branch
pattern, LibreTranslate integration with httpQueryAuth, Merge node with 3+
inputs (`numberInputs` parameter), `$getWorkflowStaticData` for persisting
XML between schedule and webhook executions, webhook response configuration
for `application/rss+xml`, and credential creation for LibreTranslate and
LLM API backends.

**RSS Feed Trigger migration (2026-07-28):** Replaced `scheduleTrigger` +
3× `rssFeedRead` with 3× native `rssFeedReadTrigger` (one per feed). Each
feed is now independently monitored — n8n detects updates and triggers
the workflow automatically instead of polling all feeds every 2h. The
correct node type is `n8n-nodes-base.rssFeedReadTrigger` (v1), NOT
`n8n-nodes-base.rssFeedTrigger` (that name is rejected by the API). See
`references/rss-curation-workflow.md` section "RSS Feed Trigger Migration"
for the full operation sequence.

**Hermes API endpoint for curation:** The HTTP Request node for AI curation
must point to `https://hermes.jefe.al/v1/responses` (Hermes API via Pangolin),
NOT `https://litellm.jefe.al/v1/chat/completions`. The body format
`{ input: ... }` matches the `/v1/responses` endpoint. The credential
`Hermes API Bearer` (httpBearerAuth) works for both endpoints but the URL
must be the Hermes API, not LiteLLM.

**⚠️ Pangolin SSO blocks Bearer token auth (2026-07-28):** If `hermes.jefe.al`
has Pangolin SSO enabled (the default for public resources), requests with
only a Bearer token get redirected to `/login` (HTTP 302) — Pangolin
intercepts BEFORE the request reaches Hermes' own Bearer auth. The fix is
to either: (a) disable SSO on the `hermes.jefe.al` resource in the Pangolin
dashboard (the Hermes API has its own `API_SERVER_KEY` Bearer auth — that's
sufficient), or (b) use `http://localhost:9119` directly from n8n since
both are on the same machine. This applies to ANY API exposed via Pangolin
that has its own auth layer — disable SSO on those resources.

Key pitfalls specific to this pattern:
- **`setNodeParameter` with JSON Pointer path creates nested `parameters` object** —
  `setNodeParameter` with `path: "/parameters/url"` creates
  `parameters.parameters.url` instead of replacing `parameters.url`.
  Use `updateNodeParameters` with `replace: true` instead.
- **`$getWorkflowStaticData` requires `$` prefix** — calling
  `getWorkflowStaticData('global')` without `$` throws
  `getWorkflowStaticData is not defined` in the Code node sandbox.
- **`localhost` ECONNREFUSED in n8n via Hermes gateway** — HTTP Request
  nodes using `http://localhost:PORT/` or `http://127.0.0.1:PORT/` may fail
  with ECONNREFUSED even though curl works from the host. Use public Pangolin
  URLs (e.g. `https://translate.jefe.ovh/translate`) for all internal
  services called from n8n HTTP Request nodes.
- **Merge node `numberInputs`** — default is 2. When merging 3+ branches,
  set `numberInputs: 3` (or N) or input index 2+ is silently dropped.
- **RSS Feed Trigger node type name** — the correct n8n node type is
  `n8n-nodes-base.rssFeedReadTrigger` (v1). The shorter name
  `n8n-nodes-base.rssFeedTrigger` is rejected with "Unrecognized node type".
  Always verify node types via `search_nodes()` before adding them.

## Web App Pattern (SPA from n8n Webhook)

For serving a complete single-page application from an n8n webhook — HTML page
+ Data Table CRUD + stats — see `references/web-app-pattern.md`. Covers the
file-based HTML embedding pattern (`JSON.stringify` + `__DATA_PLACEHOLDER__`),
multi-route webhook architecture (page/save/delete/stats), base64 data
injection, `respondToWebhook` configuration for HTML vs JSON, **iterative HTML
updates** (fetch from production → modify → push back via `updateNodeParameters`),
**schema evolution** (add columns + update upsert + update HTML + update stats),
and the user's preference that **all web tools must be built on n8n** (no
Flask/external app servers).

## n8n Webhook as Multipart Proxy for iOS Shortcuts

For bridging iOS Shortcuts (which can only send JSON via `jsonRequest()`) to APIs requiring multipart/form-data uploads (e.g. LibreTranslate `/translate_file`), see `references/n8n-multipart-proxy.md`. Covers the webhook → decode base64 → native HTTP Request with `formBinaryData` → respond pattern, magic-byte file type detection, and critical pitfalls (Code node v2.2 `jsCode` bug, `this.helpers.httpRequest` multipart corruption, `formBinaryData` vs `file` parameterType).

## Hermes API as n8n LLM Backend

To use the Hermes Agent API server (`localhost:9119`) as an OpenAI-compatible
LLM backend for n8n chatbot workflows, see
`references/hermes-api-as-llm-backend.md`. Covers credential creation via REST
API, the critical `responsesApiEnabled: false` setting (dashboard auth vs API
server auth), SDK workflow pattern, and streaming configuration.

Key gotcha: the OpenAI Chat Model node defaults to `responsesApiEnabled: true`
which hits `/v1/responses` — gated by dashboard basic_auth on Hermes. Set it to
`false` to use `/v1/chat/completions` with Bearer token auth instead.

**Adding MCP tools to the chat agent:** Use `mcpClientTool` (v1.4) connected
to the n8n MCP server. The endpoint URL is in `config.yaml` under
`mcp_servers.n8n-mcp.url` — it's `https://n8n.jefe.ovh/mcp-server/http`
with `httpStreamable` transport (NOT SSE). Wire via `ai_tool` connection,
increase `maxIterations` to 10. See `references/hermes-api-as-llm-backend.md`
section "Adding MCP Tools to the AI Agent" for the complete pattern.

**⚠️ `localhost` → IPv6 ECONNREFUSED:** n8n's Node.js resolves `localhost`
to `::1` (IPv6). If the target service listens on IPv4 only, the MCP Client
Tool fails with `connect ECONNREFUSED ::1:PORT`. Always use `127.0.0.1` or
the full domain name (e.g. `https://n8n.jefe.ovh/...`) in n8n node URLs.

**⚠️ MCP transport must match server:** Setting `serverTransport: 'sse'` on
an HTTP Streamable endpoint returns HTML instead of SSE data. Check the
server's actual transport — `httpStreamable` vs `sse` — before configuring.

## Email Triage Workflows (IMAP → Hermes → ntfy)

For real-time email monitoring workflows using IMAP triggers, Hermes Agent
for classification, and ntfy for push notifications, see
`references/email-triage-realtime.md`. Covers:

- IMAP trigger node setup (IDLE push, not polling) for multiple mailboxes
- Merge node to combine multiple IMAP sources
- Hermes Agent as email classifier (low temperature, JSON output)
- ntfy notification via HTTP Request (priority=max for urgent, default otherwise)
- IMAP and ntfy credential creation via REST API
- `setNodeCredential` works for `httpRequest` (v4.4) and `emailReadImap` (v2.1)
  but NOT for `httpRequestTool` — see credential pitfall above

Key credential creation patterns via REST API:
```bash
# IMAP (no ssl/allowSelfSigned fields — causes 400)
curl -X POST .../credentials -d '{"name":"IMAP acct","type":"imap","data":{"host":"imap.gmail.com","port":993,"user":"...","password":"..."}}'

# ntfy (httpHeaderAuth with Bearer token)
curl -X POST .../credentials -d '{"name":"ntfy","type":"httpHeaderAuth","data":{"name":"Authorization","value":"Bearer <token>"}}'
```

**ntfy message formatting (CRITICAL):** The AI Agent outputs raw JSON,
often wrapped in markdown code fences (```json ... ```). Sending this
directly to ntfy produces unreadable notifications. Always add a Code
node between the Agent and ntfy that: (1) strips markdown fences via
regex `/```(?:json)?\s*([\s\S]*?)\s*```/`, (2) parses JSON, (3) emits
human-readable `title` and `body` fields. See
`references/email-triage-realtime.md` section "Code Node — Format JSON
for ntfy" for the complete pattern including the fence-stripping regex.

**IMAP `postProcessAction` (CRITICAL):** Use `'nothing'`, NOT `'read'`.
With `'read'`, the trigger marks processed emails as Seen. Gmail may
also auto-mark emails as Seen (self-sent, opened on another device).
The next UNSEEN search then finds nothing → **silently missed emails**.
With `'nothing'`, emails stay unread but `trackLastMessageId` prevents
reprocessing. Also set `forceReconnect: 30` (not default 60) for Gmail.

**Model selection for triage:** Use `gpt-oss-20b` (lightweight, 20B)
for email classification instead of `glm-5.2`. Sufficient intelligence
for JSON classification, lower resource usage. Query available models
via `curl http://localhost:4000/v1/models -H "Authorization: Bearer $OLLAMA_API_KEY"`.

## Trakt Calendar Sync → Radicale

For syncing upcoming TV episodes and movie releases from Trakt to Radicale
(same calendar as Motorsport), there are two approaches depending on whether
the user can create a new Trakt OAuth app:

### Approach 1: MDBList API Proxy (PREFERRED when Trakt app limit is hit)

**Use this when the user's Trakt free tier is full (1 community app max).**
MDBList is likely already OAuth-connected to the user's Trakt account and
exposes a simple API-key-based API that mirrors Trakt data.

- API key from: https://mdblist.com/preferences/
- Key endpoints: `/calendar/events` (upcoming episodes, filter `!is_watched`),
  `/watchlist/items/movie` (watchlist films, filter `release_date >= today`)
- No OAuth flow — just pass `?apikey=KEY` query param
- Workflow `6DfjzsWXe4I0u5os` ("Trakt Calendar Sync") uses this approach
- See `references/mdblist-trakt-sync.md` for full endpoint details and code patterns

### Approach 2: Direct Trakt API (when OAuth slots are available)

- Trakt device-flow OAuth (no browser redirect needed, poll-based)
- Key endpoints: `/calendars/my/shows`, `/calendars/my/movies`, `/users/me/watchlist`
- Trakt's calendar endpoints already filter to the user's watched/collected/watchlisted
  content — no manual "is this in production?" check needed
- Code node patterns: Trakt JSON → iCal VEVENTs (shows with datetime, movies as all-day)
- See `references/trakt-calendar-sync.md` for full OAuth flow and code patterns
- **Pitfall**: Trakt free tier allows only 1 community app connection — user hit 4/1
  limit and must revoke an existing app at app.trakt.tv → Settings → Applications
  before authorizing a new one via device flow

Both approaches push to the **same** Radicale collection as Motorsport Calendar Sync
(`0feb942c-776d-cef4-18a5-cb0d8bccd798`) — one unified calendar.

## iCal Feed & HA Todo Sync (n8n-Only)

For a unified calendar + tasks system managed entirely in n8n (no external
See `references/caldav-bidirectional-sync.md` (rewritten).
Covers:

- **Single iCal webhook** (`GET /ical-unified`) serving VEVENTs + VTODOs from
  two Data Tables (`ical_events` + `n8n_tasks`)
- **Scheduled bidirectional sync** (5 min) between HA `todo.*` entities and
  `n8n_tasks` Data Table (upsert HA → n8n, push missing n8n → HA)
- **iOS subscription**: user adds one URL in Settings → Calendar → Subscribe
- `placeholder()` for user-configurable HA API URLs post-creation

For Radicale CalDAV deployment + external iCal feed sync (F1, sports, etc.)
via n8n → Radicale PUT, see `references/radicale-caldav-sync.md`. Covers
production-grade Docker deploy, htpasswd/bcrypt auth, iCal parsing regex,
and CalDAV PUT workflow pattern.

⚠️ **User preference**: The user initially rejected external CalDAV servers
in favor of n8n-only iCal. However, as of 2026-07-26, Radicale IS deployed
at `ical.jefe.al` (production-grade Docker, bcrypt auth, user `jefe`). The
user now uses Radicale as his CalDAV server, connected to HA and iPhone.
The n8n-only iCal webhook (`ical-unified`) remains for HA todo sync, but
external calendar subscriptions (F1, etc.) are synced via n8n → Radicale
CalDAV PUT. See `references/radicale-caldav-sync.md` for the deployment
and sync workflow pattern.

⚠️ **iOS pitfall**: the subscribe URL MUST include `https://` protocol prefix.
Without it, iOS shows "Connexion impossible avec SSL" and fails even when
offered to retry without SSL.

## n8n AI Agent — Personal Assistant Pattern

For building a Hermes-like personal AI assistant in n8n with personalized
system prompt, persistent Postgres memory, and Telegram trigger, see
`references/n8n-ai-agent-personal-assistant.md`. Covers:

- **System prompt personalization**: XML-tagged sections (role, user_profile,
  infra_context, key_memories, instructions) injected into the AI Agent node.
  Use `=` prefix for `{{ $now }}` expression evaluation.
- **Postgres Chat Memory**: Replaces Window Buffer for persistent memory
  across n8n restarts. Requires Docker network bridging between n8n and
  the Postgres container (`docker network connect`). Session key must be
  based on user identity (firstName-chatId), NOT message text.
- **Memory node type replacement**: `renameNode` does NOT change node type.
  Must `removeNode` + `addNode` with the correct `@n8n/n8n-nodes-langchain.memoryPostgres`
  type, then `addConnection` with `connectionType: "ai_memory"`.
- **Docker network bridging**: n8n and Postgres containers may be on
  different Docker networks. Use `docker network connect <net> <container>`
  + `nc -z` port check (no `apt-get` in n8n's Alpine image).
- **Telegram integration**: Trigger → Agent → Send a Text Message pattern,
  plus `telegramHitlTool` for agent-initiated messages.
- **Editor lock with concurrent modifications**: User may be building in the
  n8n UI simultaneously. Always `get_workflow_details` before updating to
  see current node names/types/connections.

**Session key pitfall**: `sessionKey` including `{{ $json.message.text }}`
creates a new session per message — the agent has NO memory between messages.
Always use identity-based keys: `{{ $json.message.from.first_name }}-{{ $json.message.chat.id }}`.

## Pitfalls

- **MCP token truncated**: check `config.yaml` for literal `...` in the Authorization header. If truncated, MCP tools won't work. Permanent fix: `hermes mcp remove n8n-mcp` then `printf "Y\n<full_token>\ny\n" | hermes mcp add n8n-mcp --url ... --auth header` — saves token to `/opt/data/.env`, bypassing redaction.
- **Vaultwarden items created via API**: 4 items created 2026-07-25 (Api n8n, MCP n8n Token, Prowlarr API Key, LibreTranslate API Key) using `scripts/vault_create.py`. Items appear in `GET /api/sync` and decrypt correctly via `vault.py`, but user's Vaultwarden client may not display them — see `references/vaultwarden-access.md` section "Client sync required after API creation" for the unresolved issue and workaround guidance.
- **Docker socket IS available from Hermes** (confirmed 2026-08-01): `docker ps`, `docker cp`, `docker exec` all work from inside Hermes. Use `docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_db.sqlite` then Python `sqlite3` for read-only DB inspection. See `references/n8n-access-from-hermes.md` for details. (Earlier versions of this skill claimed Docker was NOT accessible — this was wrong or the mount has since been added.)
- **⚠️ NEVER run `n8n user-management:reset`**: This command resets the ENTIRE n8n database to default user state, deleting ALL workflows, credentials, executions, and users. It appeared as a way to get an API key but is DESTRUCTIVE. Do not run it even in diagnostic contexts. If accidentally run, immediately `docker restart` the n8n container — the reset may not have fully committed if n8n was still running. If you need an API key, get it from the n8n UI (Settings → n8n API), from the `user_api_keys` table in the SQLite DB (`docker cp` + Python `sqlite3`), Vaultwarden, or ask the user. Confirmed destructive 2026-08-01.
- **Missing credential**: After creating a catch-all node, it has no credential. The user must assign one manually in n8n UI.
- **Bad path description**: If the `$fromAI()` description doesn't list all endpoints, the LLM won't know what it can call. Be exhaustive.
- **$fromAI description quoting**: Avoid nested quotes in `$fromAI("param", "description")` strings. Use plain text without escaped `\"` inside descriptions. Nested quotes cause `Failed to parse $fromAI arguments` errors and HTTP 500 on the SSE endpoint.
- **Connection direction**: MCP tool connections use `ai_tool` type with the tool as source and trigger as target. This is REVERSED from standard `main` connections.
- **neverError**: Always set `options.response.response.neverError: true` so API errors (4xx, 5xx) return as data rather than crashing the tool.
- **Batch limit**: `update_workflow` supports max 100 operations per call, which is enough for most refactors (up to ~97 nodes to replace).
- **n8n MCP not exposing tools?** Try the direct Python MCP server fallback pattern in `references/direct-mcp-server-python.md`.
- **DISCONNECTED_NODE warnings are normal**: After refactoring, `update_workflow` may emit `DISCONNECTED_NODE` warnings for the tool node. These are harmless — MCP tool nodes use `ai_tool` connections (not standard `main` inputs), and the warnings refer to the wrong connection type. If the `ai_tool` connection exists, the node works fine despite the warning.
- **`hermes mcp add` interactive prompt**: When adding a direct Python MCP server, `hermes mcp add` detects tools and asks "Enable all N tools? [Y/n/select]" — this blocks a non-interactive terminal call. Pipe `yes | hermes mcp add ...` or answer with `echo "Y" | hermes mcp add ...` to auto-confirm. The prompt is not shown when 0 tools are discovered (the server is saved anyway).
- **`hermes mcp add --auth header` prompts**: Three interactive prompts: (1) "Does this server require authentication? [Y/n]", (2) "API key / Bearer token:", (3) "Save config anyway? [y/N]". Pipe all three: `printf "Y\n<token>\ny\n" | hermes mcp add n8n-mcp --url ... --auth header`. The token is saved to `/opt/data/.env` as `MCP_<NAME>_API_KEY`, bypassing Hermes secret redaction that truncates tokens in `config.yaml`.
- **`hermes mcp remove` interactive prompt**: Asks "Remove server 'name'? [Y/n]". In a loop, it auto-confirms (the Y is consumed). No piping needed for remove.
- **Webhook path conflicts when creating MCP workflows**: If an MCP workflow with the same `path` parameter already exists in n8n, activating a new workflow with the same path fails with `{"message":"There is a conflict with one of the webhooks."}`. Always list existing MCP workflows before creating new ones.
- **n8n MCP workflow auth types vary**: Some MCP workflows use `authentication: "none"` (open access), others use `bearerAuth` (require the n8n MCP token). Check each workflow's MCP Trigger node `parameters.authentication` to know which SSE endpoints need auth. When n8n is behind a proxy (Pangolin), `none` is sufficient — the proxy handles auth.
- **REST API cannot DELETE data table rows**: `DELETE /api/v1/data-tables/{id}/rows/{rowId}` returns HTTP 405 "DELETE method not allowed". To delete rows, use the Data Table node's `deleteRows` operation within a workflow (it supports condition-based deletion matching the same `filters.conditions` pattern as upsert). The REST API only supports GET on rows. ⚠️ The operation name is `deleteRows`, NOT `delete` — the SDK validator rejects `"delete"` with `INVALID_PARAMETER`.
- **PUT /api/v1/workflows/{id} field restrictions**: See the dedicated section above. Short version: strip ALL metadata fields, only keep `name`, `nodes`, `connections`, `settings` (with only `executionOrder` + `availableInMCP`).
- **Workflow invisible to MCP tools (`availableInMCP: false`)**: `search_workflows()` returns `availableInMCP` per workflow. When false, `get_workflow_details()`, `get_workflow_version()`, and `execute_workflow()` all fail with "Workflow is not available in MCP. Enable MCP access from the workflow card in the workflows list, or from the workflow settings." The workflow exists and is active but is invisible to MCP tools. Fix: user goes to n8n UI → Workflows → click the workflow card → toggle "Available in MCP" ON, then Save. This is per-workflow, not global. Check `availableInMCP` in search results before attempting to read or modify a workflow — if false, tell the user it needs to be enabled first and where to find the setting. Distinct from the `active` boolean (published/unpublished state).
- **IMAP credential rejects `ssl`/`allowSelfSigned` fields**: The n8n IMAP credential type (`type: "imap"`) only accepts `host`, `port`, `user`, `password`. Adding `ssl: true` or `allowSelfSigned: false` → 400 `"data is not allowed to have the additional property 'ssl'"`. SSL/TLS is implied by port 993.
- **Hardcoded API keys in nodes**: When a credential can't be assigned via API (e.g. Prowlarr has no matching n8n credential), hardcode the key in the HTTP Request Tool node via `sendHeaders: true`, `specifyHeaders: "json"`, `jsonHeaders: '={{ { "X-Api-Key": "..." } }}'`. The key is visible in the workflow definition but works when you can't use the credential system.
- **ALWAYS publish after modifications**: The user expects every workflow update to be followed by `publish_workflow`. Never leave a workflow in draft/unpublished state after changes. This is non-negotiable — the user explicitly stated this preference. Even if the change seems minor, publish it.
- **SIMPLIFY before shipping — user rejects over-engineering**: When the user asks for a feature, build the simplest version that works. This user explicitly rejected multiple webhook endpoints (add-event, add-task, complete-task, get-tasks) when a single iCal feed URL covers the use case. Lesson: default to ONE integration point, let n8n handle the rest internally. Do NOT propose iOS Shortcuts or per-action webhooks unless the user explicitly asks for them.
- **CONSOLIDATE similar workflows — user explicitly rejected separate workflows for similar sources**: When adding NASCAR/MotoGP to an existing F1 calendar sync, the user said "tout dans le même, ça sert à rien d'en faire plusieurs." ALWAYS add new sources to an existing workflow that handles the same task. Pattern: fan out from one trigger to multiple HTTP GETs → Merge (append) → shared PUT. Never create a second workflow for the same class of task.
- **Archive rather than delete old workflows**: When superseding a workflow with a simpler version, archive the old one (`archive_workflow`) rather than deleting it. This preserves history and allows rollback.
- **Editor lock — "Cannot modify workflow while it is being edited"**: `update_workflow` and `publish_workflow` fail when the workflow is open in the n8n UI editor. The lock is per-workflow. Workarounds: (a) ask the user to close the tab, (b) use the REST API `PUT /api/v1/workflows/{id}` directly (bypasses the editor lock), (c) wait and retry. The PUT approach requires stripping metadata fields — see the "PUT /api/v1/workflows/{id}" section for field restrictions.
- **`localhost` → IPv6 ECONNREFUSED in n8n**: n8n's Node.js runtime resolves `localhost` to `::1` (IPv6). Services listening on IPv4 only will refuse the connection. Always use `127.0.0.1` or the full domain name in n8n node URLs (endpointUrl, baseURL, etc.).
- **`predefinedCredentialType` auth (Pangolin pattern)**: Some MCP catch-all workflows use `authentication: "predefinedCredentialType"` with `nodeCredentialType: "pangolinApi"` instead of the generic `genericCredentialType` + `httpHeaderAuth`/`httpBearerAuth` pattern. The `predefinedCredentialType` uses a service-specific n8n credential type (e.g. `pangolinApi`). This means the credential CANNOT be assigned via the REST API — it must be set manually in the n8n UI. The generic auth types (`httpHeaderAuth`, `httpBearerAuth`, `httpQueryAuth`) are assignable via `setNodeCredential`; predefined types like `pangolinApi` are not.
- **Direct n8n DB inspection when REST API is blocked**: When the n8n REST API key is invalid (401) and `mcp_n8n_mcp_*` tools are non-functional, you can still inspect the n8n database directly: `docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_db.sqlite` then query with Python `sqlite3`. Tables use suffixed names: `workflow_entity` (not `workflow`), `credentials_entity` (not `credentials`), `webhook_entity`, `shared_credentials`, etc. This is read-only and safe — the DB is copied out, not modified in place.
- **MCP transport mismatch**: Setting `serverTransport: 'sse'` on an HTTP Streamable MCP endpoint returns HTML (200) instead of SSE data — the MCP client gets parse errors. Check `config.yaml` `mcp_servers.<name>.url` to determine the correct transport: URLs ending in `/http` use `httpStreamable`, URLs ending in `/sse` use `sse`.
- **Empty Data Table nodes break webhook response chains**: When a Data Table `get` node returns 0 items (empty table), downstream nodes (Code, Respond to Webhook) are **silently skipped**. The webhook returns HTTP 200 with empty body + wrong content-type (`application/json` instead of `text/calendar`). iOS shows "Impossible de vérifier les données du compte". Fix: set `alwaysOutputData: true` via `setNodeSettings` on Data Table nodes in the response chain, then filter empty placeholder items in the Code node with `.filter(i => i.summary)`. **Must republish** after the fix. See `references/caldav-bidirectional-sync.md` section "CRITICAL: Empty Data Tables Break Webhook Response Chain".
- **Webhook production URL includes internal UUID**: n8n webhook triggers have two URLs: test (`/webhook-test/<uuid>/<path>`) and production (`/webhook/<uuid>/<path>`). The `triggerInfo` from `get_workflow_details` shows the full production URL with the UUID prefix. However, n8n also registers a **short path** (`/webhook/<path>` without UUID) that works when the workflow is active. If the short path returns 200 but empty body, and the full UUID path returns 404, the workflow is active but the webhook handler isn't reaching the Respond node — check executions to diagnose.
- **iOS Calendar subscription requires `https://` prefix**: iOS Settings → Calendar → Add Account → Other → Subscribe Calendar. If the user enters the URL without `https://`, iOS shows "Connexion impossible avec SSL" and fails even when offered to retry without SSL. Always provide the full URL with protocol prefix.
- **Trakt free tier app connection limit (1 app max)**: When the device flow activation page shows "Limite de connexions atteinte", the user must revoke an existing app at app.trakt.tv → Settings → Applications. Workaround: use MDBList API (already connected, simple API key) as a proxy — see `references/mdblist-trakt-sync.md`.
- **MDBList `/calendar/events` returns episodes only, NO movies**: To get watchlist movie release dates, use `/watchlist/items/movie` separately and filter `release_date >= today`. Most watchlist movies are already released — the future-date filter is critical to avoid flooding the calendar.
- **jsonQuery with `expr()` produces `[object Object]`**: When an HTTP Request node uses `specifyQuery: "json"` with `jsonQuery: '={{ { key: "val" } }}'`, n8n stringifies the JS object as `[object Object]` instead of JSON. Error: `The value in the "JSON Query Parameters" field is not valid JSON`. **Fix**: put query params directly in the URL (`url: "https://api.example.com?apikey=XXX&days=30"`) and use `updateNodeParameters` with `replace: true` to wipe ALL query-related fields (`sendQuery`, `specifyQuery`, `jsonQuery`). Setting `sendQuery: false` alone leaves stale `specifyQuery`/`jsonQuery` → `INVALID_PARAMETER` warnings.
- **`setNodeParameter` JSON Pointer creates nested `parameters` object**: `setNodeParameter` with `path: "/parameters/url"` and `value: "http://..."` creates a nested `parameters.parameters.url` field instead of replacing `parameters.url`. The node continues using the old URL. **Always use `updateNodeParameters` with `replace: true`** to change any parameter field — include the complete parameter set since `replace: true` wipes everything.
- **CalDAV `ATTACH` for images — user rejected attachments**: The iCal `ATTACH;FMTTYPE=image/jpeg:<url>` property is valid but iOS Calendar shows it as a clickable attachment link, not an inline thumbnail in the grid view. The iCal standard has no "thumbnail" or "icon" property. **User preference**: don't add `ATTACH` for poster images — keep VEVENTs clean with SUMMARY, DTSTART, UID, and optional DESCRIPTION only.
- **Web tools must be on n8n, NOT Flask/external apps**: When the user asks for a web tool, tracker, or dashboard, build it entirely as an n8n workflow (webhooks + Data Tables). Do NOT build a Flask/Node app or Docker container. The user explicitly corrected this on 2026-07-28: "Tout doit se passer sur n8n." See `references/web-app-pattern.md` for the SPA-from-webhook pattern.
- **Data Table `operation: 'deleteRows'` NOT `'delete'`**: The SDK validator rejects `"operation": "delete"` with `INVALID_PARAMETER: expected one of: "deleteRows"`. Always use `"deleteRows"` for Data Table row deletion. Confirmed 2026-07-28.
- **`respondWith: 'json'` returns placeholder `{"myField":"value"}`**: Use `respondWith: 'text'` with `responseBody: '={{ JSON.stringify($json) }}'` + Content-Type header instead. See `references/sdk-pitfalls.md` Pitfall 9. Confirmed 2026-07-28.
- **Iterative HTML update — must restore `__DATA_PLACEHOLDER__`**: When fetching live HTML from a production webhook to iterate on it, the placeholder has been replaced with actual base64 data. You MUST restore it via regex before re-embedding, or the page will show frozen/stale data forever. See `references/sdk-pitfalls.md` Pitfall 11. Confirmed 2026-07-28.
- **Apostrophes in single-quoted JS strings inside jsCode**: When the Code node `jsCode` builds HTML with single-quoted strings (e.g. `html += '...(jusqu'à 35h)...'`), apostrophes in French text terminate the string early → `Unexpected identifier` JS error → page loads but is completely dead (no buttons, no navigation). **Most reliable fix**: remove apostrophes from JS-generated text entirely (`jusqu'à` → `max`, `appliqués` → `appliques`, `cumulé` → `cumule`). Backslash escaping (`\\'`) is fragile through `updateNodeParameters`. Always verify the SERVED jsCode with `node -e "new Function(code)"` after pushing, not just the local version. See `references/sdk-pitfalls.md` Pitfall 12. Confirmed 2026-07-28.
- **`updateNodeParameters` `replace: false` merges jsCode**: When updating a Code node's `jsCode` with `replace: false` (default), the old code may persist alongside or merge with the new code. Unicode escapes (`\ud83d`) may also be converted to literal characters. Use `replace: true` to fully replace all parameters (include `mode` and all required fields). After pushing, verify stored jsCode with `get_workflow_details` + syntax check. See `references/sdk-pitfalls.md` Pitfall 14. Confirmed 2026-07-28.
- **RSS Feed Trigger 301 redirect crash**: The `rssFeedReadTrigger` node does NOT follow HTTP 301 redirects. A feed URL like `https://example.com/feed` that 301-redirects to `https://example.com/feed/` causes every poll to crash silently (execution shows "error", < 1s duration, no runData). Always test feed URLs with `curl -sI` before adding them. WordPress sites commonly redirect `/feed` → `/feed/` (trailing slash). See `references/rss-curation-workflow.md` section "RSS Feed URL 301 Redirect Crash".
- **Multi-trigger + Merge anti-pattern**: Never connect multiple independent trigger nodes (e.g. 3× `rssFeedReadTrigger`) to a single Merge node. Each trigger fires in its own execution; the Merge only combines data within one execution, so when only one trigger fires the others are empty → Merge blocks → pipeline never completes. Use 1 Schedule Trigger + multiple read (non-trigger) nodes instead. See `references/rss-curation-workflow.md` section "Multi-Trigger + Merge Anti-Pattern".
- **Rental monitoring (location) vs buy-to-let (investissement)**: The `french-real-estate-investment` skill covers property BUYING. For rental SEARCH (user looking for an apartment to rent), use SeLoger neighbourhood-specific URLs with `web_extract` (Leboncoin and SeLoger both return 403 to direct curl/urllib but work via `web_extract`). SeLoger neighbourhood codes for Le Havre: Centre-ville=`nbh2fr6210`, Saint-Vincent=`nbh2fr6211`, Bléville=`nbh2fr6221`. Set up ntfy urgent alerts (priority 4) for new listings with dedup via a seen-IDs JSON file.
- **Catch-all `jsonBody` empty string breaks GET requests**: When a catch-all tool has `sendBody: true` + `jsonBody: '={{ $fromAI("body", "...") }}'`, GET requests fail with `Unexpected end of JSON input` because the LLM sends `""` (not valid JSON). Fix: append `|| "{}"` to the `jsonBody` expression. See `references/sdk-pitfalls.md` Pitfall 15. Confirmed 2026-08-01.
- **PUT `description: null` rejected**: n8n stores `description: null`; the PUT API requires it be a string. Set `wf['description'] = ''` before PUT. See `references/sdk-pitfalls.md` Pitfall 16. Confirmed 2026-08-01.
- **SSE bridge needs Hermes venv Python, NOT system python3**: The `sse_mcp_bridge.py` script requires the `mcp` Python module which is ONLY installed in `/opt/data/hermes-agent/venv/bin/python`. System `python3` (3.13) lacks it and the bridge silently exits with `ModuleNotFoundError: No module named 'mcp'`. Always use `--command /opt/data/hermes-agent/venv/bin/python` when registering SSE bridge MCP servers via `hermes mcp add`. Confirmed 2026-08-01.
- **`hermes mcp test` false negative for SSE bridges**: SSE bridge scripts report "Connection closed" after ~8s even when the bridge works perfectly. The test closes stdin before the SSE handshake completes. Verify manually by piping JSON-RPC initialize + tools/list to the bridge script with the correct venv Python. If tools are returned, the bridge works — ignore the test failure. Tools will be available after `hermes gateway restart`. Confirmed 2026-08-01.
- **n8n-mcp hub token expired (403 Forbidden)**: The hub token at `https://n8n.jefe.ovh/mcp-server/http` can expire. `hermes mcp test n8n-mcp` returns 403. Fix: regenerate token from n8n UI → Settings → MCP, then re-add via `hermes mcp add --auth header`. Alternatively, register individual MCP workflows directly via SSE bridge (see "Hermes-Side Registration: Direct SSE" approach below). Confirmed 2026-08-01.
- **n8n MCP trigger SSE webhooks broken (webhookId=None, n8n 2.32.7)**: ALL n8n MCP Trigger workflows (Seerr, Sonarr, Radarr, Jellyfin, etc.) return HTTP 404 on their webhook endpoints (`/webhook/<path>/sse`, `/webhook/<path>/messages`) despite being `active=1` and successfully published via `publish_workflow`. Root cause: `webhook_entity` table has `webhookId=None` for all MCP trigger entries, so n8n never registers the webhook route handler. `docker restart` and `publish_workflow`/`unpublish_workflow`/`publish_workflow` cycles do NOT fix it. The MCP trigger node has a `webhookId` in its JSON (e.g. `"webhookId": "eb948270-..."`) but it's not propagated to `webhook_entity`. **Workaround:** build a standalone FastMCP server wrapping the service API directly (see `build-mcp-servers` skill), register in Hermes config.yaml as a stdio MCP server. This bypasses the n8n MCP trigger entirely. Confirmed 2026-08-01.
- **Seerr API key location**: Inside the Docker container at `/app/config/settings.json` → `main.apiKey`. Extract with: `docker exec seerr cat /app/config/settings.json | python3 -c "import sys,json; print(json.load(sys.stdin)['main']['apiKey'])"`. The key is a base64-encoded string. Auth header: `X-Api-Key: <key>`. Confirmed 2026-08-01.
- **n8n Code node v2.2 does NOT recognize `jsCode` parameter**: Setting `typeVersion: 2.2` on a Code node with `parameters.jsCode` produces "Could not get parameter jsCode" at execution time. The node stores the parameter but the execution engine doesn't read it. **Fix**: use `typeVersion: 2` (not 2.2) for Code nodes with `jsCode`. Confirmed 2026-08-04.
- **n8n Code node sandbox blocks `require()` and `fetch()`**: `require('axios')` → "Module 'axios' is disallowed". `fetch()` → "fetch is not defined". The sandbox only allows `this.helpers.httpRequest()` (based on `got`) for HTTP requests. Confirmed 2026-08-04.
- **`this.helpers.httpRequest()` corrupts multipart/form-data bodies**: When sending a Buffer as `body` with `Content-Type: multipart/form-data` header, `got` (the underlying library) mangles the body → LibreTranslate returns 400 "Invalid request: file format not supported". Manual Buffer construction (header + file + footer) does NOT help. **Fix**: use the native HTTP Request node (`n8n-nodes-base.httpRequest` v4.4) with `contentType: "multipart-form-data"` and `bodyParameters.parameters` containing `{"name": "file", "parameterType": "formBinaryData", "inputDataFieldName": "data"}` — the native node correctly constructs multipart form-data from binary data. Confirmed 2026-08-04.
- **HTTP Request node `parameterType: "file"` → INVALID_PARAMETER**: The correct value is `parameterType: "formBinaryData"` (not `"file"`) for multipart file upload fields. The node generates the multipart form-data correctly with this setting. Confirmed 2026-08-04.
- **n8n webhook as multipart proxy for iOS Shortcuts**: iOS Shortcuts (via Cherri `jsonRequest()`) can only send JSON, not multipart/form-data. To bridge to APIs requiring multipart (e.g. LibreTranslate `/translate_file`): create an n8n webhook workflow that receives JSON `{file: "<base64>", filename, source, target}`, a Code node that decodes base64 to binary (`Buffer.from(b64, 'base64')`), then a native HTTP Request node with `formBinaryData` sends it as multipart to the target API. The webhook returns JSON with the translated content. Workflow ID: `gsmd3yyG19CEt4tO`. Confirmed 2026-08-04.