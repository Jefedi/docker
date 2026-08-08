# n8n Code Node Binary Data Patterns

Lessons from building the Feuille Journalière workflow (sessions 2026-08-06 and 2026-08-07).
Three bugs in one session — all related to binary data handling in n8n Code nodes.

## Bug 1: `$items.all()` does not exist

**Error:** `TypeError: $items.all is not a function`

**Wrong:**
```javascript
const items = $items.all();
const item = items[0];
```

**Right:**
```javascript
const item = $input.first();
// or for multiple items:
const items = $input.all();
```

`$items` is not a valid n8n expression in Code nodes. Use `$input` instead.

## Bug 2: `item.binary.data` is NOT raw bytes in filesystem-v2 mode

**Error:** `Cannot decode file 'filesystem-v2'` (from downstream API receiving a filesystem reference string instead of base64)

**Wrong:**
```javascript
const binaryData = item.binary.data;
const base64 = Buffer.from(binaryData).toString('base64');
// OR
const base64 = item.binary.data.data;
// → returns "filesystem-v2://..." string, NOT actual base64
```

**Right:**
```javascript
const buffer = await this.helpers.getBinaryDataBuffer(itemIndex, 'data');
const base64 = buffer.toString('base64');
```

n8n self-hosted uses `filesystem-v2` binary storage by default. The `.data` property
of a binary item contains a filesystem reference, not the actual data. You MUST use
`getBinaryDataBuffer()` to read the real Buffer.

## Bug 3: Binary data lost when passing through non-binary nodes

**Error:** `This operation expects the node's input data to contain a binary file 'data', but none was found`

**Cause:** An HTTP Request node (e.g., Mistral OCR API call) returns only JSON — no binary.
A downstream Code node that does `item.binary` has nothing to pass through.

**Fix:** Reference binary data from an earlier node that still has it:
```javascript
// Get binary from an earlier node (not from the immediate input)
const binaryRef = $('Convert to Base64').item.binary;

return [{
  json: { ... },
  binary: binaryRef  // pass binary through to downstream nodes
}];
```

## Bug 4: Paperless-ngx multipart upload needs formBinaryData

**Error:** `Bad request - please check your parameters` / `Cannot decode file`

**Wrong** (plain text parameter):
```json
{"name": "document", "value": "data"}
```

**Right** (binary parameter):
```json
{
  "name": "document",
  "parameterType": "formBinaryData",
  "inputDataFieldName": "data",
  "isFile": true
}
```

The HTTP Request node's multipart body must use `formBinaryData` type with
`inputDataFieldName` pointing to the binary property name, and `isFile: true`.

## Telegram Node Discriminators

When creating Telegram Send Message nodes via SDK code or `update_workflow`:

For `telegram` node **typeVersion 1.2**, use `resource: "chat"` (NOT `"message"`):
```json
{
  "resource": "chat",
  "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
  "text": "...",
  "appendAttribution": false
}
```

Using `resource: "message"` causes: `Invalid value for "parameters.resource": got "message", expected one of: "chat"`.
For older typeVersions, `"message"` may work — always check the node's typeVersion first.

Missing `resource` causes validation warnings and non-functional nodes.

## Telegram Trigger Photo Download

Set `additionalFields.download: true` on the Telegram Trigger to receive photo
binary data. Without this, the trigger fires for messages but no binary data
is available downstream.

## Telegram Document (PDF) Support

The Telegram Trigger with `download: true` downloads both photos AND documents. But:

1. **The IF filter must accept both** — `$json.message.photo` only matches photos. PDFs arrive as `$json.message.document`. Use OR conditions:
   - Condition 1: `$json.message.photo` is not empty (array)
   - Condition 2: `$json.message.document` is not empty (object)

2. **Binary key name may differ** — for photos, the binary property is typically `data`. For documents, it may be under a different key. Auto-detect:
   ```javascript
   const binaryKeys = Object.keys(item.binary || {});
   const binaryKey = binaryKeys.length > 0 ? binaryKeys[0] : 'data';
   const buffer = await this.helpers.getBinaryDataBuffer(0, binaryKey);
   const mimeType = item.binary[binaryKey]?.mimeType || 'image/jpeg';
   ```

3. **Mistral OCR accepts PDFs** — send `data:application/pdf;base64,...` in the `image_url.url` field. Despite the field name, the OCR API handles PDFs natively. Multi-page PDFs return multiple `pages[]` entries.

## HTTP Request → Code Node Replacement Pattern

When an HTTP Request node's `jsonBody` contains a n8n expression (`={...}`) with dynamic data,
n8n validates JSON before expression evaluation. This causes silent failures:
`"The value in the JSON Body field is not valid JSON"` in docker logs, no execution in n8n UI.

Replace with a Code node using `this.helpers.httpRequest()`:

```javascript
// Code node: call external API with dynamic payload
const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
const base64 = buffer.toString('base64');

const response = await this.helpers.httpRequest({
  method: 'POST',
  url: 'https://api.mistral.ai/v1/ocr',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer wtSi9Bn7...'
  },
  body: JSON.stringify({
    model: 'mistral-ocr-latest',
    document: {
      type: 'image_url',
      image_url: { url: 'data:image/jpeg;base64,' + base64 }
    }
  }),
  json: true,  // auto-parse response as JSON
  timeout: 30000
});

return [{
  json: { ocr_markdown: response.pages[0].markdown, photo_base64: base64 },
  binary: $input.first().binary  // preserve binary for downstream nodes
}];
```

**Key points**:
- `this.helpers.httpRequest()` accepts `{ method, url, headers, body, json: true, timeout }`
- `json: true` auto-parses the response body as JSON
- `body` must be a string (use `JSON.stringify()`)
- Preserve binary by passing `$input.first().binary` to the output
- **Check ALL HTTP Request nodes in the pipeline** — if one has this bug, others likely do too
- The `HARDCODED_CREDENTIALS` validation warning when hardcoding auth headers is non-blocking