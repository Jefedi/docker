# n8n iCal Feed — Bridge HA vers iOS Calendar

Quand un calendrier CalDAV traditionnel (Radicale, Baikal) n'est pas disponible, **n8n peut faire office de faux serveur iCal** : l'iPhone s'abonne à une URL webhook n8n qui retourne un flux iCal généré dynamiquement depuis une table de données.

## Architecture

```
Hermes → MCP HA / curl → POST n8n webhook (/webhook/add-event)
                                   ↓
                          n8n Data Table (ical_events)
                                   ↓
iPhone abonné → GET n8n webhook (/webhook/ical) → flux iCal → iOS Calendar
```

## Prérequis

- Instance n8n accessible depuis l'iPhone (URL publique ou via tunnel Pangolin, ex: `n8n.jefe.ovh`)
- API n8n MCP accessible depuis Hermes

## Mise en place

### 1. Table de données

```javascript
// Via MCP n8n
create_data_table({
  projectId: "<project_id>",
  name: "ical_events",
  columns: [
    {name: "summary", type: "string"},
    {name: "start_datetime", type: "string"},
    {name: "end_datetime", type: "string"},
    {name: "description", type: "string"},
    {name: "uid", type: "string"}
  ]
})
```

### 2. Workflow « Add Calendar Event » (POST)

Workflow n8n avec :
- **Trigger** : Webhook (POST, path: `add-event`)
- **Set node** : Normaliser les données (optional chaining sur `body.*`)
- **Data Table** : Insert row dans `ical_events`
- **Respond to Webhook** : JSON `{success: true}`

URL finale : `https://n8n.domain/webhook/add-event`

### 3. Workflow « iCal Feed » (GET)

Workflow n8n avec :
- **Trigger** : Webhook (GET, path: `ical`, responseMode: `responseNode`)
- **Data Table** : Get all rows (`returnAll: true`)
- **Code node** (JS, runOnceForAllItems) : générer le flux iCal
- **Respond to Webhook** : text/calendar + Content-Disposition

**Code JS du code node** (runOnceForAllItems) :
```javascript
const items = $input.all();
let ical = [
  'BEGIN:VCALENDAR',
  'VERSION:2.0',
  'PRODID:-//Hermes//N8N//FR',
  'CALSCALE:GREGORIAN',
  'METHOD:PUBLISH',
  'X-WR-CALNAME:Hermes Agenda',
  'X-WR-TIMEZONE:Europe/Paris'
];
for (const item of items) {
  const e = item.json;
  const startDate = (e.start_datetime || '').replace(/[-:]/g, '').split('.')[0].replace('T', 'T') + 'Z';
  const endDate = (e.end_datetime || '').replace(/[-:]/g, '').split('.')[0].replace('T', 'T') + 'Z';
  const uid = e.uid || 'event-' + e.id;
  const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  ical.push('BEGIN:VEVENT');
  ical.push('UID:' + uid);
  ical.push('DTSTART:' + startDate);
  ical.push('DTEND:' + endDate);
  ical.push('SUMMARY:' + (e.summary || 'Event').replace(/\n/g, '\\n'));
  if (e.description) ical.push('DESCRIPTION:' + e.description.replace(/\n/g, '\\n'));
  ical.push('DTSTAMP:' + now);
  ical.push('END:VEVENT');
}
ical.push('END:VCALENDAR');
return [{ json: { icalContent: ical.join('\r\n') } }];
```

**Config Respond to Webhook** :
- respondWith: `text`
- options.responseCode: `200`
- options.responseHeaders: `Content-Type: text/calendar; charset=utf-8`, `Content-Disposition: attachment; filename="hermes.ics"`

## Abonnement iPhone

1. **Réglages → Calendrier → Comptes → Ajouter → Autre → Ajouter un calendrier avec abonnement**
2. URL : `https://n8n.domain/webhook/ical`
3. Fréquence : laisser par défaut (iOS synchronise périodiquement)

## Usage quotidien

```bash
# Ajouter un event depuis Hermes (via MCP HA ou curl)
curl -X POST "https://n8n.domain/webhook/add-event" \
  -H "Content-Type: application/json" \
  -d '{"summary": "Dentiste", "start_datetime": "2026-07-16T15:00:00", "end_datetime": "2026-07-16T16:00:00", "description": "Rendez-vous dentiste"}'
```

## Pièges

- **iOS 13+ Reminders** : Apple ne supporte plus CalDAV pour les Rappels depuis iOS 13. Le flux iCal fonctionne pour le **Calendrier** iOS, PAS pour Rappels.
- **Sync non temps réel** : iOS rafraîchit les calendriers abonnés périodiquement (pas push). Compter quelques minutes de délai.
- **Workflows désactivés** : les workflows n8n doivent être **Activer** (toggle "Active" dans l'UI n8n) pour répondre aux webhooks.
- **No auth** : les webhooks sont publics par défaut. Ne pas exposer de données sensibles sans authentification.
