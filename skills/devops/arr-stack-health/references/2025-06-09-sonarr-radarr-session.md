# 2025-06-09 Session — Sonarr Down + Radarr Queue Bottleneck

## Sonarr Recovery — n8n IP Drift

**Problem:** Sonarr MCP tools returned "connection refused" from all sessions (Hermes native, n8n bridge).

**Root cause:** Sonarr was migrated from jNas (100.64.0.4) to AX42 (100.64.0.2), but the n8n MCP workflow "MCP Sonarr" still hardcoded `http://100.64.0.4:8989/...` in all 11 httpRequestTool nodes.

**Fix applied:**
1. `get_workflow_details` → inspected all 11 tool nodes, noted `url` parameter values
2. Found that some draft nodes already had `.0.2` (sonarr_lookup_series, sonarr_list_series) — partial fix incomplete
3. `update_workflow(operations: [11x setNodeParameter on /url])` → changed all to `.0.2`
4. `publish_workflow` → activated the fix
5. Verified: `sonarr_system_status` returned version 4.0.17.2952

**Lesson:** When a backend service moves Tailscale IP, ALL tool nodes in the MCP workflow must be updated atomically. The draft may have partial fixes — always check all nodes.

## Sonarr State (Post-Recovery)

- Queue: 57 items (many with qBittorrent errors)
- Wanted/Missing: 1,631 episodes
- Status: OK, Docker on AX42, Sonarr v4.0.17.2952

## Radarr State

- Queue: 66 items total
  - ~60 in "warning" state: "qBittorrent signale une erreur" / "download stuck no connection"
  - 1 paused (Shrek 2)
  - 6 completed but stuck:
    - 3x "Unable to parse file" (Vampire Hunter D, Make Mine Music, Fairy Tail Dragon Cry)
    - 2x "Manual Import required" (Your Name, Harakiri)
    - 1x "Unable to determine if file is a sample" (Lady and the Tramp)
- Wanted/Missing: 95 movies
- History: ~30 successful imports in last 48h (quality upgrades)
- Last 24h imports: Cinderella, Braveheart, Creed III, Michael(2160p upgrade), Ne Zha 2, etc.

## qBittorrent (Not Yet Diagnosed — MCP Tool Created)

- Host: 100.64.0.2:8080, same AX42
- User: jefe, cookie-based auth
- n8n MCP workflow "MCP qBittorrent" created (needs credential setup)

## Key Numbers

| Metric | Value |
|---|---|
| Radarr queue | 66 items (~60 errored) |
| Radarr wanted | 95 movies |
| Sonarr queue | 57 items |
| Sonarr wanted | 1,631 episodes |
| Radarr history total | 1,260 events |
| qBittorrent errors | "qBittorrent signale une erreur" + "bloqué sans connexion" |

## n8n MCP Tool URLs (Current)

| Tool | MCP Path | Backend URL |
|---|---|---|
| Radarr | `/mcp/radarr/sse` | `http://100.64.0.2:7878/api/v3/` |
| Sonarr | `/mcp/sonarr/sse` | `http://100.64.0.2:8989/api/v3/` |
| qBittorrent | `/mcp/qbittorrent/sse` | `http://100.64.0.2:8080/api/v2/` |
