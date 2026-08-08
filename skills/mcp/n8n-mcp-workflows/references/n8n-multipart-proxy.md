# n8n Webhook as Multipart Proxy for iOS Shortcuts

iOS Shortcuts (compiled via Cherri) can only send JSON via `jsonRequest()` — no multipart/form-data.
This reference documents the n8n webhook proxy pattern for bridging to APIs that require multipart uploads.

## Architecture

```
iOS Shortcut                  n8n Webhook                    LibreTranslate
─────────────                 ─────────────                   ──────────────
selectFile()                  Webhook Trigger                /translate_file
base64Encode()        ──JSON──► Decode Base64 (Code)         (multipart/form-data)
jsonRequest()                 HTTP Request (formBinaryData)  ──multipart──►
                     ◄──JSON──  Download (HTTP Request)
                              Encode Response (Code)
                              Respond to Webhook
```

## Workflow Structure (5 nodes)

### 1. Webhook Trigger
- Method: POST, Path: `translate-file`
- `responseMode: "responseNode"` (must use Respond to Webhook node)

### 2. Decode Base64 (Code node v2)
```javascript
const input = $input.first().json;
const body = input.body || input;
const base64Data = body.file;
const filename = body.filename || 'document';
const source = body.source || 'auto';
const target = body.target || 'fr';
if (!base64Data) { throw new Error('No file data provided'); }
const fileBuffer = Buffer.from(base64Data, 'base64');

// Detect file type from magic bytes (LibreTranslate needs extension)
let ext = 'txt';
const magic = fileBuffer.slice(0, 5).toString('hex');
if (magic.startsWith('25504446')) ext = 'pdf';        // %PDF
else if (magic.startsWith('504b')) ext = 'docx';     // PK (ZIP-based)
else if (fileBuffer.slice(0, 8).toString('hex').startsWith('d0cf11e0a1b1')) ext = 'doc'; // OLE

let finalName = filename;
if (!filename.match(/\.(pdf|docx|doc|txt|odt|odp|pptx|epub|html|srt)$/i)) {
  finalName = filename + '.' + ext;
}

return [{ json: { filename: finalName, source, target }, binary: { data: { data: fileBuffer, mimeType: 'application/octet-stream', fileName: finalName } } }];
```

### 3. Translate File (HTTP Request node v4.4 — NOT Code node)
- Method: POST
- URL: `https://translate.jefe.ovh/translate_file`
- `contentType: "multipart-form-data"`
- `bodyParameters.parameters`:
  - `{"name": "source", "value": "={{ $json.source }}"}`
  - `{"name": "target", "value": "={{ $json.target }}"}`
  - `{"name": "api_key", "value": "<key>"}`
  - `{"name": "file", "parameterType": "formBinaryData", "inputDataFieldName": "data"}`
- `options.response.response.neverError: true` (don't crash on API errors)

### 4. Encode Response (Code node v2)
- Check if Translate File returned an error → return `{success: false, error: "..."}`
- If success, download the translated file URL via `this.helpers.httpRequest()`
- Return `{success: true, filename, translatedText, downloadUrl}`

### 5. Respond to Webhook
- `respondWith: "json"` (or `"text"` with `JSON.stringify` for reliability)
- Always return valid JSON even on error — iOS Shortcuts `dictGet()` crashes on non-dict responses

## Critical Pitfalls

1. **Code node v2.2 doesn't recognize `jsCode`** — use `typeVersion: 2` only
2. **`this.helpers.httpRequest()` mangles multipart bodies** — use native HTTP Request node with `formBinaryData` instead
3. **`parameterType: "file"` is invalid** — use `parameterType: "formBinaryData"`
4. **`fetch()` and `require('axios')` are blocked** in n8n Code node sandbox
5. **Webhook must ALWAYS return valid JSON** — `dictGet()` on a non-dict response crashes iOS with "Échec de Obtenir la valeur du dictionnaire"
6. **Filename must include extension** — LibreTranslate uses the extension to determine the file format. iOS `selectFile()` + `getFileDetail(file, "Name")` may return a name without extension. The Decode Base64 Code node should detect the format from magic bytes and append the extension.

## Production Workflow
- Workflow ID: `gsmd3yyG19CEt4tO`
- Webhook URL: `https://n8n.jefe.ovh/webhook/translate-file`
- Used by Cherri shortcut "Traduire v5" (NAS: `Traduire_v5.shortcut`)