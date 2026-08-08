# hermes-webui Migration Reference

Session-specific detail for migrating from the built-in `hermes dashboard`
to the separate `hermes-webui` project on the same port.

## Environment layout (Jefe's setup)

| Component | Path (container) | Path (host) | Container |
|-----------|-------------------|-------------|-----------|
| Built-in dashboard | `/opt/hermes/` (s6 service `/run/service/dashboard`) | N/A | Hermes Agent container |
| hermes-webui project | `/opt/data/hermes-webui/` | `~/.hermes/hermes-webui/` | Own Docker container |
| Webui `.env` | `/opt/data/hermes-webui/.env` | `~/.hermes/hermes-webui/.env` | Shared volume |
| Webui `docker-compose.yml` | `/opt/data/hermes-webui/docker-compose.yml` | `~/.hermes/hermes-webui/docker-compose.yml` | Host |
| Webui `ctl.sh` | `/opt/data/hermes-webui/ctl.sh` | `~/.hermes/hermes-webui/ctl.sh` | Works inside container if env matches |
| Webui log | `/opt/data/webui.log` | `~/.hermes/webui.log` | Shared volume |
| Pangolin resource | `hermes.jefe.al` → `127.0.0.1:9120` | N/A | Host |

## Path mapping: container vs host

The Hermes container mounts `~/.hermes` (host) → `/opt/data` (container).
This means:

| Container path | Host path |
|----------------|-----------|
| `/opt/data/hermes-webui/` | `~/.hermes/hermes-webui/` |
| `/opt/data/.env` | `~/.hermes/.env` |
| `/opt/data/config.yaml` | `~/.hermes/config.yaml` |
| `/opt/data/scripts/` | `~/.hermes/scripts/` |

**When giving the user commands to run on the host** (e.g. `docker compose`,
`cd`), ALWAYS use the host path (`~/.hermes/...`), never the container path
(`/opt/data/...`). This was a real friction point — the user tried
`cd /opt/data/hermes-webui` on the host and got "no such file or directory".

## Docker socket access: the real blocker

The Hermes container does NOT have access to the Docker daemon
(`/var/run/docker.sock` is not mounted by default). This means:

- `docker ps`, `docker compose`, `docker run` all fail with
  "Cannot connect to the Docker daemon"
- The agent CANNOT recreate the webui container from inside Hermes
- The agent CANNOT stop/start any Docker container

### Solution: mount the Docker socket

To give the Hermes agent Docker access, the user must recreate the Hermes
container with the socket mounted. **This requires explicit user approval**
— never do this without asking.

The recreate command (run on the host):

```bash
docker stop hermes && docker rm hermes && \
docker run -d --name hermes --restart unless-stopped \
  --network host \
  -v ~/.hermes:/opt/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HERMES_UID=$(id -u) -e HERMES_GID=$(id -g) \
  -e HERMES_DASHBOARD=false \
  nousresearch/hermes-agent:latest gateway run
```

Key changes from the original `docker run`:
- `-v /var/run/docker.sock:/var/run/docker.sock` — Docker access
- `-e HERMES_DASHBOARD=false` — prevents old s6 dashboard from restarting
  on port 9120 and conflicting with the webui

**Warning:** this restarts Hermes (brief session loss ~10s). All state
(config, sessions, skills, memory) persists in the `~/.hermes` volume.

### After socket access: migrate webui to port 9120

Once the agent has Docker access, it can run the migration script
(`scripts/migrate-webui-9120.sh`) or do it inline:

```bash
# Stop old webui container
docker stop hermes-webui && docker rm hermes-webui

# Start new webui on port 9120
docker run -d --name hermes-webui --restart unless-stopped \
  --network host \
  -v ~/.hermes:/home/hermeswebui/.hermes \
  -e HERMES_WEBUI_HOST=0.0.0.0 \
  -e HERMES_WEBUI_PORT=9120 \
  -e HERMES_WEBUI_PASSWORD=<password> \
  -e HERMES_WEBUI_SKIP_ONBOARDING=1 \
  -e HERMES_WEBUI_STATE_DIR=/home/hermeswebui/.hermes/webui \
  ghcr.io/nesquena/hermes-webui:latest
```

Verify:
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9120/
curl https://hermes.jefe.al/   # through Pangolin
```

## Port discovery technique (from inside Hermes container)

When you can't use `ss`/`lsof`/`fuser` (not installed), find what's
listening on a port via `/proc/net/tcp`:

```bash
# Convert port to hex (e.g. 8787 → 0x2253)
printf '%X\n' 8787

# Find the socket
cat /proc/net/tcp | grep ':2253 '

# Find the PID owning the socket inode
# (inode is column 10 in /proc/net/tcp output)
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  if ls -l /proc/$pid/fd 2>/dev/null | grep -q 'socket:\[INODE\]'; then
    echo "PID $pid: $(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | head -c 300)"
  fi
done
```

Note: if the process is in a different PID namespace (separate Docker
container), you won't find it via /proc — use `ctl.sh status` or
`curl` to confirm it's alive instead.

## ctl.sh behavior with Docker-managed instances

`ctl.sh status` will report the webui as "running (not managed by ctl.sh)"
when it was started by Docker Compose rather than ctl.sh itself:

```
● hermes-webui — running (not managed by ctl.sh)
  PID:     -
  Bound:   127.0.0.1:8787
  Log:     /opt/data/webui.log
  Health:  ok
  Note:    manage it via its own supervisor (systemctl/launchctl) or the process directly.
```

`ctl.sh stop` will refuse to stop it:
```
[ctl] Hermes WebUI is stopped
[ctl] Warning: an instance NOT managed by ctl.sh is still serving 127.0.0.1:8787 — not touching it.
```

→ Must use `docker compose down` from the host.

## s6 dashboard permanent disable

`touch /run/service/dashboard/down` prevents s6 from restarting the
service, but only until the next container restart. For a permanent
disable when migrating to hermes-webui:

1. Remove or falsify `HERMES_DASHBOARD` from the Hermes container
   environment (docker-compose.yml `environment:` section on the host).
2. Recreate the Hermes container: `docker compose up -d --force-recreate`

This frees port 9120 for the webui container to bind.

## hermes-webui .env fields

| Variable | Default | Purpose |
|----------|---------|---------|
| `HERMES_WEBUI_HOST` | `127.0.0.1` | Bind address. Set `0.0.0.0` for Pangolin. |
| `HERMES_WEBUI_PORT` | `8787` | Listen port. |
| `HERMES_WEBUI_PASSWORD` | (none) | Auth password. Required for non-loopback binds. |
| `HERMES_WEBUI_SKIP_ONBOARDING` | `0` | Set `1` to skip first-run wizard. |
| `HERMES_WEBUI_STATE_DIR` | `~/.hermes/webui` | Session/state storage. |
| `HERMES_WEBUI_DEFAULT_WORKSPACE` | `~/workspace` | Initial workspace dir. |

## docker-compose.yml port mapping

The webui docker-compose.yml has TWO places to change the port:
1. `ports:` section — host:container mapping (e.g. `"127.0.0.1:9120:9120"`)
2. `environment:` — `HERMES_WEBUI_PORT=9120` (the port the Python server listens on inside the container)

Both must match. The `.env` file in the repo root is read by `bootstrap.py`
and `ctl.sh` but the Docker Compose `environment:` section takes precedence
for the container.

## hermes-webui Docker image

The pre-built image is at `ghcr.io/nesquena/hermes-webui:latest`.
The Dockerfile is in the repo root if a local build is needed.
The two-container compose file (`docker-compose.two-container.yml`)
runs Hermes Agent + WebUI in separate containers on a shared network.