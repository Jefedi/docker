# ZDR Mistral Countdown System

## Overview

Mistral AI's ZDR (Zero Data Retention) policy retains documents sent to the OCR API for ~30 days before deletion. This system tracks the countdown in Paperless-ngx using numbered tags and a daily cron script.

## Paperless-ngx Tag Setup

32 tags created via `POST /api/tags/`:
- `zdr/j-31` (id=32, color=#FF5722 orange) — just sent to Mistral
- `zdr/j-30` (id=33) ... `zdr/j-1` (id=62) — countdown in progress
- `zdr/j-0` (id=63, color=#4CAF50 green) — last day before Mistral deletion

```python
# Create all 32 tags
for day in range(31, -1, -1):
    name = f"zdr/j-{day}"
    color = "#FF5722" if day > 0 else "#4CAF50"
    # POST /api/tags/ with {"name": name, "color": color}
```

## Workflow Integration

When uploading a document to Paperless-ngx after Mistral OCR processing:
1. Upload the document via `POST /api/documents/post_document/`
2. Get the new document ID from the response
3. Add tag `zdr/j-31` (id=32) to the document: `PATCH /api/documents/{id}/` with `{"tags": [...existing, 32]}`

## Daily Countdown — Two Implementation Options

### Option 1: n8n Workflow (PREFERRED by user)

The user explicitly prefers a visual n8n workflow over an invisible cron script — it's editable, visible, and extensible.

**Workflow**: `ZDR Mistral Countdown` (id: `0x9qijssc82xKHlc`)
- URL: https://n8n.jefe.ovh/workflow/0x9qijssc82xKHlc
- Schedule Trigger: `0 3 * * *` (daily at 3:00 AM)
- Code node: fetches all Paperless tags, iterates j-31→j-1 decrementing, removes j-0
- Sticky note with explanation
- Published and active

The workflow uses the same logic as the Python script below but inside a Code node, making it visible and editable in the n8n UI. The user can add notification nodes, data table writes, or other integrations without touching code.

**Workflow SDK code** (for reference / recreation):
```javascript
// Code node inside the ZDR Countdown workflow
const TOKEN = "${PAPERLESS_TOKEN}";
const BASE = "https://paperless.jefe.al/api";

// Fetch all tags, build name→id map
const tagsResp = await this.helpers.httpRequest({
  method: 'GET', url: BASE + '/tags/?page_size=100',
  headers: { Authorization: 'Token ' + TOKEN }, json: true
});
const tagIdByName = {};
for (const t of tagsResp.results) tagIdByName[t.name] = t.id;

const changes = [];

// Decrement j-31 → j-1
for (let day = 31; day >= 1; day--) {
  const currentTagId = tagIdByName['zdr/j-' + day];
  const nextTagId = tagIdByName['zdr/j-' + (day - 1)];
  if (!currentTagId) continue;
  const docsResp = await this.helpers.httpRequest({
    method: 'GET',
    url: BASE + '/documents/?tags__id__in=' + currentTagId + '&page_size=100',
    headers: { Authorization: 'Token ' + TOKEN }, json: true
  });
  for (const doc of docsResp.results) {
    const newTags = doc.tags.filter(t => t !== currentTagId);
    if (nextTagId) newTags.push(nextTagId);
    await this.helpers.httpRequest({
      method: 'PATCH', url: BASE + '/documents/' + doc.id + '/',
      headers: { Authorization: 'Token ' + TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags: newTags }), json: true
    });
    changes.push('doc ' + doc.id + ': zdr/j-' + day + ' -> zdr/j-' + (day - 1));
  }
}

// Remove j-0 tag entirely
const j0TagId = tagIdByName['zdr/j-0'];
if (j0TagId) {
  const docsResp = await this.helpers.httpRequest({
    method: 'GET',
    url: BASE + '/documents/?tags__id__in=' + j0TagId + '&page_size=100',
    headers: { Authorization: 'Token ' + TOKEN }, json: true
  });
  for (const doc of docsResp.results) {
    const newTags = doc.tags.filter(t => t !== j0TagId);
    await this.helpers.httpRequest({
      method: 'PATCH', url: BASE + '/documents/' + doc.id + '/',
      headers: { Authorization: 'Token ' + TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags: newTags }), json: true
    });
    changes.push('doc ' + doc.id + ': zdr/j-0 removed (Mistral ZDR expired)');
  }
}

if (changes.length === 0) return [];
return [{ json: { total_changes: changes.length, changes } }];
```

### Option 2: Hermes Cron Script (FALLBACK)

Location: `/opt/data/.hermes/scripts/zdr_mistral_countdown.py` (also at `/opt/data/scripts/zdr_mistral_countdown.py`)

Hermes cron job:
- Name: `ZDR Mistral Countdown`
- Schedule: `0 3 * * *` (daily at 3:00 AM)
- `no_agent: True` — script-only, no LLM involvement
- Silent on success, outputs only when documents are updated

### Script Logic

```python
for day in range(31, 0, -1):
    current_tag = f"zdr/j-{day}"
    next_tag = f"zdr/j-{day - 1}"
    
    # Find all docs with current_tag
    docs = GET /api/documents/?tags__id__in={current_tag_id}
    
    for doc in docs:
        # Remove current_tag, add next_tag
        new_tags = [t for t in doc.tags if t != current_tag_id]
        new_tags.append(next_tag_id)
        PATCH /api/documents/{doc.id}/ {"tags": new_tags}

# Handle j-0: remove tag entirely
docs = GET /api/documents/?tags__id__in={j0_tag_id}
for doc in docs:
    new_tags = [t for t in doc.tags if t != j0_tag_id]
    PATCH /api/documents/{doc.id}/ {"tags": new_tags}
```

## Querying ZDR Status

To check where a document is in the ZDR cycle:
```bash
# List all documents with ZDR tags
curl -s -H "Authorization: Token ${PAPERLESS_TOKEN}" \
  "https://paperless.jefe.al/api/documents/?tags__id__in=32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63&page_size=100"
```

## Paperless-ngx API Notes

- Auth: `Authorization: Token <key>` (Django REST, NOT Bearer)
- Tag creation returns `{ id, name, slug, color, ... }` — save the IDs for tag operations
- `PATCH /api/documents/{id}/` with `{"tags": [...]}` REPLACES all tags (not additive)
- The `name` query param on `/api/tags/` does partial matching, not exact — fetch all and compare in code
- Token: `${PAPERLESS_TOKEN}`