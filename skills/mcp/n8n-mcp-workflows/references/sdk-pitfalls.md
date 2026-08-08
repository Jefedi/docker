# n8n Workflow SDK & MCP — Known Pitfalls

Lessons learned from building n8n workflows via the Workflow SDK and MCP tools. Add new entries here as you discover them.

---

## Pitfall 1: Code Node jsCode vs javaScriptCode

**Symptom**: ERR_ASSERTION "Unknown error" on execution. The node shows `jsCode: ""` in the execution stack even though you set code via the SDK.

**Root Cause**: The Code v2 node with `language: 'javaScript'` reads the **`jsCode`** parameter at runtime, but the Workflow SDK generates **`javaScriptCode`**. When both exist (SDK creates javaScriptCode, your update adds jsCode), n8n picks `jsCode` — which is empty.

**Fix**:
```
updateNodeParameters → {replace: true, parameters: {language: 'javaScript', jsCode: '...your code...'}}
→ Publish workflow
```

**Prevention**: When creating Code nodes via SDK, use `jsCode` in the parameters, not `javaScriptCode`.

```javascript
// SDK code — correct
const formatNode = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Formatter',
    parameters: {
      language: 'javaScript',
      jsCode: 'return [{json: {content: "hello"}}];'
    }
  }
});
```

---

## Pitfall 2: Discord v2 Node Embed JSON

**Symptom**: `"[object Object]" is not valid JSON` error on Discord node.

**Root Cause**: The Discord node's embed `json` field with `inputMethod: 'json'` expects a **JSON string**, not a JavaScript object. `={{ $json.embeds[0] }}` evaluates to `[object Object]` which `JSON.parse()` rejects.

**Fix options**:
1. **Stringify** in Code node:
   ```javascript
   // Code node output
   return [{ json: { embedJson: JSON.stringify(embed) } }];
   // Discord node embed json field:
   // ={{ $json.embedJson }}
   ```

2. **Skip embeds** — put all content in the `content` field with markdown formatting. Simpler, no JSON issues.

---

## Pitfall 3: Must Publish After SDK/Update

**Symptom**: You update a workflow via SDK or MCP tools, the UI shows the new config, but the webhook still runs old code.

**Root Cause**: SDK/MCP tools create/update the **draft** version. The webhook execution uses the **activeVersionId**. Publishing a new version is a separate step.

**Always**:
```
1. n8n_create_workflow / n8n_update_partial_workflow → draft updated
2. n8n_workflow_versions({id, action: "publish"}) OR activateWorkflow operation → active version = draft
3. Test via webhook call + check execution details
```

---

## Pitfall 4: Webhook Body is an Array (not Object)

**Symptom**: Code node receives unexpected data shape.

**Root Cause**: Some services (like Pangolin Event Streaming) send webhook payloads as a **JSON array** (`[{...}, {...}]`), not a single object. The webhook node wraps this under `$json.body` as the array, not `$json.body.field`.

**Fix**: Always handle both cases:
```javascript
const body = $input.first().json.body || $input.first().json;
const items = Array.isArray(body) ? body : [body];
// Now process each item...
```

---

## Pitfall 6: setNodeParameter Creates Nested parameters Object

**Symptom**: You use `setNodeParameter` with `path: "/parameters/url"` to
change a node's URL, but the node still uses the old URL at runtime.

**Root Cause**: `setNodeParameter` with a JSON Pointer path like
`/parameters/url` creates a nested `parameters.parameters.url` field inside
the existing `parameters` object, instead of replacing `parameters.url`.
The original `url` field remains untouched.

**Fix**: Use `updateNodeParameters` with `replace: true` to set the full
parameter set:

```javascript
// ❌ Wrong — creates parameters.parameters.url
setNodeParameter({
  nodeName: 'My Node',
  path: '/parameters/url',
  value: 'http://new-url.com'
})

// ✅ Correct — replaces entire parameters object
updateNodeParameters({
  nodeName: 'My Node',
  replace: true,
  parameters: {
    method: 'POST',
    url: 'http://new-url.com',
    // ... include ALL other parameters
  }
})
```

## Pitfall 7: $getWorkflowStaticData Requires $ Prefix

**Symptom**: `getWorkflowStaticData is not defined [line 1]` error in
Code node execution.

**Root Cause**: The function is accessed as a built-in variable
`$getWorkflowStaticData`, not as a global function. Calling it without
the `$` prefix fails.

**Fix**:
```javascript
// ❌ Wrong
const staticData = getWorkflowStaticData('global');

// ✅ Correct
const staticData = $getWorkflowStaticData('global');
staticData.rssXml = xml;
```

## Pitfall 8: localhost ECONNREFUSED in n8n via Hermes Gateway

**Symptom**: HTTP Request nodes using `http://localhost:PORT/` or
`http://127.0.0.1:PORT/` fail with `ECONNREFUSED` even though the service
is running and `curl` works from the host shell.

**Root Cause**: When n8n runs via Hermes gateway (not in Docker), the
Node.js process may not share the same network loopback as the host shell.
`localhost` also resolves to `::1` (IPv6) which many services don't listen
on.

**Fix**: Use the public Pangolin URL for all internal services:
- LibreTranslate: `https://translate.jefe.ovh/translate`
- LiteLLM: `https://litelllm.jefe.al/v1/chat/completions`
- n8n itself: `https://n8n.jefe.ovh/webhook/...`

Do NOT use `localhost`, `127.0.0.1`, or `0.0.0.0` in n8n HTTP Request
node URLs when n8n runs via Hermes gateway.

---

## Pitfall 9: respondToWebhook `respondWith: 'json'` Returns Default Placeholder

**Symptom**: A `respondToWebhook` node with `respondWith: 'json'` and
`options: {}` returns `{"myField":"value"}` (n8n's default placeholder)
instead of the actual data from the preceding node.

**Root Cause**: `respondWith: 'json'` without a `responseBody` expression
returns n8n's built-in default JSON, NOT the upstream node's output. Unlike
`respondWith: 'allEntries'` (which returns all upstream items), `'json'`
requires an explicit `responseBody`.

**Fix**: Use `respondWith: 'text'` with an explicit `responseBody` expression
and set the Content-Type header:

```javascript
// For JSON API responses:
respondWith: 'text',
responseBody: '={{ JSON.stringify($json) }}',
options: {
  responseHeaders: {
    entries: [{ name: 'Content-Type', value: 'application/json' }]
  }
}

// For simple success responses:
respondWith: 'text',
responseBody: '={{ JSON.stringify({ success: true }) }}',
options: {}
```

For HTML responses, use `respondWith: 'text'` with
`responseBody: expr('{{ $json.html }}')` and
`Content-Type: text/html; charset=utf-8`.

**Avoid `respondWith: 'allEntries'`**: It seems like it should return all
upstream items as JSON, but in practice it returns empty or unpredictable
results when used via `updateNodeParameters` with `replace: true`. The
validator also warns `Must be an n8n expression (={{...}})` when set as a
plain string. Stick with `respondWith: 'text'` + `JSON.stringify()`.

---

## Pitfall 10: Data Table Upsert `$json.body.*` INVALID_EXPRESSION_PATH Warnings

**Symptom**: When a Data Table upsert node maps columns from webhook body
fields (`{{ $json.body.field_name }}`), the SDK validator emits
`INVALID_EXPRESSION_PATH` warnings: "uses $json.body.field_name but no
predecessor outputs this field."

**Root Cause**: The validator checks if the immediate predecessor node
outputs the referenced fields. In a webhook → upsert chain, the predecessor
is the webhook trigger, whose `output` sample data doesn't include all
possible body fields.

**Fix**: These warnings are **harmless and expected** for webhook-to-Data
Table mappings. The expressions work correctly at runtime — the webhook
body contains the fields. Do NOT try to fix them by adding fields to the
trigger's `output` sample or changing the expression. Simply proceed with
workflow creation and publishing.

---

## Pitfall 5: updateNodeParameters replace=true Wipes Parameters

**Symptom**: After updating a Discord node with `replace: true`, the node loses its `resource`, `operation`, and other discriminator parameters, causing validation warnings.

**Root Cause**: `replace: true` replaces the ENTIRE `parameters` object. You must include ALL required parameters, including discriminators like `resource`, `operation`, `sendTo`, etc.

**Fix**: Always include the full parameter set when using `replace: true`:
```javascript
// ❌ Wrong — loses operation/resource
updateNodeParameters({
  nodeName: 'Discord',
  parameters: { content: '={{ $json.content }}' },
  replace: true
})

// ✅ Correct — includes all discriminators
updateNodeParameters({
  nodeName: 'Discord',
  parameters: {
    authentication: 'botToken',
    resource: 'message',
    operation: 'send',
    sendTo: 'channel',
    guildId: { __rl: true, mode: 'id', value: 'guild-id' },
    channelId: { __rl: true, mode: 'id', value: 'channel-id' },
    content: '={{ $json.content }}'
  },
  replace: true
})
```

---

## Pitfall 11: Iterative HTML Update — Must Restore `__DATA_PLACEHOLDER__`

**Symptom**: After fetching the live HTML from a production webhook to
iterate on it, regenerating the jsCode, and pushing it back, the page
shows stale/hardcoded data that never updates — even though new entries
are being saved to the Data Table.

**Root Cause**: When you `curl` the live page, the `__DATA_PLACEHOLDER__`
token has already been replaced with actual base64-encoded data by the
Code node at runtime. If you embed this "frozen" HTML back into the
jsCode without restoring the placeholder, the `.replace()` call at the
end of the jsCode finds no placeholder to replace — the page permanently
shows the data from the moment you fetched it.

**Fix**: After fetching the live HTML, use regex to restore the
placeholder before any modifications:

```python
import re
html = re.sub(
    r'(type=\\"application/json\\">)[^<]+(</script>)',
    r'\1__DATA_PLACEHOLDER__\2',
    html
)
assert '__DATA_PLACEHOLDER__' in html, "Placeholder not restored!"
```

**Prevention**: When iterating on a deployed web app, always check for
`__DATA_PLACEHOLDER__` in the final jsCode before pushing. If it's
missing, the data injection is broken.

---

## Pitfall 12: Apostrophes in Single-Quoted JS Strings Inside jsCode

**Symptom**: The web app page loads (HTTP 200, non-zero size) but no
JavaScript runs — buttons do not work, views do not render, the page
appears dead. `node -e "new Function(code)"` reports
`Unexpected identifier` on a French accented character like `à`.

**Root Cause**: When a Code node `jsCode` builds HTML strings using
single-quoted JS strings (e.g.
`html += '...(jusqu'à 35h/sem)<br>'`), any apostrophe inside the
single-quoted string terminates it early. The text after the apostrophe
becomes an unexpected identifier.

This is basic JS escaping but easy to miss in large generated HTML.
`updateNodeParameters` complicates it further: `replace: false` may
merge old and new code, while `replace: true` may strip or double
backslash escapes. The locally-validated jsCode and the stored jsCode
can diverge.

**Fix options** (in order of reliability):

1. **Remove apostrophes from JS-generated text entirely** (most robust):
   - `jusqu'à` → `max` (e.g. "max 35h/sem")
   - `Taux appliqués` → `Taux appliques`
   - `Total cumulé` → `Total cumule`
   - `au-delà` → `au-dela`

2. **Use double-quoted JS strings** for lines containing apostrophes
   (requires escaping double quotes in HTML attributes).

3. **Backslash-escape** (`jusqu\\'à`) — fragile through
   `updateNodeParameters`. Always verify stored code after pushing.

**Prevention**: After every jsCode update, verify the ACTUAL served JS:
```bash
curl -s http://localhost:5678/webhook/PATH > /tmp/page.html
node -e "
const fs = require('fs');
const html = fs.readFileSync('/tmp/page.html', 'utf8');
const m = html.match(/<script>\n([\s\S]*?)<\/script>/);
if (m) { try { new Function(m[1]); console.log('JS OK'); }
catch(e) { console.log('JS ERROR:', e.message); } }
"
```
This checks the served JS, not the locally-generated version which may
differ after `updateNodeParameters` escaping.

---

## Pitfall 13: Data Table Delete Operation is `deleteRows` not `delete`

**Symptom**: Workflow validation reports:
`Invalid value for "parameters.operation": got "delete", expected one
of: "deleteRows"`

**Root Cause**: The Data Table node's delete operation is named
`deleteRows`, not `delete`.

**Fix**:
```javascript
parameters: {
  resource: 'row',
  operation: 'deleteRows',  // NOT 'delete'
  dataTableId: { __rl: true, mode: 'name', value: 'my_table' },
  matchType: 'allConditions',
  filters: { conditions: [{ keyName: 'date', condition: 'eq', keyValue: expr('{{ $json.body.date }}') }] },
  options: {}
}
```

---

## Pitfall 14: `updateNodeParameters` replace=false Merges jsCode

**Symptom**: After updating a Code node's `jsCode` with
`replace: false`, the node still runs old code or fails with a syntax
error. The new jsCode was appended to or merged with the old one.

**Root Cause**: `replace: false` (the default) deep-merges parameters.
For `jsCode` (a string field), this can result in the old code
persisting alongside or instead of the new code. Unicode escapes
(`\ud83d`) may also be converted to literal characters differently
than expected.

**Fix**: Use `replace: true` when updating `jsCode` to fully replace
all parameters:
```javascript
updateNodeParameters({
  nodeName: 'Build Page',
  replace: true,
  parameters: {
    mode: 'runOnceForAllItems',
    jsCode: '...new code...'
  }
})
```
⚠️ `replace: true` wipes ALL parameters — include `mode` and any other
required fields. After pushing, verify with `get_workflow_details` +
`node -e` syntax check on the stored jsCode.

---

## Pitfall 15: `jsonBody` Empty String Breaks GET Requests on Catch-All Tools

**Symptom**: A catch-all HTTP Request Tool with
`jsonBody: '={{ $fromAI("body", "...") }}'` fails on every GET request
with:
```
NodeOperationError: The value in the "JSON Body" field is not valid JSON
Details: Unexpected end of JSON input
```

**Root Cause**: The LLM sends `""` for the `body` parameter on GET
requests (no body needed). `jsonBody` tries to parse `""` as JSON and
fails — `""` is not valid JSON (`{}` would be, but the LLM sends an
empty string).

**Fix**: Append `|| "{}"` to the expression so empty input falls back
to a valid empty JSON object:
```
={{ $fromAI("body", "Request body as JSON for POST/PUT operations. Empty for GET requests.") || "{}" }}
```

This is universal — any catch-all tool that has `sendBody: true` +
`specifyBody: "json"` + `$fromAI("body")` needs this fallback, even if
the tool is primarily for GET requests.

---

## Pitfall 16: PUT `/api/v1/workflows/{id}` Rejects `description: null`

**Symptom**: `PUT /api/v1/workflows/{id}` returns 400:
```
request/body/description must be string
```

**Root Cause**: n8n stores `description: null` on workflows created
without a description. The GET response includes `description: null`.
When you strip metadata fields for PUT but leave `description` as `null`,
the API rejects it — it must be a string (empty string is fine).

**Fix**: Always set `wf['description'] = ''` (or a real description)
before PUT, alongside stripping the other forbidden fields:
```python
for field in ['id', 'versionId', ...]:
    wf.pop(field, None)
wf['description'] = ''  # null → empty string
```

This is NOT in the existing "PUT field restrictions" list because
`description` is a top-level string field, not a forbidden field — it
just can't be `null`.
