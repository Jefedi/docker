---
name: n8n-instance-maintenance
description: >-
  Clean up n8n workflows — archive, stop spam, fix nodes.
---

# n8n Instance Maintenance

Clean up and maintain an n8n instance: disable error spammers, archive dead
workflows, organize by folder, and fix common node errors.

## Cleanup Procedure

### 1. Stop Error Spammers First
A webhook workflow can generate thousands of errors/day. Disable before diagnosing:
```
mcp_n8n_mcp_search_executions(status=["error","crashed"], limit=30)
mcp_n8n_mcp_unpublish_workflow(workflowId="<id>")  # disable
```
Look for workflows with 1000+ errors — these need immediate disabling.

### 2. Inventory All Workflows
```
mcp_n8n_mcp_search_workflows(limit=200)
```
Categorize each:
- **Active + erroring** → already disabled in step 1, diagnose/fix
- **Inactive + 0 executions + old** → archive (tests, one-shots, abandoned)
- **Active + working** → leave alone

### 3. Archive Dead Workflows (SERIAL, not parallel!)
```
mcp_n8n_mcp_archive_workflow(workflowId="<id>")  # ONE AT A TIME
```

⚠️ **MCP rate limiting**: More than ~5 parallel MCP calls crash the n8n MCP
server for ~60s. Serialize archive calls. If MCP goes unreachable, `sleep 60`
and retry. Never batch 10+ operations in one response.

⚠️ **`availableInMCP: false`**: Some workflows (older ones, or with MCP access
off) return `{"error":"Workflow is not available in MCP"}`. These can ONLY be
archived from the n8n UI — no API workaround. List them for the user to archive
manually.

### 4. Organize by Folder (UI-only)
n8n Community Edition has **no folder API**:
- `GET /api/v1/folders` → 404
- `PATCH /api/v1/workflows/{id}` → "PATCH method not allowed"
- `PUT` with `parentFolderId` → "additional properties" rejected

Moving workflows to folders is **UI-only**: Workflows page → filter → select all
→ right-click → Move to folder.

## Common Fixes

> **Deep-dive case studies**: `references/multi-trigger-merge-fix.md` — RSS Curation workflow with 3 independent triggers feeding a Merge node (68 errors → fixed with single Schedule Trigger + non-trigger RSS reads). `references/n8n-db-direct-edit.md` — When CLI import/publish doesn't apply changes, edit the SQLite DB directly (procedure, connection graph structure, permission fixes). `references/n8n-sqlite-execution-parsing.md` — Parse n8n's flat-array execution_data format from SQLite (when MCP refuses `availableInMCP: false` workflows).

### AI Agent: "Cannot read properties of undefined (reading 'map')"
**Cause**: The LLM node connected to the AI Agent (e.g. OpenAI Chat Model) has an **empty model field** (`value: ''`). The agent crashes in `ToolsAgent/V3/helpers/executeBatch.ts` trying to iterate tool definitions with no model.
**Fix**: Set a valid model name in the LLM node. If using a custom endpoint (Hermes API, LiteLLM), also verify `base_url` and `api_key` are valid.
**Diagnosis via SQLite** (when MCP unavailable — `availableInMCP: false`):
```python
import sqlite3, json
conn = sqlite3.connect('/tmp/n8n.db')
cur = conn.cursor()
cur.execute("SELECT nodes FROM workflow_entity WHERE name='<name>'")
nodes = json.loads(cur.fetchone()[0])
for n in nodes:
    params = n.get("parameters", {})
    if n["type"] == "@n8n/n8n-nodes-langchain.lmChatOpenAi":
        model = params.get("model", {})
        print(f"Model value: '{model.get('value', '')}'")  # empty = root cause
```

### Discord "Cannot send an empty message" (50006)
**Cause**: `content: ""` (empty string) in Discord node, even when embeds present.
**Fix**: Set content to a non-empty summary:
```javascript
// BAD
return [{ json: { content: '', embed } }];
// GOOD
const summary = `📊 ${events.length} events`;
return [{ json: { content: summary, embed } }];
```

### ETIMEDOUT on Tailscale IP
**Cause**: Target service (Radarr, Sonarr, etc.) is down or IP changed on Tailscale.
**Fix**: Disable workflow. Check service with `ping -c1 -W2 <ip>`. Update workflow
URL when service is back.

### Postgres "Connection refused" on Docker bridge IP (172.x.x.x:5432)
**Cause**: Postgres container restarted with new IP, or Docker network recreated.
**Fix**: Disable workflow. Restart Postgres or update n8n credential to new IP.
See `references/postgres-backend-rebuild.md` in the n8n-workflow-doctor skill.

## API Access

- **n8n API key**: `/opt/data/.n8n_api_key` (header: `X-N8N-API-KEY`)
- **API base**: `https://n8n.jefe.ovh/api/v1/`
- **MCP JWT**: `MCP_N8N_MCP_API_KEY` env var (for MCP server only, NOT REST API)
- **API key ≠ login password** — the API key only works for the public REST API,
  not the internal `/rest/` endpoints or UI session auth

## Pitfalls
- Never parallelize more than 5 MCP calls — the server crashes and needs 60s recovery
- `availableInMCP: false` workflows are invisible to MCP API; must use UI
- n8n Community Edition has no folder API endpoint at all
- Always disable error spammers BEFORE diagnosing — stop the flood first
- The n8n API key (JWT) is scoped to the public API only; internal REST API
  (`/rest/`) requires browser session cookies
- **Editor lock**: `update_workflow` and `publish_workflow` MCP tools fail with
  "Cannot modify workflow while it is being edited by a user in the editor" when
  someone has the workflow open in n8n UI. Ask user to close the tab, then retry.
- **LibreTranslate auth — `httpQueryAuth` does NOT work**: LibreTranslate
  expects `api_key` in the **JSON body**, NOT as a query parameter and NOT in
  `Authorization` header. The n8n `httpQueryAuth` credential type sends it as
  a query param — this fails silently (400 error, "Please contact the server
  operator to get an API key"). The correct approach is:
  1. Set the HTTP Request node authentication to `none`
  2. Remove any `httpQueryAuth` credential reference from the node
  3. Add `api_key` directly in the JSON body expression:
     `={{ { q: $json.title, source: "en", target: "fr", api_key: "<KEY>" } }}`
  4. The API key for this instance is stored in the LibreTranslate container's
     SQLite DB at `/app/db/api_keys.db` (table `api_keys`, first row).
- **LibreTranslate now requires API key**: As of July 2026, translate.jefe.ovh
  returns `400 — "Please contact the server operator to get an API key"` for
  requests without a key. Do NOT bypass/disable the Translate node — fix it
  by putting `api_key` in the body (see above). If the workflow includes an LLM
  curation step (e.g. Hermes), the LLM can handle translation in its prompt as
  a fallback, but LibreTranslate should be the primary translation mechanism.
- **Multi-trigger + Merge = crash loop**: When N independent trigger nodes
  (e.g. 3 RSS Feed Read Triggers) feed a single Merge node with N inputs, each
  trigger fires independently — the Merge receives only 1/N inputs → instant
  crash (<100ms, 0% success). Fix: replace N triggers with 1 Schedule Trigger
  → N non-trigger RSS Feed Read nodes (`n8n-nodes-base.rssFeedRead`, NOT
  `rssFeedReadTrigger`). All feeds arrive at the Merge in the same execution.
- **Testing Schedule Triggers in multi-trigger workflows**: `execute_workflow`
  in `manual` mode fires the **first trigger found** (often a Webhook), not the
  Schedule. To test the schedule branch: temporarily set interval to 1 min via
  `updateNodeParameters` (NOT `setNodeParameter` — JSON pointer paths fail on
  nested objects like `rule.interval`), publish, wait 60-90s, check executions,
  then restore original interval and re-publish.
- **setNodeParameter vs updateNodeParameters for nested objects**: `setNodeParameter`
  with a JSON Pointer path (e.g. `/rule/interval/0/minutesInterval`) fails with
  `cannot descend into non-object`. Use `updateNodeParameters` with `replace: true`
  and the full parameters object instead.
- **Disabled nodes are silent**: A node with `"disabled": true` produces no error,
  no warning — the workflow reports `status: success` but the node's processing
  is skipped entirely. Always check for `disabled: true` when a workflow "succeeds"
  but output is missing a transformation step (e.g. translation not applied).
- **Connection graph bypass**: A node can be active (not disabled) yet completely
  disconnected from the main flow if an upstream node was reconnected around it.
  Always trace the FULL connection graph: for each node, check what feeds INTO it,
  not just what it outputs to. A node with no incoming connections is dead even
  if it has valid outgoing connections.
- **n8n CLI import/publish may not apply connection changes**: When you modify
  a workflow's connection graph and re-import via `npx n8n import:workflow` +
  `npx n8n publish:workflow`, the connections may not update. In this case, edit
  the SQLite DB directly (stop n8n, `docker cp` the DB, modify with Python
  `sqlite3`, copy back, fix permissions, restart). See
  `references/n8n-db-direct-edit.md` for the full procedure.
- **DB permission crash after docker cp**: `docker cp` writes files with the
  host user's UID, but n8n runs as UID 1000 (user `node`). A copied
  `database.sqlite` with wrong ownership causes `SQLITE_READONLY: attempt to
  write a readonly database` on startup. Fix with
  `docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite`
  (also fix `-shm` and `-wal` files).
- **n8n API keys in the DB are masked**: The `apiKey` column in `user_api_keys`
  table shows truncated values like `eyJhbG...mKk4` — you cannot read the full
  key from SQLite. Use the MCP n8n tools or the env var `MCP_N8N_MCP_API_KEY`.
- **Schedule triggers reset after restart**: The first run after an n8n restart
  may be delayed up to one full interval (e.g. 30 min for a 30-min schedule).
  Plan validation accordingly — don't expect immediate execution after restart.
- **Downstream field mapping after HTTP Request transform nodes**: When a
  node like `Translate HN` (HTTP Request to LibreTranslate) sits between `Tag HN`
  and `Rebuild HN`, the HTTP response replaces `$json` entirely — the downstream
  Set node sees `{ translatedText: "..." }`, NOT the original RSS item fields.
  The Set node must:
  1. Use the API response field: `title = {{ $json.translatedText || $json.title }}`
  2. Recover lost fields via cross-node reference:
     `link = {{ $json.link || $("Tag HN").item.json.link }}`
  3. Same for `content`, `pubDate`, etc. — anything not in the API response.
  Without this fix, the translation "works" (no error) but the title silently
  falls back to the original English and links are empty.
- **Existing RSS workflow**: The workflow "RSS Curation par Hermes"
  (`JAWwQaCUx1mN0IA7`) that scans LoKan + Korben + HN every 30 min, translates
  HN via LibreTranslate, curates via Hermes API, and outputs RSS XML at
  `/webhook/rss-curation`. Do NOT create parallel RSS monitoring — extend this
  workflow instead.
- **AI Agent memory nodes — Mem0 is NOT a memory backend**: The
  `@mem0/n8n-nodes-mem0` community node is an **action/tool node** (`group:
  ['transform']`, `usableAsTool: true`), NOT a LangChain memory node. It does
  NOT appear in the AI Agent "Memory" dropdown — it appears in the **Tools**
  dropdown. It connects via `ai_tool`, not `ai_memory`. If the user installed
  Mem0 and can't find it in the Memory list, this is why. It can be used
  ALONGSIDE a native memory node (Postgres for context + Mem0 for long-term
  facts). For the full comparison of memory options, see
  `references/n8n-ai-agent-memory-options.md`.
- **Zep memory is deprecated in n8n**: n8n removed the native Zep node. Zep CE
  is deprecated, SDK incompatible with self-hosted. Even HTTP Request
  workarounds fail. Do not recommend Zep — use Postgres Chat Memory (native) or
  Hindsight (`@vectorize-io/n8n-nodes-hindsight`, self-hosted, MIT) instead.
- **Postgres Chat Memory setup on this instance**: litellm-db (postgres:16-alpine)
  is connected to n8n via the `shared-db` Docker network (run
  `docker network connect shared-db litellm-db` if not yet connected). A
  dedicated database `n8n_memory` has been created. The existing n8n credential
  "Postgres - NextDNS" (ID: `Is6egWrIg98IAzdo`) can be reused or a new one
  created. pgvector is NOT available on this Postgres instance. Session key
  for Telegram-based agents should be `firstName-chatId`, NOT message content.
- **renameNode does not change node type**: The MCP `update_workflow`
  `renameNode` operation only changes the display name, NOT the underlying node
  type. A `memoryBufferWindow` renamed to "Chat Memory (Postgres)" is still a
  Window Buffer in RAM. To actually switch to Postgres memory, you must
  `removeNode` the old one and `addNode` a new one with type
  `@n8n/n8n-nodes-langchain.memoryPostgres`, then `addConnection` with
  `connectionType: "ai_memory"`. The addNode `node.type` field must match the
  n8n node type exactly, and `node.typeVersion` must be set (1.3 for Postgres
  memory).
- **Editor lock blocks MCP updates**: `update_workflow` fails with "Cannot
  modify workflow while it is being edited by a user in the editor" when the
  workflow tab is open in the n8n UI. Ask the user to close the tab, then
  retry. Do NOT loop on this error — it will not resolve until the tab is
  closed.
- **AI Agent system prompt via update_workflow**: To inject a custom system
  prompt into an AI Agent node, use `updateNodeParameters` with the full
  `options` object containing `systemMessage`. The system message supports n8n
  expressions like `{{ $now }}` for dynamic date/time. Prefix with `=` to mark
  it as an expression. Large multi-section prompts (role, user profile,
  infra context, instructions) work fine — the field has no practical size
  limit. See the "AI Perso" workflow (`uZauAh51svOgYrpk`) for an example of
  a Hermes-like system prompt injected into n8n.