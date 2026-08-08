# hermes-webui Docker Compose Deployment Reference

Session-specific detail for deploying the hermes-webui container via
`docker-compose.yml` with `build: .`, covering the full first-deployment
path encountered on Jefe's host (2026-07-30).

## Environment

| Component | Value |
|-----------|-------|
| Host data path | `/srv/docker/hermes/.hermes` |
| Webui repo (container) | `/opt/data/hermes-webui/` |
| Webui repo (host) | `~/.hermes/hermes-webui/` |
| docker-compose binary | `/opt/data/profiles/business/home/.docker/cli-plugins/docker-compose` (v2.29.7) |
| Target port | `127.0.0.1:9120` |
| Pangolin resource | `hermes.jefe.al` → `127.0.0.1:9120` |

## Prerequisites

1. **docker.sock must be mounted in the Hermes container** — without it,
   the agent cannot run `docker ps`, `docker compose`, or any Docker
   command. Verify:
   ```bash
   docker inspect hermes --format '{{json .Mounts}}' | grep docker.sock
   ```
   If missing, add to the Hermes `docker-compose.yml`:
   ```yaml
   volumes:
     - /srv/docker/hermes/.hermes:/opt/data
     - /var/run/docker.sock:/var/run/docker.sock
   ```
   And set `HERMES_DASHBOARD=false` to disable the old s6 dashboard.

2. **`HERMES_HOME` in webui `.env`** — the compose file mounts
   `${HERMES_HOME:-${HOME}/.hermes}`. On Jefe's host, `HOME` is not the
   right data path. Add to `/opt/data/hermes-webui/.env`:
   ```
   HERMES_HOME=/srv/docker/hermes/.hermes
   ```

## .env file (complete)

```env
HERMES_HOME=/srv/docker/hermes/.hermes
HERMES_WEBUI_HOST=0.0.0.0
HERMES_WEBUI_PORT=9120
HERMES_WEBUI_PASSWORD=<password>
HERMES_WEBUI_SKIP_ONBOARDING=1
```

## First deployment (build + up)

The compose file uses `build: .` — no pre-built image. First run needs
`--build`:

```bash
cd /opt/data/hermes-webui
/path/to/docker-compose up -d --build
```

On Jefe's host, `docker compose` (subcommand) is not installed. The
standalone binary is at:
```
/opt/data/profiles/business/home/.docker/cli-plugins/docker-compose
```

Use it directly:
```bash
cd /opt/data/hermes-webui && \
  /opt/data/profiles/business/home/.docker/cli-plugins/docker-compose up -d --build
```

Build takes ~30s (downloads uv, copies app, no heavy deps).

## Verification

```bash
# Container running
docker ps --filter "name=hermes-webui" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
# Expected: hermes-webui-hermes-webui-1  Up N seconds  8787/tcp, 127.0.0.1:9120->9120/tcp

# HTTP local
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9120/
# Expected: 200

# Through Pangolin
curl -s -o /dev/null -w "%{http_code}" https://hermes.jefe.al/
# Expected: 200
```

## Container naming

The compose service is named `hermes-webui`, so the container becomes
`hermes-webui-hermes-webui-1` (compose prefixes with project dir name
`hermes-webui` then service name `hermes-webui`). This is verbose but
expected — don't try to rename it.

## Notes

- The compose file binds `127.0.0.1:9120:9120` — the port is NOT exposed
  to the host network. Pangolin reaches it via localhost on the same
  host. This is the intended setup.
- The `8787/tcp` in `docker ps` output is an EXPOSE directive from the
  Dockerfile, not a published port. The actual published port is 9120.
- `HERMES_WEBUI_SKIP_ONBOARDING=1` bypasses the first-run wizard.
- The webui container has its own network (`hermes-webui_default`) — it
  does NOT share the host network or the Hermes container's network.