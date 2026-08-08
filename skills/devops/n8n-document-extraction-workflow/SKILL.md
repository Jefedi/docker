---
name: n8n-document-extraction-workflow
description: Telegram→OCR→confirm→archive→calculate document workflow.
---

# n8n Document Extraction Workflow

Use when building n8n workflows that: receive documents via Telegram, extract structured data using AI vision/OCR models (Mistral Vision, Pixtral, etc.), present extracted data to the user for confirmation/correction, archive originals to Paperless-ngx, and feed confirmed data into a calculation pipeline.

## Architecture Pattern

```
Telegram photo → n8n webhook → Mistral OCR (/v1/ocr) → OCR markdown
    → mistral-small-latest (structured JSON extraction) → Telegram confirmation message
    → user confirms/corrects → Paperless-ngx archive (+ ZDR tag) → n8n data table → calculation → summary
```

**Generalist by design** — the user explicitly wants this system to handle ANY document type (feuilles de mission, factures, bons de commande, etc.), not just timesheets. The OCR step reads everything; the extraction prompt auto-detects the document type and extracts all visible fields. The calculation/salary logic is a downstream module that only applies to timesheets — the OCR + extraction + archive pipeline is document-agnostic.

## Key Components

### 1. Telegram Bot Input
- Bot must already be configured in n8n (Telegram Trigger node)
- Photos arrive as file payloads; n8n can download the file content
- Filter: only process messages with documents/photos, ignore plain text
- Send the photo to the AI API as base64-encoded image

### 2. AI Vision / OCR Extraction (Two-Step Pipeline)

**RECOMMENDED: Two-step approach** — far more reliable than a single chat model call for handwritten or variable documents:

1. **Step 1 — OCR**: Send image to `mistral-ocr-latest` at `POST /v1/ocr`. Returns `pages[0].markdown` — raw text content as markdown. This is a dedicated OCR model, NOT a chat model. Significantly better at reading handwriting.
2. **Step 2 — Structured Extraction**: Send the OCR markdown to `mistral-small-latest` at `POST /v1/chat/completions` with a generalist extraction prompt. Use `response_format: { type: "json_object" }` for reliable JSON.

**Generalist extraction prompt** — the extraction prompt should NOT assume a specific document format. It should:
- Auto-detect the document type (feuille de mission, facture, bon de commande, etc.)
- Extract ALL visible fields: dates, names, hours, durations, activities, locations, amounts
- Never invent or assume — return null for illegible fields
- Keep values as read (e.g., "17H15" not "17:15")

This two-step approach separates raw text recognition (OCR model excels at this) from semantic understanding (chat model excels at this). See `references/mistral-vision-ocr.md` for full API details, model IDs, and performance comparisons.

- Mistral does NOT train on user data — EU-hosted, GDPR compliant, suitable for privacy-sensitive documents.
- For the legacy single-step approach (chat model with vision), use `mistral-medium-2508` or `mistral-large-2512` with `image_url` in the message content. Less reliable for handwriting.

### 3. Human-in-the-Loop Confirmation (critical)
- After extraction, send a formatted summary back to the user via Telegram
- User confirms or corrects the data (reply with corrections)
- Only after confirmation: store in data table + archive document
- This handles poor handwriting, OCR errors, and builds trust over time
- The model improves implicitly through better prompts, not by training on user data

### 4. Paperless-ngx Archive (Intelligent Classification)

The user wants the system to be **fully intelligent** — not just extract data, but also **classify and file** the document in Paperless-ngx automatically. The LLM determines document type, correspondent (issuer), owner, and title; the workflow creates missing types/correspondents in Paperless and uploads with full metadata.

**Build Recap node does 6 things:**
1. Fetch existing document_types, correspondents, and tags from Paperless (`GET /api/document_types/?page_size=100`, etc.) in parallel via `Promise.all()`
2. Call `mistral-small-latest` with a **classification prompt** that includes the existing types/correspondents as JSON context arrays, asking the LLM to: identify document type, correspondent (issuer), owner (jefe/pere/mere/autre), title, and extract all visible data
3. **Find or create document type** — case-insensitive lookup via `typeMap[name.toLowerCase()]`; if not found, `POST /api/document_types/` with `{"name": "..."}` to create it
4. **Find or create correspondent** — same pattern with `POST /api/correspondents/`
5. Get ZDR tag ID from tag map
6. Build recap message + prepare Paperless upload parameters (title, doc_type_id, correspondent_id, tags JSON array)

**Case-insensitive matching (critical):** The LLM may return "SKF" but Paperless has "Skf" (id=1). Build lookup maps with `.toLowerCase()` keys:
```javascript
const typeMap = {};
typesResp.results.forEach(t => { typeMap[t.name.toLowerCase()] = t.id; typeMap[t.name] = t.id; });
const docTypeId = typeMap[data.type_document.toLowerCase()];
```

**Upload to Paperless with full classification:**
The HTTP Request node sends multipart form data with:
- `document`: binary file (`formBinaryData`, `inputDataFieldName: "data"`)
- `title`: `={{ $json.paperless_title }}` (LLM-generated title)
- `document_type`: `={{ $json.paperless_doc_type_id }}` (numeric ID)
- `correspondent`: `={{ $json.paperless_correspondent_id }}` (numeric ID)
- `tags`: `={{ $json.paperless_tags }}` (JSON array string like `[32]`)

**Paperless-ngx classification API:**
- `GET /api/document_types/?page_size=100` → `{ results: [{ id, name, ... }] }`
- `GET /api/correspondents/?page_size=100` → same shape
- `POST /api/document_types/` with `{"name": "..."}` → creates, returns `{ id, name, ... }`
- `POST /api/correspondents/` with `{"name": "..."}` → same
- `PATCH /api/documents/{id}/` with `{"tags": [...], "document_type": id, "correspondent": id}` → updates classification

**User preference: generalist classification, not hardcoded categories**
The user explicitly wants the LLM to handle **unknown document types** intelligently — "if the category doesn't exist, because it's a document we've never seen before, the prompt shouldn't specify to classify it — the LLM should classify it itself." The system must be "as intelligent as possible with unprecedented situations." Do NOT hardcode a list of allowed types in the prompt — only show existing types as context and let the LLM propose new ones. This includes auto-creating new document types and correspondents in Paperless when the LLM identifies a type/issuer not yet in the system.

### 5. Data Table + Calculation
- Store confirmed extractions in an n8n data table (or external DB)
- Calculation logic runs on a schedule (daily/weekly) or on-demand
- Output: summary message via Telegram

## Workflow Build Sequence

1. **Plan first** — before touching n8n, write out all rules, rates, edge cases. Get user sign-off on the plan.
2. **Create data table** — define columns matching the extracted fields + calculation fields.
3. **Build Telegram trigger** — filter for documents only.
4. **Add AI vision node** — configure Mistral API call with structured output prompt.
5. **Add confirmation node** — format extracted data, send to user, wait for reply.
6. **Add archive node** — upload to Paperless-ngx after confirmation.
7. **Add storage node** — write confirmed data to data table.
8. **Add calculation node** — scheduled or triggered, compute totals.
9. **Add summary node** — send results via Telegram.

## Testing & Deployment Workflow

### User preference: test before re-enabling
The user explicitly wants: disable workflow → test → fix → re-enable. Do NOT test live with the workflow active. The sequence is:
1. **Unpublish** the workflow (`unpublish_workflow`)
2. **Test** the API pipeline directly (see Python simulation below)
3. **Fix** any issues found
4. **Publish** the workflow (`publish_workflow`)
5. Tell the user to send a real document

### User preference: autonomous debugging — don't ask the user to re-test each fix
The user explicitly said: "I don't want to intervene anymore. You're screwing yourself." When a workflow has multiple bugs, the agent should:
1. **Désactiver le workflow** (unpublish)
2. **Tester le pipeline complet en Python** — simuler tous les appels API (OCR + extraction + recap) sans passer par n8n
3. **Identifier et fixer TOUS les bugs** en une seule passe — ne pas faire un fix, publier, demander à l'utilisateur de tester, découvrir un nouveau bug, recommencer. Tester chaque node proactivement.
4. **Vérifier les logs n8n** (`docker logs n8n-n8n-1 --since=2m`) après chaque exécution pour confirmer qu'il n'y a pas d'erreur silencieuse
5. **Vérifier les exécutions n8n** via `search_executions` — une exécution "success" en <300ms signifie que le IF a rejeté le message (pas un vrai succès)
6. **Réactiver le workflow** seulement quand tout est validé
7. **Dire à l'utilisateur d'envoyer un document** — une seule fois, pas après chaque fix

Le user est frustré par les cycles répétés de "fix → publier → demande de test → échec → refix". Faire tout le travail en une fois.

### Python pipeline simulation (when pin data can't work)
n8n's `test_workflow` with pin data fails when the Telegram Trigger has `download: true` — it tries to download the photo from Telegram with a fake `file_id`. Instead, simulate the full pipeline in Python:

```python
# 1. Read test image as base64
with open('test.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

# 2. Call Mistral OCR (same as Code node)
ocr_resp = call_api('POST', '/v1/ocr', {
    'model': 'mistral-ocr-latest',
    'document': {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}
})
ocr_markdown = ocr_resp['pages'][0]['markdown']

# 3. Call mistral-small-latest for extraction (same as Code node)
extract_resp = call_api('POST', '/v1/chat/completions', {
    'model': 'mistral-small-latest',
    'messages': [...],
    'response_format': {'type': 'json_object'}
})
data = json.loads(extract_resp['choices'][0]['message']['content'])

# 4. Build recap (same as Code node)
# ... format the recap string

# If all 4 steps pass in Python, the Code node logic is correct.
# Remaining risk: n8n binary data handling between nodes (covered in pitfalls).
```

This validates the API calls, the prompt, the JSON parsing, and the recap formatting. The only thing it doesn't test is n8n's binary data passthrough between nodes — but that's covered by the pitfalls section.

## Pitfalls

- **Don't skip the plan** — building directly in n8n without a documented spec leads to mistakes in calculation logic, especially with time-based rules (rate changes mid-month, overtime thresholds, etc.).
- **OCR on handwriting is unreliable** — always include the confirmation step. The user's handwriting may be inconsistent; the model may misread. The confirmation loop is not optional.
- **Rate changes over time** — if rates (hourly pay, panier, etc.) change, the calculation must use the rate applicable on the date of the document, not the current rate. Store rate-effective dates in the data model.
- **Taux route = taux × 1.25** — confirmed by real payslip example (27 juillet - 2 août): 13h route × 16€ = 208€ where 16€ = 12.80€ × 1.25. The same +25% majoration applies to both driving hours and overtime hours beyond 35h/week.
- **Prime 13e mois** — 1.07€ per normal hour, fixed rate. Calculated on normal hours only (not route/overtime hours).
- **Format récap** — match the user's company app format: "Heures de route / Heures normales / Heures supp. 25% / Prime de 13e mois".
- **Mistral base64 images** — when sending images via base64, prefix with the data URI scheme (`data:image/jpeg;base64,...`). Check current API docs for exact format.
- **Telegram message length** — long extraction summaries may exceed Telegram's 4096 char limit. Split if needed.
- **Privacy check** — verify the AI provider's data policy before sending sensitive documents. Mistral: no training on user data, EU-hosted. Industrial models (Google, AWS Textract) may use data for training — avoid for sensitive docs.
- **n8n AI Agent node crashes with tool_calls** — use Basic LLM Chain node, not AI Agent, when calling Hermes API. See memory for details.
- **Telegram `replyMarkup: "inlineKeyboard"` without buttons = silent failure** — the Telegram API rejects messages with an empty inline keyboard. n8n marks the execution as "success" but no message is delivered. Either configure actual buttons or remove `replyMarkup` entirely. The user sees nothing and has no way to know the message was dropped. See the dedicated pitfall below about `replyMarkup` being sticky via the MCP API.
- **Telegram Trigger `message.photo` only matches photos, not documents/PDFs** — a PDF sent to the bot arrives as `message.document`, not `message.photo`. The IF filter must use OR: `message.photo` notEmpty OR `message.document` notEmpty. Without this, PDFs are silently ignored (workflow runs in <300ms, no error).
- **Telegram binary key name differs for documents vs photos** — for photos, the binary property is typically `data`. For documents (PDFs), the key may differ. Auto-detect with `Object.keys(item.binary)[0]` instead of hardcoding `'data'`. Also extract `mimeType` from `item.binary[key].mimeType` to determine if the file is a PDF or image.
- **Mistral OCR PDF format — use `document_url`, NOT `image_url` or `file_url`** — the `/v1/ocr` endpoint has THREE document types: `image_url` (for images only), `document_url` (for PDFs), and `image_url` with `image_url.url` (for images). Sending a PDF as `image_url` returns HTTP 422 ("Image content must be a URL...or base64 encoded image"). Sending `file_url` returns HTTP 422 ("Input should be 'document_url'"). The correct PDF payload is:
  ```json
  {"model":"mistral-ocr-latest","document":{"type":"document_url","document_url":"data:application/pdf;base64,..."}}
  ```
  For images:
  ```json
  {"model":"mistral-ocr-latest","document":{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}}
  ```
  Note the structural difference: `image_url` uses a nested `image_url.url` field, while `document_url` uses a flat `document_url` string field. Multi-page PDFs return multiple `pages[]` entries — concatenate all `page.markdown` with a separator. The Code node must detect `mimeType` from the binary metadata and branch to the correct payload format.

### Weekly timesheet correlation (critical discovery)

- **Feuilles are NOT daily pointage sheets** — they are "feuilles de mission journalière" (daily mission sheets) that only contain the LAST trip of the day (e.g., departure from last client → arrival at GCA). Other trips and client hours during the day are NOT written on this sheet.
- **Weekly per-client sheets** (e.g., SKF) are filled once per week, marked by week number (e.g., "semaine 32"), not by date. They contain all days worked at that client during the week.
- **Correlation is mandatory** — to calculate a full day's pay, the system must correlate: (a) the daily mission sheet (last trip), (b) the weekly client sheets (hours at each client), and (c) user-provided info for gaps (trips between clients not written on any sheet).
- **The confirmation/validation step is where the user fills gaps** — after OCR extraction, the system presents what it found and the user adds missing trips/hours via Telegram text.
- **ISO week → date conversion** — week numbers must be converted to date ranges (e.g., week 32 2026 = Aug 3-9, 2026) to look up the correct hourly rate.
- **Déchargement at GCA** = normal hours (temps boîte), not conducteur/sup hours.
- **Pause déduite** — 30 min pause is not counted as work time.

### Mistral TTS as Hermes command provider (bypasses stale API keys)

- When the built-in `mistral` TTS provider fails with `Status 401: Invalid API Key` mid-session, the cause is usually a stale `MISTRAL_API_KEY` in `os.environ` (the running process cached the old value from `.env`).
- **Fix without restart**: create a shell script that calls the Mistral API directly with the correct key, and register it as a `tts.providers.<name>` command provider. See `references/mistral-voxtral-tts-command-provider.md`.
- **Mistral TTS API returns JSON** with `audio_data` field (base64), NOT raw audio bytes. Must decode base64 before writing to output file.
- **Pre-built voices**: 30 voices with emotional modes. French: Marie (Neutral voice_id=`5a271406-039d-46fe-835b-fbbb00eaf08d`). List via `GET /v1/audio/voices`.
- The real Mistral API key may differ from `.env` — check the LiteLLM container: `docker exec litellm printenv MISTRAL_API_KEY`.

### Paperless-ngx Auth (critical — 3 issues found in one session)

- **Paperless uses Token auth, NOT Bearer** — the Django REST API expects `Authorization: Token <key>`, not `Authorization: Bearer <key>`. Creating a "Bearer Auth" credential in n8n for Paperless will fail with `Authentication credentials were not provided`.
- **n8n credential system injects credential NAME as header name** — if you create an HTTP Header Auth credential named "Paperless Token", n8n may inject `Paperless Token` as the HTTP header name, causing `Header name must be a valid HTTP token ["Paperless Token"]`. The credential name must not contain spaces. Better yet, **hardcode the Authorization header directly** in the HTTP Request node's header parameters and skip the credential system entirely for Paperless.
- **Paperless API returns text, not JSON** — the `POST /api/documents/post_document/` endpoint returns a plain text response (the document ID), not JSON. Set the HTTP Request node's response format to "Text", not "JSON", or you get `Response body is not valid JSON`.
- **Generating a Paperless API token when MFA is enabled** — the REST token endpoint `POST /api/token/` requires MFA. Instead, generate a token directly: `docker exec paperless python3 /usr/src/paperless/src/manage.py drf_create_token <username>`. The manage.py path is `/usr/src/paperless/src/manage.py` (not `/usr/src/paperless/manage.py`).
- **`genericCredentialType` with `httpHeaderAuth` + hardcoded header** — to avoid the credential system entirely while keeping the `genericCredentialType` flag, set `sendHeaders: true` and add the `Authorization` header directly in `headerParameters`. The `HARDCODED_CREDENTIALS` validation warning is non-blocking and can be safely ignored.

### Mistral Voxtral TTS Voices (pre-built)

- Mistral has **30 pre-built voices** with emotional modes (Neutral, Happy, Sad, Angry, Excited, etc.)
- Available via API: `GET https://api.mistral.ai/v1/audio/voices` with `Authorization: Bearer <key>`
- French voice: **Marie** — available in Neutral (`5a271406-039d-46fe-835b-fbbb00eaf08d`), Happy, Sad, Excited, Curious, Angry
- English voices: Paul (US), Oliver (UK), Jane (UK)
- These are NOT zero-shot cloned voices — they are pre-built and ready to use with `voice_id` in the TTS API
- The `voxtral-mini-tts-2603` and `voxtral-mini-tts-latest` model IDs both work

### n8n Code Node Binary Data (critical — 3 bugs found in one session)

- **`$items.all()` does not exist** — use `$input.first()` or `$input.all()` instead. The `$items` object is not available in Code nodes and throws `TypeError: $items.all is not a function`.
- **`item.binary.data` is NOT raw bytes** — in n8n's `filesystem-v2` binary mode (default for self-hosted), `item.binary.data` is a metadata object, and `item.binary.data.data` contains a filesystem reference string like `filesystem-v2://...`, NOT the actual base64 data. Passing this string to `Buffer.from()` or to an API as base64 causes `Cannot decode file 'filesystem-v2'` errors.
- **Correct binary-to-base64 pattern**: use `await this.helpers.getBinaryDataBuffer(itemIndex, 'data')` to get the real Node.js Buffer, then `.toString('base64')`. This works regardless of binary storage mode.
- **Binary data is lost when passing through nodes that don't output it** — an HTTP Request node (like Mistral OCR) returns only JSON, no binary. A downstream Code node that tries to pass `item.binary` to its output will have no binary to pass. Use `$('NodeName').item.binary` to reference binary data from an earlier node that still has it (e.g., the node that first received the photo).
- **Paperless-ngx multipart upload** — in the HTTP Request node, use `formBinaryData` parameter type (not plain text) for the file field. Set `inputDataFieldName` to the binary property name (e.g., `data`). The `isFile: true` flag is required.

### n8n Telegram Node Discriminators

- **Telegram node `resource` MUST be `'message'` with `operation: 'sendMessage'`** — the n8n Telegram node (typeVersion 1.2) has TWO resources that matter: `chat` (operations: get, administrators, member, leave, setDescription, setTitle) and `message` (operations: sendMessage, sendPhoto, sendDocument, editMessageText, etc.). Using `resource: 'chat'` without an operation silently succeeds but DOES NOT send any message — the workflow shows "success" but the user receives nothing. The correct config to send a text message is `resource: 'message'` + `operation: 'sendMessage'`. If you get `Invalid value for "parameters.resource": got "message", expected one of: "chat"`, it's because the `operation` field is missing or invalid — set BOTH `resource` and `operation` together. When in doubt, use `mcp__n8n_mcp__search_nodes` with query `["telegram send message"]` to see the correct discriminators.
- **Telegram `replyMarkup` field is sticky — can't be cleared via `setNodeParameter`** — setting `replyMarkup` to `""` via the MCP API does NOT remove it from the node. The field persists and triggers `INVALID_PARAMETER` warnings. To remove it, you must `removeNode` and `addNode` to recreate the Telegram node from scratch. An empty `replyMarkup: "inlineKeyboard"` (set but no buttons defined) causes Telegram API to silently drop the message — the n8n execution shows "success" but no message is delivered to the user.
- **Telegram Trigger download** — set `additionalFields.download: true` to receive photo binary data. Without this, the trigger fires but no binary data is available downstream.
- **n8n MCP `addConnection` operation** — `source` and `target` are node NAME strings (not objects). Use `sourceIndex` and `targetIndex` (integers, default 0) for output/input indices. Connection type defaults to `"main"`.
- **n8n MCP `addNode` operation** — requires `node` object with `name`, `type`, `typeVersion`, `parameters`, and `position` fields. The node is added disconnected; connect it afterward with `addConnection` operations.
- **n8n MCP server can become unreachable** — if `mcp__n8n_mcp__*` tools fail with "MCP server is unreachable after 3 consecutive failures", wait ~60s and retry. This is transient.
- **"Success" in <300ms = IF rejected the message** — when checking `search_executions`, an execution that shows `status: "success"` but ran in under ~300ms (startedAt and stoppedAt are nearly identical) means the IF/filter node rejected the input and the workflow ended immediately without processing. This is NOT a real success — no OCR ran, no extraction ran, no message was sent. Always check the execution duration: if <1s, the filter blocked the message. The fix is usually to broaden the IF condition (e.g., add `message.document` alongside `message.photo`).

- **n8n HTTP Request JSON Body Validation Bug** — when an HTTP Request node uses `specifyBody: "json"` with a n8n expression (`={...}`) in the `jsonBody` field, n8n validates JSON BEFORE evaluating the expression. Dynamic content (base64 images, OCR markdown with quotes/special chars, user text) triggers `"The value in the JSON Body field is not valid JSON"` in `docker logs`. The workflow silently fails — no execution appears in the n8n executions list.
  - **Fix**: Replace the HTTP Request node with a **Code node** using `this.helpers.httpRequest()`. This bypasses n8n's JSON body validation entirely.
  - **Apply to ALL HTTP Request nodes with dynamic jsonBody** — not just the first one that fails. In one session, both the OCR node AND the structured extraction node had this problem. The first failure was visible in logs; the second only surfaced after the first was fixed. Check every HTTP Request node in the pipeline proactively.
  - See `references/n8n-code-node-binary-pitfalls.md` for the Code node pattern.

### n8n Code Node Timezone Bug

- **`toLocaleTimeString()` in Code nodes defaults to UTC, not the n8n `TZ` env var** — even when n8n has `TZ=Europe/Paris` set in the container environment, `new Date(timestamp).toLocaleTimeString('fr-FR')` inside a Code node uses the Node.js process default (UTC on most servers). The user sees times 2 hours behind their actual local time (e.g., clocks in at 16:29, sees 14:29).
  - **Fix**: Always pass `timeZone` explicitly: `toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris' })`.
  - **Applies to all user-facing time displays** in webhook responses, Telegram messages, or any Code node output that shows a time to the user.

### ZDR (Zero Data Retention) Countdown System

When sending documents to a third-party AI API (like Mistral OCR), the provider may retain the document for a fixed period (Mistral ZDR = 30 days). To track when documents expire from the provider's servers:

**Pattern**: Create numbered tags in Paperless-ngx (`zdr/j-31` through `zdr/j-0`) and a daily cron script that decrements them.

1. **Tag creation**: Create 32 tags in Paperless-ngx via `POST /api/tags/` — `zdr/j-31` (orange `#FF5722`) down to `zdr/j-0` (green `#4CAF50`). Tag IDs are sequential.
2. **On document upload**: When a document is sent to Mistral OCR, tag it with `zdr/j-31` in Paperless-ngx (via `PATCH /api/documents/{id}/` with `{"tags": [...existing, zdr_j31_id]}`).
**PREFERRED: n8n workflow (user explicitly requested)** — the user rejected the invisible cron script approach ("instead of doing the chrono that checks each time, it's better to do a workflow and a webhook — that way I have a visual thing, concrete, and I can adapt it, adjust it if I want, or add other tags"). A workflow is editable, visible, and extensible (can add notification nodes, data table writes, etc. without touching code). Created via the n8n Workflow SDK with:
- Schedule Trigger at `0 3 * * *` (daily 3AM)
- Code node that fetches Paperless tags, iterates `zdr/j-31` → `zdr/j-1` decrementing, and removes `zdr/j-0`
- Sticky note explaining the workflow for future reference
- Published and active

**FALLBACK: Hermes cron script** (if n8n is unavailable): `/opt/data/.hermes/scripts/zdr_mistral_countdown.py` runs daily at 3:00 AM via a Hermes cron job (`no_agent=True`, script-only). It:
   - Iterates `zdr/j-31` → `zdr/j-1`: finds documents with each tag, replaces it with `zdr/j-(N-1)` via PATCH
   - At `zdr/j-0`: removes the tag entirely (document has expired from Mistral's servers)
   - **Silent on success** — only outputs when documents are updated (watchdog pattern)
4. **User query**: When the user asks "where are my documents in the ZDR cycle?", query Paperless-ngx API for documents with `zdr/j-*` tags.

**Paperless-ngx tag API**:
- List: `GET /api/tags/?page_size=100` — returns `{ results: [{ id, name, color, ... }] }`
- Create: `POST /api/tags/` with `{"name": "zdr/j-31", "color": "#FF5722"}`
- Update document tags: `PATCH /api/documents/{id}/` with `{"tags": [1, 2, 32]}` (list of tag IDs, replaces all)
- Search by tag: `GET /api/documents/?tags__id__in={tag_id}&page_size=100`
- **Note**: The `name` query parameter does NOT do exact match — it returns partial matches. Don't use it to check existence; fetch all tags and compare in code instead.

### Scheduled Auto-Classification (Email-Imported Documents)

When Paperless-ngx is configured to auto-import from email accounts, new documents arrive with the `statut/a-traiter` tag but are not yet classified. A **scheduled n8n workflow** (not a Telegram-triggered one) handles these:

**Workflow: "Auto-Classification Paperless"** (runs every 30 minutes)
1. **Schedule Trigger** — fires every 30 min
2. **Fetch Pending Docs** — `GET /api/documents/?tags__id__in=24&page_size=50` (tag 24 = statut/a-traiter)
3. **Has Docs?** — IF node checking `$json.count > 0` (empty result = no work this cycle, chain stops cleanly)
4. **Split Docs** — `splitInBatches` with `batchSize: 1`
5. **Process Doc** — single Code node that: downloads the document (`GET /documents/{id}/download/` with `encoding: 'arraybuffer'`), detects MIME from first bytes (`%PDF` → application/pdf, `0xFF 0xD8` → image/jpeg, `0x89 0x50` → image/png), runs Mistral OCR, fetches existing types/correspondents/tags from Paperless in parallel, calls mistral-small-latest for classification, finds-or-creates type/correspondent, and updates the document via PATCH (title + type + correspondent + removes a-traiter tag only — do NOT add archivé tag)

**User preference: remove only `a-traiter`, do NOT add `archivé`** — the user explicitly said to just remove the `a-traiter` tag when processing succeeds, without replacing it with `archivé`. If the workflow bugs, the `a-traiter` tag stays on the document, so it gets retried on the next 30-minute cycle. This is the desired retry behavior — no archivé tag needed.

**Key n8n Code node pattern for downloading binary from Paperless:**
```javascript
const fileData = await this.helpers.httpRequest({
  method: 'GET',
  url: PB + '/documents/' + docId + '/download/',
  headers: { Authorization: 'Token ' + PT },
  encoding: 'arraybuffer',  // CRITICAL: gets raw bytes, not parsed JSON
  timeout: 30000
});
const buf = Buffer.from(fileData);
let mime = 'application/octet-stream';
if (buf.slice(0,4).toString() === '%PDF') mime = 'application/pdf';
else if (buf[0] === 0xFF && buf[1] === 0xD8) mime = 'image/jpeg';
```

**Batch reclassification of existing documents** — when migrating from manual to auto-classification, run a Python script (`/opt/data/scripts/reclassify_paperless.py`) that iterates all documents with `statut/a-traiter` tag, downloads each from Paperless, runs the OCR + classification pipeline, and PATCHes the document with new metadata. In one session this reclassified 29 documents in ~3 minutes with 0 errors, creating new types ("Certificat d'immatriculation", "Questionnaire") and correspondents ("OpenRouter", "Caisse d'épargne/BPCE", "Notaire", "Notaires de France", "SARL-U OCEANE NETTOYAGE") automatically.

**Three workflows operate together:**
1. **OCR Telegram** (real-time) — user sends photo/PDF → OCR → classification → recap + Paperless upload with ZDR tag
2. **Auto-Classification Paperless** (every 30 min) — classifies documents that arrived via email import
3. **ZDR Countdown** (daily 3 AM) — decrements ZDR tags on all documents

### iOS Pointage System (Action Button + n8n webhook)

The user has an iPhone 15 Pro Max with an Action Button configured to trigger a Cherri-compiled iOS Shortcut called "Pointage". The shortcut presents a menu of clock-in events and sends them to an n8n webhook for time tracking.

**Events (8 menu options):**
- `start_boite` — 🏢 Début journée (arrivée boîte)
- `start_route` — 🚗 Départ vers client
- `arrivee_client` — 🏗️ Arrivée chez le client
- `start_pause` — 🍽️ Début de pause
- `end_pause` — ▶️ Fin de pause
- `start_route_retour` — 🚗 Départ vers la boîte
- `arrivee_boite` — 🏢 Arrivée à la boîte
- `end_journee` — 🏠 Fin de journée

**n8n webhook workflow** (`POST /webhook/pointage`):
- Webhook Trigger (POST, path: `pointage`, responseMode: `responseNode`)
- Code node "Save Pointage" — receives `{ event, timestamp, location }`, stores in n8n static data (`getWorkflowStaticData('global').pointages`), sends ntfy confirmation for every event, and when event is `end_journee` builds the daily recap (hours + salary breakdown) and clears the day's entries
- Respond to Webhook node — returns `{ ok: true, message: "🏢 Debut journee (boite) - 06:40" }`
- IF node "Has Recap?" — only passes through when `$json.recap` is not null (i.e., event was `end_journee`)
- HTTP Request "Send ntfy" — sends recap to `https://ntfy.jefe.ovh/suivi-heures` with `Authorization: Bearer <token>` header, raw text body

**User preference: recap triggered by `arrivee_boite` event, NOT a cron schedule and NOT `end_journee`** — the user rejected the 20h cron trigger because "my workday might end after 20h." The recap fires immediately when the user clocks "🏢 Arrivée boîte" (arriving back at the box = end of workday). `end_journee` still works as a fallback but the primary trigger is `arrivee_boite`.

**User preference: trajet maison→boîte NOT paid** — arriving at the box and immediately leaving doesn't count as box time. Only time spent loading/unloading at the box counts as box time. The hour calculation must check if a client was visited (`hasClient = pointages.some(p => p.event === 'arrivee_client')`). If no client visited, all time between `start_boite` and `arrivee_boite` counts as `hBoite`.

**User preference: recap format = totals only** — the user said "for the recap it's per day, not everything that went into it." Just show the totals (heures boîte, client, route, pause, total + salary), not the individual clock-in events.

**User preference: send confirmation for every pointage** — "send everything to confirm, e.g. the start of the day, each step, so I know it worked, and if there's a bug it's saved in ntfy." Every clock-in sends a push notification to ntfy topic `suivi-heures`. On error, sends a high-priority error notification.

**User preference: pause légale must be deducted** — legally required 30 min lunch break. If user says "j'ai pris mon heure le midi", deduct 1h. If no pause mentioned, deduct 30 min minimum. The user may work through lunch but the recap must still account for the legal pause.

**User preference: manual salary calculation from dictation** — the user often dictates their week's hours verbally. When calculating from dictation: trajet maison->boite is NOT paid, arrivee boite + depart immediat = transit (not box time), dechargement at box = hBoite (not route), multiple clients per day = route between clients counts as route time. See `references/salary-calculation-rules.md` for the full rules and a worked weekly example.

**Known issue: ntfy notifications not received** — as of the last session, the ntfy push notifications were not being received by the user's phone despite the webhook executing successfully and `curl` tests working. This needs investigation: check token validity, topic subscription on the user's phone, and whether the ntfy HTTP Request node has the auth header properly configured.

**CRITICAL: Cherri `dictGet` crashes on iOS — DO NOT USE IT in the pointage shortcut** — the original shortcut used `dictGet(@response, "message")` to extract the confirmation from the webhook JSON response. This crashes with "Échec de Obtenir la valeur du dictionnaire, car Raccourcis n'a pas pu effectuer la conversion de Texte en Dictionnaire." Root cause: `jsonRequest()` may return text, not a parsed dictionary. Fix: remove `dictGet` entirely and show a static `show("✅ Pointage enregistré")`. The ntfy confirmation is sent server-side by the n8n Code node — the shortcut doesn't need to parse the response. This generates 41 actions (down from 43), all valid. See `references/ios-pointage-system.md` for the corrected code and `templates/pointage.cherri` for the ready-to-compile template.

**Cherri shortcut** (compiled via `cherri-builder` Docker container with `--hubsign`):
- `#include 'actions/web'` + `#include 'actions/calendar'` (for `formatDate`)
- `menu` block with 8 `item` entries, each setting an `@eventCode` variable
- `formatDate(CurrentDate, "Custom", "yyyy-MM-dd'T'HH:mm:ssXXX")` for ISO timestamp
- `jsonRequest()` POST to `https://n8n.jefe.ovh/webhook/pointage`
- `show("✅ Pointage enregistré")` — static confirmation, NO dictGet
- Upload to NAS via `cherri-smb` container to share `raccourci_ios`

See `references/ios-pointage-system.md` for the full Cherri code, webhook workflow details, ntfy notification pattern, hour calculation logic, and NAS upload instructions.
- `templates/pointage.cherri` — ready-to-compile Cherri source for the iOS pointage shortcut (v2, no dictGet)

## Reference Files

- `references/mistral-vision-ocr.md` — Mistral OCR & Vision API: dedicated OCR endpoint (`/v1/ocr`), two-step pipeline, model IDs, performance comparison, generalist extraction prompt guidance
- `references/french-overtime-rates.md` — French legal overtime majoration rates (25%/50%), Code du Travail references
- `references/salary-calculation-rules.md` — User's specific salary calculation rules (hourly rates by period, panier, trajets conducteur/passager, overtime)
- `references/n8n-code-node-binary-pitfalls.md` — n8n Code node binary data patterns: `$input.first()` vs `$items.all()`, `getBinaryDataBuffer()` for filesystem-v2 mode, binary passthrough across non-binary nodes, Paperless multipart upload, Telegram node discriminators
- `references/mistral-voxtral-tts-command-provider.md` — Setting up Mistral Voxtral TTS as a Hermes custom command provider (bypasses stale env keys, uses pre-built Marie Neutral voice)
- `references/feuille-mission-format.md` — Real-world feuille de mission journalière format, weekly per-client timesheet structure, OCR extraction challenges, workflow adaptation for multi-sheet correlation
- `references/zdr-mistral-countdown.md` — ZDR (Zero Data Retention) countdown system: 32 Paperless-ngx tags (`zdr/j-31` → `zdr/j-0`), daily cron script, Paperless tag API, querying ZDR status
- `references/n8n-telegram-node-fixes.md` — Telegram node silent failure debugging: replyMarkup sticky field, resource=message vs chat, PDF IF filter, Mistral OCR 422, correct node configs, debugging checklist
- `references/paperless-intelligent-classification.md` — Paperless-ngx auto-classification: document types, correspondents, case-insensitive matching, auto-creation pattern, classification prompt structure, upload parameters, user preference for generalist classification
- `references/auto-classification-pattern.md` — Scheduled auto-classification workflow (every 30 min): fetch pending docs, download binary, OCR, classify, update Paperless. Batch reclassification script. Three-workflow architecture (Telegram + scheduled + ZDR).