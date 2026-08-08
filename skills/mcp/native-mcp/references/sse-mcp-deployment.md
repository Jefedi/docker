# SSE vs StreamableHTTP Transport

## StreamableHTTP (Preferred)
Used by modern MCP servers like n8n MCP. Single POST endpoint, bidirectional.

```yaml
mcp_servers:
  n8n:
    url: "https://n8n.example.com/mcp-server/http"
    headers:
      Authorization: "Bearer <jwt-token>"
```

## SSE (Legacy/Older servers)
Requires two-step handshake: GET SSE endpoint → receive session URL → POST JSON-RPC.

n8n exposes SSE endpoints at: `https://n8n.example.com/mcp/{service}/sse`

Known working SSE services via n8n MCP bridge (tested):
- discord: 1 tool (discord_api)
- uptimekuma: 4 tools (push heartbeat, status pages, metrics)
- jellyfin: 19 tools (search, play, library)
- paymenter: 1 tool (admin API)
- pterodactyl: 2 tools (client + application API)
- cineverse: 1 tool (bot API)
- seerr: 1 tool (API)
- radarr: 1 tool (API)
- sonarr: 11 tools (series, queue, calendar, etc.)

## Testing

Test SSE endpoint connectivity:
```bash
curl -s --max-time 5 -H "Authorization: Bearer <token>" "https://host/mcp/service/sse"
# Expected: HTTP 200, event: endpoint / data: /mcp/service/messages?sessionId=...
```

## Common Pitfalls

1. The JWT token for the StreamableHTTP endpoint may DIFFER from the token for SSE endpoints.
2. When using the bridge with config.yaml, the token can be shared across all servers by writing to `~/.hermes/scripts/sse_token.txt`.
3. Adding new MCP servers requires a gateway restart (`hermes gateway restart`).
4. Allow `~/.hermes/scripts/` to exist before bridge starts.
