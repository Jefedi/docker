# Pangolin Event Streaming

Stream events from your organization to external destinations in real time. Sends logs as HTTP POST requests to configured endpoints.

## Configuration Location

UI only — `pangolin.jefe.ovh` → **Event Streaming** → **Add Destination**

**API limitation:** The MCP `create_org_by_orgId_event_streaming_destination` tool registers but the API path returns 404 (`Cannot PUT /v1/org/{orgId}/event-streaming-destination`). The event streaming feature must be configured via the Pangolin web UI.

## Event Types

| Type | What it contains |
|------|-----------------|
| **Access logs** | Who authenticated, login/logout, auth failures |
| **Action logs** | Admin operations (create/delete resources, modify users) |
| **Connection logs** | VPN/Newt client connections, tunnels |
| **Request logs** | HTTP request details per proxied resource |

## Recommended Integration: Pangolin → n8n → Discord

The most flexible pattern: Pangolin streams to an n8n webhook, n8n formats and forwards to Discord (or any other platform).

### Step 1 — Create n8n Webhook Workflow

Create an n8n workflow with 3 nodes:

1. **Webhook** (POST, path: `pangolin-events`) — receives the raw event
2. **Code node** (JavaScript) — formats the payload into a Discord embed
3. **Discord** (botToken, message/send) — posts to a channel

**Workflow code pattern (SDK):**

```javascript
import { workflow, node, trigger, newCredential, expr, placeholder } from '@n8n/workflow-sdk';

const webhookTrigger = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Pangolin Event',
    parameters: { httpMethod: 'POST', path: 'pangolin-events' }
  }
});

const formatMessage = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Formater message',
    parameters: {
      language: 'javaScript',
      javaScriptCode: `
const item = $input.first().json;
const body = item.body || item;
const event_type = body.type || 'unknown';
const event_action = body.action || 'unknown';
const actor = body.actor || body.actorId || 'inconnu';
const timestamp = body.timestamp || body.time || '';
const resource = body.resource || body.resourceId || body.location || 'N/A';
const details = body.details || body.message || body.description || '';

const icons = {
  access: '\u{1F511}', action: '\u{2699}\u{FE0F}', connection: '\u{1F517}',
  request: '\u{1F310}', health_check: '\u{1F49A}', site: '\u{1F3E0}',
  resource: '\u{1F4E1}', user: '\u{1F464}'
};
const icon = icons[event_type] || '\u{1F4CB}';

const colors = { access: 5793266, action: 16753920, connection: 4886754,
  request: 10181046, health_check: 5763719, site: 10070709,
  resource: 10070709, user: 14830198 };
const color = colors[event_type] || 9807270;

return [{
  json: {
    content: icon + ' **' + event_type.toUpperCase() + '** - ' + event_action,
    embeds: [{
      title: icon + ' Pangolin - ' + event_type.toUpperCase(),
      description: '**' + event_action + '** par **' + actor + '**',
      color: color,
      fields: [
        { name: '\u{1F4E1} Ressource', value: String(resource).substring(0, 250), inline: true },
        { name: '\u{1F464} Acteur', value: String(actor).substring(0, 250), inline: true },
        { name: '\u{1F550} Quand', value: String(timestamp).substring(0, 250), inline: true },
        { name: '\u{1F4DD} D\u00E9tails', value: details ? String(details).substring(0, 1000) : 'Aucun' }
      ],
      timestamp: timestamp || undefined,
      footer: { text: 'Pangolin Event Streaming' }
    }]
  }
}];`
    }
  }
});

const sendDiscord = node({
  type: 'n8n-nodes-base.discord',
  version: 2,
  config: {
    name: 'Notifier Discord',
    parameters: {
      authentication: 'botToken',
      resource: 'message', operation: 'send', sendTo: 'channel',
      guildId: { __rl: true, mode: 'id', value: 'GUILD_ID' },
      channelId: { __rl: true, mode: 'id', value: 'CHANNEL_ID' },
      content: placeholder('Content from Code node'),
      embeds: { values: [{ inputMethod: 'json', json: expr('{{ $json.embeds[0] }}') }] }
    },
    credentials: { discordBotApi: newCredential('Discord Bot') }
  }
});

export default workflow('pangolin-events', 'Pangolin Events → Discord')
  .add(webhookTrigger).to(formatMessage).to(sendDiscord);
```

### Step 2 — Get the Webhook URL

After publishing the workflow, n8n provides a URL:
`https://n8n.jefe.ovh/webhook/pangolin-events`

### Step 3 — Configure Pangolin Event Streaming

1. Go to `pangolin.jefe.ovh` → **Event Streaming** → **Add Destination**
2. **Name:** `n8n Discord` (or similar)
3. **Destination URL:** `https://n8n.jefe.ovh/webhook/pangolin-events`
4. **Authentication:** `No Authentication` (n8n webhooks are public by design)
5. Check which event types to stream (Access, Action, Connection, Request)
6. **Create Destination**

### Step 4 — Verify

The first event (any login, resource change, or connection) will appear as a Discord embed.

## Event Payload Shape

Pangolin Event Streaming sends a JSON POST with fields like:
```json
{
  "type": "access|action|connection|request",
  "action": "login|create|delete|start|stop|...",
  "actor": "username or email",
  "actorId": "internal ID",
  "timestamp": "ISO8601 timestamp",
  "resource": "target resource or subdomain",
  "resourceId": "internal resource ID",
  "details": "description of what happened",
  "location": "source IP or location",
  "method": "GET|POST|... (request logs)",
  "path": "/api/... (request logs)"
}
```

The Code node in the workflow handles field fallbacks so unknown event shapes still produce readable messages.

## Pitfalls

- **API doesn't support this programmatically** — must configure in the web UI
- **n8n webhooks are unauthenticated by default** — if the endpoint is exposed publicly, anyone who knows the URL can POST to it. For production, add a header auth check in n8n or Pangolin's Bearer Token option
- **Pangolin does not retry failed deliveries** — if the n8n webhook is down, events are lost
- **Rate of events** — on a busy Pangolin instance with request logs enabled, the Discord rate limit (5 req/s per channel) could be hit. Filter to Action + Access logs only unless you need request-level detail
