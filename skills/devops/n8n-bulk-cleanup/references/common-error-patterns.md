# Common n8n Error Patterns

Error → root cause → fix mappings encountered during workflow cleanup sessions.

## Discord "Cannot send an empty message" (error 50006)

**Symptom**: Discord node fails with `"Cannot send an empty message"`, code `50006`.

**Cause**: A Code node returns `{ content: '', embed: {...} }`. Discord API rejects messages where `content` is an empty string even when an embed is present.

**Fix**: Set `content` to a non-empty summary string:
```javascript
// BAD — Discord rejects this
return [{ json: { content: '', embed } }];

// GOOD — content has a summary
const summary = `📊 ${events.length} events · ${hosts.size} services`;
return [{ json: { content: summary, embed } }];
```

**Workflow**: Pangolin Events → Discord (IIqWZRSkKJfsdHdu) — had 10,074 errors from this.

---

## ETIMEDOUT on Tailscale IP (100.x.x.x)

**Symptom**: HTTP Request node fails with `connect ETIMEDOUT 100.64.0.4:7878`.

**Cause**: Target service (Radarr, Sonarr, etc.) is down or its Tailscale IP changed. Not a workflow bug.

**Action**: Disable workflow via `unpublish_workflow`. Tell the user which service to restart. Do NOT attempt to fix the workflow — the fix is on the infrastructure side.

**Workflow**: arr* sync with database (GypB_Dkf-HZap4tC9rZqw) — Radarr at 100.64.0.4:7878 unreachable.

---

## Postgres "Connection refused" on Docker bridge IP (172.x.x.x:5432)

**Symptom**: Postgres node fails with `Connection refused`, description shows `172.19.0.2:5432`.

**Cause**: Postgres container restarted with a new Docker bridge IP, or the DB was recreated. The n8n credential points to the old IP.

**Action**: Disable workflow. The fix requires updating the n8n Postgres credential to the new IP/hostname, or exposing Postgres on a stable IP (Tailscale, dedicated Docker network with static IPs).

**Workflow**: NextDNS Stats - Cache Postgres (eI0BnOMPcJ93uBry) — `172.19.0.2:5432` unreachable.

---

## Pangolin Event Streaming payload shape

Pangolin Event Streaming sends a **JSON array** as the POST body. Each element:
```json
{ "event": "request", "data": { "host": "...", "ip": "...", "method": "GET", "path": "...", "location": "..." } }
```

The Code node must:
1. Check `Array.isArray(input.body)` and iterate
2. Access fields via `e.data.host` (not `e.host`)
3. Use fallback `const d = e.data || e;` for robustness across payload variants

```javascript
const events = items[0].json.body;
if (!Array.isArray(events) || events.length === 0) {
  return [{ json: { content: '✅ Aucun événement' } }];
}
// Iterate and access via e.data.*
for (const e of events) {
  const d = e.data || e;
  const host = d.host || '?';
  // ...
}
```

---

## MCP batch operation rate limiting

**Symptom**: After 5-6 parallel MCP calls of the same type (e.g. `archive_workflow`), the MCP server becomes unreachable. Error: `"MCP server 'n8n-mcp' is unreachable after N consecutive failures. Auto-retry available in ~60s."`

**Cause**: The n8n MCP server has connection/transaction limits. Too many simultaneous operations overwhelm it.

**Fix**:
- Batch MCP calls in groups of 5 max
- Wait for each batch to complete before starting the next
- If unreachable: `sleep 65` in terminal, then retry
- Serial calls work but are slow — small parallel batches are the sweet spot

---

## `availableInMCP: false` blocks MCP operations

**Symptom**: `archive_workflow` or `update_workflow` fails with `"Workflow is not available in MCP. Enable MCP access from the workflow card in the workflows list, or from the workflow settings."`

**Cause**: The workflow has `availableInMCP: false` in its settings. This is a per-workflow MCP access toggle.

**Action**: Cannot be fixed via MCP. List the workflow for the user to archive/modify manually in the n8n UI.

---

## MCP Pangolin validation error on update

**Symptom**: `update_workflow` fails with `"Invalid connection: a node was wired as a tool to an agent, but its type does not produce an ai_tool output. 'MCP Pangolin' (@n8n/n8n-nodes-langchain.mcpTrigger) cannot be used as a tool for 'pangolin_api'"`.

**Cause**: The MCP Pangolin workflow has a connection configuration that n8n's validator rejects. The mcpTrigger node type doesn't produce an `ai_tool` output but is wired as one.

**Action**: 
- `addTags` operations alone sometimes succeed (they don't trigger full validation)
- `setWorkflowMetadata` (rename) always fails because it triggers a full workflow validation pass
- The fix must be done manually in the n8n UI: rewire the connection or fix the node configuration

---

## HTTP Request credential linking in SDK-created workflows

**Symptom**: `setNodeCredential` fails with `"node type 'n8n-nodes-base.httpRequest' does not accept credential 'httpBearerAuth'"` when trying to link a bearer token credential to an HTTP Request node.

**Cause**: The HTTP Request node needs its authentication mode set to `predefinedCredentialType` with the correct `nodeCredentialType` BEFORE the credential can be linked.

**Fix** (two-step):
```
# Step 1: Set auth type
mcp__n8n_mcp__update_workflow(operations=[{
  "type": "updateNodeParameters",
  "nodeName": "Send ntfy",
  "parameters": {
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpBearerAuth"
  }
}])

# Step 2: Link credential (now works)
mcp__n8n_mcp__update_workflow(operations=[{
  "type": "setNodeCredential",
  "nodeName": "Send ntfy",
  "credentialKey": "httpBearerAuth",
  "credentialId": "<cred-id>",
  "credentialName": "NTFY"
}])
```

---

## Credentials with hardcoded passwords in workflows

**Symptom**: A workflow (e.g. qBittorrent Check) contains plaintext passwords in node parameters.

**Risk**: Passwords exposed in workflow JSON, visible to anyone with workflow read access.

**Action**: Archive the workflow if a MCP server equivalent exists (MCP servers use credentials, not hardcoded passwords). If the workflow is still needed, replace hardcoded auth with n8n credentials.

**Example**: `qBittorrent Check` (oS40zUtM4QkQRtdI) had `password: "vegan-smirk-grub-stumbling-deviant-backwater-salvaging-cough-parish-poise"` in the Login node. Archived in favor of `MCP - qBittorrent` which uses proper credentials.