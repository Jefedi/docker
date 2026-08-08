# Pangolin Event Streaming — Payload Reference

When Pangolin Event Streaming sends events to a webhook destination, the payload is a **JSON array** (not a single object):

```json
[
  {
    "event": "request",
    "timestamp": "2026-06-14T11:52:37.000Z",
    "data": {
      "id": 10836644,
      "timestamp": 1781437957,
      "orgId": "jorganisation",
      "action": true,
      "reason": 101,
      "actorType": null,
      "actor": null,
      "actorId": null,
      "resourceId": 10,
      "siteResourceId": null,
      "ip": "37.27.126.113",
      "location": "FI",
      "userAgent": null,
      "metadata": null,
      "headers": null,
      "query": null,
      "originalRequestURL": "https://example.com/",
      "scheme": "",
      "host": "example.com",
      "path": "/",
      "method": "GET",
      "tls": true
    }
  },
  ...
]
```

## Event Types

| event field | Description |
|-------------|-------------|
| `request` | HTTP request log (every request through Pangolin proxy) |
| `access` | Authentication/access event |
| `action` | Admin/config change action |
| `connection` | VPN/connection event |
| `health_check` | Health check result |

## Key Data Fields

| Field | Description |
|-------|-------------|
| `data.id` | Unique event ID |
| `data.orgId` | Organization (always `jorganisation` for Jefe) |
| `data.reason` | HTTP status code (101=200, 302=redirect, etc.) |
| `data.resourceId` | Pangolin resource ID |
| `data.ip` | Client IP |
| `data.location` | 2-letter country code (FI, FR, DE, etc.) |
| `data.originalRequestURL` | Full URL that was accessed |
| `data.method` | HTTP method (GET, POST, etc.) |
| `data.tls` | Whether connection was TLS |

## n8n Handling

In n8n, the webhook node wraps this under `$json.body`. Since it's an array, the simplest approach is to use the Code node to process items:

```javascript
const items = $input.first().json.body;
if (Array.isArray(items)) {
  for (const item of items) {
    // Process each event
    const event = item.event;
    const url = item.data?.originalRequestURL;
    // ...
  }
}
```

## Discord Output (Simplified)

For minimal intervention, skip Discord embeds and just send formatted text:

```javascript
const body = $input.first().json.body;
if (!Array.isArray(body)) return [];
// Take latest event or aggregate
const last = body[body.length - 1];
const msg = `🔑 **${last.event.toUpperCase()}**\\n👤 ${last.data.ip}\\n📡 ${last.data.originalRequestURL}\\n🕐 ${last.timestamp}`;
return [{ json: { content: msg.substring(0, 2000) } }];
```
