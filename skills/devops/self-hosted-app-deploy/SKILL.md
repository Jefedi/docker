---
name: self-hosted-app-deploy
title: Self-Hosted App Deployment
description: Deploy self-hosted apps with OAuth and Docker on homelab.
tags: [docker, self-hosted, oauth, spotify, homelab, pangolin]
---

# Self-Hosted App Deployment

Deploy self-hosted applications that require external OAuth (Spotify, etc.) + Docker + Pangolin reverse proxy on Jefe's infrastructure.

## General Workflow

1. **Create OAuth app** on the provider's developer dashboard
2. **Configure redirect URI** — must match the deployment URL exactly, including path prefix (varies by image)
3. **Write docker-compose.yml** — include ALL required services (DB, cache, etc.)
4. **Deploy** via Portainer or `docker compose up -d`
5. **Configure Pangolin** — point domain to the container's HTTP port
6. **Verify** — check logs for DB connection, test OAuth flow end-to-end
7. **Import data** if the app supports history import

## Key Pitfalls (cross-app)

### Redirect URI path prefix varies by image
Different Docker images of the same app may use different callback paths. ALWAYS check the image docs:
- linuxserver images often add `/api/` prefix vs upstream
- Example: YourSpotify — linuxserver: `/api/oauth/spotify/callback` vs upstream: `/oauth/spotify/callback`

### Missing DB service in compose
Apps that need MongoDB/PostgreSQL will 502 if the DB service is missing from the compose file. The app retries N times then crashes. Always include the DB service in the same compose.

### Docker network pool exhaustion
Error: `all predefined address pools have been fully subnetted`
- Per-stack fix: add explicit subnet under `networks.default.ipam.config`
- Global fix: `/etc/docker/daemon.json` → `default-address-pools` with multiple /16s at size:24
- Cleanup: `docker network prune`

### Subnet overlap
Error: `Pool overlaps with other one on this address space`
- Change to an unused /16 in the compose network config
- Check existing: `docker network inspect $(docker network ls -q) --format '{{.Name}} {{.IPAM.Config}}'`

### OAuth app description validation
Some providers (Spotify) reject gibberish in the description field. Use a real description. Browser spellcheck red underline is a visual cue.

### Indentation in YAML networks block
`networks:` must be at the SAME indentation level as `services:` (top-level key), NOT nested inside a service. Common copy-paste error.

### `env_file` missing → OIDC/OAuth vars never loaded
If OIDC vars are in a `.env` file but `env_file: .env` is not in the compose service definition, the vars never reach the container. The app starts without auth and shows no error — it just falls back to local auth silently. ALWAYS include `env_file: .env` in the service when using a separate env file.

### `OIDC_ALLOW_REGISTRATION` vs `ALLOW_REGISTRATION` (Termix-specific, general pattern)
Two separate flags. `ALLOW_REGISTRATION: false` blocks general registration but does NOT block OIDC-created accounts. Set `OIDC_ALLOW_REGISTRATION: false` explicitly to prevent new accounts via SSO. Check each app's docs for the specific flag name — the pattern of separate "general registration" vs "SSO registration" flags is common.

### OIDC callback URL mismatch behind reverse proxy
When an app sits behind a TLS-terminating proxy (Pangolin), it may build callback URLs with `http://` instead of `https://`, causing a mismatch with the OIDC provider's registered callback. Look for a `FORCE_HTTPS` or similar env var. For Termix: `OIDC_FORCE_HTTPS: 'true'`. Verify the callback URL in the browser address bar before the redirect to the OIDC provider.

### First-launch data gap
Many self-hosted tracking apps (Spotify stats, fitness, etc.) only pull recent data on first launch. Full history usually requires a separate data export + import step via the app's Settings UI.

### Dev-mode compose files overwrite Dockerfile build
Many open-source projects ship a `docker-compose.yaml` designed for development with a `.:/app` bind mount that overwrites the Dockerfile `COPY` layer. For production deployment, remove this volume mount — otherwise the container sees an empty/wrong directory and crashes (e.g. Mem0's `alembic.ini` not found because the mount replaces `/app` with the host `server/` dir which lacks the build artifacts).

### File mounts becoming directories
When a compose file mounts a single file (e.g. `./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh`) and the host file doesn't exist on first `docker compose up`, Docker creates a **directory** at that path inside the container instead of a file. The service then fails silently or with a confusing error. Fix: remove the mount from the compose and create the resource manually after startup (e.g. `docker exec <pg> psql -c "CREATE DATABASE ..."`).

### `OPENAI_BASE_URL` vs `OPENAI_API_BASE_URL`
The OpenAI Python SDK reads `OPENAI_BASE_URL` for the API endpoint, NOT `OPENAI_API_BASE_URL`. Many `.env.example` files use the wrong variable name. If a service hits `api.openai.com` despite a custom base URL being set, check the variable name — this is the #1 cause.

### Docker network reconnect after `compose down`
`docker compose down && up` recreates containers from scratch. Manual `docker network connect <net> <container>` connections are LOST. Either add the external network to the compose file (`networks: [default, litellm_default]` with `external: true`), or re-run `docker network connect` after every `up`.

### Hardcoded passwords in upstream config files
Some projects hardcode credentials in config files (e.g. Mem0's `alembic.ini` has `sqlalchemy.url = ...postgres:postgres@...`). The `.env` password MUST match the hardcoded value — not the other way around — or the service crashes on migration. Always `grep` the upstream config for hardcoded credentials before setting a custom password in `.env`.

### LiteLLM virtual keys invalidated by config changes
When you modify models or routes in the LiteLLM Web UI (adding `mistral-embed`, changing model routing), previously generated virtual API keys can become invalid ("Invalid hash key" error). Regenerate keys after config changes and update downstream `.env` files.

### Docker services go in `/srv/docker/<stack>/`
Jefe's convention for all Docker stacks. Clone repos there, not in `~/` or `/opt/data/`.

### NFS consume/watch directories require polling, not inotify
Apps that watch a directory for new files (Paperless-ngx consumer, *arr inotify, etc.) **cannot use inotify on NFS mounts**. NFS doesn't support filesystem notifications. The app appears to run fine but never detects new files. Always switch to polling mode when the watch directory is on NFS:
- Paperless-ngx: `PAPERLESS_CONSUMER_POLLING_INTERVAL: "30"` (NOT `PAPERLESS_CONSUMER_INOTIFY_DELAY` which doesn't exist and is silently ignored)
- Sonarr/Radarr: enable polling in media management settings
- Generic: look for `polling`, `watch_interval`, or similar config options

## App-Specific References

- **YourSpotify** (linuxserver image): `references/your-spotify.md` — full compose, env vars, OAuth setup, data import
- **Remote deployment** (agent on different host than target server): `references/remote-deployment.md` — sudo vs root on fresh VPS, passwd cracklib rules, pre-existing root-owned dirs, Telegram command format, resuming interrupted deployments
- **Termix** (web SSH/RDP terminal + Pocket ID OIDC): `references/termix.md` — compose with guacd, OIDC env vars, callback URL pitfalls, clipboard paste bug workaround
- **Mem0 self-hosted** (AI agent memory layer): `references/mem0-self-hosted.md` — dev compose pitfalls, LiteLLM routing, pgvector setup, n8n community node integration
- **Technitium DNS** (DNS server with DoH + NextDNS forwarder): `references/technitium-dns.md` — Docker compose, DoH via Pangolin, zones locales, NextDNS forwarder config, limitations of cross-country DNS setup
- **Paperless-ngx** (document management + OCR): `references/paperless-ngx.md` — compose mariadb-tika, NFS consume folder requires polling (not inotify), Redis log spam fix, Valkey vs Redis

## Pangolin Config

Point the domain to the container's **HTTP port** (not HTTPS). Example:
```
sp.jefe.al → http://<host_ip>:8544
```

## Style Notes

- User deploys via Portainer on remote host (ax42) — agent has no direct Docker socket access
- Provide corrected compose as a code block the user can paste into Portainer
- User shares screenshots of errors — read them carefully for the specific error string
- Keep responses concise: identify the failing field/component, give the fix, no preamble
- **Telegram command format**: When sending shell commands for the user to execute, send ONLY the command in its own message (no backticks, no surrounding text). See `references/remote-deployment.md` and `assistant-plugin/references/user-preferences.md`.