# Webhook Payload Field Audit

When an n8n webhook produces garbage output (fallback values like "inconnu", "N/A", "Aucun"), the Code node is referencing wrong field paths. This reference shows how to audit and fix such mismatches.

## Audit Procedure

1. Get raw execution data:
```python
mcp_n8n_mcp_get_execution(
    workflowId="<id>",
    executionId="<id>",
    includeData=True,
    nodeNames=["<WebhookNodeName>"],
    truncateData=1
)
```

2. Locate the `body` field in the output — this is what the webhook received.
3. Compare its structure against what the Code node expects.

## Pangolin Event Streaming Format

Pangolin's event streaming sends batch POSTs as a **JSON array** to the configured webhook URL.

### Full Payload Shape

```json
[
  {
    "event": "request",
    "timestamp": "2026-06-14T13:32:57.000Z",
    "data": {
      "id": 10848359,
      "timestamp": 1781443977,
      "orgId": "jorganisation",
      "action": true,
      "reason": 101,
      "actorType": null,
      "actor": null,
      "actorId": null,
      "resourceId": 3,
      "siteResourceId": null,
      "ip": "37.27.126.113",
      "location": "FI",
      "userAgent": null,
      "metadata": null,
      "headers": null,
      "query": null,
      "originalRequestURL": "https://jflix.jefe.al/Sessions",
      "scheme": "",
      "host": "jflix.jefe.al",
      "path": "/Sessions",
      "method": "GET",
      "tls": true
    }
  }
]
```

### Field Mapping Table (Code → Pangolin)

| Code expects | Pangolin provides | Notes |
|---|---|---|
| `body.type` | `event` ("request") or not present | Always "request" for HTTP events |
| `body.actor` | `data.ip` + `data.location` | `actor` is always `null` |
| `body.resource` | `data.host` + `data.path` | `resourceId` is numeric only |
| `body.resourceId` | `data.resourceId` (number) | Not human-readable |
| `body.timestamp` | `timestamp` (ISO string) | Direct match |
| `body.details` / `body.message` | `data.originalRequestURL` | Full request URL |
| `body.description` | None | Not provided by Pangolin |

### Key Quirks

- **`actor` is always `null`** — Pangolin request events don't track authenticated users
- **`data.ip` and `data.location`** are the best proxy for "who": IP + 2-letter country code
- **`data.originalRequestURL`** is the richest single field — full URL including scheme+host+path+query
- **All request events have `action: true`** (meaning the request was allowed) and `reason: 101`
- **No event type differentiation** — every HTTP request triggers `event: "request"` regardless of resource/status

### JavaScript Code Node Fix

```javascript
// Run Once for All Items mode
const input = $input.first().json;
const events = Array.isArray(input.body) ? input.body : [input.body];

const results = events.map((evt, index) => {
  const d = evt.data || {};
  return {
    json: {
      method: d.method || 'GET',
      host: d.host || 'N/A',
      path: d.path || '/',
      ip: d.ip || '',
      location: d.location || '',
      url: d.originalRequestURL || '',
      timestamp: evt.timestamp || ''
    },
    pairedItem: { item: index }
  };
});

return results;
```
