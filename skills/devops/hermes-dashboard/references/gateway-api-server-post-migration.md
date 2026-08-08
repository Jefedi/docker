# Gateway API Server Post-Migration State

Reference for verifying the Hermes dashboard migration from the built-in
`hermes dashboard` to the gateway API server on port 9120.

## Health endpoint differences

| Server | Endpoint | Response |
|--------|----------|----------|
| Built-in `hermes dashboard` | `GET /api/status` | JSON status |
| Gateway API server | `GET /health` | `{"status": "ok", "platform": "hermes-agent", "version": "..."}` |
| Gateway API server | `GET /api/status` | 404 (does not exist) |
| Gateway API server | `GET /api/v1/status` | 404 (does not exist) |
| Gateway API server | `GET /` | 404 (no web UI served) |

**Key learning:** After migration, the correct health check is `/health`.
The old `/api/status` endpoint was served by the built-in dashboard, not
by the gateway API server. Using `/api/status` for verification will
return 404 and cause false-negative diagnostics.

## Expected config.yaml state after migration

```yaml
# Gateway API server on the Pangolin-exposed port
gateway:
  api_server:
    max_concurrent_runs: 10
    port: 9120

# Old dashboard config — harmless residue, can be left in place
dashboard:
  theme: default
  basic_auth:
    username: jefe
    password_hash: scrypt$...
    password: ''
    secret: hermes-jefe-dashboard-2026
    session_ttl_seconds: 0

# WebUI section
webui:
  dashboard:
    enabled: auto
```

## Container environment state

```
HERMES_DASHBOARD=false          # old s6 dashboard disabled
HERMES_DASHBOARD_HOST=0.0.0.0   # residue (unused since dashboard=false)
HERMES_DASHBOARD_PORT=9120      # residue (unused since dashboard=false)
```

The `HERMES_DASHBOARD_HOST` and `HERMES_DASHBOARD_PORT` env vars are
harmless residue — they're only read by the s6 `dashboard/run` script,
which exits immediately when `HERMES_DASHBOARD=false`.

## s6 service state

The s6 dashboard service (`/etc/s6-overlay/s6-rc.d/dashboard/`) is always
declared so s6 has a supervised slot. When `HERMES_DASHBOARD=false`:
- The `run` script exits 0 immediately
- The `finish` script exits 125 (permanent failure marker)
- s6-supervise leaves the slot in "down" state
- No process runs, no port is listened on

This is by design, not an error.

## Verifying from inside the Hermes container

The Hermes Docker container does NOT have `ss`, `netstat`, `lsof`, or
`fuser` installed. Use Python with `/proc/net/tcp`:

### Check if a specific port is listening

```bash
docker exec hermes python3 -c "
import socket
s = socket.socket(); s.settimeout(2)
result = s.connect_ex(('127.0.0.1', 9120))
print('OPEN' if result == 0 else 'CLOSED')
s.close()
"
```

### List all listening ports (state 0A = LISTEN)

```bash
docker exec hermes python3 -c "
import socket, struct
with open('/proc/net/tcp') as f:
    next(f)
    for line in f:
        parts = line.split()
        local = parts[1]
        state = parts[3]
        if state == '0A':
            ip_hex, port_hex = local.split(':')
            port = int(port_hex, 16)
            ip = socket.inet_ntoa(struct.pack('<I', int(ip_hex, 16)))
            if port > 1000:
                print(f'{ip}:{port}')
"
```

### Check a specific port via /proc/net/tcp

```bash
docker exec hermes python3 -c "
import socket, struct
target = 9120
found = False
with open('/proc/net/tcp') as f:
    next(f)
    for line in f:
        parts = line.split()
        local = parts[1]
        state = parts[3]
        if state == '0A':
            ip_hex, port_hex = local.split(':')
            port = int(port_hex, 16)
            if port == target:
                ip = socket.inet_ntoa(struct.pack('<I', int(ip_hex, 16)))
                print(f'FOUND: {ip}:{port}')
                found = True
                break
if not found:
    print(f'Port {target} NOT found in /proc/net/tcp')
"
```

## Diagnosing "Bad Gateway" through Pangolin

When `curl https://hermes.jefe.al/health` returns "Bad Gateway", the Pangolin
controller has a route for the domain but the Newt tunnel client on the target
host cannot reach the local backend. The fastest diagnostic path:

### Step 1 — Check Newt logs for the exact target port

```bash
docker logs newt --tail 20 2>&1 | grep -i 'connect.*refused\|error.*target'
```

This will show lines like:
```
Error connecting to target: dial tcp 127.0.0.1:9120: connect: connection refused
```

The port in the error message is what Pangolin/Newt is trying to reach. If this
port doesn't match what the gateway API server is actually listening on, you have
a port mismatch.

### Step 2 — Find the actual listening port

```bash
# From the host (Hermes uses host networking, so container ports = host ports)
curl -s http://127.0.0.1:9119/health
curl -s http://127.0.0.1:9120/health
```

Or scan `/proc/net/tcp` inside the container (see commands above).

### Step 3 — Fix the mismatch

Two options:
1. **Restart the Hermes container** so the gateway picks up the new `config.yaml`
   port setting: `docker restart hermes` (requires user confirmation).
2. **Update the Pangolin resource** to target the port the gateway is actually
   listening on (via the Pangolin dashboard at `pangolin.jefe.ovh`).

### Architecture note: Jefe's Pangolin setup

- **Pangolin controller** runs on a separate server at `pangolin.jefe.ovh`
  (public IP 46.62.210.41 — NOT the Hermes host).
- **Newt client** runs as a Docker container (`fosrl/newt:latest`) on the Hermes
  host, tunneling traffic to the controller.
- **`hermes.jefe.al`** DNS resolves to the Pangolin controller's public IP.
- The Pangolin controller routes requests through the Newt tunnel to the local
  backend port specified in the resource config.
- There is also a `pangolin-cli` container (`fosrl/pangolin-cli`) and a second
  Newt instance (`Trakii-newt`) for a separate site.

## Config change without restart — the silent mismatch

A subtle failure mode: `config.yaml` is edited (e.g. `api_server.port: 9120` via
`docker exec hermes sed -i ...`) but the container is NOT restarted. The file on
disk reflects the new port, but the running gateway process keeps listening on
the old default port (9119). Pangolin/Newt targets the port from its resource
config (which may have been set to match the new config.yaml value), resulting in
"Bad Gateway" even though everything looks correct in the config files.

**Diagnostic clue:** `config.yaml` says port 9120, `/proc/net/tcp` shows 9119
listening, 9120 is closed. This is a definitive sign the container needs a
restart to pick up the config change.

## Common post-migration log warnings (normal, not errors)

- `[Api_Server] API server is network-accessible (0.0.0.0) AND the terminal backend is 'local' (unsandboxed)` — expected when the API server binds 0.0.0.0 for Pangolin access.
- `SQLite session store unavailable, falling back to JSONL: malformed database schema ()` — separate issue (state.db corruption), not related to the dashboard migration. When state.db is corrupt, `session_search` also fails with the same error. The gateway attempts automatic repair on boot (backup + REINDEX) but may fail, requiring manual restore from the `.malformed-backup-*` file.
- `Previous gateway life exited UNCLEANLY (no exit path ran — SIGKILL / OOM / VM death)` — container was restarted; the gateway auto-recovers on boot.