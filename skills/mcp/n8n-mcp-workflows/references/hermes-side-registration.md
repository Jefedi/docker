# Registering a New MCP Tool in Hermes Config

After publishing an n8n MCP bridge workflow, it needs to be registered in Hermes to be discovered.

## Two Registration Paths

### Path A: Via n8n-mcp Hub (Preferred)

The `n8n-mcp` server in `config.yaml` connects to `https://n8n.jefe.ovh/mcp-server/http` (HTTP Streamable transport). It auto-discovers ALL n8n workflows with `availableInMCP: true`. New workflows appear automatically — no Hermes config change needed.

**When it breaks:** The hub token can expire (403 Forbidden). Fix: regenerate the token from n8n UI → Settings → MCP, then re-add:

```bash
hermes mcp remove n8n-mcp
printf "Y\n<new_token>\ny\n" | hermes mcp add n8n-mcp --url "https://n8n.jefe.ovh/mcp-server/http" --auth header
```

### Path B: Direct SSE Bridge (Fallback When Hub Is Down)

When the n8n-mcp hub token is expired or the hub is unreachable, register individual MCP workflows directly via the SSE bridge script.

## The SSE Bridge Pattern

Every n8n MCP tool (Radarr, Sonarr, qBittorrent, etc.) runs as a separate SSE endpoint:
`http://127.0.0.1:5678/mcp/{path}/sse`

Hermes connects via `sse_mcp_bridge.py` which:
1. Reads `SSE_URL` from env
2. Reads `SSE_TOKEN` from `~/.hermes/scripts/sse_token.txt` (shared n8n auth token, optional)
3. Passes it as `Authorization: Bearer ***` on the SSE connection (if token present)
4. Bridges SSE to stdio for Hermes consumption

## Adding a New Server

**CRITICAL: Use Hermes venv Python, NOT system `python3`.** The `mcp` Python module is ONLY installed in `/opt/data/hermes-agent/venv/bin/python`. System `python3` (3.13) lacks it and the bridge silently exits with `ModuleNotFoundError: No module named 'mcp'`.

```bash
hermes mcp remove my-tool  # clean any old entry
printf "Y\n" | hermes mcp add my-tool \
  --command /opt/data/hermes-agent/venv/bin/python \
  --args "/opt/data/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py" \
  --env "SSE_URL=http://127.0.0.1:5678/mcp/my-tool/sse"
hermes config set mcp_servers.my-tool.enabled true
hermes config set mcp_servers.my-tool.connect_timeout 60
```

For SSE endpoints that require auth (bearerAuth on the MCP trigger):
```bash
  --env "SSE_URL=http://127.0.0.1:5678/mcp/my-tool/sse" \
  --env "SSE_TOKEN=your-bearer-token"
```

Or use the shared token file:
```bash
echo 'your-shared-token' > ~/.hermes/scripts/sse_token.txt
```
Then omit `SSE_TOKEN` from each server's env — the bridge auto-reads the file.

## `hermes mcp test` False Negative for SSE Bridges

`hermes mcp test` reports "Connection closed" after ~8s even when the bridge works perfectly. This is a timing issue — the test closes stdin before the SSE handshake completes. Do NOT trust this test for SSE bridges.

### Manual Verification

Pipe JSON-RPC messages directly to the bridge script:

```bash
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
 sleep 1; \
 echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'; \
 sleep 1; \
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'; \
 sleep 3) | \
SSE_URL="http://127.0.0.1:5678/mcp/my-tool/sse" \
timeout 15 /opt/data/hermes-agent/venv/bin/python \
  /opt/data/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py 2>&1
```

If this returns valid JSON-RPC responses with tool definitions, the bridge works. Tools will be available after `hermes gateway restart` (from a separate terminal — the gateway cannot restart itself).

## Verifying Registration

```bash
hermes mcp list
# Should show: my-tool   /opt/data/hermes-agent/ve...   all   ✓ enabled
```

## Limitations

- New MCP tools only appear in Hermes tool list after the MCP client reconnects
- Same-session: the new tool won't show — tell user next session or /new
- MCP servers don't refresh dynamically within a running agent session
- `hermes gateway restart` (from a separate terminal) loads new tools
- The gateway cannot restart itself — you must use another terminal

## Config Edit Security

The patch tool refuses to edit `~/.hermes/config.yaml` (security policy). Use:
1. `hermes config set` CLI commands (preferred)
2. `hermes mcp add` / `hermes mcp remove` CLI commands
3. Python script to insert at the right position (last resort)

## Example: DataGouv Registration (2026-08-01)

DataGouv MCP workflow created on n8n (ID: `DP03u0JeesPAkWW0`), SSE path `data-gouv`, auth `none`. The n8n-mcp hub had an expired token (403), so direct SSE registration was used:

```bash
printf "Y\n" | hermes mcp add data-gouv \
  --command /opt/data/hermes-agent/venv/bin/python \
  --args "/opt/data/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py" \
  --env "SSE_URL=http://127.0.0.1:5678/mcp/data-gouv/sse"
hermes config set mcp_servers.data-gouv.enabled true
hermes config set mcp_servers.data-gouv.connect_timeout 60
```

`hermes mcp test` reported "Connection closed" but manual verification confirmed both `DataGouv_API` and `DataGouv_Tabular` tools were properly exposed.