# 2025-06-09 Session 2 — qBittorrent Down + localhost Fix

## Context

qBittorrent at `100.64.0.2:8080` returned ECONNREFUSED from both VPS and n8n. Sonarr and Radarr still accessible (on different ports), both reported "qBittorrent signale une erreur" on all active downloads.

## Fix Applied: qBittorrent Check Workflow URL

The "qBittorrent Check" n8n workflow (`oS40zUtM4QkQRtdI`) hardcoded `http://100.64.0.2:8080/...` in all three nodes (Login, Get Torrents, Get Transfer).

**Fix:**
1. `unpublish_workflow` to deactivate first
2. `update_workflow(operations: [{updateNodeParameters: Login → /url: localhost}, {updateNodeParameters: Get Torrents → /url: localhost}, {updateNodeParameters: Get Transfer → /url: localhost}])`
3. `publish_workflow` to activate

Even with the fix, qBittorrent was still ECONNREFUSED on localhost — because the container itself was down, not just unreachable from the wrong IP.

**Lesson:** `localhost` is the correct address when n8n shares the Docker host, but a container-level refusal means the service is actually stopped.

## Workflow Execution Patterns

The "MCP qBittorrent" workflow (`UMCiYYHUuLOxWwVU`) uses an MCP Trigger node and is `availableInMCP: true`. It cannot be executed via `execute_workflow` — only MCP Trigger workflows with `@n8n/n8n-nodes-langchain.mcpTrigger` are supported as MCP tools.

The "qBittorrent Check" workflow uses a regular Webhook trigger, so it CAN be executed with:
```
execute_workflow(
  workflowId="oS40zUtM4QkQRtdI",
  executionMode="manual",
  inputs={type: "webhook", webhookData: {body: {}, headers: {}, method: "GET", query: {}}}
)
```

## Queue State Snapshot

| Queue | Total | Warning/Error | Completed (blocked) | Paused |
|-------|-------|---------------|---------------------|--------|
| Radarr | 66 | 59 + 7 blocked | 5 (importBlocked/importPending) | 1 |
| Sonarr | 57 | 43 (Adventure Time S6) | 7 (importing) | 0 |

## qBittorrent Error Messages Observed

- "qBittorrent signale une erreur" — most common, generic client error
- "Le téléchargement est bloqué sans aucune connexion" — no peers/trackers reachable
- "Unable to parse file" — download complete but Radarr can't read the file
- "Manual Import required" — matched by ID, needs manual routing
- "Unable to determine if file is a sample" — file detected as potential sample

## IP Connectivity Notes

- qBittorrent n8n MCP workflow uses `localhost:8080` (correct, since n8n is on AX42)
- Original "qBittorrent Check" used `100.64.0.2:8080` (wrong — unreachable from Docker)
- The "MCP qBittorrent" workflow already used `localhost:8080` (was correct from the start)
- Even `localhost:8080` fails when qBittorrent container is genuinely stopped
