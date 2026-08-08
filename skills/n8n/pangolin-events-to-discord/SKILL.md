---
name: pangolin-events-to-discord
description: Workflow n8n qui reçoit les events Pangolin Event Streaming (Tableau JSON) et les affiche dans Discord via un embed groupé par host.
---

# Pangolin Events → Discord (n8n)

## Prérequis
- n8n avec accès Discord Bot
- Pangolin Event Streaming configuré en mode **Tableau JSON**
- Credential Discord Bot Token dans n8n

## Structure du workflow

### 1. Pangolin Event (Webhook)
- **Type**: Webhook node (POST)
- **Path**: `/webhook/pangolin-events`
- **Response**: "Workflow got started."
- Pangolin POSTe sur cette URL avec le streaming configuré

### 2. Formater message (Code node)
Itère sur le tableau d'events Pangolin, groupe par host, génère un embed Discord.

```javascript
const items = $input.all();
const events = items[0].json.body;

if (!Array.isArray(events) || events.length === 0) {
  return [{ json: { content: '✅ Aucun événement' } }];
}

const methodMeta = {
  GET:    { emoji: '📥', color: 3447003 },
  POST:   { emoji: '📤', color: 3066993 },
  PUT:    { emoji: '📝', color: 15844367 },
  PATCH:  { emoji: '🔧', color: 16744448 },
  DELETE: { emoji: '🗑️', color: 15158332 },
  HEAD:   { emoji: '👀', color: 10181046 },
};

// Grouper par host
const hosts = new Map();
for (const e of events) {
  const d = e.data || {};
  const host = d.host || '?';
  if (!hosts.has(host)) hosts.set(host, { methods: {}, ips: new Set(), locs: new Set(), count: 0, paths: new Set() });
  const h = hosts.get(host);
  h.count++;
  const m = (d.method || '?').toUpperCase();
  h.methods[m] = (h.methods[m] || 0) + 1;
  if (d.ip) h.ips.add(d.ip);
  if (d.location) h.locs.add(d.location);
  if (d.path) h.paths.add(d.path);
}

// Construire les fields de l'embed (un par host)
const fields = [];
let worstColor = 3447003; // blue par défaut
for (const [host, info] of hosts) {
  const methodSummary = Object.entries(info.methods)
    .sort((a, b) => b[1] - a[1])
    .map(([m, c]) => {
      const meta = methodMeta[m] || { emoji: '🔑', color: 9478874 };
      if (meta.color < worstColor) worstColor = meta.color;
      return `${meta.emoji} **${m}** ×${c}`;
    })
    .join(' · ');
  const locs = [...info.locs].filter(Boolean).join(', ');
  const extra = locs ? ` 🌍 ${locs}` : '';
  fields.push({
    name: `${host} (${info.count})`,
    value: `${methodSummary}${extra}`.substring(0, 1024),
    inline: true
  });
}

// Compter les IPs uniques
const allIps = new Set();
for (const [, info] of hosts) for (const ip of info.ips) allIps.add(ip);

const embed = {
  title: '📊 Pangolin Events',
  description: `${events.length} requêtes · ${allIps.size} IPs · ${hosts.size} services`,
  color: worstColor,
  fields: fields.slice(0, 25),
  footer: { text: `Streaming Pangolin · ${new Date().toISOString().substring(0, 19)}Z` },
  timestamp: new Date().toISOString()
};

return [{ json: { content: '', embed } }];
```

### 3. Notifier Discord (Discord node)
- **Resource**: Message
- **Guild ID**: ID du serveur Discord
- **Channel ID**: ID du channel cible
- **Content**: `={{ $json.content }}`
- **Embeds**: `={{ [$json.embed] }}`

## Format des events Pangolin (Tableau JSON)
```json
[{
  "event": "request",
  "timestamp": "2026-06-14T13:32:57.000Z",
  "data": {
    "id": 10848359,
    "orgId": "jorganisation",
    "action": true,
    "reason": 101,
    "resourceId": 3,
    "ip": "37.27.126.113",
    "location": "FI",
    "originalRequestURL": "https://jflix.jefe.al/Sessions",
    "host": "jflix.jefe.al",
    "path": "/Sessions",
    "method": "GET"
  }
}]
```

## Pitfalls
- **Ne pas utiliser `$input.first()`** — le body est un Array, pas un objet. Il faut itérer.
- **Champs inexistants dans les events Pangolin** : `actor`, `type`, `resource`, `details`, `description` sont absents ou null. Toujours mapper `data.host`, `data.method`, `data.path`, `data.ip`, `data.location`.
- **Limite embed Discord** : max 25 fields, 1024 chars par value, 6000 chars total. Le code `.slice(0, 25)` protège les fields.
- **Couleur** : la bordure de l'embed prend la couleur de la méthode la plus "critique" (DELETE < PATCH < POST < GET).
- **Pangolin event streaming** peut envoyer jusqu'à ~50 events par batch toutes les 30s. Le groupement par host évite le spam Discord.
