# Auto-Classification Paperless — Scheduled Workflow Pattern

## Architecture

Three n8n workflows work together:

1. **OCR Telegram** (workflow `iRdoNkAhwSAbkeT7`) — real-time, Telegram-triggered
2. **Auto-Classification Paperless** (workflow `y2DdIZbhVxtd4DaF`) — scheduled every 30 min
3. **ZDR Countdown** (workflow `0x9qijssc82xKHlc`) — scheduled daily at 3 AM

## Auto-Classification Workflow Details

**Trigger**: Schedule, every 30 minutes (`minutesInterval: 30`)

**Nodes**:
1. `Fetch Pending Docs` — HTTP GET to `https://paperless.jefe.al/api/documents/?tags__id__in=24&page_size=50`
   - Tag ID 24 = `statut/a-traiter`
   - Returns `{ count, results: [{ id, title, tags, ... }] }`
2. `Has Docs?` — IF node, checks `$json.count > 0`
   - Empty result = no work this cycle → chain stops cleanly (zero-item safety)
3. `Split Docs` — `splitInBatches` with `batchSize: 1`
4. `Process Doc` — single Code node doing the full pipeline

## Process Doc Code Node — Full Pipeline

The Code node does 7 steps per document:

### Step 1: Download document binary
```javascript
const fileData = await this.helpers.httpRequest({
  method: 'GET',
  url: PB + '/documents/' + docId + '/download/',
  headers: { Authorization: 'Token ' + PT },
  encoding: 'arraybuffer',  // CRITICAL: returns raw bytes
  timeout: 30000
});
const buf = Buffer.from(fileData);
```

### Step 2: Detect MIME type from magic bytes
```javascript
let mime = 'application/octet-stream';
if (buf.slice(0,4).toString() === '%PDF') mime = 'application/pdf';
else if (buf[0] === 0xFF && buf[1] === 0xD8) mime = 'image/jpeg';
else if (buf[0] === 0x89 && buf[1] === 0x50) mime = 'image/png';
```

### Step 3: Mistral OCR (branch on MIME type)
- PDF → `{ type: 'document_url', document_url: 'data:application/pdf;base64,...' }`
- Image → `{ type: 'image_url', image_url: { url: 'data:image/jpeg;base64,...' } }`
- Concatenate all `pages[].markdown` for multi-page PDFs

### Step 4: Fetch existing Paperless metadata in parallel
```javascript
const [typesResp, corrResp, tagsResp] = await Promise.all([
  this.helpers.httpRequest({method:'GET', url:PB+'/document_types/?page_size=100', ...}),
  this.helpers.httpRequest({method:'GET', url:PB+'/correspondents/?page_size=100', ...}),
  this.helpers.httpRequest({method:'GET', url:PB+'/tags/?page_size=100', ...})
]);
```
Build case-insensitive lookup maps from results.

### Step 5: Classify with mistral-small-latest
- System prompt includes existing types/correspondents as JSON arrays
- LLM returns: `{ type_document, correspondant, proprietaire, titre }`
- `response_format: { type: 'json_object' }` for reliable JSON

### Step 6: Find or create type/correspondent
```javascript
let docTypeId = typeMap[data.type_document.toLowerCase()];
if (!docTypeId) {
  const newType = await this.helpers.httpRequest({
    method:'POST', url:PB+'/document_types/',
    headers:{Authorization:'Token '+PT,'Content-Type':'application/json'},
    body: JSON.stringify({name:data.type_document}), json:true
  });
  docTypeId = newType.id;
}
```
Same pattern for correspondents.

### Step 7: Update document in Paperless — remove only a-traiter, NO archivé
```javascript
// Remove only the a-traiter tag, do NOT add archivé
// If the workflow bugs, a-traiter stays and the doc gets retried next cycle
const tagTraiter = tagMap['statut/a-traiter'];
const currentTags = doc.tags || [];
const newTags = currentTags.filter(t => t !== tagTraiter);

await this.helpers.httpRequest({
  method:'PATCH', url:PB+'/documents/'+docId+'/',
  headers:{Authorization:'Token '+PT,'Content-Type':'application/json'},
  body: JSON.stringify({
    title: data.titre,
    document_type: docTypeId,
    correspondent: corrId,
    tags: newTags
  }),
  json: true
});
```

**User preference: remove only `a-traiter`, do NOT add `archivé`** — the user explicitly corrected this. The `a-traiter` tag is removed on success, but no `archivé` tag is added. If the workflow fails, the tag stays and the document is retried on the next 30-minute cycle. This provides automatic retry without needing a separate "processed" tag.

## Batch Reclassification Script

For migrating existing unclassified documents, use the Python script at `/opt/data/scripts/reclassify_paperless.py`. It:

1. Fetches all documents with `statut/a-traiter` tag
2. For each: downloads → OCR → classify → find-or-create type/correspondent → PATCH update
3. Rate-limited with 1-second sleep between documents
4. Prints a summary at the end (X/total succeeded)

In one session: 29 documents reclassified in ~3 minutes, 0 errors. Created:
- New types: "Certificat d'immatriculation", "Questionnaire"
- New correspondents: "OpenRouter", "Caisse d'épargne/BPCE", "Notaire", "Notaires de France", "SARL-U OCEANE NETTOYAGE"

## Paperless-ngx Tag Workflow

- `statut/a-traiter` (id=24) — documents pending classification (auto-added by email import)
- `statut/archivé` (id=25) — exists but NOT used by the auto-classification workflow (user preference)
- `zdr/j-31` through `zdr/j-0` (ids 32-63) — ZDR countdown tags
- Other tags: `cat/perso`, `cat/pro`, `cat/alex`, `fiscal/2024`, etc.

The classification workflow removes `a-traiter` after processing. No replacement tag is added.