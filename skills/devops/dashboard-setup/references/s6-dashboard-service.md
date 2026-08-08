# s6 Dashboard Service Internals

## Service layout

| Component | Path |
|-----------|------|
| s6 service slot | `/run/service/dashboard/` |
| Run script | `/etc/s6-overlay/s6-rc.d/dashboard/run` |
| Finish script | `/etc/s6-overlay/s6-rc.d/dashboard/finish` |
| Type file | `/etc/s6-overlay/s6-rc.d/dashboard/type` (`longrun`) |
| Dependencies | `/etc/s6-overlay/s6-rc.d/dashboard/dependencies.d/base` |
| s6 binary prefix | `/command/` |

## Run script flow

```
${HERMES_DASHBOARD} truthy? → no  → exit 0 → finish exits 125 → s6 permanent failure
                          → yes → cd /opt/data, activate venv,
                                   exec hermes dashboard --host $HERMES_DASHBOARD_HOST --port $HERMES_DASHBOARD_PORT --no-open
```

Env var defaults (from run script):
- `HERMES_DASHBOARD_HOST` → `0.0.0.0`
- `HERMES_DASHBOARD_PORT` → `9119` (override to `9120` for separate-from-gateway)

## Finish script logic

- `HERMES_DASHBOARD` truthy → `exit 0` (s6 will restart on crash)
- `HERMES_DASHBOARD` falsy → `exit 125` (permanent failure — s6 won't restart)

## Container environment vs .env

| Source | Read by | When |
|--------|---------|------|
| `/run/s6/container_environment/*` | s6 run/finish scripts (via `with-contenv`) | Before Python starts |
| `/opt/data/.env` | Python `hermes` process | At runtime, after Python loads |

The s6 run script is a **shell script** — it cannot read `.env`.
Only Docker ENV directives or `docker-compose.yml` `environment:` entries
populate `/run/s6/container_environment/`.

## Checking container environment

```bash
# List all HERMES_* vars s6 sees
ls /run/s6/container_environment/ | grep HERMES

# Read a specific var
cat /run/s6/container_environment/HERMES_DASHBOARD
```

## s6 commands (no systemctl in s6-overlay containers)

```bash
# Status
/command/s6-svstat /run/service/dashboard

# Stop (down)
/command/s6-svc -d /run/service/dashboard

# Start (up)
/command/s6-svc -u /run/service/dashboard

# Kill (sends SIGTERM, s6 auto-restarts)
/command/s6-svc -k /run/service/dashboard
```

## docker-compose.yml changes required

The `hermes` service in `docker-compose.yml` needs these environment
variables for the s6 dashboard to auto-start:

```yaml
services:
  hermes:
    # ... existing config ...
    environment:
      - HERMES_DASHBOARD=true
      - HERMES_DASHBOARD_HOST=0.0.0.0
      - HERMES_DASHBOARD_PORT=9120
```

After editing, recreate the container:
```bash
docker compose up -d hermes
```

## Auth requirement on 0.0.0.0 bind

Non-loopback binds ALWAYS require an auth provider (June 2026 hardening).
The dashboard will fail to start if no provider is configured.

Two options:
1. **Basic auth** in `config.yaml`:
   ```yaml
   dashboard:
     basic_auth:
       username: jefe
       password_hash: scrypt$...
   ```
2. **OAuth** via `HERMES_DASHBOARD_OAUTH_CLIENT_ID` env var.

`HERMES_DASHBOARD_INSECURE` is accepted but **ignored** — it no longer
disables the auth gate.