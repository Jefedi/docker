# Eden AI — Detailed Evaluation (2026-07)

## Company
- **Registered**: France
- **Endpoint EU**: `https://api.eu.edenai.run/v3/`
- **Standard endpoint**: `https://api.edenai.run/v3/` (global, non-EU routing)
- **CLOUD Act**: ❌ Not applicable (EU company)

## Certifications — THE differentiator
- ✅ SOC 2 certified
- ✅ ISO 27001 certified
- ✅ GDPR compliant, DPA available
- ✅ Zero Data Retention by default (not opt-in)
- ✅ No training on customer data
- ✅ EU data residency endpoint

## Pricing model
- **No subscription** — pay-as-you-go
- **0% markup** on provider prices
- **5.5% platform fee** applied at credit purchase
- Credits deducted per API call
- Auto-refill optional (threshold-based)
- Payment: credit card or bank transfer (Stripe)

## ZDR details
- Prompts, uploaded files, and model outputs are NOT retained by default
- Data processed only for duration of request
- EU endpoint: if model not available in EU → request **blocked** (not routed to US)
- SOC 2 + ISO 27001 provide third-party validation of ZDR claims

## Capabilities (beyond LLMs)
| Capability | Providers (EU) | Use case |
|-----------|---------------|----------|
| OCR multi-page | Google Vision EU, AWS Textract EU, Mindee | Document text extraction |
| Invoice parser | Mindee, Google, AWS, Base64 | Invoice → structured data |
| Receipt parser | Mindee, Google, Taggun | Receipts |
| ID/Passport parser | Mindee, Amazon | Identity documents |
| Table OCR | Google, AWS, Microsoft EU | Tables in PDFs |
| Document data extraction | Multiple EU providers | Custom field extraction |
| Language detection | Google, Amazon, OpenAI EU | Auto language ID |
| Translation | DeepL, Google, AWS, Microsoft | Translation |
| Summarization | Multiple EU LLMs | Document summaries |
| Sentiment analysis | Multiple | Text analysis |
| Speech recognition | Multiple EU | STT |
| Speech generation | Multiple EU | TTS |
| Image generation | Multiple | Visual content |

## n8n integration
- No native n8n node — use HTTP Request node
- Auth: Header Auth → `Authorization: Bearer <api_key>`
- Tutorial: https://www.edenai.co/post/a-step-by-step-guide-to-implementing-ai-in-your-app-with-n8n
- Pattern: Telegram trigger → HTTP Request (Eden AI) → Move binary data → Telegram send

## Key advantages over alternatives
| vs | Advantage |
|----|-----------|
| TensorX | SOC 2 + ISO 27001 certified (TensorX: in progress) |
| Mistral | ZDR by default (Mistral: 30-day retention, ZDR enterprise only) |
| EURouter | 5.5% fee (EURouter: 15% markup + €39/mo subscription) |
| Ollama Cloud | EU sovereign + certified (Ollama: US, no certs) |

## Limitations
- Router/gateway — forwards to upstream providers (not self-hosted inference)
- ZDR depends on upstream provider compliance, but Eden AI enforces at gateway level
- LLM model availability on EU endpoint needs verification (glm-5.2 may not be available)
- Per-request pricing can add up at high volume
- No node n8n natif (HTTP Request required)

## Cost examples
- Invoice parsing (Mindee EU): ~$0.05-0.15/invoice + 5.5% = ~$0.05-0.16
- OCR multi-page (Google EU): ~$1.50/1000 pages + 5.5% = ~$0.0016/page
- 50 documents/month: ~$3-8/month total