---
name: dashboard-setup
author: Hermes Agent
description: |
  Quick‑start guide to enable the Hermes dashboard (port 9120)
  and update the Pangolin resource for the iOS app.
license: MIT
---

# Dashboard‑Setup

> **⚠️ Post-migration state (confirmed July 30, 2026, updated Aug 1, 2026):**
> The built-in dashboard (s6-supervised) has been **disabled**
> (`HERMES_DASHBOARD=false` in the container environment). The gateway API
> server serves on port **9119** (configured via `API_SERVER_PORT` in `.env`).
>
> **⚠️ Hermex iOS app connects to hermes-webui (port 8788), NOT `hermes serve`.**
> Confirmed Aug 1, 2026: The Hermex app (github.com/uzairansaruzi/hermex) is a
> client for hermes-webui, not the Hermes dashboard. Its README states: "Hermex
> is a native SwiftUI iPhone app for driving a self-hosted hermes-webui server."
> The Pangolin resource `hermes.jefe.al` must route to port **8788** (hermes-webui),
> not 9120 (dashboard). If routed to 9120, the app shows "Could not reach this
> gateway yet" even if `hermes serve` is running.
>
> **⚠️ Pitfall: `.env` overrides `config.yaml` for API server port.**
> If `API_SERVER_PORT=9119` is still in `/opt/data/.env`, it takes precedence
> over `config.yaml`'s `api_server.port: 9120` at gateway startup. After a
> container restart, the API server silently comes back on 9119 while Pangolin
> routes to 9120 → **502 on `hermes.jefe.al/`**. Fix: update `.env` to
> `API_SERVER_PORT=9120` (or remove the line so config.yaml is the sole source
> of truth) and restart the gateway. See `references/api-server-port-mismatch.md`.
>
> Verify with `curl http://127.0.0.1:9120/health`. The sections below remain
> for historical reference and for re-enabling the built-in dashboard if needed.

## Three Hermes HTTP Services — Port Map (August 2026)

Hermes runs **three separate HTTP servers**. Confusing them is the #1 cause of
502/404 errors behind Pangolin:

| Service | Port | Command | Purpose | Used by |
|---------|------|---------|---------|---------|
| **`hermes serve`** (dashboard backend) | 9120 | `hermes serve --port 9120 --host 0.0.0.0 --skip-build` | Hermes Desktop (Electron) remote backend | Hermes Desktop only |
| **API server** (gateway platform) | 9119 | Auto-started by gateway when `API_SERVER_ENABLED=true` | OpenAI-compatible `/v1/responses`, programmatic access | n8n, programmatic clients |
| **hermes-webui** (community WebUI) | 8788 | `cd hermes-webui && python server.py` | Browser-based chat UI, session management | **Hermex iOS app** |

**⚠️ CLI command is `hermes serve`, NOT `hermes dashboard`.** The current CLI
exposes `hermes serve` with flags `--port`, `--host`, `--skip-build`, `--status`,
`--stop`. There is no `hermes dashboard` subcommand. The `hermes serve --status`
and `hermes serve --stop` flags manage the process. Use `--skip-build` in
headless/Docker contexts where npm isn't available. (Older docs and the s6
run scripts may still reference `hermes dashboard` — treat as synonymous with
`hermes serve`.)

**Hermex connection flow (connects to hermes-webui, port 8788):**
1. App's "Remote URL" → `https://webui.jefe.al` → Pangolin → port **8788** → hermes-webui
2. hermes-webui handles its own auth (`HERMES_WEBUI_PASSWORD`) and API calls internally
3. If Pangolin routes to port 9120 instead of 8788 → app shows "Could not reach this gateway yet" / 502

**Hermes Desktop connection flow (connects to `hermes serve`, port 9120):**
1. App's "Remote URL" → `https://hermes.jefe.al` → Pangolin → port **9120** → dashboard natif
2. Dashboard natif handles auth via `dashboard.basic_auth` in config.yaml (scrypt hash)
3. App calls `GET /api/status` → expects `{auth_required: true, auth_providers: ["basic"]}` (200)

**⚠️ Critical: Hermes Desktop Remote URL must NOT include `/api`.**
The app concatenates `{base_url}/api/status`. If base_url = `https://hermes.jefe.al/api`,
the result is `https://hermes.jefe.al/api/api/status` (double `/api`) → 404 on sign-in.
Correct URL: `https://hermes.jefe.al` (no `/api`, no trailing slash).

**⚠️ Pangolin route conflict with `/api` prefix:**
If Pangolin has a `/api` prefix route → 9119 AND a racine `/` route → 9120,
the `/api` prefix intercepts all `/api/*` calls from Hermes Desktop and sends
them to the API server (which has no `/api/status` → 404). Fix: remove the
`/api` prefix route, or point racine `/` to 9120 as well.

**Changing the dashboard password (scrypt):**
```bash
# 1. Generate hash
/opt/hermes/.venv/bin/python -c "
from plugins.dashboard_auth.basic import hash_password
print(hash_password('NEW_PASSWORD'))
"
# 2. Update config.yaml (patch tool refuses config.yaml — use sed)
sed -i 's|password_hash: OLD_HASH|password_hash: NEW_HASH|' /opt/data/config.yaml
# 3. Restart hermes serve
pkill -f "hermes serve"; sleep 2
hermes serve --port 9120 --host 0.0.0.0 --skip-build &
# 4. Verify
curl -s http://localhost:9120/api/status | grep auth_providers
```

**Quick fix when Hermex can't connect (502/404 on remote URL):**
```bash
# 1. Check if hermes-webui is running on port 8788
curl -s -o /dev/null -w "%{http_code}" http://localhost:8788/api/status
# Should be 401 (auth required). If connection refused → webui not running.

# 2. Check what Pangolin routes to (should be 8788, not 9120)
curl -s -o /dev/null -w "%{http_code}" https://hermes.jefe.al/api/status
# 401 = correct (webui responding). 502 = wrong port or service down. 404 = routed to API server.

# 3. If 502: check Newt logs to see which port Pangolin targets
docker logs newt --tail 10 2>&1 | grep "connection refused"
# Port 9120 in logs = Pangolin routes to dashboard, should be 8788

# 4. Fix: change Pangolin resource target from 9120 → 8788 (in Pangolin dashboard on VPS)
```

**⚠️ Manual `hermes serve` is not persistent.** It dies when the container
restarts or the process is killed. For production, either:
- Add it to the s6-overlay supervision tree, or
- Set the container env vars so the gateway manages it automatically, or
- Use a cron job / keep-alive mechanism

The dashboard is started only when the ``HERMES_DASHBOARD`` env var
or config option is set.  The gateway keeps a WebSocket on
``127.0.0.1:9119`` for the iOS application – therefore the
dashboard must listen on a separate port, the default being
``127.0.0.1:9120``.

## Checklist

1. Enable the dashboard in the container env or ``config.yaml``:
   ```yaml
   hermes:
     dashboard: 1
   ```

2. Restart the gateway:
   ```bash
   hermes gateway restart
   ```

3. **Bind on 0.0.0.0 — not 127.0.0.1** (see Pitfall below):
   ```bash
   hermes serve --port 9120 --host 0.0.0.0 --skip-build &
   ```

4. Update the Pangolin resource (``hermes.jefe.al``) to point to port
   9120:
   ```json
   {
     "resource": "hermes.jefe.al",
     "url": "http://127.0.0.1:9120"
   }
   ```

5. Verify locally **and** through the proxy:
   ```bash
   curl http://127.0.0.1:9120/api/status
   curl https://hermes.jefe.al/api/status
   ```
   Both must return JSON. If the proxy call returns ``400 Invalid Host
  header``, the dashboard is bound to 127.0.0.1 — re-launch with
   ``--host 0.0.0.0``.

6. Leave the iOS app’s remote URL at ``https://hermes.jefe.al`` – the
   gateway will use the WebSocket on 9119 and the HTTP endpoints on
   9120 automatically.

## Pitfall: Host header rejection behind Pangolin (GHSA-ppp5-vxwm-4cf7)

The dashboard middleware (`web_server.py:host_header_middleware`) rejects
any request whose ``Host`` header doesn't match the bound interface. This
prevents DNS rebinding attacks.

**Symptom:** ``curl https://hermes.jefe.al/api/status`` returns:
```json
{"detail":"Invalid Host header. Dashboard requests must use the hostname the server was bound to."}
```
**Cause:** Dashboard bound to ``127.0.0.1`` → Pangolin sends
``Host: hermes.jefe.al`` → middleware rejects it (not a loopback host).
**Fix:** Launch with ``--host 0.0.0.0``. The middleware accepts any Host
when bound to 0.0.0.0. Basic auth (configured in ``config.yaml`` under
``dashboard.basic_auth``) still protects the dashboard — the June 2026
hardening ensures non-loopback binds always require an auth provider.

``should_require_auth()`` truth table:
- ``host ∈ {127.0.0.1, localhost, ::1}`` → no auth (local trusted)
- ``host == 0.0.0.0`` → auth required (basic_auth or OAuth)

So ``--host 0.0.0.0`` is safe behind Pangolin as long as basic_auth is
configured.

## s6-Overlay Supervision (Docker Deployments)

In Docker + s6-overlay deployments, the dashboard has a dedicated s6
service slot at `/run/service/dashboard`. The run script lives at
`/etc/s6-overlay/s6-rc.d/dashboard/run` and is **always declared** so s6
has a supervised slot.

### Critical: .env vs container environment

The s6 `dashboard/run` script checks `${HERMES_DASHBOARD:-}` from the
**container environment** (populated from Docker ENV directives or
`docker-compose.yml` `environment:` section) — NOT from `/opt/data/.env`.

`.env` is only read by Python code at runtime. The s6 run script is a
shell script that runs **before** Python starts, so it cannot see `.env`
values.

**Symptom:** `HERMES_DASHBOARD=true` is in `.env`, but
`/command/s6-svstat /run/service/dashboard` shows:
```
down (exitcode 0) 7569 seconds, normally up, ready 7569 seconds
```
The run script exited 0 (HERMES_DASHBOARD not seen), then the finish
script exited 125 (permanent failure marker → s6 won't restart).

**Fix:** Add the env vars to `docker-compose.yml` under the `hermes`
service `environment:` section:
```yaml
environment:
  - HERMES_DASHBOARD=true
  - HERMES_DASHBOARD_HOST=0.0.0.0
  - HERMES_DASHBOARD_PORT=9120
```

Then recreate the container from the host:
```bash
cd /srv/docker/hermes   # or wherever the compose file lives
docker compose up -d hermes
```

### Verifying the s6 dashboard service

```bash
# Check service status
/command/s6-svstat /run/service/dashboard
# Expected when running: up (pid XXXX) N seconds, normally up, ready N seconds

# Check if env var reaches the container
cat /run/s6/container_environment/HERMES_DASHBOARD 2>/dev/null
# Should print: true

# Manually restart the s6 dashboard service (if env is already set)
/command/s6-svc -d /run/service/dashboard   # stop
/command/s6-svc -u /run/service/dashboard   # start
```

### What the s6 run script does

The run script (`/etc/s6-overlay/s6-rc.d/dashboard/run`):
1. Checks `${HERMES_DASHBOARD:-}` — if not truthy, exits 0 (finish
   script exits 125 → permanent failure, no restart)
2. Sources the venv: `. /opt/hermes/.venv/bin/activate`
3. Reads `HERMES_DASHBOARD_HOST` (default `0.0.0.0`) and
   `HERMES_DASHBOARD_PORT` (default `9119`)
4. Execs `hermes serve --host "$dash_host" --port "$dash_port" --skip-build`
   (older s6 run scripts may still call `hermes dashboard` — treat as
   synonymous; the CLI command was renamed to `hermes serve`)

The finish script exits 125 when HERMES_DASHBOARD is falsy (permanent
failure — s6 won't restart) and 0 when truthy (s6 will restart on crash).

### Why manual `hermes serve` doesn't survive gateway restarts

When you manually run `hermes serve --port 9120 --host 0.0.0.0 --skip-build`, it
works but:
- It's NOT supervised by s6 → no auto-restart on crash
- It's NOT restarted when the gateway restarts
- It's a detached process that dies with the container

Only the s6-supervised dashboard (started via the run script when
`HERMES_DASHBOARD` is in the container env) gets proper lifecycle
management.

## Stopping and restarting (manual, non-s6)

```bash
# Stop
hermes serve --stop

# Restart (manual — not supervised, won't survive gateway restart)
hermes serve --port 9120 --host 0.0.0.0 --skip-build &
```

For supervised, auto-restarting dashboard: use the s6 approach above.

## Migrating to hermes-webui (new WebUI project)

There is a **separate project** called `hermes-webui` — a lightweight,
dark-themed web app with full CLI parity (three-panel layout, session
management, workspace browser). It lives at `/opt/data/hermes-webui/`
(container path = `~/.hermes/hermes-webui/` on the host) and runs in
its **own Docker container**.

For the full migration procedure (port reuse, s6 disable, docker-compose
changes, Docker socket access, path mapping pitfalls), load
``hermes-dashboard`` — it has a complete migration section with
``references/hermes-webui-migration.md`` and
``references/hermes-webui-docker-deploy.md`` (Docker Compose first-deployment
recipe with build, .env, and docker-compose plugin discovery).

**Key pitfall:** `/opt/data/` is container-internal. When giving the user
host-side commands, use `~/.hermes/hermes-webui/` as the path, never
`/opt/data/hermes-webui/`.

**⚠️ Hermex iOS app uses hermes-webui directly.** Hermex
(github.com/uzairansaruzi/hermex) is a client for hermes-webui, not the Hermes
dashboard. Its "Remote URL" field connects to the hermes-webui server (port 8788)
using `HERMES_WEBUI_PASSWORD` for auth. The Pangolin resource for
`hermes.jefe.al` should point to port 8788. Do NOT route Hermex through
`hermes serve` (9120) — it will show "Could not reach this gateway yet."
The app's Remote URL must be `https://hermes.jefe.al` (with `https://`, no
trailing slash, no `/api` suffix).

**⚠️ Health endpoint after migration:** The gateway API server uses `/health`
(not `/api/status`). Verify with `curl -s http://127.0.0.1:9120/health` —
should return `{"status": "ok", "platform": "hermes-agent", "version": "..."}`.
`/api/status` returns 404 on the gateway API server (it was a built-in
dashboard endpoint). See `hermes-dashboard` skill →
`references/gateway-api-server-post-migration.md` for full details.

## Reference

For detailed code and backup reference, see
``skill_view(name="dashboard-setup", file_path="references/dashboard-9120.md")``.
For s6 dashboard service internals, see
``skill_view(name="dashboard-setup", file_path="references/s6-dashboard-service.md")``.
For the `.env` vs `config.yaml` port mismatch diagnostic (502 after port
migration), see
``skill_view(name="dashboard-setup", file_path="references/api-server-port-mismatch.md")``.

For Pangolin API permission limits, Bitwarden CLI + Vaultwarden patterns, and
the web-research-first preference, see
``skill_view(name="dashboard-setup", file_path="references/pangolin-api-bitwarden-patterns.md")``.
