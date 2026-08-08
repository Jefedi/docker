---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP/SSE)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## Workflow: MCP-First

Whenever the user asks you to **access a service** (Radarr, Sonarr, Jellyfin, GitHub, databases, APIs), do NOT reach for `curl`/`terminal` first. Follow this order:

1. **Run `hermes mcp list`** — check what MCP servers are configured and their status
2. If the server is **enabled**, look for its tools in your available tool list (prefixed `mcp_{name}_*`)
3. If tools aren't available but the server is enabled, **diagnose** the connection (see Troubleshooting section)
4. Only fall back to direct HTTP/terminal if the MCP route is genuinely blocked

The user's MCP infrastructure is the intended path for accessing managed services. Skipping it and jumping to raw curl wastes time and misses the architecture they've set up. This is especially important for SSE-bridged MCPs (via n8n) — they may need an auth token or their backend may be temporarily unreachable.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Connect to remote SSE-based MCP servers (via included bridge script)
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## CLI Quick Add (Alternative to Manual Config)

Instead of editing `config.yaml` by hand, use the `hermes mcp add` command:

```bash
# Stdio transport
hermes mcp add server-name --command "npx" --args "-y" --args "some-mcp-package"

# With env vars
hermes mcp add server-name --command python3 --args "/path/to/script.py" --env "API_KEY=*** --env "URL=https://api.example.com"

# HTTP transport
hermes mcp add server-name --url "https://my-server.com/mcp" --env "MY_VAR=value"
```

The CLI automatically:
1. Connects to the server
2. Discovers tools
3. Prompts to enable them
4. Saves the config to `~/.hermes/config.yaml`

### Known Pitfall: `--args` with `--`-prefixed arguments

If the server command takes `--`-prefixed flags (e.g. `--openapi`, `--base-url`), `hermes mcp add --args` fails because `hermes` parses them as its own options:

```bash
# BROKEN — --openapi gets eaten by hermes CLI
hermes mcp add pangolin --command ./binary --args --openapi /path/to/spec.json --base-url https://api.example.com/v1
# → Error: unrecognized arguments: --openapi
```

**Workaround:** Write a wrapper script that hardcodes the flags, then register just the wrapper:

```bash
#!/bin/bash
exec /path/to/mcp-server --openapi /path/to/spec.json --base-url "https://api.example.com/v1" "$@"
```

```bash
hermes mcp add server-name --command /path/to/wrapper.sh
```

No `--args` needed — the flags are embedded in the script, not on the CLI.

## Advanced: Setting Up a 3rd-Party PyPI MCP Server

When installing an external MCP server from PyPI (e.g. `pip install mcp-portainer`, `pip install mcp-filesystem`, etc.), the workflow has several gotchas beyond the basic `hermes mcp add`.

### Full Setup Recipe

```bash
# 1. Install the package (in Hermes venv if using that python)
pip install mcp-portainer

# 2. Verify the binary is on PATH
which mcp-portainer  # or wherever it was installed

# 3. Add via hermes CLI
hermes mcp add server-name \
  --command /path/to/venv/bin/mcp-portainer \
  --env "API_KEY=*** \
  --env "BASE_URL=https://internal.example.com" \
  --connect-timeout 30

# 4. Check what was actually saved
grep -A 10 "server-name" ~/.hermes/config.yaml
# ⚠️ `hermes mcp add --env` may NOT persist env vars to config.yaml!
```

### Env Vars Lost After `hermes mcp add` (Known Pitfall)

`hermes mcp add --env KEY=VALUE` accepts the env vars at add time but does **not** always write them to `~/.hermes/config.yaml`. If the server crashes at startup or tools don't appear, check the config directly:

```bash
# Env vars were accepted but not persisted → manually set them:
hermes config set --mcp server-name env.API_KEY "abc123"
hermes config set --mcp server-name env.BASE_URL "https://..."

# Also check the server is enabled:
hermes config set --mcp server-name enabled true
```

After fixing the config, verify connectivity:

```bash
hermes mcp test server-name
# Expected:
#   ✓ Connected (Nms)
#   ✓ Tools discovered: N
```

### Servers Behind a Reverse Proxy / Internal Network

If the service (e.g. Portainer on `portainer.jefe.ovh`) is behind a reverse proxy like Pangolin/Newt, the public DNS may resolve to the proxy's external IP and produce a "Private Placeholder" or proxy-GET error. Fix with internal routing:

```bash
# 1. Find the internal IP routing to the target host
#    (e.g. WireGuard IP of the server running the service)
curl -sk https://internal-pangolin/api/tunnels  # or check pangolin-cli client status

# 2. Add hosts entry to bypass the public proxy
echo "<wireguard-ip> <service-domain>" >> /etc/hosts
# Example: echo "100.96.128.22 portainer.jefe.ovh" >> /etc/hosts

# 3. Verify the internal route works
curl -sk https://service-domain/api/system/version
# Should return real data, not a placeholder page
```

The `/etc/hosts` entry makes the MCP server connect to the internal IP, bypassing the public reverse proxy entirely while keeping the service bound to `127.0.0.1` on the target host.

### Patching a 3rd-Party MCP for Version Mismatch

When the installed MCP package version doesn't match the server version (e.g. `mcp-portainer~=2.42.6` connecting to Portainer CE 2.39.3), you may need to patch the package source.

**Common fixes:**

1. **HTTP header case sensitivity**: Older servers may expect `X-API-Key` (mixed case) vs `X-API-KEY` (all caps). Find and patch:

   ```bash
   grep -rn "X-API-KEY" /path/to/venv/lib/python*/site-packages/mcp_*/
   # → passthrough.py:107: headers["X-API-KEY"] = self.token
   ```

   ```python
   # Change:
   headers["X-API-KEY"] = self.token
   # To:
   headers["X-API-Key"] = self.token
   ```

2. **Double `/api` prefix**: If the base URL already contains `/api` (e.g. `https://host/api`) and the MCP SDK also appends `/api`, you get `https://host/api/api/...`. Solution:
   - Set `BASE_URL` or `PORTAINER_URL` to `https://host` (without `/api`)
   - The SDK appends `/api` automatically

3. **Test the patch**:
   ```bash
   hermes mcp test server-name
   # Should now connect and show N tools
   ```

4. **Symlink vs pip path**: The binary registered by `hermes mcp add` may be a symlink from `~/.local/bin/` or Hermes venv `bin/`. Use `readlink -f` to find the real package location for patching.

### Gateway Restart Limitation

MCP tools are only loaded into the session at gateway startup. If you add a new MCP server mid-session, the tools will **not** appear in your tool list until the gateway restarts.

You **cannot** restart the gateway from inside the gateway itself (`hermes gateway restart` is blocked to prevent loops). Options:

```bash
# From a separate terminal (SSH, tmux pane, etc.):
hermes gateway restart

# Or, if the session has MCP test working, that confirms the plumbing
# is correct — the tools will load on the next full conversation start.
```

`hermes mcp test server-name` confirms the server works, even if tools aren't available in the current session tool manifest.

### Non‑interactive `hermes mcp add`

When run interactively, `hermes mcp add` prompts:
```
Enable all N tools? [Y/n/select]:
```

For automation from a script or provisioning pipeline, pipe input:

```bash
echo "Y" | hermes mcp add server-name --command ...
yes | hermes mcp add server-name --command ...
```

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

Each entry under `mcp_servers` is a server name mapped to its config. There are three transport types: **stdio** (command-based), **HTTP** (url-based), and **SSE** (via stdio bridge).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### SSE Transport (stdio bridge)

For remote MCP servers that use the SSE transport protocol (standard in raw MCP — the client connects to an SSE endpoint, receives a session-specific message URL, then sends JSON-RPC requests via POST and reads responses via SSE).

> **Designing MCP tools in n8n?** See `references/n8n-mcp-catchall-pattern.md` — a single catch-all tool with `$fromAI()` is better than N individual endpoint-specific nodes.

Hermes does NOT have a native SSE client. Connect to SSE servers using a **bridge script** that acts as a stdio MCP server wrapping an SSE client. The bridge is shipped with this skill as `scripts/sse_mcp_bridge.py`.

```yaml
mcp_servers:
  my-sse-server:
    command: "python3"
    args: ["/root/.hermes/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py"]
    env:
      SSE_URL: "https://example.com/mcp/discord/sse"   # (required) SSE endpoint URL
      SSE_TOKEN: "your-bearer-token"                     # (optional) Bearer token
    connect_timeout: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

### SSE Transport (via bridge script)

For remote MCP servers that use the SSE transport protocol. The standard MCP SSE handshake is:
1. Client connects to an SSE endpoint (GET) and receives `event: endpoint / data: <messages_url>`
2. Client POSTs JSON-RPC requests to the messages URL
3. Client receives responses as SSE events

Hermes does not have a native SSE client transport. Use the **SSE→stdio bridge script** (`scripts/sse_mcp_bridge.py` shipped with this skill) to wrap an SSE server as a local stdio MCP server:

```yaml
mcp_servers:
  discord:
    command: "python3"
    args: ["/root/.hermes/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py"]
    env:
      SSE_URL: "https://n8n.jefe.ovh/mcp/discord/sse"   # (required) SSE endpoint
      SSE_TOKEN: "bearer-token-here"                      # (optional) Bearer token
    connect_timeout: 60
```

The bridge script (`scripts/sse_mcp_bridge.py`) connects to the SSE endpoint, awaits the session handshake, and proxies `list_tools` / `call_tool` requests between stdio and the remote SSE session. The connection persists for the lifetime of the Hermes process.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### StreamableHTTP server returns 406 Not Acceptable or "Client must accept both application/json and text/event-stream"

Some HTTP MCP servers (e.g., n8n MCP) require the client to advertise both `application/json` and `text/event-stream` in the `Accept` header during initialization. If you see this error when testing manually, include both:

```bash
curl -s -X POST <url> \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'
```

The native MCP client handles this automatically via the `mcp` SDK — no manual header config needed in `~/.hermes/config.yaml`.

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern
- Run `hermes mcp list` to confirm the server is enabled and shows expected tool count

### MCP enabled but no tools injected into session

Even when `hermes mcp list` shows a server as `✓ enabled` with `all` tools, those tools may not appear in your current session. This happens when the MCP server connects to a proxy (e.g., n8n) that relays to a backend that is unreachable. Diagnosis workflow:

1. **List MCPs**: `hermes mcp list` — note which servers show `✓ enabled`
2. **Check tool availability**: look for `mcp_{server}_*` in your actual tool list
3. **Test SSE bridge directly** if the server uses SSE transport:

```python
import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def test():
    url = "https://your-n8n/mcp/service-name/sse"
    with open('/root/.hermes/scripts/sse_token.txt') as f:
        token = f.read().strip()
    headers = {'Authorization': f'Bearer {token}'}
    async with sse_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            for t in result.tools:
                print(f'{t.name}: {t.description[:100]}')
            # Then try calling a tool:
            r = await session.call_tool(tool_name, {...})
            print(r.content)
asyncio.run(test())
```

If the SSE connection succeeds (tools are listed) but tool calls return `NodeOperationError: The service refused the connection - perhaps it is offline`, the **n8n/backend cannot reach the target service** even though the MCP plumbing works. Fix options:
- Ensure the n8n SSO/HTTP node can reach the backend's host:port
- Access the backend directly from the Hermes host if it has network access (use `hermes mcp list`-discovered ports)
- Provide API keys for direct access as a fallback

4. **For HTTP MCPs (n8n-mcp style)**: check that the `headers.Authorization` Bearer token is valid and hasn't expired. Test with curl:

```bash
curl -s -X POST <url> \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'
```

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

#### Token file fallback

If many SSE servers share a single token, write it to `~/.hermes/scripts/sse_token.txt` and omit `SSE_TOKEN` from the `env` block — the bridge script reads it automatically:

```bash
echo 'your-shared-token' > ~/.hermes/scripts/sse_token.txt
```

Then each SSE config entry can skip the token:

```yaml
mcp_servers:
  discord:
    command: "python3"
    args: ["/root/.hermes/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py"]
    env:
      SSE_URL: "https://example.com/mcp/discord/sse"
```

### SSE bridge returns 403 Forbidden

If the SSE bridge script fails with a 403 during connection:
- Verify `SSE_TOKEN` is set correctly in the `env` block — it is passed as `Authorization: Bearer <token>`
- The token may differ from the token used for the HTTP/StreamableHTTP endpoint on the same host
- If the token contains shell-special characters (`$`, `!`, `&`, `^`, `%`, `@`, `#`, etc.), ensure YAML quoting handles them — wrap the value in double quotes

### SSE bridge hangs or times out

- Increase `connect_timeout` (default: 60) — some SSE servers take time to establish a session
- Check that the server supports SSE transport at the given URL
- Some SSE implementations return the session ID in the initial `event: endpoint` SSE event — ensure the MCP SDK version supports this handshake

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either {"result": "..."} or {"error": "..."}
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)

## SSE Bridge Script

The SSE→stdio bridge (`scripts/sse_mcp_bridge.py`) is shipped as a support file under this skill's `scripts/` directory. When configuring SSE servers, reference it with the absolute path:

```
/root/.hermes/skills/mcp/native-mcp/scripts/sse_mcp_bridge.py
```

The script requires the `mcp` Python SDK and uses `mcp.client.sse.sse_client` for SSE transport and `mcp.server.stdio.stdio_server` for the stdio side. It runs as a persistent asyncio task — the SSE connection stays alive for the lifetime of the Hermes process.
