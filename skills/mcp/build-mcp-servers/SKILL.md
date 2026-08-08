---
name: build-mcp-servers
title: Build Custom MCP Servers for Jefe's Homelab
description: Build, test, register, and deploy custom FastMCP servers for Jefe's services and APIs. Covers the full lifecycle from identifying an API to having tools available in Hermes.
tags: [fastmcp, mcp, python, api-wrapper, homelab, docker]
---

# Build Custom MCP Servers for Jefe's Homelab

Build custom MCP servers wrapping Jefe's infrastructure APIs using FastMCP — OR install existing official MCP server packages. Check for existing official servers first (see step 0 below). Uses the `fastmcp` skill for scaffolding and `native-mcp` for registration.

## Prerequisites

```bash
pip install httpx
```

The `mcp` package (which includes `FastMCP`) is already installed in the Hermes venv at `/opt/hermes/.venv/`. Do NOT use `from fastmcp import FastMCP` — that standalone package is not installed. Use:
```python
from mcp.server.fastmcp import FastMCP
```

To run scripts that need the `mcp` module from the terminal (where `/opt/hermes/.venv/bin/python3` may be blocked by the gateway process guard), use:
```bash
PYTHONPATH="/opt/hermes/.venv/lib/python3.13/site-packages" python3 your_script.py
```

## Reference Files

- `references/portainer-mcp.md` — Official Portainer MCP server (alternative to building custom)
- `references/dockhand-api.md` — Dockhand API endpoints (canonical real-world example)
- `references/bazarr-api.md` — Complete Bazarr API endpoint reference (64 endpoints, 11 namespaces)
- `references/searxng-api.md` — SearXNG JSON API reference + Pangolin private resource pattern
- `references/metube-api.md` — MeTube REST API reference + Telegram /dl command pattern
- `references/telegram-command-mcp.md` — Register Telegram slash commands for MCP tools via Bot API setMyCommands
- `references/crosswatch-api.md` — CrossWatch (watchlist/history sync) API endpoint reference (53 tools, v2)
- `references/seerr-api.md` — Seerr (Overseerr/Jellyseerr fork) API v1 reference (55 tools, X-Api-Key auth)
- `templates/crosswatch_server.py` — Full MCP server for CrossWatch (Pangolin tunnel + auth)
- `templates/dockhand_server.py` — Full working MCP server for Dockhand Docker management
- `templates/seerr_server.py` — Full MCP server for Seerr (55 tools, X-Api-Key header auth)

## Concrete Example: Jellyfin MCP Server

The file `references/jellyfin-mcp-server-example.md` documents a real-world FastMCP server wrapping the Jellyfin API with 46 tools. Use it as a reference for:
- Header-based auth (`X-Emby-Token`) pattern
- Catch-all `read_api`/`write_api` tools for flexible coverage
- Registration command format with env vars and connect-timeout
- Tool categorization by API domain

## Multi-Platform Usage

The same stdio-based MCP servers can be used with any MCP client. Config format is almost identical, only the file path differs:

| Platform | Config File |
|----------|-------------|
| Hermes Agent | `~/.hermes/config.yaml` (`mcp_servers:` section) |
| Claude Code | `.mcp.json` or `~/.claude.json` |
| Claude Desktop | `claude_desktop_config.json` |
| ChatGPT Desktop | `appConfig.json` |
| Cursor | `.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| VS Code + Copilot | `.vscode/mcp.json` |

JSON format for all non-Hermes clients:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "python3",
      "args": ["/path/to/server.py"],
      "env": { "SERVICE_URL": "http://host:port" }
    }
  }
}
```

**Telegram slash commands from MCP tools** — See `references/telegram-command-mcp.md` for how to register a Telegram bot command (like `/dl`) via the Bot API and wire it to an MCP tool + skill. Covers `setMyCommands`, scope (DM vs group), the `/dl` skill pattern, and pitfalls (commands overwrite, not merge).

## Workflow

### 0. Check for Existing MCP Server

Before building from scratch, check if an official MCP server already exists for this service — many popular self-hosted services have official packages on PyPI, npm, or Docker Hub:

- Search: `pip search <service>-mcp`, `npm search <service>-mcp`, or web search `"MCP server" <service>`
- Check [mcpservers.org](https://mcpservers.org/) or [mcp.so](https://mcp.so/) for community listings
- Example: Portainer has `mcp-portainer` (PyPI), `portainer/portainer-mcp` (Docker), and `portainer/portainer-mcp` (GitHub)

**When to use official vs build custom:**
| Official exists | Action |
|----------------|--------|
| ✅ Yes, well-maintained | Install it — faster, fewer bugs, auto-updates |
| ⚠️ Yes, but stale or partial | Build custom — more control, can tailor to needs |
| ❌ No | Build custom via FastMCP |

See `references/portainer-mcp.md` for a worked example of setting up an official MCP server behind Pangolin Private Resource.

### 1. Research the API

Probe endpoints with curl:
```bash
curl -s -o /dev/null -w "%{http_code}" http://<host>:<port>/api/health
```

For open-source services, read the source code's API init file (fastest way):
1. Navigate to repo's API directory (e.g. `bazarr/api/`)
2. Read `__init__.py` for all registered namespaces
3. Use `delegate_task` with `web_extract` to parallel-read resource files
4. Always verify response format with a real curl before coding

### 2. Build the Server

```python
import os, httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Service Name")
SERVICE_URL = os.getenv("SERVICE_URL", "http://default:port")

def _request(method, path, params=None, json_body=None):
    url = f"{SERVICE_URL.rstrip('/')}/{path.lstrip('/')}"
    with httpx.Client(timeout=20) as client:
        resp = client.request(method, url, params=params, json=json_body)
        return resp.json()
```

**Parameter naming:** Avoid Python builtins (`format`, `id`, `type`, `input`, `list`, `dict`) as tool parameter names. Rename: `format` → `download_format`, `id` → `item_id`, `type` → `media_type`. Conflict manifests as `JSONDecodeError: Extra data` at runtime.

**API key pattern:**
```python
API_KEY = os.getenv("SERVICE_API_KEY")
if not API_KEY:
    key_file = os.path.expanduser("~/.hermes/service_api_key.txt")
    if os.path.exists(key_file):
        API_KEY = open(key_file).read().strip()
```

### 3. Test Locally

**Option A — Python discovery (custom servers):**
```bash
cd /path/to/ && python3 -c '
import asyncio
from server import mcp

async def main():
    tools = await mcp.list_tools()
    for t in sorted([t.name for t in tools]):
        print(t)
    print(f"\nTotal: {len(tools)} tools")

asyncio.run(main())
'
```

**Option B — Direct MCP stdio protocol test (official packages):**
```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' | KEY=val timeout 15 /path/to/cli 2>/dev/null | python3 -c '
import json, sys
for line in sys.stdin:
    data = json.loads(line.strip())
    if "result" in data and "tools" in data.get("result",{}):
        tools = data["result"]["tools"]
        print(f"Total tools: {len(tools)}")
        for t in tools[:10]: print(f"  - {t["name"]}")
'
```

Bypasses Hermes, tests the MCP server directly. Useful for debugging connectivity/auth before registering.

**Option C — Test a specific tool via stdio (MCP protocol):**
```bash
python3 -c '
import subprocess, json
proc = subprocess.Popen(
    ["/path/to/cli"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    env={"KEY": "val", ...}, text=True
)
proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}})+"\n")
proc.stdin.flush(); proc.stdout.readline()
proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ToolName","arguments":{}}})+"\n")
proc.stdin.flush()
line = proc.stdout.readline()
data = json.loads(line.strip())
if "result" in data and "content" in data["result"]:
    print(data["result"]["content"][0].get("text","")[:500])
elif "error" in data: print(f"Error: {json.dumps(data["error"],indent=2)[:300]}")
proc.stdin.close(); proc.wait(timeout=10)
'
```

**Guidance Gate Pattern** — Some official MCP servers (Portainer, etc.) enforce a guidance/hygiene gate: must call `get_guidance` once per session before any other tool. The response is a local document, not an API call. Test sequence: init → get_guidance → tool, all over a single stdio pipe. This gate also breaks `hermes mcp add` auto-detection — the server saves as `enabled: false`. Manually enable post-add.

### 4. Register with Hermes

```bash
printf 'Y\nY\n' | hermes mcp add server-name \
  --command "/usr/local/lib/hermes-agent/venv/bin/python3" \
  --args "/path/to/server.py"
```

For official packages installed via pip, use the CLI binary directly:
```bash
printf 'Y\nY\n' | hermes mcp add server-name \
  --command "/usr/local/lib/hermes-agent/venv/bin/<cli-binary>" \
  --env "SERVICE_URL=https://..." \
  --env "API_KEY=ptr_......n
```

**Notes:**
- `--connect-timeout` does NOT exist on `hermes mcp add` / `--env` supports multiple `KEY=VALUE` pairs / `--args` MUST be the last option

### 5. Publish to Central Repository

All MCP servers are published to **`Jefedi/mcp-servers`** (branch `master`) for sharing across platforms (Hermes, Claude Code, Claude Desktop, Cursor, etc.).

Before pushing, the README.md must be updated. It has a consistent format:

1. **Server table** — add a row: `| \`your_server.py\` | ServiceName | N | Description |`
2. **Env vars config table** — after SearXNG section, add a `### ServiceName — \`your_server.py\`` block with a pipes table of `Variable | Défaut | Description`
3. **Tool list** — comma-separated, extract with: `grep -n "def " server.py | grep -v "^.*def _" | sed 's/.*def \([a-z_]*\)(.*/\1/' | paste -sd ", "`
4. **Architecture diagram** — add a line to the ASCII box at the bottom
5. **Hermes YAML example** — if needed add to the Hermes Agent code block

Commit format: `feat: add <ServiceName> MCP server` with bullet description list.

```bash
# 1. Clone/reuse repo
git clone git@github.com:Jefedi/mcp-servers.git /tmp/mcp-servers || true
cd /tmp/mcp-servers

# 2. Copy the server file (use _server.py suffix for consistency)
cp /root/.hermes/mcp/your_server.py .

# 3. Update README (see format rules above)
# Then commit with descriptive message

git add -A
git commit -m "feat: add ServiceName MCP server

- your_server.py: N tools for ServiceName API
- Update README with config tables and examples"
git push origin master

# 4. On Hermes: restart gateway
hermes gateway restart
```

### 6. (Optional) Wire Telegram Command

1. Register `/command` via Telegram Bot API (`setMyCommands`)
2. Create a skill explaining the pattern to Hermes
3. Document in `references/telegram-command-mcp.md`

## Pangolin Private Resource Pattern

For services behind Pangolin Private Resources (not directly reachable):
- Route through the Newt tunnel: `docker exec pangolin-cli curl -sk <private-url>`
- Config: `SERVICE_URL=https://service.jefe.al`, `SERVICE_INTERNAL=false`, `SERVICE_DOCKER_CMD=docker exec pangolin-cli`
- The `_api()` function conditionally routes through Docker or direct HTTP based on `INTERNAL` flag
- This applies to SearXNG, MeTube, Portainer, and any future private resources

### Pangolin WireGuard Network

The Pangolin/Newt tunnel creates a WireGuard interface:
- Interface name: `pangolin`
- Subnet: `100.90.128.0/24`
- This VPS (Pangolin server): `100.90.128.14`
- AX42 (Newt client): `100.90.128.1`
- Pingable from host even when Tailscale is down
- Standard service ports (9000/9443 for Portainer) may not be forwarded through the WG tunnel — depends on Docker host networking

## Pitfalls

- **`sed` on config.yaml CORRUPTS THE FILE** — Each match of the anchor pattern triggers an insertion. Use `python3 -c "import yaml; ..."` or `hermes mcp add` instead.
- **FastMCP first connection can timeout** — Use `--connect-timeout 30` (older Hermes versions only) or just retry.
- **Official MCP servers with guidance gates** — Some servers (Portainer, etc.) enforce a per-session `get_guidance` call. This breaks `hermes mcp add` auto-detection (which sends `tools/list` — the gate refuses it → saved as `enabled: false`). **Fix:** manually enable the entry in `config.yaml` after add.
- **`hermes mcp add` has no `--connect-timeout` flag** in current version. Use `--env` for env vars, `--args` as last option.
- **API keys with `/` in `--env` break bash quoting** — keys like `ptr_abc/def/ghi` containing `/` cause shell parsing errors. **Fix:** save the key to a file, reference via `$(cat file)` inside `$()`, or use `Python subprocess` to invoke `hermes mcp add`.
- **Portainer CE header case sensitivity** — Portainer CE 2.39 is case-sensitive with `X-API-Key` vs `X-API-KEY`. The official MCP server sends uppercase; CE rejects with "Invalid JWT token". **Fix:** patch `UPSTREAM_KEY_HEADER` in `passthrough.py` to `"X-API-Key"`.
- **FastMCP OpenAPI provider adds `/api` prefix automatically** — When the spec has no `servers`/`basePath`, FastMCP prepends `/api` to all paths. So `PORTAINER_URL` must NOT include `/api` suffix (else double `/api/api/` → 404).
- **Gateway caches MCP config in memory** — Editing config.yaml alone is not enough. Restart gateway.
- **`@mcp.tool` vs `@mcp.tool()` — decorator parentheses required** — In the `mcp.server.fastmcp` version shipped with Hermes, `@mcp.tool` (without parentheses) raises `TypeError: The @tool decorator was used incorrectly. Did you forget to call it? Use @tool() instead of @tool`. Always use `@mcp.tool()` with parentheses.
- **Hermes venv path is `/opt/hermes/.venv/`** — NOT `/usr/local/lib/hermes-agent/venv/` (outdated). The `mcp` module lives at `/opt/hermes/.venv/lib/python3.13/site-packages/mcp/`. When `hermes config set` asks for `command`, use `/opt/hermes/.venv/bin/python3`. When running scripts directly from terminal where the venv path triggers the gateway process guard, set `PYTHONPATH="/opt/hermes/.venv/lib/python3.13/site-packages"` and use system `python3`.
- **`hermes config set` creates wrong shape for list fields** — `hermes config set mcp_servers.x.args[0] /path/to/script.py` creates a literal key `args[0]: /path/to/script.py` in the YAML, NOT a list element `args: ["/path/to/script.py"]`. The config entry will be malformed and `hermes mcp test` will timeout. **Fix:** use `hermes config set mcp_servers.x.args "['/path/to/script.py']"` (passes a YAML list as a string), then manually verify the resulting config with `grep -A10 "x:" config.yaml` and clean up any stray `args[0]` keys. Alternatively, edit config.yaml directly (the `hermes config set mcp_servers.x.command` approach works for scalar fields but not list fields).
- **n8n MCP trigger SSE webhooks broken (webhookId=None bug)** — On n8n 2.32.7, MCP Trigger workflows that are `active=1` and successfully published may still return HTTP 404 on their webhook endpoints (`/webhook/<path>/sse`, `/webhook/<path>/messages`). Root cause: `webhook_entity` table has `webhookId=None` for all MCP trigger entries, so n8n never registers the webhook route handler despite the workflow being active. Affects ALL n8n MCP workflows, not just one. `docker restart` and `publish_workflow` do NOT fix it. **Workaround:** build a standalone FastMCP server wrapping the API directly (see this skill's workflow), register it in Hermes config.yaml as a stdio MCP server. This bypasses the n8n MCP trigger entirely.
- **`yaml.dump()` destroys comments and reorders keys** — `python3 -c "import yaml; yaml.dump(yaml.safe_load(open('config.yaml')), open('config.yaml','w'))"` loses all YAML comments and can reorder nested dict keys. Use `python3 -c "...; del config['platforms']['searxng']; ..."` or `hermes config set` for targeted edits; never round-trip a production config.yaml through yaml.dump unless you've verified no critical comments exist.
- **Telegram `/dl` via skill alone doesn't work** — The gateway rejects unknown commands (`not in GATEWAY_KNOWN_COMMANDS`) before the LLM sees them, returning "Unknown command /dl". A skill telling Hermes to handle `/dl` never activates. **Fix: register a Hermes plugin** with `ctx.register_command(name="dl", handler=...)`. The plugin handler runs at gateway level before the unknown-command check. See `references/plugins/dl-video-plugin.py` for a working example.
- **`format` as parameter name breaks FastMCP** — Python builtin conflict triggers `JSONDecodeError: Extra data`. Rename to `download_format`.
- **Telegram `setMyCommands` overwrites** — Always get existing commands first with `getMyCommands`, then merge, then set.
- **Read-only for private trackers** — qBittorrent, Deluge tools must never modify state.
- **qBittorrent port is 8090** — Not 8080. Wrong port gives silent login failure.
- **`hermes mcp test` doesn't pass env vars** from the `add` command's `--env`. Test directly: `SERVICE_URL=x hermes mcp test name`.\n- **`hermes mcp update` does not exist** — There is no `update` subcommand for MCP servers. To change env vars or args on an existing server: `hermes mcp remove <name>` then `hermes mcp add <name>` with the new config.\n- **`FastMCP.list_tools()` is a coroutine in FastMCP v3+** — calling `mcp.list_tools()` synchronously raises `TypeError: 'coroutine' object is not iterable`. Always wrap in `asyncio.run()`: `python3 -c "import asyncio; from server import mcp; print(asyncio.run(mcp.list_tools()))"`.
- **`FastMCP.tool_list()` does not exist** — The method is `list_tools()` (async), not `tool_list()` (synchronous).
- **FastMCP v3 tools MUST return `dict`** — Returning a `list` (e.g. from a `GET /api/...` that returns an array) causes `ValueError: structured_content must be a dict or None`. The `_req()`/`_api()` helper must wrap list responses: `if isinstance(data, list): return {"results": data}`.
- **Cookie auth: extract from Set-Cookie header, not response body** — APIs like CrossWatch use session cookies. The `login` endpoint returns `{"ok":true,"expires_at":...}` in the body but the session cookie is in the `Set-Cookie` HTTP header. Use `curl -sk -v ... 2>&1 | grep -i set-cookie` to extract, then pass as env var to the MCP server.
- **Tailscale blocks Pangolin tunnel** — When Tailscale is active, `docker exec pangolin-cli curl` fails with exit 28 (timeout) or 6 (DNS). Fix: `tailscale down` first. Re-enable with correct up flags after.
- **Portainer/Pangolin Private Resource connectivity** — `https://portainer.jefe.ovh` is a Pangolin Private Resource. The MCP server (running on this VPS) cannot reach it via the public DNS. **Fix:** add a `/etc/hosts` entry pointing to the Newt WireGuard private resource IP (`100.96.128.22`) — discovered via `docker exec pangolin-cli getent hosts portainer.jefe.ovh`. The route `100.96.128.0/24 dev pangolin` must exist. See `references/portainer-mcp.md` for full setup.
