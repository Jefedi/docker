---
name: n8n-bulk-cleanup
title: n8n Bulk Workflow Cleanup
description: Use when cleaning up, tidying up, tagging, or doing maintenance on n8n workflows en masse. Covers archiving, error alerting setup, credential auditing, stale workflow detection, and tagging.
tags: [n8n, workflow, cleanup, maintenance, archive, triage]
---

# n8n Bulk Workflow Cleanup

When the user asks to "faire le ménage", "clean up", "tidy up", or do maintenance on n8n workflows, follow this procedure.

## 1. Inventory

```
mcp__n8n_mcp__search_workflows(limit=200)
```

Categorize results:
- **MCP servers**: workflows named `MCP - <service>` or `MCP <service>` — tool servers, leave active
- **Automation workflows**: active with real triggers (schedule, webhook) — check for errors
- **Inactive/dead**: `active: false`, `triggerCount: 0`, old creation date — archive candidates
- **One-shot tests**: names like "Test ...", "Recherche ..." — archive

## 2. Find Failing Workflows

```
mcp__n8n_mcp__search_executions(status=["error","crashed"], limit=30)
```

Group by `workflowId`. Key thresholds:
- **10k+ errors**: workflow is spamming — **unpublish immediately** before diagnosis
- **Recurring errors**: check latest execution for root cause
- **One-off errors**: likely transient, skip

## 3. Triage (3 buckets)

| Bucket | Signal | Action |
|---|---|---|
| **Repairable** | Workflow logic bug (empty message, wrong field, schema mismatch) | Fix via `update_workflow`, test with `test_workflow`, republish |
| **Infra down** | `ECONNREFUSED`, `ETIMEDOUT`, `Connection refused` | Disable via `unpublish_workflow`, tell user what to restart |
| **Dead/inactive** | `active: false`, `triggerCount: 0`, old date, one-shot | Archive via `archive_workflow` |

## 4. Disable Spamming Workflows FIRST

Before any diagnosis, disable workflows that are generating massive error counts:
```
mcp__n8n_mcp__unpublish_workflow(workflowId="<id>")
```
This stops the error flood while you investigate.

## 5. Fix Repairable Workflows

Get execution details, identify the failing node, apply fix:
```
mcp__n8n_mcp__get_execution(workflowId, executionId, includeData=true, truncateData=1)
mcp__n8n_mcp__update_workflow(workflowId, operations=[{...}])
mcp__n8n_mcp__prepare_test_pin_data(workflowId)
mcp__n8n_mcp__test_workflow(workflowId, pinData={...})
mcp__n8n_mcp__publish_workflow(workflowId)
```

See `references/common-error-patterns.md` for error → fix mappings.

## 6. Archive Dead Workflows

```
mcp__n8n_mcp__archive_workflow(workflowId="<id>")
```

### ⚠️ MCP Rate Limiting — CRITICAL

**Never fire more than 5-6 `archive_workflow` calls in parallel.** The MCP server becomes unreachable after consecutive failures and needs a 60s cooldown.

Strategy:
1. Batch archives in groups of 5
2. Wait for each batch to complete before starting the next
3. If MCP goes unreachable: `sleep 65` in terminal, then retry
4. Serial calls work but are slow — small parallel batches are the sweet spot

### ⚠️ `availableInMCP: false`

Some workflows have MCP access disabled (`availableInMCP: false` in search results). These **cannot** be archived via the MCP API — they must be archived manually in the n8n UI.

List them for the user at the end:
> "These N workflows need manual archiving in n8n UI: [names]"

## 7. Tag and Organize (after archiving)

### Tagging
Add tags to workflows for filtering. Tags are created automatically if they don't exist:
```
mcp__n8n_mcp__update_workflow(workflowId, operations=[{"type": "addTags", "names": ["mcp", "infra"]}])
```

Suggested tag scheme:
- `mcp` — all MCP server workflows
- `arr` — Sonarr/Radarr/Prowlarr/Profilarr
- `media` — Jellyfin/Seerr/Bazarr/CrossWatch/MyAnimeList/MeTube
- `infra` — Pangolin/Portainer/DockHand/SearXNG/GitHub/Paperless
- `notif` — notification workflows (ntfy, Discord)
- `discord` — Discord-related
- `nasa` — NASA APOD workflows
- `spotify` — Spotify workflows
- `smarthome` — Home Assistant
- `ai` — AI/LLM workflows
- `torrent` — qBittorrent

### Renaming (standardize MCP names)
Normalize `MCP X` → `MCP - X` for consistency:
```
mcp__n8n_mcp__update_workflow(workflowId, operations=[
  {"type": "addTags", "names": ["mcp", "tag2"]},
  {"type": "setWorkflowMetadata", "name": "MCP - NewName"}
])
```
Tag + rename can be done in a single update_workflow call with 2 operations.

### Folder organization (UI-only)
n8n Community Edition has no folder API. Moving workflows to folders must be done in the UI:
Workflows page → filter by tag → select all → right-click → Move to folder.

⚠️ Some workflows (e.g. MCP Pangolin) may fail validation on update due to invalid ai_tool connections. Tag them without renaming — the rename triggers a full validation check.

## 8. Stale Workflow Detection

After archiving, check remaining active workflows for staleness:
```
mcp__n8n_mcp__search_executions(workflowId="<id>", limit=3)
```
If an active workflow has **0 total executions**, it's stale — either never triggered or broken silently. Deactivate it:
```
mcp__n8n_mcp__unpublish_workflow(workflowId="<id>")
```

## 9. Credential Audit (post-archiving)

After archiving workflows, some credentials become orphaned. Cross-reference:
1. List all credentials: `mcp__n8n_mcp__list_credentials(limit=200)`
2. List all active workflows: `mcp__n8n_mcp__search_workflows(limit=200)`
3. Get details of non-MCP active workflows to extract credential IDs from node configs
4. MCP workflows typically use `MCP AUTH` (httpBearerAuth) or `MCP n8n` — not service-specific creds
5. Report credentials not referenced by any active workflow

Common orphaned credentials after cleanup:
- Supabase, lm-studio, openwebui-ollama (replaced by Hermes API)
- Test credentials (Test_loko, Discord Bot Test AI)
- NextDNS/Postgres credentials (if NextDNS workflows were deactivated)
- Trakii X (if Trakii workflow was archived)
- Duplicate ntfy credentials (NTFY vs ntfy vs ntfy jefe)

⚠️ Credentials cannot be deleted via MCP API — list them for manual cleanup in n8n UI.

## 10. Error Alerting Setup

### Create a global error alert workflow
When any workflow crashes in production, an Error Trigger fires automatically. Create a workflow that sends a notification to ntfy:

**Pattern**: Error Trigger (`n8n-nodes-base.errorTrigger`) → Code (format message) → HTTP Request (POST to ntfy)

Key SDK details:
- Error Trigger type: `n8n-nodes-base.errorTrigger`, version 1
- The trigger provides: `$json.workflow.name`, `$json.execution.id`, `$json.execution.error.message`, `$json.execution.error.node.name`
- HTTP Request to ntfy needs: `authentication: "predefinedCredentialType"`, `nodeCredentialType: "httpBearerAuth"` set first via `updateNodeParameters`, then link credential via `setNodeCredential`
- ntfy headers: `Title` (with emoji), `Priority: urgent`, `Tags: warning`
- Body: raw text/plain with workflow name, node, error message, execution ID
- Full SDK code template: `templates/error-alert-workflow.ts`

### Link error workflow to key workflows
```
mcp__n8n_mcp__update_workflow(workflowId, operations=[
  {"type": "setWorkflowSettings", "settings": {"errorWorkflow": "<error-alert-workflow-id>"}}
])
```
Link to workflows that handle critical automations: notifications, email triage, AI chat, scheduled backups.

⚠️ The Error Trigger fires for **production** executions only, not manual/test runs.

## 11. Report Format

After cleanup, summarize concisely:

```
## ✅ Ménage terminé

### Réparations
- **Workflow name** → ✅ fixed and republished. [Root cause → fix]

### Désactivations (infra down)
- **Workflow name** → disabled. [What infra to restart]

### Archivage — N workflows archivés
[Names of archived workflows]

### Tags — N workflows taggés
[Tags created + workflow count per tag]

### Stale workflows désactivés
[Names of active workflows with 0 executions]

### Credentials orphelins (à nettoyer UI)
[Names of credentials not used by any active workflow]

### Error alerting
- Workflow `🔔 Error Alert → ntfy` créé et publié
- Lié à N workflows clés

### ⚠️ N workflows à archiver manuellement (UI n8n)
[Names of workflows with availableInMCP=false]

**Avant: N workflows (X erreurs/jour) → Après: M workflows actifs, 0 erreur**
```

### Data Table column name mismatch
When a Data Table node (upsert/insert) fails with `Validation error with data table request: unknown column name '<col>'`:
1. The table exists but column names don't match — check via `docker exec n8n-n8n-1 node -e "..."` (SQLite query on `data_table_column`)
2. The table doesn't exist — must be created from n8n UI (Data Tables → New)
3. Fix: update the node's column mapping via `update_workflow` with `updateNodeParameters` + `replace: true`

See `n8n-mcp-local-config` skill → `references/data-table-db-manipulation.md` for DB-level column addition scripts.

## Pitfalls
- Always **unpublish spamming workflows first** — don't diagnose while 10k errors are accumulating
- Don't fire >5-6 parallel MCP calls of the same type (archive, update, etc.) — rate limit + 60s cooldown
- `availableInMCP: false` workflows are invisible to MCP operations — list them for manual UI action
- For ETIMEDOUT on Tailscale IPs (100.x.x.x): the service is down, not a workflow bug — disable and inform
- For Postgres Connection refused on Docker bridge IPs (172.x.x.x): Postgres container IP changed — disable and inform
- Test fixed workflows with `test_workflow` before republishing
- Ask the user before fixing: "Désactiver seulement / Désactiver + réparer / Tout faire" — let them choose the scope
- **MCP Pangolin validation error**: workflows with invalid ai_tool connections fail on any update that triggers validation (e.g. rename). Tag-only updates (addTags) sometimes work; rename always fails. Needs manual fix in UI.
- **Credential linking for HTTP Request nodes**: must set `authentication: "predefinedCredentialType"` and `nodeCredentialType: "httpBearerAuth"` via `updateNodeParameters` BEFORE linking credential via `setNodeCredential` — otherwise the node doesn't accept the credential type.
- **Error Trigger workflow**: the Error Trigger fires for production executions only, not manual/test runs. Test pin data won't trigger it — test by running a workflow that fails in production mode.