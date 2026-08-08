# iOS Pointage System

## Overview

The user has an iPhone 15 Pro Max with an Action Button configured to trigger a Cherri-compiled iOS Shortcut called "Pointage". The shortcut presents a menu of 8 clock-in events and sends them to an n8n webhook for time tracking.

## n8n Webhook Workflow

**Workflow name:** "Pointage iOS"
**Webhook URL:** `POST https://n8n.jefe.ovh/webhook/pointage`

### Nodes:
1. **Webhook Trigger** — `httpMethod: POST`, `path: 'pointage'`, `responseMode: 'responseNode'`
2. **Save Pointage (Code node)** — receives `{ event, timestamp, location }`, stores in n8n static data, sends ntfy confirmation for every event, and when event is `arrivee_boite` (or `end_journee`) builds the daily recap (hours + salary) and clears the day's entries
3. **Respond to Webhook** — returns `{ ok: true, message: "🏢 Debut journee (boite) - 06:40" }`
4. **Has Recap? (IF node)** — checks if `$json.recap` is not empty (only true when event was `arrivee_boite` or `end_journee`)
5. **Send ntfy (HTTP Request)** — sends the recap to `https://ntfy.jefe.ovh/suivi-heures` with `Authorization: Bearer <token>` header, raw text body

### Data Storage

Pointage entries are stored in n8n's `getWorkflowStaticData('global')` under a `pointages` array. Each entry: `{ event, label, timestamp, time, date, location }`. Entries are cleared after the daily recap is sent (on `arrivee_boite`).

### ntfy Notifications

**Every pointage event sends a confirmation to ntfy:**
- Title: "Pointage"
- Tags: "white_check_mark"
- Body: emoji + label + time (e.g., "🏢 Debut journee (boite) - 06:40")

**On `arrivee_boite` (or `end_journee`), the recap is sent to ntfy:**
- Title: "Recap journee"
- Tags: "chart_with_upwards_trend"
- Body: full recap with hours (boîte, client, route, pause, total) + salary breakdown

**On error, an error notification is sent to ntfy:**
- Title: "ERREUR Pointage"
- Tags: "x"
- Priority: "high"
- Body: error message + event that failed

### User Preferences (corrections from this session)

1. **Recap triggered by `arrivee_boite`, NOT `end_journee` and NOT a cron schedule** — the user rejected the 20h cron trigger because "my workday might end after 20h." The recap fires when the user clocks "🏢 Arrivée boîte" (arriving back at the box = end of workday). The `end_journee` event still works as a fallback.

2. **Send confirmation for every pointage** — "send everything to confirm, e.g. the start of the day, each step, so I know it worked, and if there's a bug it's saved in ntfy."

3. **Trajet maison→boîte NOT paid** — arriving at the box and immediately leaving doesn't count as box time. It's transit. Only time spent loading/unloading at the box counts as box time.

4. **No-client days** — if the user never visits a client (no `arrivee_client` event), all time between `start_boite` and `arrivee_boite` counts as `hBoite` (hours at the box).

5. **Recap format: totals only, no individual pointage list** — the user said "for the recap it's per day, not everything that went into it." Just show the totals (heures boîte, client, route, pause, total + salary), not the individual clock-in events.

### ntfy Auth

ntfy requires authentication. Create a token for the jefe user:
```bash
docker exec ntfy ntfy token add --label "n8n-pointage" jefe
# Output: token tk_XXXX created for user jefe
```

Use the token in the HTTP Request node headers:
```
Authorization: Bearer tk_ymabd6elb6221ay7se62esynwgq63
```

### Event labels and emojis:

```javascript
const eventLabels = {
  'start_boite': 'Debut journee (boite)',
  'start_route': 'Depart vers client',
  'arrivee_client': 'Arrivee chez le client',
  'start_pause': 'Debut de pause',
  'end_pause': 'Fin de pause',
  'start_route_retour': 'Depart vers la boite',
  'arrivee_boite': 'Arrivee a la boite',
  'end_journee': 'Fin de journee'
};

const emojis = {
  'start_boite': '🏢', 'start_route': '🚗', 'arrivee_client': '🏗️',
  'start_pause': '🍽️', 'end_pause': '▶️', 'start_route_retour': '🚗',
  'arrivee_boite': '🏢', 'end_journee': '🏠'
};
```

### Hour Calculation Logic

The recap calculates hours between consecutive pointages:

| Current Event | Next Event | Category |
|---|---|---|
| start_boite / arrivee_boite | start_route | Hours boîte (only if client visited) |
| start_boite | (any, no client visited) | Hours boîte (entire duration) |
| start_route / start_route_retour | (any) | Hours route (conducteur, ×1.25) |
| arrivee_client | start_pause / start_route_retour / arrivee_boite | Hours client |
| start_pause | (any) | Pause (deducted, not paid) |
| end_pause | start_route_retour / start_route / arrivee_boite | Hours client |

**No-client day handling:** If no `arrivee_client` event exists in the day's pointages, ALL time between `start_boite` and `arrivee_boite` counts as `hBoite`.

**Salary calculation:**
- Taux normal: 13€/h (hBoite + hClient)
- Taux route: 13€ × 1.25 = 16.25€/h (hRoute)
- Panier: 19€ if hClient > 0
- Prime 13e: (hBoite + hClient) × 1.07€/h (normal hours only, not route)
- Total = normal + route + panier + prime13e

### Known issue: ntfy not receiving notifications

As of the last session, the ntfy confirmation notifications were NOT being received by the user. The webhook execution showed success, and `curl` test worked, but the user's phone received nothing. This needs investigation:
- Check if the ntfy token is valid: `docker exec ntfy ntfy token list` and look for the `n8n-pointage` token
- Test manually: `curl -X POST https://ntfy.jefe.ovh/suivi-heures -H "Authorization: Bearer <token>" -H "Title: Test" -d "Test"`
- Check if the user's ntfy app is subscribed to the `suivi-heures` topic
- The ntfy HTTP Request node in the workflow may need authentication headers configured (the ntfy server has `auth-default-access: deny-all`)
- The ntfy notification is sent INSIDE the Save Pointage Code node via `this.helpers.httpRequest()`, AND ALSO via the separate "Send ntfy" HTTP Request node for the recap. Both need the auth token.

### Manual salary calculation from user dictation

The user often dictates their week's hours verbally (not through the pointage system). When calculating salary from dictation, these rules apply:

1. **Arrivée boîte ≠ temps boîte** — if the user arrives at the box and immediately leaves for a client, that time is NOT box time. It's transit. Only loading/unloading at the box counts as box hours.
2. **Trajet maison→boîte is NOT paid** — the commute from home to the box is never counted as work time.
3. **Recap triggered by `arrivee_boite`** — the workday ends when arriving back at the box, not when arriving home.
4. **No-client days** — if no client was visited (no `start_route`/`arrivee_client`), all time at the box counts as hBoite.
5. **Pause légale** — legally must take 30 min minimum lunch break. If user says "j'ai pris mon heure le midi", deduct 1h. If no explicit pause mentioned, deduct 30 min minimum.
6. **Prime 13e** is calculated on normal hours only (hBoite + hClient), NOT on route hours.
7. **Panier** (19€) only if the user visited a client that day.
8. **Multiple clients per day** — route between clients counts as route time. Time at each client counts as client time.
9. **Déchargement at the box** — counts as hBoite (normal rate), NOT route/sup rate.
10. **Pause réglementaire** — if the user works through a legal break period (e.g., no pause clocked but legally required), the recap must still deduct it.

## Cherri Shortcut Code

### CRITICAL: `dictGet` crashes on iOS — DO NOT USE IT

The original shortcut used `dictGet(@response, "message")` to extract the confirmation message from the webhook JSON response. This crashes on iOS with "Échec de Obtenir la valeur du dictionnaire, car Raccourcis n'a pas pu effectuer la conversion de Texte en Dictionnaire."

**Root cause:** `jsonRequest()` in Cherri may return a text representation instead of a parsed dictionary. When `dictGet` tries to extract a key from what iOS sees as a text value (not a dictionary), it crashes.

**Fix:** Remove the `dictGet` action definition and the `@message = dictGet(@response, "message")` line entirely. The n8n webhook sends the ntfy notification separately — the shortcut doesn't need to parse the response. Just show a static confirmation:

```cherri
show("✅ Pointage enregistré")
```

### Working Cherri code (v2, no dictGet):

```cherri
#include 'actions/web'
#include 'actions/calendar'

#define name "Pointage"
#define glyph clock
#define color orange

menu "Pointage" {
    item "🏢 Debut journee":
        @eventCode = "start_boite"
    item "🚗 Depart vers client":
        @eventCode = "start_route"
    item "🏗️ Arrivee client":
        @eventCode = "arrivee_client"
    item "🍽️ Debut pause":
        @eventCode = "start_pause"
    item "▶️ Fin pause":
        @eventCode = "end_pause"
    item "🚗 Depart vers boite":
        @eventCode = "start_route_retour"
    item "🏢 Arrivee boite":
        @eventCode = "arrivee_boite"
    item "🏠 Fin journee":
        @eventCode = "end_journee"
}

@now = CurrentDate
@isoDate = formatDate(@now, "Custom", "yyyy-MM-dd'T'HH:mm:ssXXX")

@response = jsonRequest("https://n8n.jefe.ovh/webhook/pointage", 'POST', {"event": "{@eventCode}", "timestamp": "{@isoDate}"}, {"Content-Type": "application/json"})

show("✅ Pointage enregistré")
```

This generates 41 actions (all valid iOS action IDs). The `dictGet` action definition and extraction are removed.

### Pitfall: dictGet in Cherri shortcuts (general)

This is not specific to the pointage shortcut. ANY Cherri shortcut that uses `jsonRequest()` + `dictGet()` to extract a field from the JSON response may crash on iOS if the response is not parsed as a dictionary. When the webhook response is not needed by the shortcut (e.g., ntfy notifications are sent server-side), skip the extraction entirely and show a static message.

## Timezone Bug (critical fix discovered in testing)

The `Save Pointage` Code node must use `timeZone: 'Europe/Paris'` in `toLocaleTimeString()`. Without it, the server's UTC timezone is used, showing times 2 hours behind real local time (e.g., user clocks in at 16:29, sees 14:29).

**Fixed code:**
```javascript
const time = date.toLocaleTimeString('fr-FR', { 
  hour: '2-digit', 
  minute: '2-digit', 
  timeZone: 'Europe/Paris' 
});
```

Even though n8n has `TZ=Europe/Paris` in its environment, `toLocaleTimeString()` inside Code nodes uses the Node.js process default which may be UTC. Always pass `timeZone` explicitly.

## Compilation

```bash
# Compile and sign via cherri-builder Docker container
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder:/work \
  --entrypoint sh \
  cherri-builder -c 'cherri /work/output/pointage.cherri --hubsign 2>&1'
```

Generates 41 actions (all valid iOS action IDs) with the v2 code (no dictGet).

## NAS Upload

```bash
# Upload to NAS via cherri-smb container
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh \
  cherri-smb -c 'cp "/work/\"Pointage\".shortcut" /work/upload.shortcut && smbclient "//100.64.0.1/raccourci_ios" -U "ax42-SMB%<password>" -c "put /work/upload.shortcut Pointage_v2.shortcut; ls" 2>&1; rm -f /work/upload.shortcut 2>/dev/null'
```

Output file: `"Pointage".shortcut` (AEA1 signed, ~24KB)

## iPhone Setup

1. Download the `.shortcut` file from NAS share `raccourci_ios`
2. Open in **Files** app → **Add Shortcut**
3. Go to **Settings → Action Button → Shortcut → Pointage**
4. Press the Action Button to trigger the menu

## ntfy Topic

The user subscribes to the `suivi-heures` topic on ntfy. All pointage confirmations and the daily recap are sent there. The user receives push notifications on their iPhone for every clock-in event.