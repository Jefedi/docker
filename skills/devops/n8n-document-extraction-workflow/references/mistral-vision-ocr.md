# Mistral OCR & Vision API — OCR & Document Extraction

## Two Approaches (as of Aug 2026)

### A. Dedicated OCR API (RECOMMENDED for handwriting/scans)

Mistral offers a dedicated OCR model at a separate endpoint. This is NOT a chat model — it's a specialized OCR service that returns markdown.

**Endpoint**: `POST https://api.mistral.ai/v1/ocr`

**Models**: `mistral-ocr-latest`, `mistral-ocr-2512`, `mistral-ocr-3-0`, `mistral-ocr-3`, `mistral-ocr-4-0`, `mistral-ocr-4`, `mistral-ocr-4-1`

**Request format** depends on file type — this is CRITICAL, using the wrong type returns HTTP 422:

**For images** (JPEG, PNG, etc.):
```json
{
  "model": "mistral-ocr-latest",
  "document": {
    "type": "image_url",
    "image_url": {"url": "data:image/jpeg;base64,<BASE64>"}
  }
}
```
Note: `image_url` is an OBJECT with a nested `url` field.

**For PDFs**:
```json
{
  "model": "mistral-ocr-latest",
  "document": {
    "type": "document_url",
    "document_url": "data:application/pdf;base64,<BASE64>"
  }
}
```
Note: `document_url` is a flat STRING field (not nested like `image_url`).

**WRONG formats that return 422**:
- `type: "image_url"` with PDF data → 422 "Image content must be a URL...or base64 encoded image"
- `type: "file_url"` with `file_url` field → 422 "Input should be 'document_url'"

**Response format**: Returns `pages[0].markdown` — the full text content of the document as markdown, including tables. Also returns `pages[0].blocks` with bounding boxes and block types (title, text, caption, table).

**Performance on handwritten documents**: Significantly better than chat models. In a real test on a handwritten "feuille de mission journalière":
- `mistral-ocr-latest` correctly extracted: client name (SKF), departure time (17H15), activity (DECHARGEMENT), arrival location (GCA). Some errors on handwritten names (ZAP FRENO → "2eF PRETO") and dates (2026 → "2020"), but captured the critical structured data.
- `mistral-small-latest` (chat model with vision) missed almost all handwritten content — returned generic form structure with zero extracted data.
- `pixtral-12b-2409` and `pixtral-large-latest` model IDs do NOT exist on the API. `pixtral-12b-2409` silently maps to `ministral-14b-latest`. `pixtral-large-latest` returns HTTP 400 "Invalid model".

### B. Chat Completions with Vision (for structured extraction / reasoning)

Chat models can accept images and do both OCR + reasoning in one call, but are less reliable for raw text extraction.

**Endpoint**: `POST https://api.mistral.ai/v1/chat/completions`

**Models with vision** (verified via `GET /v1/models`):

| Model ID | Notes |
|---|---|
| `mistral-large-2512` | Best quality |
| `mistral-medium-2508` | Balanced |
| `mistral-small-latest` | Cost-effective, text reasoning from OCR output |
| `ministral-14b-latest` | Auto-redirected from `pixtral-12b-2409` |
| `ministral-8b-latest` | Smallest |

**Sending images in chat**: use `content` array with `type: "image_url"` and `image_url.url` as data URI (`data:image/jpeg;base64,...`).

## RECOMMENDED: Two-Step Pipeline

For best results on handwritten/variable documents, use a two-step approach:

1. **Step 1 — OCR**: Send image to `mistral-ocr-latest` at `/v1/ocr`. Get back markdown text.
2. **Step 2 — Structured Extraction**: Send the OCR markdown to `mistral-small-latest` at `/v1/chat/completions` with a prompt to extract structured JSON (type, dates, hours, names, amounts, etc.).

This separates raw text recognition (OCR model is best at this) from semantic understanding (chat model is best at this). It also allows using `response_format: { type: "json_object" }` on the chat model for reliable JSON output.

## Discovering Available Models

```bash
curl -s https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer $MISTRAL_API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    print(m['id'])
"
```

## Privacy Stance

- Mistral AI is EU-hosted (Paris, France)
- Does NOT train models on user-submitted data
- GDPR compliant, no CLOUD Act exposure (unlike US providers)
- Suitable for sensitive documents (payroll, timesheets, personal info)

## Tips for Handwritten Documents

- **Use `mistral-ocr-latest`** (dedicated OCR), not chat models, for raw text extraction from handwriting
- For difficult handwriting, OCR may still make errors on names and dates — the confirmation loop is critical
- Use `temperature: 0.1` for the extraction step to minimize creative interpretation
- The generalist extraction prompt should detect document type automatically (feuille de mission, facture, bon de commande, etc.) and extract all visible fields without assuming a specific format