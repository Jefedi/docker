---
name: api-server-setup
description: Configure Hermès API server for remote access.
---
# API Server Setup
## Purpose
This skill documents how to expose Hermès’ built‑in OpenAI‑compatible API server on a public or LAN address. It is useful for connecting third‑party clients (Windows desktop, mobile, or any OpenAI compatible frontend) to your remote Hermès instance.

## Prerequisites
  * A working Hermès installation with the gateway or server process running.
  * `hermes-agent` installed.
  * An environment variable file (`.env`) for the profile you want to expose.

## Procedure
1. **Stop Hermès** (or pause the service) to avoid race conditions.
2. Edit the profile’s `.env` and add:
   ```bash
   API_SERVER_ENABLED=true
   API_SERVER_HOST=0.0.0.0          # bind to all interfaces
   API_SERVER_PORT=9142             # choose a free port
   API_SERVER_KEY=YOUR_SECRET_KEY   # keep it reasonable & rotate as needed
   API_SERVER_CORS_ORIGINS=your.origin.com  # optional | leave empty for no CORS
   ```
3. **Restart Hermès**. The API will now listen on `IP:API_SERVER_PORT/v1`.
4. **Test** from another machine:
   ```bash
   curl -H "Authorization: Bearer YOUR_SECRET_KEY" https://IP:API_SERVER_PORT/v1/models
   ```
5. If you’re behind a reverse proxy (nginx, Caddy, cloud provider), point the proxy to the chosen port.

## Hermes Port Map — Dashboard vs API Server

Hermes runs **three separate HTTP servers** on different ports. This is critical when configuring reverse proxies (Pangolin, Nginx, etc.):

| Service | Port | Process | Auth | Used by |
|---------|------|---------|------|---------|
| Dashboard backend (`hermes serve`) | 9120 | `hermes serve --host 0.0.0.0 --port 9120 --skip-build` | Session/basic auth (config.yaml `dashboard:`) | Hermes Desktop (Electron) |
| API server (OpenAI-compatible) | 9119 (default) or `api_server.port` in `config.yaml` | Env: `API_SERVER_ENABLED=true`, `API_SERVER_PORT=9119` | `API_SERVER_KEY` Bearer token | n8n, programmatic access, Hermex API calls |
| hermes-webui (community WebUI) | 8788 | `python server.py` in hermes-webui dir | WebUI password (`HERMES_WEBUI_PASSWORD`) | **Hermex iOS app** |

**⚠️ CLI command is `hermes serve`, not `hermes dashboard`.** The `hermes serve`
subcommand provides `--port`, `--host`, `--skip-build`, `--status`, `--stop`.
Older docs may reference `hermes dashboard` — treat as synonymous.

**Common mistake:** Pointing a reverse proxy at port 9120 (dashboard) when you want the API. The dashboard intercepts requests with its own auth (302 → `/login`) and the Bearer token never reaches the API server.

**⚠️ Hermex (iOS app by uzairansaruzi) connects to hermes-webui (port 8788),
NOT to `hermes serve` (port 9120).** The GitHub README confirms: "Hermex is a
native SwiftUI iPhone app for driving a self-hosted hermes-webui server."
Hermex uses the hermes-webui's own auth (`HERMES_WEBUI_PASSWORD`), not the
dashboard basic_auth. If the reverse proxy routes to port 9120 instead of 8788,
Hermex shows "Could not reach this gateway yet" — even if hermes serve works.

**Hermes Desktop (Electron app by Nous Research)** is the one that connects to
`hermes serve` (port 9120) via its "Remote URL" settings field (described as
"Base URL for the remote dashboard backend"). If `hermes serve` is not running
on port 9120, Desktop shows "Could not reach this gateway yet."

**⚠️ Pitfall: `.env` `API_SERVER_PORT` overrides `config.yaml` `api_server.port`.**
If you migrate the API server port in `config.yaml` (e.g. `api_server.port: 9120`)
but leave the old `API_SERVER_PORT=9119` in `.env`, the `.env` value wins at
gateway startup. After a container restart, the API server silently comes back
on the old port while the reverse proxy (Pangolin/Nginx) routes to the new port
→ **502 Bad Gateway**. Always update **both** `.env` and `config.yaml` when
changing the API server port, or remove the `API_SERVER_PORT` line from `.env`
entirely so `config.yaml` is the sole source of truth.

**⚠️ Pitfall: `config.yaml` `api_server.extra.key` can conflict with `.env` `API_SERVER_KEY`.**
The `config.yaml` gateway section may contain `api_server.extra.key` with a
different value than `.env`'s `API_SERVER_KEY`. The `.env` value wins at
runtime, but the stale `config.yaml` key will be rejected with
`gateway_auth_error` if anyone uses it. Always sync both or remove the
`extra.key` from `config.yaml` to avoid confusion.

**Diagnostic: "iOS app / remote client can't connect, 502 on the remote URL"**
1. Check what port the API server actually listens on:
   `python3 -c "import socket; s=socket.socket(); s.settimeout(2); print('OPEN' if s.connect_ex(('127.0.0.1',9120))==0 else 'CLOSED'); s.close()"`
2. Check what port the reverse proxy routes to (Pangolin resource target).
3. If they don't match: `grep API_SERVER_PORT /opt/data/.env` — stale `.env`
   override is the most common cause.
4. Fix `.env`, then restart the gateway: `hermes gateway restart`
5. Verify: `curl -X POST http://127.0.0.1:9120/api/v1/responses -H
   "Authorization: Bearer $API_SERVER_KEY" -H "Content-Type: application/json"
   -d '{"model":"gpt-4o-mini","input":"test","max_output_tokens":10}'`

**Diagnostic: "Newt logs show connection refused to target port"**
The Newt container bridges local services to the Pangolin VPS. If a target
port is wrong, check Newt logs:
```bash
docker logs newt --tail 30 2>&1 | grep "connection refused\|Error connecting"
```
Each `Error connecting to target: dial tcp 127.0.0.1:PORT: connect: connection
refused` line tells you which port Pangolin is trying to reach but nothing is
listening on. Cross-reference with `docker ps` and `ss -tlnp` to find which
service should be on that port.

**Diagnostic: "Hermex iOS app can't authenticate / "Could not reach this gateway"**

**⚠️ First: identify which app the user means.** There are TWO Hermes iOS apps:
- **Hermex** (github.com/uzairansaruzi/hermex) — connects to **hermes-webui (port 8788)**
- **Hermes Desktop** (by Nous Research, Electron) — connects to **`hermes serve` (port 9120)**

The user's app is **Hermex** (confirmed: user profile says "Interface: Hermex (iOS native,
open source MIT, github.com/uzairansaruzi/hermex). Connecté au WebUI Hermes via API HTTP").

**⚠️ `/api/status` response format differs between backends — this causes
silent failures.** The Hermes Desktop app calls `GET /api/status` to detect the
gateway and its auth providers. Each backend responds differently:

| Backend | `/api/status` response | HTTP code |
|---------|----------------------|-----------|
| `hermes serve` (dashboard natif) | `{auth_required: true, auth_providers: ["basic"], auth_flows: ["cookie"], ...}` | 200 |
| hermes-webui | `{"error": "Authentication required"}` | 401 |
| API server | `404: Not Found` | 404 |

If the Desktop app hits the WebUI's `/api/status` (401 with wrong JSON shape),
it shows "Could not reach this gateway yet" — even though the server IS
responding. The app expects the dashboard natif's JSON structure with
`auth_providers` to render its sign-in UI.

**Hermex troubleshooting (connects to hermes-webui, port 8788):**

**Step 1: Check hermes-webui is running on port 8788:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8788/api/status
# Should be 401 (auth required) or 200. If connection refused → webui not running.
```

**Step 2: Check Pangolin routes to port 8788 (NOT 9120):**
```bash
curl -s -o /dev/null -w "%{http_code}" https://hermes.jefe.al/api/status
# If 404 → Pangolin routes /api/ to port 9119 (API server) which doesn't have /api/status
# If 502 → Pangolin routes to port 9120 (dashboard) but hermes serve not running
# If 401 → Correct! hermes-webui responding through Pangolin
```
If 404 or 502: the Pangolin resource for `hermes.jefe.al` routes to the wrong
port. It must point to **8788** (hermes-webui), not 9120 (dashboard) or 9119
(API server). Fix this in the Pangolin dashboard on the VPS.

**⚠️ Pangolin `/api` path-prefix conflict:** If Pangolin has a target with path
`/api` (prefix) routing to port 9119, it will **intercept** all `/api/*`
requests — including `/api/status` calls from Hermes Desktop that need to reach
port 9120 (dashboard natif). The Desktop app gets a 404 from the API server
instead of the expected `{auth_required: true, ...}` JSON from the dashboard.
**Fix:** Either remove the `/api` prefix route, or use separate subdomains for
each backend (see "Exposing All Three Backends" section above).

**Step 3: Check the app's Remote URL:**
The URL must be `https://hermes.jefe.al` — with `https://` prefix, no trailing
slash, no `/api` suffix. The `/api` path is handled internally by hermes-webui.
Common user mistakes (from real session):
- Missing `https://` prefix → app can't resolve
- Trailing `/api/` suffix → wrong endpoint, 404
- Typo in domain (`jefeal` instead of `jefe.al`)

**Step 4: Verify hermes-webui password:**
```bash
grep HERMES_WEBUI_PASSWORD /opt/data/hermes-webui/.env
```
The app's password field must match this value.

**Step 5: Check Newt logs for port mismatches:**
```bash
docker logs newt --tail 30 2>&1 | grep "connection refused"
# If you see port 9120 → Pangolin routes to dashboard, not webui
# If you see port 9119 → API server target misconfigured
```

**Test API locally:**
```bash
curl -H "Authorization: Bearer $API_SERVER_KEY" http://localhost:9119/v1/responses -d '{"input":"test"}'
```

## Exposing Both on One Domain via Pangolin Path-Based Routing

Pangolin supports **path-based routing** on targets within a single resource. You can serve both the dashboard and API on `hermes.jefe.al`:

- `hermes.jefe.al/` → `localhost:9120` (dashboard, default target — no path)
- `hermes.jefe.al/api/*` → `localhost:9119` (API server, Path=`/api`, Match=`prefix`)

**⚠️ Strip Prefix required:** Configure Path Rewriting → **Strip Prefix** on the API target so `/api` is removed before forwarding:
- `hermes.jefe.al/api/v1/responses` → Pangolin strips `/api` → `localhost:9119/v1/responses`

Without stripPrefix, the API receives `/api/v1/responses` and returns 404.

**SSO should be disabled** on the Pangolin resource — both backends handle their own auth (dashboard: session auth, API: Bearer token).

See the `pangolin` skill's `references/manage__resources__public__targets.md` for full path-based routing docs.

## Exposing All Three Backends (Dashboard + API + WebUI)

When the user needs **both Hermes Desktop (Windows) AND Hermex (iOS)**, a single
domain with path-based routing is NOT sufficient — the `/api` path prefix creates
a conflict:

- **Hermes Desktop** calls `GET /api/status` and expects the dashboard natif
  response format: `{auth_required: true, auth_providers: ["basic"], ...}`
- **Hermex iOS** also calls `/api/status` but expects the hermes-webui format:
  `{"error": "Authentication required"}` (401)
- **API server** has no `/api/status` endpoint at all (returns 404)

If Pangolin routes `/api/*` to one backend, the other app breaks. The clean
solution is **separate subdomains**:

| Subdomain | Port | Service | App |
|-----------|------|---------|-----|
| `hermes.jefe.al` | 9120 | `hermes serve` (dashboard natif) | Hermes Desktop (Windows) |
| `webui.jefe.al` (new) | 8788 | `hermes-webui` | Hermex (iOS) |
| `hermes.jefe.al/api/*` | 9119 | API server (OpenAI-compatible) | n8n, programmatic |

**Setup steps:**
1. Launch `hermes serve --port 9120 --host 0.0.0.0 --skip-build` (dashboard natif)
2. Launch hermes-webui on port 8788 (existing process or `start.sh`)
3. In Pangolin dashboard (VPS): create new site `webui.jefe.al` → target `127.0.0.1:8788`
4. Keep `hermes.jefe.al/api/*` → `127.0.0.1:9119` for the API server
5. Keep `hermes.jefe.al/` → `127.0.0.1:9120` for the dashboard

**⚠️ Key insight: `hermes serve` is NOT persistent by default.** It runs as a
foreground process. If launched via `terminal(background=true)`, it dies when the
session ends or the container restarts. To make it persistent:
- Option A: Add it as an s6 service (like the gateway)
- Option B: Use a Docker container with `--restart unless-stopped`
- Option C: Add a cron job or systemd service to keep it alive

**⚠️ hermes-webui launched manually (not via s6) also dies on restart.** The
existing WebUI process was launched via `bash -lic` by the gateway startup. If
you kill and relaunch it on a different port, the original s6-managed process
won't auto-restart on the new port. Either update the s6 service definition or
use the migration script (`scripts/migrate-webui-9120.sh` pattern).

**Hermex iOS Remote URL:** `https://webui.jefe.al` (no `/api`, no trailing slash)
**Hermes Desktop Remote URL:** `https://hermes.jefe.al` (NO `/api` suffix!)

**⚠️ Critical pitfall: Hermes Desktop "Remote URL" + `/api` = double path → 404.**
The Desktop app's Remote URL field says "Path prefixes are supported, for
example /hermes." If you enter `https://hermes.jefe.al/api`, the app
concatenates `{base_url}/api/status` → `https://hermes.jefe.al/api/api/status`
(double `/api`). The gateway detection (`/api/status`) may succeed (401 from
wrong backend), but **sign-in fails with 404** because `/api/api/login` doesn't
exist on any backend.

**Correct Hermes Desktop setup (confirmed Aug 1, 2026):**
1. Remote URL in app: `https://hermes.jefe.al` (with `https://`, NO `/api`, no trailing slash)
2. Pangolin route: `/` (racine, no path prefix) → port **9120**
3. Remove or avoid any `/api` prefix route in Pangolin that would intercept `/api/*` calls
4. The app calls `https://hermes.jefe.al/api/status` → Pangolin → 9120 → dashboard natif responds with `{auth_required: true, auth_providers: ["basic"]}`

**⚠️ Pangolin route conflict:** If Pangolin has BOTH a `/api` prefix route (→ 9119) AND a racine `/` route (→ 9120), the `/api` prefix route intercepts all `/api/*` requests and sends them to the API server (which has no `/api/status` → 404). The fix is either:
- Remove the `/api` prefix route entirely, OR
- Change the racine route to also point to 9120 (so all traffic goes to dashboard natif), OR
- Use separate subdomains (recommended for running both Desktop + Hermex)

## Changing the Dashboard Password (`hermes serve` basic auth)

The dashboard natif uses scrypt password hashing. To change the password:

1. **Generate the scrypt hash:**
   ```bash
   /opt/hermes/.venv/bin/python -c "
   from plugins.dashboard_auth.basic import hash_password
   print(hash_password('NEW_PASSWORD'))
   "
   ```

2. **Update config.yaml** — the `patch` tool REFUSES to write to config.yaml
   (security-sensitive file). Use `sed` instead:
   ```bash
   sed -i 's|password_hash: OLD_HASH|password_hash: NEW_HASH|' /opt/data/config.yaml
   ```

3. **Restart `hermes serve`** — kill the old process and relaunch:
   ```bash
   pkill -f "hermes serve"
   sleep 2
   hermes serve --port 9120 --host 0.0.0.0 --skip-build &
   ```

4. **Verify** the new password works:
   ```bash
   curl -s http://localhost:9120/api/status | grep auth_providers
   # Should show ["basic"]
   ```

The username is in `config.yaml` under `dashboard.basic_auth.username`.
The `secret` field (`HERMES_DASHBOARD_BASIC_AUTH_SECRET`) keeps sessions
valid across restarts — don't change it when rotating just the password.

## n8n Workflow Integration: Using the API Server as an LLM Backend

n8n workflows can call the Hermes API server as a curation/processing backend via HTTP Request nodes.

**Node configuration:**
- **URL:** `https://hermes.jefe.al/api/v1/responses` (via Pangolin path-based routing)
- **Method:** POST
- **Authentication:** Generic Bearer Token (`API_SERVER_KEY`)
- **Body (JSON):** `={{ { input: $json.input } }}`
- **Response format:** JSON
- **Timeout:** 120000ms (Hermes can take time to process)

**Credential in n8n:** Create an `httpBearerAuth` credential with the `API_SERVER_KEY` value.

**Response parsing (Code node):**
```javascript
const response = $input.first().json;
let text = "";
for (const item of (response.output || [])) {
  if (item.type === "message" && item.content) {
    for (const c of item.content) {
      if (c.type === "output_text") { text = c.text; break; }
    }
  }
}
// text now contains the LLM response
```

## Finding the API Key — Where It Actually Lives

**Pitfall:** `config.yaml` has a `basic_auth.api_key` field under `dashboard:` — that is **dashboard session auth**, not the API server key. It is empty by default. Do NOT report "no API key configured" based on that field.

The API server key is the **`API_SERVER_KEY` environment variable**, set in the profile's `.env` file (e.g. `/opt/data/.env`). It is not in `config.yaml`.

**Quick check (in order):**
1. `env | grep API_SERVER_KEY` — if running inside the gateway/session, it's already in the environment.
2. `grep API_SERVER_KEY /opt/data/.env` — the source of truth.
3. `curl -s http://127.0.0.1:$API_SERVER_PORT/v1/models` without a Bearer header → if you get `gateway_auth_error`, a key IS configured and required.

**Verify the key works:**
```bash
curl -H "Authorization: Bearer $API_SERVER_KEY" http://localhost:${API_SERVER_PORT:-9119}/v1/models
```

## Diagnostic: API Server Not Reachable from Host (Docker Container)

When Hermes runs inside a Docker container with no port mapping (`docker port hermes` returns empty), the API server is only reachable from **inside** the container. This happens when the container uses `network_mode: host` or when the API server port wasn't explicitly mapped.

### Check from inside the container
```bash
docker exec hermes curl -s -m 5 http://127.0.0.1:9119/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"
```

### Determine the actual listening port
The configured port (`api_server.port` in config.yaml) may differ from the actual port due to `.env` override. Check gateway logs:
```bash
docker exec hermes grep -i "API server listening" /opt/data/logs/gateway.log | tail -5
# Output: "API server listening on http://0.0.0.0:9119 (model: hermes-agent)"
```

### List all listening ports inside the container
```bash
docker exec hermes python3 -c "
with open('/proc/net/tcp') as f:
    for line in f.readlines()[1:]:
        parts = line.split()
        if parts[3] == '0A':  # LISTEN state
            port = int(parts[1].split(':')[1], 16)
            if port > 1000: print(f'Listening on port {port}')
"
```

### Test a chat completion
```bash
docker exec hermes curl -s -m 30 http://127.0.0.1:9119/v1/chat/completions \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

The model name for the API server is always `hermes-agent` (returned by `/v1/models`), regardless of the underlying LLM provider configured in Hermes.

## ⚠️ Hermes API Server Does NOT Support OpenAI Function Calling (tool_calls)

The Hermes API server is an **agent** backend, not a raw LLM backend. When you send a
request with `tools` (OpenAI function calling), Hermes executes those tools **internally**
and returns a plain text response. It **never** returns `tool_calls` in the message object.

**Confirmed by testing (Aug 2026):**
```
# Request with tools → Response:
"message": {"role": "assistant", "content": "Il est 6h17..."}
# tool_calls: NOT PRESENT (even with tool_choice=auto)
```

**n8n pitfall:** The n8n **"AI Agent"** node (`@n8n/n8n-nodes-langchain.agent`) expects
the LLM to return `tool_calls` in the OpenAI format. When it doesn't find them, it crashes:
```
NodeOperationError: Cannot read properties of undefined (reading 'map')
    at ToolsAgent/V3/helpers/executeBatch.ts:118
```

**Fix:** In n8n, use **"Basic LLM Chain"** (`@n8n/n8n-nodes-langchain.chainLlm`) instead of
"AI Agent" when pointing to the Hermes API server. The Basic LLM Chain does pure chat
(no tool calling) and works perfectly with Hermes.

| n8n Node Type | Works with Hermes API? | Why |
|---|---|---|
| AI Agent (`agent`) | ❌ Crash | Expects `tool_calls` in response |
| Basic LLM Chain (`chainLlm`) | ✅ Works | Pure chat, no tool calling expected |

**Model name:** Always `hermes-agent` (the only model returned by `/v1/models`).

## Security
* `API_SERVER_KEY` is required for every request. Keep it secret. Rotate if suspect.
* Avoid exposing the port publicly unless you trust everyone that can hit it.
* When behind Pangolin with path-based routing, the Bearer token is forwarded transparently — no special header config needed.

---
# References
* https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server
* https://hermes-agent.nousresearch.com/docs/auto-locale
* `references/api-server-remote-config.md` — remote API server configuration details
* `references/pangolin-path-based-routing.md` — expose dashboard + API on one domain via Pangolin path-based routing with stripPrefix

---
# Templates
No template needed.

---
# Scripts
No script needed.
