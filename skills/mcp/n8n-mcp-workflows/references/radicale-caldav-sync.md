# Radicale CalDAV Deployment + n8n Sync

## Radicale Server (Docker, production-grade)

Deployed at `ical.jefe.al` via Pangolin. Docker Compose at `/srv/docker/radicale/compose.yaml`.

### Key config points
- Image: `tomsquest/docker-radicale:latest`
- Port: `127.0.0.1:5232` (localhost only, Pangolin handles external access)
- Auth: htpasswd with bcrypt (`htpasswd -cB /srv/docker/radicale/data/users.htpasswd jefe`)
- Config file at `./config/config` mounted read-only:
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
- Hardening: `read_only: true`, `cap_drop: ALL`, `no-new-privileges`, `pids_limit: 50`, `mem_limit: 256M`
- `TAKE_FILE_OWNERSHIP=false` env var to avoid permission issues
- Volumes: `./data:/data` (bind mount, NOT named volume — keeps htpasswd on host)

### Pitfall: htpasswd not in container
If using a named Docker volume (`radicale_data:/data`), the htpasswd file created on the host at `./data/users.htpasswd` is NOT inside the container's `/data`. The container returns 401 for all requests. Fix: either `docker cp` the file in, or use bind mount `./data:/data` instead of a named volume.

### Pitfall: Docker network pool exhaustion
`docker compose up -d` can fail with `all predefined address pools have been fully subnetted`. Fix: `docker network prune -f` to clear unused networks from stopped containers.

## n8n → Radicale CalDAV Sync Pattern

For syncing external iCal feeds (F1, sports, etc.) into Radicale so they appear on iPhone and HA.

### Workflow structure
```
[Schedule Trigger] → [HTTP GET iCal feed] → [Code: parse VEVENTs] → [Split in Batches] → [HTTP PUT each event to Radicale] → [Done]
```

### CalDAV PUT details
- Method: `PUT`
- URL: `https://ical.jefe.al/jefe/<collection-uuid>/<event-uid>.ics`
- Auth: `httpBasicAuth` credential (user: jefe, password: Radicale password)
- Content-Type: `raw` with `rawContentType: text/calendar`
- Body: full iCal content for each VEVENT (wrapped in VCALENDAR)

### iCal parsing (Code node, runOnceForAllItems)
Parse the raw iCal text with regex to extract VEVENT blocks and their UIDs:
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

### Motorsport Calendar Sync workflow (multi-source)
- Workflow ID: `A4F90ZXY7FGD4zop`
- URL: https://n8n.jefe.ovh/workflow/A4F90ZXY7FGD4zop
- Name: "Motorsport Calendar Sync" (renamed from "F1 Calendar Sync")
- Schedule: every 1 hour
- Target: Radicale collection `0feb942c-776d-cef4-18a5-cb0d8bccd798`
- Credential: `httpBasicAuth` named "Radicale" (must be assigned manually in n8n UI)
- Sources (3 parallel branches merged via Merge node `mode: append`):
  1. F1: `https://ics.ecal.com/ecal-sub/6a65b95060d5e000022518b5/Formula%201.ics`
  2. NASCAR Cup: `https://calendar.google.com/calendar/ical/db8c47ne2bt9qbld2mhdabm0u8%40group.calendar.google.com/public/basic.ics`
  3. MotoGP: `https://calendar.google.com/calendar/ical/832vbii8pmrvma356b4vn3v42c%40group.calendar.google.com/public/basic.ics`

### Multi-source pattern (CRITICAL — user preference)
**ALWAYS consolidate similar sources into ONE workflow.** The user explicitly rejected
separate workflows for NASCAR/MotoGP when F1 already existed. Pattern:
- One Schedule Trigger → fan out to N HTTP GET nodes (one per source)
- Each HTTP GET → its own Code node to parse VEVENTs
- All parse outputs → Merge node (`mode: append`, `numberInputs: N`)
- Merge → Split in Batches → PUT to Radicale (shared)
- Add new sources by: addNode (HTTP + Code) + addConnection to Merge + updateNodeParameters on Merge to set `numberInputs`

### Merge node pitfall: numberInputs
When adding a 3rd branch to a Merge node that was created with 2 inputs, `update_workflow`
emits `INVALID_INPUT_INDEX` warning: "Merge node has a connection to input index 2 but
numberInputs is 2". Fix: `updateNodeParameters` with `numberInputs: 3` (or N) in a
follow-up operation.

### Reusable for other iCal feeds
Change the source URL in the HTTP GET node and optionally the target collection UUID.
The parsing and PUT logic stays the same. For multiple feeds, use the multi-source
pattern above — do NOT create separate workflows.

### Telegram copy-paste pitfall (multi-line files)
When sending multi-line file content (compose.yaml, config files) to the user via
Telegram, copy-paste BREAKS multi-line content — Telegram adds/removes characters,
merges lines, or truncates. **Always use base64 encoding**:
```
echo '<base64-encoded-content>' | base64 -d > /path/to/file
```
This guarantees the file content is exact. The user long-press → copy → paste in SSH
and it works perfectly.