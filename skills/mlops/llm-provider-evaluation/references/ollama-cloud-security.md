# Ollama Cloud & Security — Deep Dive (2026-07)

## Privacy Policy (March 2026)

### Local models (safe)
- No data collected — prompts, responses, interactions stay on machine
- Collects only: device metadata (app version, request counts, IP, OS)
- Local history in `~/.ollama/history` (disable: `OLLAMA_KEEP_HISTORY=false`)

### Cloud models (:cloud tag)
- Prompts/responses processed transiently, not stored beyond request time
- Never used for training
- Technical measures to minimize retention
- Partner NCPs under "no logging, no training, zero data retention" contracts

### What they collect
| Type | Detail |
|------|--------|
| Account | name, email, user ID |
| Payment | via Stripe |
| Device | IP, OS, browser, country |
| Usage | request counts (NOT content) |

### What they DON'T collect
- ❌ Prompt/response content (local)
- ❌ Cloud storage beyond request
- ❌ Training on data
- ❌ Selling data

## Critical concerns

### 1. No SOC 2, no ISO 27001, no third-party audit
- 21-person team
- ZDR is a vendor promise, not certifiable
- No way to technically verify ZDR is active (unlike Azure OpenAI's ContentLogging: false)

### 2. "Local-first" branding as trojan horse (HN)
- `ollama run glm-5.2:cloud` looks identical to local commands
- Same CLI, same API (localhost:11434), same libraries
- No warning when data leaves machine
- `OLLAMA_NOCLOUD=1` exists but is opt-in (default allows cloud)
- Cloud models show alongside local in `ollama ls` — only diff is `-` for size

### 3. Unknown proxy behavior
- Does `glm-5.2:cloud` proxy to Z.ai (formerly Zhipu AI, Chinese AI lab)?
- Ollama says "NVIDIA Cloud Provider infrastructure" but models are from Z.ai
- Who actually sees the prompts? Unverified

### 4. Jurisdiction
- Data transits through US → subject to CLOUD Act, FISA 702
- May also route to Singapore — different jurisdiction, same concerns
- For EU users: transborder data transfers without adequate safeguards

### 5. CVE-2026-7482 "Bleeding Llama" (May 2026)
- **CVSS 9.1-9.3 CRITICAL**
- Heap out-of-bounds read in GGUF model loader
- ~300,000 Ollama servers exposed on public internet
- Unauthenticated — 3 API calls to exploit
- **What attacker can steal**:
  - All prompts and messages in memory
  - Environment variables (API keys, tokens, secrets)
  - Source code submitted to AI
  - Tool outputs from agentic integrations
- **Attack**: upload crafted GGUF → trigger model creation (OOB read) → push model with heap data to attacker server
- **Fix**: Ollama 0.17.1+
- **Disclosure**: Cyera Research, May 5, 2026

### 6. Missing privacy policy at launch
- Cloud models launched Sep 2025 without public privacy policy
- Current policy added after community criticism
- Closed-source models (MiniMax, GLM) add opacity — what do model creators do with data?

## Pricing
| Plan | Price | Concurrency | Notes |
|------|-------|-------------|-------|
| Free | $0 | 1 model | Light usage |
| Pro | $20/mo | 3 models | 50x more usage than Free |
| Max | $100/mo | 10 models | Paused for new signups |

## Infrastructure
- "Primarily US, may route to Europe and Singapore"
- NVIDIA Cloud Providers (NCPs)
- Native weights from model providers

## Risk assessment for homelab
- If port 11434 is exposed (Pangolin, NAT): CVE-2026-7482 risk
- Check version: must be ≥ 0.17.1
- Set `OLLAMA_NOCLOUD=1` for local-only mode
- Ensure firewall blocks external access to 11434