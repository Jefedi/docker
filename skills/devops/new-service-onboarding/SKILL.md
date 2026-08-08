---
name: new-service-onboarding
title: New Service Onboarding
description: Deploy and configure a new containerized service end-to-end — create Docker container, set up Pangolin reverse proxy, add Uptime Kuma monitor, configure ntfy alerts.
tags: [pangolin, docker, uptime-kuma, ntfy, onboarding, homelab]
---

# New Service Onboarding

Full onboarding pipeline for a new service on Jefe's infrastructure. Run this when deploying a new container.

## Workflow

### 1. Gather Details
- Service name
- Docker image / docker-compose config
- Port the service listens on
- Desired domain (e.g. `service.jefe.al`)
- Which server (this machine `100.64.0.9` or Hetzner server)
- Volume/data persistence needs
- Network (bridge, host, or existing docker network)

### 2. Deploy Container
Either deploy via docker-compose or docker run:
```bash
docker run -d \
  --name <service> \
  --restart unless-stopped \
  -p <port>:<port> \
  -v <data_dir>:/data \
  <image>
```

Or write a docker-compose.yml, then `docker compose up -d`.

### 6. Verify Pangolin Proxy

After creating the Pangolin resource and target, verify both locally AND through the proxy:

```bash
# 1. Local check (container responds)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/v1/about  # or /health, /

# 2. Through Pangolin (wait a few seconds for Newt sync)
curl -skL -o /dev/null -w "%{http_code}" https://<service>.jefe.al/v1/about
```

If step 1 works but step 2 shows **"no available server"** or **503**:
- **Check the target `method`**: Must be `"http"` for HTTP resources (not `null` / TCP tunnel)
- **Check the site**: Target must be on the same site as the machine where the container runs (not a different Newt site)

### 4. Uptime Kuma Monitor
Create a monitor in Uptime Kuma for the public URL (manual via Uptime Kuma UI, or API).

### 5. ntfy Alert
Add ntfy notification for the service:
```bash
curl -u "<ntfy_user>:<ntfy_pass>" \
  -d '{"topic":"<service>-alerts","title":"<Service> Notifications"}' \
  "https://ntfy.jefe.ovh/..."
```
Note: This may require config — ask user how they want to receive alerts.

## Special Modes

### `--network host` Services (media servers, streaming, DLNA)
Some services (Music Assistant, Plex, Jellyfin, AirPlay receivers) **require** `--network host` for mDNS/UPnP discovery. This changes the rules:
- **No port mapping** (`-p` flags are ignored) — the service uses the host's ports directly
- Ports must be free on the host before starting (`ss -tlnp | grep <port>`)
- `--network host` is incompatible with standard Docker bridge networking
- **localhost-only rule**: With `--network host`, you CAN'T restrict to `127.0.0.1` via Docker port binding. The service binds to `0.0.0.0` on the host. Security relies on the host firewall not exposing the port externally. Pangolin private resources (Newt tunnel) still work since they connect locally.
- Example capabilities often needed: `--cap-add=SYS_ADMIN --cap-add=DAC_READ_SEARCH` (required by Music Assistant for SMB/NFS mounts)
- Security note: `--network host` removes container network isolation — only use for services that genuinely need it

### Music Assistant (specific example)
See `references/music-assistant.md` for full Docker deploy + Spotify auth fix.
A docker-compose template is at `templates/music-assistant-compose.yml`.

### Signal Messenger REST API (signal-cli-rest-api)
See `references/signal-cli-rest-api.md` for deployment details (json-rpc-native mode, QR device linking, Pangolin config on signal.jefe.al).

## Pitfalls
- Check port conflicts before deploying (`ss -tlnp | grep <port>`)
- Always use `--restart unless-stopped` for services that should auto-recover
- For database services, mount volumes outside container for persistence
- **`docker compose up -d` + tool guard**: Running `cd /path && docker compose up -d` may be blocked by the tool's background-process guard. Workaround: use `docker compose -f /path/to/compose.yml up -d` in a single command (no `cd`). The `-f` flag lets the agent run it as a foreground command.
- **Verify the service after deploy**: After `docker compose up -d`, check:
  1. `docker ps --filter name=<service>` → confirm `Up` and `health: starting` or `healthy`
  2. `docker logs --tail 10 <service>` → confirm no crash loops
  3. `curl -s http://127.0.0.1:<port>/` or `/v1/about` or `/health` → confirm API responds
- **RULE: localhost-only, jamais en publique.** Jefe NEVER exposes services directly to the public internet. Services that need external access go through Pangolin reverse proxy only. Use `127.0.0.1:<port>:<container_port>` for bridge-mode containers, or rely on Tailscale for direct access (e.g. `100.64.0.x:<port>`).
- **Access URL listing**: When telling Jefe the access URL, list BOTH `http://localhost:<port>` AND `http://127.0.0.1:<port>` explicitly — Jefe considers them different and wants both mentioned.
- Docker cleanup old containers first if disk space is tight
- Check if the service needs a specific Docker network (e.g. `discord-net` for bots)
- **Nginx static files**: When serving static HTML with nginx:alpine via a mounted volume, files must be `chmod 644` (world-readable), not the default 600 — nginx runs as non-root and can't read restricted files, returning 403. Always `chmod 644 <dir>/*` after copying files.
- **Localhost-only port binding**: When the service only needs Pangolin access (no direct public), bind to `127.0.0.1:<port>:<container_port>` instead of `<port>:<container_port>` to avoid exposing the port on the public interface. ⚠️ This ONLY applies to bridge/overlay networking — `--network host` services CANNOT be restricted this way.
