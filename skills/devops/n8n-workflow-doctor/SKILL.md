---
name: n8n-workflow-doctor
title: n8n Workflow Doctor
description: Diagnose a failing n8n workflow — retrieve execution history, analyze error messages, identify the failing node, and propose a fix.
tags: [n8n, workflow, debugging, automation, fix]
---

# n8n Workflow Doctor

Diagnose and fix failing n8n workflows in Jefe's n8n instance at n8n.jefe.ovh.

## Workflow

### 1. Identify the Workflow
Either the user tells you the workflow name/ID, or search for failing ones:
```
mcp_n8n_mcp_search_workflows(query="<name>")
mcp_n8n_mcp_search_executions(status=["error"], limit=5)
```

### 2. Get Execution Details
For the failed execution:
```
mcp_n8n_mcp_get_execution(
  workflowId="<id>",
  executionId="<id>",
  includeData=true,
  truncateData=1
)
```

### 3. Analyze the Error
Look for:
- Which node failed
- What error message / status code
- Input data that caused the failure
- Credential issues (auth errors)
- Schema mismatches

### 4. Propose Fix
Common issues and their fixes:
- **Credential expired** → re-authenticate the service
- **Schema change** → update the node's expected data shape
- **API rate limit** → add delay between nodes or retry logic
- **Missing data** → add error handling / fallback values
- **Node config wrong** → update parameters (use `mcp_n8n_mcp_update_workflow`)

### 5. Apply Fix (if user approves)
```
mcp_n8n_mcp_update_workflow(
  workflowId="<id>",
  operations=[{...}]
)
```

Then re-test:
```
# Get the test pin data
mcp_n8n_mcp_prepare_test_pin_data(workflowId="<id>")
# Test
mcp_n8n_mcp_test_workflow(workflowId="<id>", pinData={...})
```

## Silent Failures: Wrong Output, No Error

The hardest bug class: workflow status is **"success"** but output contains fallback/garbage values ("inconnu", "N/A", "Aucun", "Unknown", empty fields).

### Root Cause: Array Payload Treated as Object

The webhook receives a **JSON array** `[{...}, {...}]` as the POST body, but the Code node treats it as a single object. JavaScript silently returns `undefined` for `.field` access on arrays — no error thrown.

**Diagnosis:**
```python
# Get raw incoming payload (use 'success' executions too!)
mcp_n8n_mcp_get_execution(
    workflowId="<id>",
    executionId="<id>",
    includeData=True,
    nodeNames=["WebhookNodeName"],
    truncateData=1
)
```

**What to check in the payload:**
- Is `body` an **array** `[{event: "request", data: {...}}]` or an object?
- If array: the Code must iterate with `.map()` or a loop, not `$input.first()`
- Check **actual field names**: Pangolin wraps fields under `data.*` (e.g. `event.data.host` not `body.host`)
- Compare actual vs expected fields with a table audit (see `references/webhook-payload-field-audit.md`)

**Fix pattern for array webhooks:**
```javascript
const input = $input.first().json;
const events = Array.isArray(input.body) ? input.body : [input.body];

return events.map((event, index) => ({
  json: {
    type: event.event || event.data?.event || 'EVENT',
    host: event.data?.host || event.host || 'N/A',
    path: event.data?.path || '',
    ip: event.data?.ip || '',
    location: event.data?.location || '',
    url: event.data?.originalRequestURL || ''
  },
  pairedItem: { item: index }
}));
```

### Common Payload Sources

| Source | Body type | Key nesting |
|---|---|---|
| Pangolin Event Streaming | Array | `event.data.<field>` |
| GitHub webhooks | Object (some events: array) | Varies by event type |
| Batch relay/aggregator | Array | Items directly in body |

## Pipeline Diagnosis (multi-workflow)

When a workflow fails, it's often part of a **pipeline** (data flows through several workflows). Always check:

### 1. Find Related Workflows
Search for workflows sharing the same name prefix or service:
```python
mcp_n8n_mcp_search_workflows(query="<service-name>")
```

### 2. Check All Pipeline Stages
For each related workflow:
- Is it active? (`mcp_n8n_mcp_get_workflowDetails`)
- Does it have recent executions? (`mcp_n8n_mcp_search_executions`)
- Are they failing too? Same error pattern?
- Are they up/downstream dependencies? (one feeds data to another)

⚠️ **Distinguish "never run" from "failing":**
- A workflow with 0 total executions has **never triggered** — check if it's inactive, unpublished, or waiting on an upstream dependency
- A workflow with `active: true` but `activeVersionId: null` has **never been properly published** — the active version on disk hasn't been committed
- A workflow with 1000+ error executions needs infrastructure fixing (credential, DB, API) before you can fix the workflow logic

### 3. Check Shared Credentials
The same credential is often reused across pipeline workflows:
```python
mcp_n8n_mcp_list_credentials(query="<name>")
```
Then for each workflow using that credential, check if they all fail identically.

### 4. Map Dependency Graph
Before proposing fixes, map which workflow feeds data to which:
- **Upstream** (ingestion/logs): fetch external data, store in DB/data table
- **Middleware** (cache/aggregation): transform raw data into pre-computed stats
- **Downstream** (dashboard/presentation): serve data to end users (webhooks)
- A fix is only complete when ALL stages in the pipeline work end-to-end

### 5. Check Backend Dependencies
Some workflows depend on **database-side objects** (not visible in n8n):
- Stored functions: `SELECT compute_dashboard_stats() AS payload` → if the DB was recreated, the function may not exist
- Tables: `nextdns_logs`, `dashboard_cache` → if missing, workflows fail silently
- Database users/credentials: the n8n credential may point to an IP/host that no longer exists
- To check: connect to Postgres directly and verify the schema:

## Pitfalls
- Don't modify workflows without user confirmation
- Some errors are transient (rate limits, network blips) — check if it's intermittent
- Check if the workflow is active/published — a draft fix won't affect production
- If the error is "unauthorized" or "401", it's almost always a credential issue
- For "ECONNREFUSED" errors, the external service may be down — not a workflow issue
- Always explain the root cause before offering to fix it

### Postgres "Connection refused" — Backend Gone Stale
A common pattern when Postgres ran in Docker and the container restarted, or the entire DB was recreated:
- Error shows `172.x.x.x:5432` (Docker bridge IP) → **"Connection refused"**
- The Postgres container got a new IP after restart, or the Docker network was recreated
- Or Postgres is now running on a different machine entirely

**To diagnose:**
1. Check if Postgres is running locally: `ss -tlnp | grep 5432`
2. Check if the expected IP responds: `ping -c1 -W2 <ip>`
3. Check `pg_hba.conf` for allowed hosts: `cat /etc/postgresql/*/main/pg_hba.conf`
4. Check if Postgres listens on network vs localhost: `grep listen_addresses /etc/postgresql/*/main/postgresql.conf`
5. Cross-reference: list all workflows using the same Postgres credential — if they all fail identically, the fix is at the credential level, not per-workflow
6. **Check database-side dependencies**: the workflow may call `SELECT compute_dashboard_stats()` — if the DB was recreated, this function needs to be recreated too

**Fix options:**
- Update the n8n credential to point to the new Docker IP or hostname
- Or expose Postgres on a stable Tailscale IP and update pg_hba.conf to accept it
- Or create a dedicated Docker network with static IP assignment for Postgres
- Full backend rebuild procedure → see `references/postgres-backend-rebuild.md`
