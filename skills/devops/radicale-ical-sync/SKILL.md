---
name: radicale-ical-sync
title: Radicale CalDAV + iCal Sync
description: Deploy Radicale CalDAV and sync external iCal feeds via n8n.
tags: [radicale, caldav, ical, calendar, n8n, docker, sync]
---

# Radicale CalDAV + iCal Sync

Deploy a self-hosted CalDAV server (Radicale) and sync external iCal calendar feeds into it via n8n, so events appear on iPhone, Home Assistant, and any CalDAV client.

## Deploy Radicale in Docker

### Compose (hardened, production-grade)

Image: `tomsquest/docker-radicale:latest`
Port: `127.0.0.1:5232:5232` (localhost-only, expose via Pangolin)
Config: `./config/config` mounted read-only
Data: `./data` bind mount (NOT a Docker named volume — see pitfalls)

Key hardening:
- `read_only: true` + `tmpfs` for /tmp
- `cap_drop: ALL` + minimal `cap_add` (CHOWN, SETUID, SETGID, KILL)
- `no-new-privileges: true`
- `init: true`
- `pids_limit: 50`, `mem_limit: 256M`
- healthcheck with curl

### Config file (`config/config`)

```ini
[server]
hosts = 0.0.0.0:5232

[auth]
type = htpasswd
htpasswd_filename = /data/users.htpasswd
htpasswd_encryption = bcrypt

[storage]
filesystem_folder = /data/collections
```

### Create user

```bash
# Requires apache2-utils
sudo apt install -y apache2-utils
htpasswd -cB /srv/docker/radicale/data/users.htpasswd jefe
```

### Expose via Pangolin

Create a Pangolin resource for the desired domain (e.g. `ical.jefe.al`) pointing to `127.0.0.1:5232`.

### Connect clients

- **iPhone**: Réglages → Calendrier → Comptes → Ajouter → Autre → Compte CalDAV. Serveur = domaine Pangolin, user/password = htpasswd credentials.
- **Home Assistant**: Paramètres → Appareils et services → CalDAV. URL = `https://ical.jefe.al` (via Pangolin) ou `http://127.0.0.1:5232` (si même serveur).

## iCal Sync via n8n

### Pattern

External iCal feeds (F1, NASCAR, MotoGP, etc.) → n8n fetches them hourly → parses VEVENTs → PUTs each event to Radicale via CalDAV.

### Workflow structure

1. **Schedule Trigger** — every 1h (or daily for static calendars)
2. **HTTP Request** (one per source) — GET the .ics URL, responseFormat=text
3. **Code node** (one per source) — parse VEVENTs with regex, extract UID, wrap each in a full VCALENDAR
4. **Merge** (append mode) — combine all sources into one stream
5. **Split in Batches** — loop over events
6. **HTTP Request (PUT)** — push each event to Radicale
7. **Set** — mark sync complete

### CalDAV PUT node config

- Method: PUT
- URL: `https://<domain>/<user>/<collection-uuid>/<uid>.ics`
- Auth: genericCredentialType, httpBasicAuth
- Body: raw, rawContentType: `text/calendar`
- Body content: full VCALENDAR wrapping the VEVENT

### iCal parsing code (JavaScript)

```javascript
const raw = $input.first().json.data || $input.first().json;
const text = typeof raw === 'string' ? raw : JSON.stringify(raw);
const events = [];
const veventRegex = /BEGIN:VEVENT[\s\S]*?END:VEVENT/g;
const matches = text.match(veventRegex) || [];
for (const vevent of matches) {
  const uidMatch = vevent.match(/UID:(.+)/);
  const uid = uidMatch ? uidMatch[1].trim() : null;
  if (!uid) continue;
  const icsContent = 'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//n8n//Sync//FR\n' + vevent + '\nEND:VCALENDAR\n';
  events.push({ json: { uid, icsContent } });
}
return events;
```

### Known iCal feed sources

| Series | URL |
|---|---|
| F1 | `https://ics.ecal.com/ecal-sub/6a65b95060d5e000022518b5/Formula%201.ics` |
| NASCAR Cup | `https://calendar.google.com/calendar/ical/db8c47ne2bt9qbld2mhdabm0u8%40group.calendar.google.com/public/basic.ics` |
| MotoGP | `https://calendar.google.com/calendar/ical/832vbii8pmrvma356b4vn3v42c%40group.calendar.google.com/public/basic.ics` |
| More series | `https://toomuchracing.com/calendar/` (IndyCar, WEC, WSBK, BSB, etc.) |

## Pitfalls

- **Bind mount vs named volume**: If you use a Docker named volume (`radicale_data:/data`), files created on the host (like `users.htpasswd`) won't be inside the container's volume. Either use a bind mount (`./data:/data`) or `docker cp` the htpasswd file into the container. Bind mount is simpler and persists across container recreation.
- **htpasswd not found (401)**: The htpasswd file must be at the path specified in `htpasswd_filename` config — if using a named volume, the file on the host is NOT the same as the file in the container. Use bind mount or `docker cp`.
- **Docker network exhaustion**: `docker compose up -d` fails with "all predefined address pools have been fully subnetted" when too many unused networks exist. Fix: `docker network prune -f` before retry.
- **read_only + chown Permission denied**: The `tomsquest/docker-radicale` entrypoint tries to `chown /data` on startup. With `read_only: true`, this fails with `chown: /data: Permission denied` and the container loops on restart. Fix: set `TAKE_FILE_OWNERSHIP=false` env var. The volume already belongs to UID 2999 (radicale) so chown is unnecessary.
- **Docker-in-Docker bind mount path mismatch**: When Hermes runs inside a container with the Docker socket mounted, `docker compose up` resolves bind mount paths relative to the **host** filesystem, not Hermes's filesystem. `./config` in a compose file at `/opt/data/radicale/` resolves to `/opt/data/radicale/config` on the **host** — which may not exist. The actual host paths are under `/srv/docker/radicale/`. Always verify bind mount targets with `docker run --rm -v /path:/check alpine ls -la /check` before recreating. Named Docker volumes work fine (resolved by the daemon, not by path).
- **Recreating containers without compose**: When the compose file is inaccessible (piped via stdin, or on a path only visible to the host), recreate the container with `docker run` using absolute host paths for bind mounts and named volumes (`-v radicale_radicale_data:/data`). Preserve the full config: env vars, caps, read-only, security-opt, healthcheck, restart policy.
- **Telegram copy-paste breaks multi-line commands**: When guiding a user through terminal commands via Telegram, heredocs and multi-line Python break. Use base64: `echo '<base64>' | base64 -d > /path/to/file` — single line, copies perfectly.
- **Commands as standalone messages**: Send EACH command in a separate Telegram message containing ONLY the command (no backticks, no formatting, no surrounding text). User long-presses to copy. Explanations go in separate messages.
- **Merge numberInputs**: When connecting N branches to a Merge node in append mode, set `numberInputs: N` in parameters. Otherwise branches beyond input 1 are silently dropped (validation warning INVALID_INPUT_INDEX).
- **One workflow, not many**: The user wants ALL similar sources in a SINGLE workflow, not separate workflows per source. Add new sources to the existing workflow via update_workflow (addNode + addConnection + Merge). Archive any duplicate workflow created by mistake.
- **Pangolin + CalDAV**: Pangolin reverse proxy works for CalDAV PUT/GET. HA CalDAV integration connects through the Pangolin domain without issues.