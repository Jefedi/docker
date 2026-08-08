# EU Sovereign LLM Providers Comparison (2026-07)

## Tier 1: Sovereign Inference (self-hosted open weights on EU GPUs)

### TensorX (eurouter.ai redirects here)
- **Company**: TensorX Ltd, Ireland (№796387)
- **Datacenters**: Dublin (Digital Realty) + Helsinki (Verda), Tier III+
- **GPUs**: NVIDIA Blackwell B300 (€8M committed)
- **ZDR**: Architectural — ephemeral enclaves, no disk writes, stateless
- **GDPR**: Processor, DPA auto-incorporated, Art 33 breach notif 72h
- **Certifications**: ISO 27001 in progress, SOC 2 planned, NVIDIA Inception
- **Models**: glm-5.2 ($1.50/$4.50), minimax-m3 ($0.40/$2.00), deepseek-v4-pro ($1.75/$3.50), deepseek-v4-flash ($0.15/$0.30), kimi-k2.6 ($1.00/$4.00), kimi-k2.7-code ($1.25/$4.50), gpt-oss-120b ($0.04/$0.20), + 17 more
- **Pricing**: Pay-as-you-go per 1M tokens, no subscription, no minimum
- **API**: OpenAI-compatible (`https://api.tensorx.ai/v1`)
- **Key advantage**: No proxy to model creators — hosts open weights on own infra
- **Key risk**: Young startup (seed €8M, late 2025), no public audit yet
- **Community**: HN users prefer TensorX over EURouter ("EURouter wanted 15% more money")

### Regolo.ai
- **Company**: Italy
- **ZDR**: Zero retention by default, OpenAI-compatible
- **Pricing**: Token-based
- **Note**: Smaller catalog, focused on Italian/EU market

## Tier 2: EU Routers/Gateways (forward to upstream providers)

### EURouter (eurouter.ai)
- **Company**: EUrouter B.V., Amsterdam (KVK 42054357)
- **Model**: Router/gateway — forwards to providers (TensorX, AWS Bedrock, Microsoft Foundry)
- **Pricing**: Free (15% markup), Plus €39/mo (9%), Pro €99/mo (3%) + token costs
- **ZDR**: Claims EU-only but includes US providers (AWS, Microsoft) in provider list
- **Critical issue**: HN user "7bit" — homepage promise "all requests in EU" vs privacy policy "routed to provider you select" + AWS/Microsoft US listed = "blatant lie"
- **Community sentiment**: Mostly negative on price ("ridiculous 15% markup"), "found a niche to milk"
- **Note**: TensorX is both cheaper and more sovereign when used directly

### Requesty EU
- **Company**: Germany
- **Endpoint**: Frankfurt (`router.eu.requesty.ai`)
- **Models**: Claude, GPT, Gemini, Mistral via EU regions
- **GDPR**: DPA available, EU data residency per model family
- **Note**: Routes to AWS Bedrock EU / Azure OpenAI EU — better than US-direct but parent companies still US

### Eden AI
- **Company**: France
- **Certifications**: ✅ SOC 2 + ✅ ISO 27001 + ✅ ZDR by default + ✅ GDPR DPA
- **EU endpoint**: `https://api.eu.edenai.run/v3/` (blocks non-EU requests, no US fallback)
- **Models**: 500+ (LLMs + OCR, speech, translation, embeddings, image)
- **Pricing**: No subscription, 0% markup on providers, 5.5% platform fee at credit purchase
- **Capabilities**: OCR, invoice parsing, receipt parsing, ID parsing, table OCR, translation, summarization, sentiment, STT, TTS, image gen
- **n8n**: HTTP Request node (no native node), official tutorial available
- **ZDR**: Enforced at gateway level, prompts/files/outputs never retained
- **Key advantage**: ONLY EU provider with both SOC 2 AND ISO 27001 certified + ZDR by default
- **Key limitation**: Router (not host) — ZDR depends on upstream provider; LLM model availability on EU endpoint needs verification
- **See**: `references/eden-ai-details.md`

## Tier 3: US Providers with EU Regions (NOT sovereign)

### Azure OpenAI (EU regions)
- EU data residency via EU Data Boundary
- Parent Microsoft = US → CLOUD Act applies
- ZDR configurable but not default

### AWS Bedrock (EU regions)
- Frankfurt/Ireland/Paris/Stockholm regions
- Parent Amazon = US → CLOUD Act applies
- ZDR toggle available on some providers

### Ollama Cloud
- Company: Ollama Inc, US
- Datacenters: "Primarily US, may route to Europe and Singapore"
- ZDR: Policy promise ("not stored beyond request"), no architectural proof
- No SOC 2, no ISO 27001, no audit
- CLOUD Act applies (US company)
- Models may proxy to original creators (Z.ai, MiniMax) — unverified
- CVE-2026-7482 "Bleeding Llama" — CVSS 9.1, 300K servers exposed
- Pricing: $20/mo Pro (flat rate, usage within limits)

## Tier 4: EU Model Providers (own models, not open-weight hosting)

### Mistral AI
- **Company**: France (Paris)
- **Certifications**: ✅ SOC 2 Type II + ✅ ISO 27001/27701
- **CLOUD Act**: ❌ Not applicable
- **ZDR**: ⚠️ **Scale plan ONLY** (enterprise, custom pricing). Free/PAYG = 30-day retention
- **No training** on customer data (even without ZDR)
- **Models**: Mistral only (Large 3, Medium 3.5, Small 4, Ministral, Codestral, Pixtral, Magistral)
- **OCR 3**: $2/1000 pages ($1/1000 batch) — 97% cheaper than AWS Textract
- **LLM pricing**: Small 4 $0.15/$0.60, Large 3 $0.50/$1.50, Medium 3.5 $1.50/$7.50
- **Key advantage**: Cheapest OCR on the market + SOC 2 + ISO 27001 + EU
- **Key limitation**: ZDR requires enterprise contract; only Mistral models (no GLM/DeepSeek/Kimi)
- **See**: `references/mistral-ai-details.md`

## Decision framework

| Need | Best choice |
|-----|-------------|
| Max privacy (sensitive docs) | Local model (gpt-oss-20b on jTower) |
| EU sovereign + open-weight models | TensorX direct |
| SOC 2 + ISO 27001 + ZDR by default | Eden AI EU endpoint |
| Cheapest OCR | Mistral OCR 3 ($2/1000p) |
| Cheapest flat-rate LLM | Ollama Cloud (but US jurisdiction) |
| Mistral models only | Mistral AI direct |
| EU gateway for multiple providers | Requesty EU (if OK with US parent companies) |
| Broadest model catalog | Eden AI |