# RSS Curation Workflow Pattern

Pattern for building RSS aggregation + translation + AI curation workflows
that output a single RSS feed served via n8n webhook.

## RSS Feed Trigger Migration (2026-07-28)

Replaced the `scheduleTrigger` (every 2h) + 3× `rssFeedRead` pattern with
3× native `rssFeedReadTrigger` nodes. Each feed is now independently
monitored by its own trigger — n8n detects feed updates and fires the
workflow automatically, instead of polling all feeds on a fixed schedule.

### Node Type

The correct n8n node type is `n8n-nodes-base.rssFeedReadTrigger` (version 1).
The shorter name `n8n-nodes-base.rssFeedTrigger` is **rejected** by the API
with "Unrecognized node type". Always verify via `search_nodes()` first.

### Migration Operation Sequence

Using `update_workflow` with these operations (in order):

1. **Add 3 trigger nodes** (`addNode`):
   - `Trigger LoKan` → `feedUrl: "https://lokan.fr/feed"`, position [240, 80]
   - `Trigger Korben` → `feedUrl: "https://korben.info/feed"`, position [240, 304]
   - `Trigger HN` → `feedUrl: "https://news.ycombinator.com/rss"`, position [240, 528]

2. **Add connections** from each new trigger to its existing Tag node (`addConnection`):
   - `Trigger LoKan` → `Tag LoKan` (index 0)
   - `Trigger Korben` → `Tag Korben` (index 0)
   - `Trigger HN` → `Tag HN` (index 0)

3. **Remove old connections** (`removeConnection`):
   - `Every 2 Hours` → `RSS LoKan`, `RSS Korben`, `RSS Hacker News`
   - `RSS LoKan` → `Tag LoKan`, `RSS Korben` → `Tag Korben`, `RSS Hacker News` → `Tag HN`

4. **Remove old nodes** (`removeNode`):
   - `Every 2 Hours` (scheduleTrigger)
   - `RSS LoKan`, `RSS Korben`, `RSS Hacker News` (rssFeedRead)

### Parameters for rssFeedReadTrigger

```json
{
  "feedUrl": "https://example.com/feed",
  "options": {}
}
```

The `feedUrl` parameter replaces the `url` parameter used by `rssFeedRead`.
Output fields are the same as `rssFeedRead` (title, link, content,
contentSnippet, pubDate, isoDate).

### Post-Migration

- **Republish** the workflow (`publish_workflow`) — the new triggers need
  to be registered in production.
- **Editor lock**: if the workflow is open in the n8n UI, `update_workflow`
  fails with "Cannot modify workflow while it is being edited by a user".
  Ask the user to close the tab, or use `PUT /api/v1/workflows/{id}` directly.
- The downstream pipeline (Tag → Merge → Aggregate → Hermes Curation →
  Generate XML → Webhook) stays unchanged — only the trigger layer changes.

### ⚠️ CRITICAL: Multi-Trigger + Merge Anti-Pattern (2026-07-29)

The RSS Feed Trigger migration (replacing 1 scheduleTrigger + 3 rssFeedRead
with 3 rssFeedReadTrigger) **introduced a structural bug** that caused
~100% of trigger executions to fail.

**Root cause:** Each `rssFeedReadTrigger` fires in its **own independent
execution** when its feed has new items. The Merge node (3 inputs) only
combines data **within a single execution**. When only one trigger fires,
the other two inputs are empty → the Merge blocks indefinitely → the
pipeline never completes → execution shows "error" with no runData.

**Symptoms:**
- All trigger executions show `status: "error"`, duration < 1 second
- Webhook output shows stale/default data ("En attente du premier cycle")
- 100+ executions with ~0% success rate
- No error detail in execution data (the execution fails before any node runs)

**The fix:** Revert to **1 Schedule Trigger + multiple rssFeedRead (non-trigger)
nodes**. This ensures one execution reads all feeds simultaneously, and the
Merge receives all inputs together:

```
Schedule Trigger → [RSS Read LoKan, RSS Read Korben, RSS Read HN] → Merge → ...
```

**Lesson:** Never connect multiple independent trigger nodes to a single
Merge node. Triggers fire independently; Merge needs all inputs in the same
execution. Use ONE trigger + multiple read nodes instead.

### ⚠️ RSS Feed URL 301 Redirect Crash (2026-07-29)

The `rssFeedReadTrigger` node does NOT follow HTTP 301 redirects. If a feed
URL returns 301 (e.g. `https://lokan.fr/feed` → `https://lokan.fr/feed/`),
the trigger crashes silently on every poll.

**Diagnosis:**
- Executions show `status: "error"`, `mode: "trigger"`, duration < 1s, no
  runData (the execution fails before any node executes)
- Test the feed URL: `curl -sI <url>` — if you see `301` + `location:`
  header, that's the bug
- Common: WordPress sites redirect `/feed` → `/feed/` (trailing slash).
  Cloudflare-enforced redirects also cause this.

**Fix:** Use `setNodeParameter` with `path: "/feedUrl"` to update the URL
to the final destination (with trailing slash or correct path):

```javascript
mcp__n8n_mcp__update_workflow({
  workflowId: "...",
  operations: [{
    type: "setNodeParameter",
    nodeName: "Trigger LoKan",
    path: "/feedUrl",
    value: "https://lokan.fr/feed/"  // trailing slash = no redirect
  }],
  versionName: "Fix LoKan feed URL 301"
})
```

**Prevention:** Before adding an RSS feed URL to a trigger, always test with
`curl -sI <url>` to verify it returns 200 directly (not 301/302).

## Architecture (Legacy: scheduleTrigger + rssFeedRead)

The original architecture used a single schedule trigger fanning out to
3 RSS Read nodes:

```
Schedule Trigger (every 2h)
    ↓
3 parallel branches → RSS Read (lokan, korben, HN)
    ↓                       ↓
    ↓               HN → LibreTranslate (EN→FR)
    ↓                       ↓
Merge (append, 3 inputs) ←←←
    ↓
Aggregate (all items → single item with articles array)
    ↓
Code node (build prompt from articles)
    ↓
HTTP Request → LLM API (curation/selection)
    ↓
Code node (parse LLM JSON → generate RSS XML)
    ↓
$getWorkflowStaticData('global').rssXml = xml

Webhook GET /rss-curation
    ↓
Code node (read $getWorkflowStaticData('global').rssXml)
    ↓
Respond with XML (content-type: application/rss+xml)
```

## Key Design Decisions

### Static Data for XML Storage
Use `$getWorkflowStaticData('global')` to persist the generated XML between
executions. The webhook branch reads from static data — it responds instantly
without re-running the curation pipeline.

**CRITICAL**: The function is `$getWorkflowStaticData('global')` with the `$`
prefix. Calling `getWorkflowStaticData('global')` without `$` throws
`getWorkflowStaticData is not defined` in the Code node sandbox.

### Webhook Response Configuration
```json
{
  "httpMethod": "GET",
  "path": "rss-curation",
  "responseMode": "lastNode",
  "responseData": "firstEntryJson",
  "responseContentType": "application/rss+xml; charset=utf-8",
  "options": {
    "responsePropertyName": "xml"
  }
}
```

The `responsePropertyName: "xml"` tells n8n to serve the `xml` field from the
last node's output as the raw response body.

### RSS Read Node Output Fields
The `n8n-nodes-base.rssFeedRead` (v1.2) outputs items with these fields:
- `title` — article title
- `link` — article URL
- `content` — full HTML content (if available in feed)
- `contentSnippet` — plain text snippet
- `pubDate` — publication date (RFC 822 format)
- `isoDate` — ISO 8601 date

### LibreTranslate Integration
- API: `POST https://translate.jefe.ovh/translate`
- Auth: `httpQueryAuth` credential (API key as query parameter `api_key`)
- Body: `{"q": "text", "source": "en", "target": "fr", "format": "text"}`
- Response: `{"translatedText": "..."}`
- Use batching: `options.batching.batch = { batchSize: 5, batchInterval: 500 }`

### Merge Node with 3+ Inputs
When merging more than 2 branches, set `numberInputs` in the Merge node
parameters:
```javascript
merge({
  version: 3.2,
  config: {
    name: 'Merge Feeds',
    parameters: { mode: 'append', numberInputs: 3 }
  }
})
```
Default is 2 inputs. Without `numberInputs: 3`, input index 2 is silently
dropped with an `INVALID_INPUT_INDEX` validation warning.

### Credential Creation via REST API
```bash
# httpQueryAuth (for LibreTranslate API key)
curl -X POST "https://n8n.jefe.ovh/api/v1/credentials" \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"LibreTranslate API","type":"httpQueryAuth","data":{"name":"api_key","value":"..."}}'

# httpBearerAuth (for Hermes/LiteLLM API)
curl -X POST "https://n8n.jefe.ovh/api/v1/credentials" \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hermes API Bearer","type":"httpBearerAuth","data":{"token":"..."}}'
```

Then assign via `setNodeCredential` operation in `update_workflow`.

## Pitfalls Encountered

### 1. `setNodeParameter` creates nested `parameters` object
**Symptom**: `setNodeParameter` with `path: "/parameters/url"` creates a
nested `parameters.parameters.url` instead of replacing `parameters.url`.

**Fix**: Use `updateNodeParameters` with `replace: true` to set the full
parameter set. This is the only reliable way to change a single field
without breaking the node.

### 2. `localhost` ECONNREFUSED in n8n via Hermes gateway
**Symptom**: HTTP Request nodes using `http://localhost:5000/` or
`http://127.0.0.1:5000/` fail with `ECONNREFUSED` even though the service
is running and curl works from the host shell.

**Root cause**: When n8n runs via Hermes gateway (not Docker), the Node.js
process may have a different network namespace or IPv6 resolution issue.
`localhost` resolves to `::1` (IPv6) and `127.0.0.1` may not reach the
service either.

**Fix**: Use the public Pangolin URL for the service:
- LibreTranslate: `https://translate.jefe.ovh/translate`
- LiteLLM: `https://litelllm.jefe.al/v1/chat/completions`
- Hermes API: `https://hermes.jefe.al/v1/responses` (via Pangolin, Bearer token)

### 3. `$getWorkflowStaticData` requires `$` prefix
**Symptom**: `getWorkflowStaticData is not defined [line 1]` in Code node.

**Fix**: Use `$getWorkflowStaticData('global')` with the `$` prefix.
The function is a built-in variable, not a global function.

### 4. LLM API response parsing
The Hermes API (`/v1/responses`) returns:
```json
{
  "output": [
    { "type": "message", "content": [{ "type": "output_text", "text": "..." }] }
  ]
}
```
Extract the text from `output[0].content[0].text`, then parse as JSON.
Always include a fallback regex extraction `text.match(/\{[\s\S]*\}/)` in
case the LLM wraps the JSON in markdown code fences.

### 5. XML escaping in Code node
When generating RSS XML in a Code node, escape `&`, `<`, `>` in all
user-provided content:
```javascript
function esc(s) {
  return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
```

### 6. Pangolin SSO blocks Hermes API Bearer token (2026-07-28)
**Symptom**: The Hermes Curation HTTP Request node (`https://hermes.jefe.al/v1/responses`)
returns HTTP 302 redirect to `/login` instead of the API response.

**Root cause**: Pangolin SSO (Platform SSO) is enabled by default on public
resources. It intercepts all requests and redirects unauthenticated ones to
`/login` — BEFORE the request reaches the Hermes backend. The Bearer token
in the n8n credential (`Hermes API Bearer`) never arrives at Hermes' own
auth layer (`API_SERVER_KEY`).

**Diagnosis**:
1. `curl -s -H "Authorization: Bearer <token>" http://localhost:9119/v1/responses`
   works → Hermes API is fine
2. `curl -sv https://hermes.jefe.al/v1/responses` with same token returns
   302 → `/login?next=...` → Pangolin SSO is intercepting

**Fix**: Disable SSO on the `hermes.jefe.al` resource in the Pangolin
dashboard. The Hermes API has its own Bearer token auth — SSO is redundant
and breaks programmatic access. This applies to any API endpoint exposed
via Pangolin that has its own auth layer.

**Alternative**: Use `http://localhost:9119` directly in the n8n node URL
(both n8n and Hermes are on the same machine). This bypasses Pangolin entirely.

### 7. LibreTranslate manual testing — API key in body, not headers
When testing the Translate HN node's backend with curl, the LibreTranslate
API key must go in the **request body** as `api_key`, NOT in an
`Authorization` header:

```bash
# CORRECT
curl -X POST https://translate.jefe.ovh/translate \
  -H "Content-Type: application/json" \
  -d '{"q":"Hello","source":"en","target":"fr","format":"text","api_key":"KEY"}'

# WRONG — returns "Please contact the server operator to get an API key"
curl -H "Authorization: Api-Key KEY" ...
```

The n8n `httpQueryAuth` credential handles this correctly (passes key as
query parameter). Only manual curl testing is affected.