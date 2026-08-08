# hermes-webui Direct In-Container Deployment

Session-specific detail for running hermes-webui's `server.py` directly
inside the Hermes container (no Docker Compose, no separate container),
targeting Tailscale access from an iPhone. Encountered on 2026-07-30.

## Environment

| Component | Value |
|-----------|-------|
| Container | Hermes Agent Docker (host networking, s6-overlay) |
| OS | Debian 13 (trixie) inside container |
| Webui repo | `/opt/data/hermes-webui/` |
| Hermes home | `/opt/data` (config.yaml, sessions, skills) |
| Python | 3.13.5 (system), uv for venv |
| Tailscale IPs | `100.64.0.2`, `100.90.128.18` (via host bridge) |
| Target port | 8788 (8787 had zombie socket) |

## Why `server.py` directly, not `bootstrap.py`

`bootstrap.py` is a heavy wrapper that:
1. Creates a venv and installs ALL Hermes dependencies (full agent stack)
2. Syncs skills to `~/.hermes/skills/`
3. Runs the setup wizard (if not skipped)
4. Spawns `server.py` as a detached subprocess
5. Probes `/health` and exits

The detached subprocess model is fragile: if `bootstrap.py` is killed, the
child `server.py` may crash but leave the TCP socket in LISTEN state with no
process holding it (zombie socket). This blocks the port until kernel
TIME_WAIT timeout (minutes).

**Direct `server.py` launch** avoids all of this — it's a single process that
owns its socket cleanly.

## Deployment steps

### 1. Venv + deps

```bash
cd /opt/data/hermes-webui
uv venv .venv --python 3.13
uv pip install -r requirements.txt
# Only 4 packages: cryptography, cffi, pycparser, pyyaml
```

### 2. `.env` file

```env
HERMES_HOME=/opt/data
HERMES_WEBUI_HOST=0.0.0.0
HERMES_WEBUI_PORT=8788
HERMES_WEBUI_PASSWORD=<password>
HERMES_WEBUI_SKIP_ONBOARDING=1
```

**Note:** `HERMES_HOME` must point to the container's Hermes data dir
(`/opt/data`), NOT the host path (`/srv/docker/hermes/.hermes`). The `server.py`
process runs inside the container.

### 3. Launch (background, via Hermes terminal tool)

```bash
cd /opt/data/hermes-webui
HERMES_HOME=/opt/data \
HERMES_WEBUI_HOST=0.0.0.0 \
HERMES_WEBUI_PORT=8788 \
HERMES_WEBUI_PASSWORD='<password>' \
HERMES_WEBUI_SKIP_ONBOARDING=1 \
.venv/bin/python server.py
```

Use `terminal(background=true)` for the Hermes agent — `server.py` is a
long-lived process. Do NOT use `notify_on_complete=true` (it never exits).

### 4. Verify

```bash
# Health (GET, not HEAD — HEAD returns 501)
curl -s http://127.0.0.1:8788/health
# {"status": "ok", "sessions": 0, "active_streams": 0, ...}

# Bind address check (no ss/netstat/lsof in container)
printf '%04X\n' 8788  # → 2254
cat /proc/net/tcp | grep '2254.*0A'
# 00000000:2254 = 0.0.0.0 (correct — all interfaces)
# 0100007F:2254 = 127.0.0.1 (wrong — not reachable via Tailscale)

# Tailscale access
curl -s http://100.64.0.2:8788/health
# Should return same JSON as localhost
```

## Server.py vs bootstrap.py behavior differences

| Aspect | `bootstrap.py` | `server.py` direct |
|--------|----------------|-------------------|
| Deps installed | Full Hermes agent stack | Only `requirements.txt` (4 pkgs) |
| Skill sync | Yes | No |
| Onboarding wizard | Yes (unless skipped) | No |
| Process model | Detached subprocess | Single foreground process |
| Server type | uvicorn (via bootstrap) | `ThreadingHTTPServer` |
| `HEAD /health` | 302 redirect to `/login` | 501 Unsupported method |
| `GET /health` | 302 redirect to `/login` | JSON `{"status": "ok", ...}` |
| Password auth | Active (302 → /login) | Active (GET / → login page) |

**Note:** `server.py` uses `ThreadingHTTPServer` (Python stdlib), not
uvicorn/aiohttp. The `HEAD` method is not supported — always use `GET`
for health checks.

## Tailscale access

The Hermes container on Jefe's host has Tailscale IPs already assigned
through the host's bridge network. No Tailscale installation inside the
container is possible (no `/dev/net/tun`, no `SYS_ADMIN` capability).

Verify container's Tailscale IPs:
```bash
hostname -I  # includes 100.64.0.2, 100.90.128.18, and others
```

The WebUI bound to `0.0.0.0:8788` is accessible from any Tailscale-connected
device at `http://100.64.0.2:8788`.

## Zombie socket debugging

**Symptom:** Port shows LISTEN in `/proc/net/tcp` but no process holds it.
`curl` gets empty response. `ctl.sh start` refuses: "a live server is already
responding." New `server.py` launch fails: "Another server is already
responding."

**Diagnosis:**
```bash
# 1. Check if port is in LISTEN state
printf '%04X\n' <port>
cat /proc/net/tcp | grep '<hex>.*0A'

# 2. Find process holding the socket inode
# (from /proc/net/tcp, column 10 = inode)
INODE=<inode_from_step_1>
for pid in $(ls /proc/ | grep -E '^[0-9]+$'); do
  for fd in /proc/$pid/fd/*; do
    target=$(readlink "$fd" 2>/dev/null)
    [[ "$target" == "socket:[$INODE]" ]] && echo "PID $pid: $(cat /proc/$pid/cmdline | tr '\0' ' ')"
  done
done 2>/dev/null

# 3. If no process found → zombie socket (kernel will reclaim eventually)
```

**Fix:** Use a different port. The zombie socket clears after kernel
TIME_WAIT timeout (typically 60-120s). Container restart clears it
immediately.

## Auto-start (not yet implemented)

The `server.py` process does NOT survive container restarts. Options for
persistence:

1. **s6 service** — create a new s6-rc service slot that launches `server.py`
   with the right env vars. Most robust but requires writing s6 service files
   under `/etc/s6-overlay/s6-rc.d/`.
2. **Hermes cron watchdog** — schedule a `2m` cron job that pings
   `/health` and relaunches `server.py` if down. Pattern is documented in
   the `hermes-dashboard` skill (see "Layer 2 — Watchdog cron").
3. **`.env` + s6 container_environment** — add `HERMES_WEBUI_*` vars to
   the Hermes container environment so a future s6 service can read them.

As of 2026-07-30, auto-start was not yet configured — the server runs as a
background process via the Hermes agent terminal tool.