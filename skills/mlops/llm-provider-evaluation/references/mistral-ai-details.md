# Mistral AI — Detailed Evaluation (2026-07)

## Company
- **Registered**: France (Paris)
- **Law**: GDPR + EU AI Act + French Data Protection Act
- **CLOUD Act**: ❌ Not applicable (EU company, no US parent)
- **Regulator**: CNIL (France)

## Certifications
- ✅ SOC 2 Type II
- ✅ ISO 27001 / ISO 27701
- ✅ EU AI Act compliant (general-purpose AI provider)
- ✅ GDPR DPA available

## ZDR — CRITICAL FINDING
**ZDR is ONLY available on the Scale plan (enterprise, custom pricing).**
- Free and pay-as-you-go plans: **30-day retention** of prompts/outputs for abuse monitoring
- No training on customer data (even without ZDR)
- To get ZDR: must contact sales, sign Scale contract
- Source: https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr

## Data retention detail (without ZDR)
| Data | Retained | Duration |
|------|----------|----------|
| Prompts/outputs | ✅ | 30 rolling days |
| Token counts/metadata | ✅ | Billing period |
| Training on data | ❌ Never | — |

## LLM Pricing (per 1M tokens)
| Model | Input | Output | Context | Use case |
|-------|-------|--------|---------|----------|
| Ministral 3B | $0.10 | $0.10 | 128K | Cheapest utility |
| Mistral Small 4 | $0.15 | $0.60 | 128K | Daily tasks, extraction |
| Ministral 8B | $0.15 | $0.15 | 128K | Edge/lightweight |
| Ministral 14B | $0.20 | $0.20 | 262K | Small+ |
| Mistral Medium 3 | $0.40 | $2.00 | 131K | Reasoning |
| Mistral Medium 3.5 | $1.50 | $7.50 | 262K | Highest quality |
| Mistral Large 3 | $0.50 | $1.50 | 262K | Flagship |
| Codestral | $0.30 | $0.90 | — | Code |
| Magistral Medium | $2.00 | $5.00 | — | Reasoning |
| Pixtral 12B | $0.15 | $0.15 | 128K | Vision |

## OCR / Document AI — Major advantage
| Service | Standard | Batch (async) |
|---------|----------|---------------|
| OCR 3 | $2 / 1000 pages | $1 / 1000 pages |
| OCR + annotations | $3 / 1000 pages | — |

**OCR price comparison**:
- Mistral OCR 3: $2/1000p
- Azure Form Recognizer: $1.50-$6/1000p
- Google Document AI: $30-45/1000p
- AWS Textract: $65/1000p

Mistral is 97% cheaper than AWS Textract for structured document extraction.
OCR 3 achieves 98%+ accuracy, natively multilingual (99.20% fuzzy match on French).

## API
- OpenAI-compatible endpoint
- Python SDK: `from mistralai.client import Mistral`
- OCR API: `client.ocr.process(model="mistral-ocr-latest", document={...})`
- EU hosted by default

## Limitations
- Only Mistral models (no GLM, DeepSeek, Kimi, MiniMax)
- ZDR requires enterprise contract (Scale plan)
- 30-day data retention without Scale plan
- One account per person

## Use case assessment
- ✅ Excellent for OCR/document processing ($2/1000p, EU, SOC 2 + ISO 27001)
- ✅ Good for LLM if Mistral models suffice (Small 4 is cheap at $0.15/$0.60)
- ⚠️ 30-day retention is a compromise for sensitive docs without Scale plan
- ❌ No open-weight models (GLM, DeepSeek, etc.)