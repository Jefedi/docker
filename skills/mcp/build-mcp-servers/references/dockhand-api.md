# Dockhand API Reference

Dockhand (Docker management UI) on AX42: `http://100.64.0.2:3000`

**Auth:** None (password-less in current setup)

## Environments / Docker Hosts

| ID | Name | IP | Connection | Type |
|----|------|----|------------|------|
| 1 | ax42 | 100.64.0.2 | `/var/run/docker.sock` | local socket |
| 2 | jnas | 100.64.0.4:2376 | Hawser agent | remote (HA token) |
| 3 | VPS Pangolin | 100.64.0.12:2376 | Hawser agent | remote (HA token) |
| 4 | jtower | 100.64.0.5:2376 | Hawser agent | remote (HA token) |

```
GET /api/environments → list of {id, name, host, port, connectionType, publicIp, ...}
```

## Containers

```
GET  /api/containers?environmentId=N          → list containers
GET  /api/containers/N/logs?environmentId=N   → container logs
POST /api/containers/N/start                  → start container
POST /api/containers/N/stop                   → stop container
POST /api/containers/N/restart                → restart container
```

## Stacks

```
GET  /api/stacks?environmentId=N    → list stacks
POST /api/stacks/N/deploy            → deploy/update stack
POST /api/stacks/N/stop              → stop stack
```

## Other Resources

```
GET /api/images?environmentId=N        → list images
GET /api/volumes?environmentId=N       → list volumes
GET /api/networks?environmentId=N      → list networks
GET /api/system                        → system info (runtime, DB, aggregate stats)
GET /api/events?environmentId=N        → Docker events
GET /api/notifications                 → notifications
GET /api/environments/{id}            → single environment details
GET /api/license                      → license info
```

## System Info Stats (from /api/system)

```json
{
  "stats": {
    "containers": {"total": N, "running": N, "stopped": N},
    "images": N,
    "volumes": N,
    "networks": N,
    "stacks": N
  }
}
```

## Notes

- All `environmentId` params are optional — omit to query across all hosts
- Hawser agents (jnas, jtower, VPS Pangolin) may show `hawserLastSeen: null` if not connected
- No auth required on current setup (Dockhand settings show `"error":"Authentication is not enabled"`)
- The MCP server uses httpx with 20s timeout and no auth headers
