---
name: llm-provider-evaluation
description: "Use when vetting LLM providers for privacy or compliance."
---

# LLM Provider Evaluation

## When to use
- User asks to research/compare AI inference providers
- User wants to verify privacy/ZDR/GDPR claims before adopting a provider
- User needs cost comparison between providers
- User wants community sentiment (Reddit, HN, X) about a provider

## Methodology (ordered)

### 1. Official documents first
Extract and analyze:
- **Privacy Policy** — look for "zero data retention", "ephemeral", "not stored", "not logged"
- **Terms of Service** — Controller vs Processor role, jurisdiction, liability caps
- **DPA** (Data Processing Agreement) — GDPR Article 28 compliance
- **Pricing page** — per-token vs subscription, markup layers, hidden costs (cache read pricing)
- **Trust/Security page** — datacenter locations, encryption, certifications (SOC 2, ISO 27001)

Key distinction: **policy promise** ("we don't store") vs **architectural guarantee** ("ephemeral enclaves, no disk writes, stateless processing"). The latter is verifiable; the former is trust.

### 2. Community sentiment (Reddit, HN, X)
Search patterns:
- `site:reddit.com "<provider>" review experience privacy`
- `site:news.ycombinator.com "<provider>"`
- `site:x.com "<provider>" privacy data`
- `"<provider>" review experience feedback 2025 2026`

Look for:
- **HN launch threads** — founders respond, users critique transparently
- **Reddit r/ollama, r/LocalLLaMA, r/LocalLLM** — power user feedback
- **Negative reviews** — price complaints, reliability issues, hidden costs
- **Comparisons** — users who switched between providers and why

### 3. Security advisories
Search:
- `CVE <provider>` — known vulnerabilities
- `<provider> vulnerability security breach`
- Shodan/exposure data if self-hosted (e.g. Ollama CVE-2026-7482 "Bleeding Llama")

### 4. Cross-reference claims vs reality
Common gaps to check:
- Homepage says "EU only" but provider list includes AWS/Microsoft (US parent then CLOUD Act)
- "Zero data retention" promised but no audit/SOC 2 to prove it
- Router/gateway providers forward to upstream providers - ZDR depends on the upstream, not the router
- "EU hosted" on US hyperscaler is not EU sovereign (parent company subject to US surveillance law)

### 5. Cost analysis
- Subscription (flat rate) vs per-token (usage-based)
- For per-token: estimate monthly tokens (conversations/day x avg tokens x 30)
- Check cache read pricing (can be 100x different between providers)
- Markup layers (router adds % on top of provider token cost)
- Compare at user's actual usage level, not advertised "savings"

## Key evaluation criteria

| Criterion | What to check |
|-----------|--------------|
| Jurisdiction | Company registration, datacenter location, US parent? |
| CLOUD Act | EU company with no US parent = not subject |
| ZDR type | Policy promise vs architectural guarantee |
| ZDR proof | SOC 2, ISO 27001, third-party audit, or just "trust us" |
| Model hosting | Self-hosted open weights vs proxy to creator API |
| GDPR role | Processor (good) vs Controller, DPA available |
| Breach notification | 72h per GDPR Art 33 |
| Sub-processors | Public list, vetted, EU-only? |
| Community trust | HN/Reddit sentiment, track record |
| Reliability | 503/error rates, status page, uptime |

## Red flags
- "EU cloud" but company is US-owned (CLOUD Act applies)
- Router that includes US providers but markets as "EU sovereign"
- No public pricing (token costs hidden behind signup)
- ZDR claimed but no audit/SOC 2/ISO 27001
- **ZDR marketed as available but actually requires enterprise plan** (Mistral: ZDR is Scale-only, Free/PAYG retain 30 days)
- Young startup with strong promises but no track record
- Cache read pricing 100x higher than direct provider (EURouter/TensorX DeepSeek cache: $0.44 vs $0.003625 direct)
- Homepage looks "vibecoded" (AI-generated) for a security-sensitive service
- Cloud models that look identical to local in CLI (Ollama `:cloud` tag — no warning when data leaves machine)

## Pitfalls learned from session

### Mistral ZDR trap
Mistral markets SOC 2 + ISO 27001 + EU + GDPR, but **ZDR is only on Scale plan (enterprise)**.
Free and pay-as-you-go plans retain prompts/outputs for **30 days**. This is NOT in the
marketing pages — it's buried in the help center. Always check the ZDR plan requirements,
not just whether ZDR exists. See `references/mistral-ai-details.md`.

### Ollama Cloud UX trap
`ollama run glm-5.2:cloud` uses the same CLI/API as local models. No warning that data
leaves the machine. `OLLAMA_NOCLOUD=1` is opt-in. CVE-2026-7482 (Bleeding Llama, CVSS 9.1)
affects all pre-0.17.1 instances with port 11434 exposed. See `references/ollama-cloud-security.md`.

### Router vs hoster distinction
EURouter is a **router** (forwards to TensorX, AWS, Microsoft) — not a host. Its "EU only"
promise depends on which provider you select. TensorX is the actual **host** (owns GPUs in
Dublin/Helsinki). Routers add markup (EURouter: 3-15%) on top of the underlying provider.
Always go direct to the host when possible.

## EU sovereign providers (as of 2026-07)

See `references/eu-providers-comparison.md` for the full comparison matrix.

### Detailed reference files
- `references/eu-providers-comparison.md` — Full tier-based comparison table
- `references/mistral-ai-details.md` — Mistral pricing, ZDR plan trap, OCR advantage
- `references/ollama-cloud-security.md` — Ollama privacy policy, CVE-2026-7482, UX trap
- `references/eden-ai-details.md` — Eden AI certifications, pricing, n8n integration, capabilities

### Quick decision matrix

| Need | Best choice | Why |
|------|------------|-----|
| Max privacy (sensitive docs) | Local model (gpt-oss-20b) | Zero network transit |
| EU sovereign + your models (GLM, MiniMax) | TensorX direct | ZDR architectural, hosts own weights |
| SOC 2 + ISO 27001 certified | Eden AI EU endpoint | Only EU provider with both certs + ZDR by default |
| Cheapest OCR ($2/1000p) | Mistral OCR 3 | 97% cheaper than AWS, 98%+ accuracy |
| Cheapest flat-rate LLM | Ollama Cloud ($20/mo) | But US jurisdiction, no certs |
| Cheapest per-token LLM | TensorX or Mistral Small 4 | Both EU, pay-as-you-go |