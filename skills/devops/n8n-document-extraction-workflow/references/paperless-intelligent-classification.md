# Paperless-ngx Intelligent Document Classification

## Overview

The Build Recap Code node in the OCR workflow performs full intelligent classification:
- Fetches existing Paperless types/correspondents/tags
- Calls mistral-small-latest to classify the document (type, correspondent, owner, title + extract all data)
- Finds or creates the document type and correspondent in Paperless
- Prepares all upload parameters for the Paperless HTTP Request node

## Paperless-ngx Classification Objects

Paperless has three main classification dimensions:

| Object | API Endpoint | Purpose |
|--------|-------------|---------|
| Document Types | `/api/document_types/` | What kind of document (bulletin de salaire, facture, contrat...) |
| Correspondents | `/api/correspondents/` | Who issued the document (SKF, GCA, EDF, Banque...) |
| Tags | `/api/tags/` | Free-form tags (categories, ZDR countdown, status...) |

Storage path uses: `{{ correspondent }}/{{ created_year }}/{{ document_type }} - {{ title }}`

## Classification Prompt Structure

The system prompt includes existing types and correspondents as JSON arrays (fetched live from Paperless):
- LLM rules: use existing type/correspondent if case-insensitive match exists; otherwise propose new one
- Be intelligent with unknown documents — guess the type and correspondent logically
- Generate a short descriptive title (e.g., "Bulletin de salaire janvier 2026", "Facture EDF mars 2026")
- For daily timesheets, include the date in the title

Response JSON:
```json
{
  "type_document": "string",
  "correspondant": "string",
  "proprietaire": "jefe|pere|mere|autre",
  "titre": "string",
  "donnees_extraites": { ... }
}
```

## Case-Insensitive Matching

The LLM may return "SKF" but Paperless has "Skf" (id=1). Build dual-key lookup maps:

```javascript
const typeMap = {};
typesResp.results.forEach(t => {
  typeMap[t.name.toLowerCase()] = t.id;
  typeMap[t.name] = t.id;
});
const docTypeId = typeMap[data.type_document.toLowerCase()];
```

## Auto-Creation Pattern

When the LLM identifies a type or correspondent that doesn't exist in Paperless:

```javascript
let docTypeId = typeMap[data.type_document.toLowerCase()];
if (!docTypeId) {
  const newType = await this.helpers.httpRequest({
    method: 'POST',
    url: PAPERLESS_BASE + '/document_types/',
    headers: { Authorization: 'Token ' + TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: data.type_document }),
    json: true
  });
  docTypeId = newType.id;
}
```

Same pattern for correspondents via `/api/correspondents/`.

## Upload Parameters

The HTTP Request node (Upload to Paperless) sends multipart form data with:
- `document`: binary file (`formBinaryData`, `inputDataFieldName: "data"`)
- `title`: `={{ $json.paperless_title }}`
- `document_type`: `={{ $json.paperless_doc_type_id }}` (numeric ID, not name)
- `correspondent`: `={{ $json.paperless_correspondent_id }}` (numeric ID)
- `tags`: `={{ $json.paperless_tags }}` (JSON array string like `[32]`)

The `document_type` and `correspondent` fields accept numeric IDs (not names). The Paperless API resolves the ID to the object.

## User Preference: Generalist, Not Hardcoded

The user explicitly rejected hardcoded category lists in the prompt. The LLM must handle unknown document types autonomously — "if the category doesn't exist, it's a document we've never seen before, the LLM should classify it itself." Only show existing types as context; let the LLM propose new ones and auto-create them.

## Existing Paperless Objects (as of 2026-08-07)

**Document Types (21):** Feuille d'heures SKF, Feuille d'heures GCA, CV, Bulletin de salaire, ATTESTATION FRANCE TRAVAIL, CERTIFICAT DE TRAVAIL, Contrat, Devis, Relevé bancaire, Facture, Avis d'imposition, Courrier administratif, Ticket de caisse, Attestation, Demande d'autorisation d'absence, Annonce immobilière, Document médical, Certificat formation, Mutuelle Sante, Information, Conditions générales

**Correspondents (27):** Skf, IZIWORK 1, France Travail, Trésor Public, EDF, Banque, Assurance, Hetzner, Orange, OVH, Free, Cybertek, o2switch, Histoire d'Or, La Poste, Relais Vision, Amazon, Google, PayPal, GCA, La Forêt immo, Matmut, Netim, Revolut, Sanef, AXA, Cloudflare

**Tags (45):** cat/*, fiscal/*, statut/*, zdr/j-*, Heure de route