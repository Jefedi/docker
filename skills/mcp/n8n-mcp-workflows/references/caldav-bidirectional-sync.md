# iCal Feed & HA Todo Sync — n8n-Only Pattern

**Preferred approach**: n8n Data Tables as source of truth, single iCal webhook
for iOS/HA subscription, scheduled bidirectional sync with HA todos.

⚠️ **User preference (CRITICAL)**: The user explicitly rejected the Radicale
CalDAV server approach and iOS Shortcuts webhooks. They want ONE URL to
subscribe to, with n8n handling everything else internally. Do NOT propose
external CalDAV servers or per-action webhooks unless the user asks.

## Architecture (n8n-only)

```
iOS Calendar ──subscribe──→ GET /ical-unified ──→ n8n Data Tables
HA Calendar  ──subscribe──→ GET /ical-unified      (ical_events + n8n_tasks)
HA todo.*    ←──sync 5min──→ n8n Data Tables
```

- **One webhook**: `GET /ical-unified` serves a combined iCal feed (VEVENTs +
  VTODOs) from two Data Tables
- **Scheduled sync**: every 5 min, HA `todo.*` items are upserted into
  `n8n_tasks`, and tasks not yet in HA are pushed via HA API
- **No external services**: no Radicale, no CalDAV server, no iOS Shortcuts

## Data Tables

### `ical_events` (pre-existing)
Columns: `summary`, `start_datetime`, `end_datetime`, `description`, `uid`

### `n8n_tasks` (created in this session)
Columns: `summary`, `status`, `priority`, `due_date`, `uid`, `source`

The `source` column tracks origin: `ha:todo.liste_dachats`, `ios`, etc.

## Workflow Structure (14 nodes, 2 triggers)

### Branch 1: Scheduled HA Sync (5 min)
```
ScheduleTrigger → Get HA States → Extract HA Todos → Upsert HA Todos
                                                        ↓
                               Get All Tasks for Sync → Find Tasks Not in HA
                                                        ↓
                               Loop Push to HA ← splitInBatches ← Push Missing to HA
```

1. **Get HA States**: `GET /api/states` with HA Bearer credential
2. **Extract HA Todos**: Code node filters `todo.*` entities, flattens items
3. **Upsert HA Todos**: Data Table upsert by `uid` into `n8n_tasks`
4. **Get All Tasks for Sync**: Read back all `n8n_tasks` rows
5. **Find Tasks Not in HA**: Compare UIDs, filter tasks missing from HA
6. **Push Missing to HA**: `POST /api/services/todo/add_item` per task

### Branch 2: iCal Feed Webhook
```
GET /ical-unified → Get Events → Get Tasks → Generate iCal → Respond iCal
```

1. **Get Events**: Data Table get all from `ical_events`
2. **Get Tasks**: Data Table get all from `n8n_tasks`
3. **Generate iCal**: Code node builds combined VCALENDAR with VEVENTs + VTODOs
4. **Respond iCal**: `text/calendar` content-type, `attachment; filename="hermes.ics"`

## Key Techniques

### Generating iCal in Code Node

```javascript
const events = $('Get Events').all().map(i => i.json);
const tasks = $('Get Tasks').all().map(i => i.json);
const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
const fmtDT = (s) => { try { return new Date(s).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'; } catch(e) { return s; } };
let lines = [
  'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Hermes//n8n//FR',
  'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
  'X-WR-CALNAME:Hermes Agenda', 'X-WR-TIMEZONE:Europe/Paris'
];
for (const ev of events) {
  lines.push('BEGIN:VEVENT', 'UID:' + (ev.uid || ev.id), 'SUMMARY:' + (ev.summary || 'Sans titre'), 'DTSTAMP:' + now);
  if (ev.start_datetime) lines.push('DTSTART:' + fmtDT(ev.start_datetime));
  if (ev.end_datetime) lines.push('DTEND:' + fmtDT(ev.end_datetime));
  if (ev.description) lines.push('DESCRIPTION:' + ev.description);
  lines.push('END:VEVENT');
}
for (const tk of tasks) {
  lines.push('BEGIN:VTODO', 'UID:' + (tk.uid || tk.id), 'SUMMARY:' + (tk.summary || 'Sans titre'),
    'STATUS:' + (tk.status || 'NEEDS-ACTION'), 'DTSTAMP:' + now);
  if (tk.due_date) lines.push('DUE:' + fmtDT(tk.due_date));
  if (tk.priority) lines.push('PRIORITY:' + tk.priority);
  lines.push('END:VTODO');
}
lines.push('END:VCALENDAR');
return [{ json: { ical: lines.join('\r\n') } }];
```

### Data Table Upsert by UID

```javascript
{
  resource: 'row',
  operation: 'upsert',
  dataTableId: { __rl: true, mode: 'name', value: 'n8n_tasks' },
  matchType: 'allConditions',
  filters: { conditions: [{ keyName: 'uid', condition: 'eq', keyValue: '={{ $json.uid }}' }] },
  columns: { mappingMode: 'defineBelow', value: { ... }, schema: [...] }
}
```

### `placeholder()` for User-Configurable URLs

Use `placeholder('hint text')` for HA API URLs that need manual configuration:

```javascript
url: placeholder('HA URL + /api/states (e.g. https://ha.jefe.ovh/api/states)')
```

## CRITICAL: Empty Data Tables Break Webhook Response Chain

When a Data Table node in the iCal feed chain returns **0 items** (empty table),
the downstream chain **stops silently** — the Code node and Respond to Webhook
node never execute. The webhook returns HTTP 200 with an **empty body** and
`content-type: application/json` instead of `text/calendar`.

iOS shows: **"Impossible de vérifier les données du compte"** (Unable to verify
account data).

### Diagnosis

```bash
# Test the webhook — if body is empty and content-type is application/json,
# the chain stopped at a Data Table node
curl -s -D - "https://n8n.jefe.ovh/webhook/ical-unified"
# HTTP/2 200
# content-type: application/json; charset=utf-8  ← WRONG, should be text/calendar
# content-length: 0  ← EMPTY
```

Check the execution:
```python
mcp__n8n_mcp__get_execution(
    workflowId="<id>",
    executionId="<id>",
    includeData=True
)
# Look for: "lastNodeExecuted": "Get Events" with data.main: [[]]  ← 0 items
```

### Fix: `alwaysOutputData: true` on Data Table nodes

Set `alwaysOutputData: true` via `setNodeSettings` on EVERY Data Table node
that feeds the response chain:

```python
mcp__n8n_mcp__update_workflow(
    workflowId="<id>",
    operations=[
        {"type": "setNodeSettings", "nodeName": "Get Events", "settings": {"alwaysOutputData": True}},
        {"type": "setNodeSettings", "nodeName": "Get Tasks", "settings": {"alwaysOutputData": True}},
        # Also update the Code node to filter out empty placeholder items:
        {"type": "updateNodeParameters", "nodeName": "Generate iCal", "parameters": {
            "jsCode": "const events = $('Get Events').all().map(i => i.json).filter(i => i.summary); ...",
            "mode": "runOnceForAllItems"
        }}
    ]
)
```

Then **republish** the workflow — the fix only takes effect in production after
`publish_workflow`.

### Why This Happens

n8n's execution model: when a node outputs 0 items, downstream nodes are skipped
for that run. This is correct for scheduled/polling workflows ("nothing to do").
But for **webhook response chains**, the Respond to Webhook node MUST execute
regardless — it needs to return a valid iCal body even when tables are empty.

`alwaysOutputData: true` forces a synthetic `{json: {}}` item downstream. The
Code node must then `.filter(i => i.summary)` to skip these empty placeholders.

## iOS Calendar Subscription — Pitfall

⚠️ **iOS requires the full URL with `https://` protocol prefix.** If the user
enters just `n8n.jefe.ovh/webhook/ical-unified` (without `https://`), iOS shows
"Connexion impossible avec SSL" (Connection impossible with SSL) and offers to
retry without SSL — which also fails.

**Fix**: Always provide the full URL: `https://n8n.jefe.ovh/webhook/ical-unified`

## Credentials Needed

1. **Home Assistant Bearer** (`httpBearerAuth`) — HA long-lived access token

Must be assigned manually in n8n UI after workflow creation (HTTP Request
nodes with `genericCredentialType` are skipped during auto-assignment).

## SDK Code Escaping

Use **double-quoted strings** with `\n` for line breaks in `jsCode`. See
`references/sdk-pitfalls.md` for the full escaping rules.

## Workflow Reference

Active workflow: `📅 Calendrier Unifié` (ID: 4CP4NStyjt7YhD25)
- 14 nodes, 2 triggers (schedule + webhook)
- URL: https://n8n.jefe.ovh/workflow/4CP4NStyjt7YhD25
- iCal feed: `https://n8n.jefe.ovh/webhook/ical-unified`

Archived workflows (superseded):
- `📅 Calendrier & Tâches Unifiés` (HvqS5WWIKLicmoi8) — 33 nodes with webhooks
  for add-event/add-task/complete-task/get-tasks. Archived per user request:
  "Simplifie le avec une seule url".
- `📅 Radicale CalDAV Sync` (WgmnvenaW2BYl87W) — 18 nodes with Radicale
  CalDAV server. Archived: user chose n8n-only approach, no external services.