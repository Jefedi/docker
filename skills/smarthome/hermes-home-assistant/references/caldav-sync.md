# CalDAV Calendar + Task Sync (Radicale)

Pattern for syncing HA todo entities and calendar events with a self-hosted
Radicale CalDAV server, enabling multi-device sync (iOS, HA, n8n).

## Architecture

```
iOS Calendar ←CalDAV→ Radicale ←API→ n8n ←API→ HA todo/calendar
                                     ↑
                            Webhook (iOS Shortcuts)
```

- **iOS ↔ Radicale**: native CalDAV account in iOS Settings (bidirectional)
- **HA Calendar ↔ Radicale**: HA CalDAV integration (Settings → Devices → CalDAV)
- **HA Todos ↔ Radicale VTODOs**: n8n scheduled workflow (5-min sync)
- **iOS Shortcuts → Radicale events**: POST webhook → n8n → PUT `.ics` to Radicale

## Radicale Deployment

Docker image `tomsquest/docker-radicale:latest`, port 5232, htpasswd bcrypt auth.
Config file at `config/config`, users at `config/users`.

Create two collections after deploy:
1. **calendar** (VEVENT) — for calendar events
2. **tasks** (VTODO) — for tasks/todos

Expose via Pangolin on e.g. `cal.jefe.ovh`.

## HA CalDAV Integration

Settings → Devices & Services → Add Integration → CalDAV:
- URL: `https://cal.jefe.ovh/jefe/calendar/`
- Username + Password

Events appear as `calendar.hermes_calendar` entity.

## HA Todo Sync via n8n

The n8n workflow `📅 Radicale CalDAV Sync` (ID: WgmnvenaW2BYl87W) handles:
- **Every 5 min**: GET HA `/api/states` → extract `todo.*` items ↔ REPORT Radicale VTODOs → compare UIDs → push new items both ways
- **Webhook `POST /cal-add-event`**: iOS Shortcut sends JSON → n8n builds VEVENT → PUT to Radicale

Credentials needed (assign manually in n8n UI):
1. `Radicale Basic Auth` (httpBasicAuth)
2. `Home Assistant Bearer` (httpBearerAuth)

## iOS Setup

### Calendar (native)
Settings → Calendar → Accounts → Add Account → Other → CalDAV:
- Server: `cal.jefe.ovh`
- Username + Password

### Tasks (VTODO)
iOS Calendar doesn't sync VTODOs natively. Options:
- **GoodTask** (iOS, paid) — reads CalDAV tasks
- **iOS Shortcut** — POST to n8n webhook `cal-add-event` (events only, not tasks)
- **OpenTasks** (Android only)

### iOS Shortcut for Events
```
Get contents of URL: https://n8n.jefe.ovh/webhook/cal-add-event
Method: POST
Headers: Content-Type: application/json
Body: {"summary":"RDV","start":"2026-01-01T10:00:00","end":"2026-01-01T11:00:00"}
```

## HA CalDAV Native VTODO Support (iOS Reminders → HA Todo)

HA's built-in CalDAV integration does **not** only sync VEVENTs — it also exposes
VTODOs (iOS Reminders / Rappels) as `todo.*` entities. On this instance:

| iOS source          | HA entity         | Domain   | Notes                           |
|---------------------|-------------------|----------|---------------------------------|
| Calendar (VEVENT)   | `calendar.sync`   | calendar | iOS Calendar app, all-day/timed |
| Reminders (VTODO)   | `todo.rappel`     | todo     | iOS Reminders app, `needs_action` status |
| Reminders (2nd list)| `todo.utcugckg...`| todo     | Second iOS reminder list        |

supported_features for the CalDAV todo entities = 127 (full: create, update,
delete, set due date/datetime, set status). The built-in shopping list
(`todo.liste_dachats`) is only 15 (basic add/remove).

### Querying via MCP ha-mcp tools

- **List all todo lists:** `ha_get_todo()` → returns entity_id, friendly_name,
  state (item count), supported_features for each list.
- **List items in a list:** `ha_get_todo(entity_id="todo.rappel")` → returns
  summary, uid, status for each item.
- **Add item:** `ha_set_todo_item(entity_id="todo.rappel", summary="...")`
  with optional `due_datetime` / `due_date`.
- **Update status:** `ha_set_todo_item(entity_id="todo.rappel",
  item="<uid or summary>", status="completed")`.
- **Calendar events:** `ha_config_get_calendar_events(entity_id="calendar.sync",
  start=..., end=..., max_results=...)`.

### Key insight

iOS Reminders added on the iPhone appear in `todo.rappel` within the HA CalDAV
sync interval — no n8n workflow needed for the read path. The n8n workflow
documented above remains useful for bidirectional sync and webhook-based event
creation, but for simply **reading** iOS-created reminders from HA, the native
CalDAV integration + MCP tools suffice.

### Automation opportunities

HA automations can trigger on `todo.rappel` state changes (item added, item
completed, item due). Use `state_changed` trigger or `todo` domain trigger to
send push notifications via `notify.mobile_app_sm_a556e` or run scripts.