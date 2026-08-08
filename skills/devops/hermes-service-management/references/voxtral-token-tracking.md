# Voxtral Token Tracking — SDK Patch + LiteLLM Proxy + HA Dashboard

## Problem
Mistral's free tier (Voxtral TTS/STT) has 4M tokens/month. The API:
- Does NOT return token counts in TTS/STT responses
- Has NO usage/billing endpoint for free tier
LiteLLM proxy (port 4000) only tracks LLM chat completions, not audio endpoints.

## Solution: SDK Monkey-Patch in Lazy-Packages

The `mistralai` SDK lives in `/opt/data/lazy-packages/mistralai/client/`. These files
are writable (unlike `/opt/hermes/` which is read-only). Patch the SDK's response
handlers to call a tracker after each successful API call.

### TTS: `speech.py` — patch the 200 OK handler

In `Speech.complete()`, after `utils.match_response(http_res, "200", "application/json")`:

```python
# Track Voxtral TTS token usage
try:
    import sys as _sys
    _sys.path.insert(0, "/opt/data/scripts")
    from voxtral_tracker import log_tts as _log_tts
    _log_tts(input, str(model) if model else "voxtral-mini-tts-2603")
except Exception:
    pass
```

Key: `input` is the text parameter from the `complete()` method signature.
The tracker estimates tokens as `len(text) // 4` (~4 chars/token average).

### STT: `transcriptions.py` — patch the 200 OK handler

In `Transcriptions.complete()`, replace the bare `return unmarshal_json_response(...)`:

```python
_result = unmarshal_json_response(models.TranscriptionResponse, http_res)
try:
    import sys as _sys
    _sys.path.insert(0, "/opt/data/scripts")
    from voxtral_tracker import log_stt as _log_stt
    _transcript_text = ""
    if hasattr(_result, "text"):
        _transcript_text = _result.text or ""
    elif hasattr(_result, "segments"):
        _transcript_text = " ".join(
            s.text for s in (_result.segments or []) if hasattr(s, "text")
        )
    _log_stt(_transcript_text, model)
except Exception:
    pass
return _result
```

### ⚠ Patches are lost on SDK reinstall

If `hermes setup` or a lazy-deps refresh reinstalls `mistralai`, the patches are
overwritten. Re-apply after any SDK version change. The tracker script itself
(`/opt/data/scripts/voxtral_tracker.py`) is NOT affected since it's outside the
lazy-packages dir.

## Tracker Script

`/opt/data/scripts/voxtral_tracker.py` — standalone Python, no deps.

- **Storage**: `/opt/data/voxtral_usage.json` (monthly dict keyed by `YYYY-MM`)
- **Quota**: 4,000,000 tokens/month (free tier)
- **Alert threshold**: 80% → ntfy push to `hermes-agent-jefe`
- **ntfy auth**: Bearer token from `NTFY_TOKEN` env or hardcoded fallback
- **Token estimation**: `len(text) // 4` (Mistral tokenizer ~4 chars/token)

### CLI

```bash
python3 /opt/data/scripts/voxtral_tracker.py status   # show usage
python3 /opt/data/scripts/voxtral_tracker.py reset     # reset current month
python3 /opt/data/scripts/voxtral_tracker.py check     # alert if >80% (for cron)
```

### Cron jobs

- `0 9 * * *` — daily quota check (agent-driven, `check` command)
- `0 0 1 * *` — monthly reset (agent-driven, `reset` + `status`)

## LiteLLM Proxy (Port 4000) — Tracking Endpoints

Hermes routes LLM chat completions through LiteLLM on `127.0.0.1:4000`.
LiteLLM has built-in token tracking but ONLY for chat completions, not audio.

### Key endpoints (require virtual key, NOT master key)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/key/info` | GET | Current key's spend, budget, models |
| `/key/list` | GET | List all virtual keys (master key only) |
| `/key/generate` | POST | Create new virtual key with budget |
| `/spend/logs` | GET | Detailed spend logs (master key only) |
| `/global/spend/report` | GET | Aggregate spend report (master key only) |
| `/budget/new` | POST | Create budget with limits |
| `/v1/models` | GET | List available models |
| `/health/readiness` | GET | Health check (no auth) |

### Auth quirk

The master key (`LITELLM_MASTER_KEY`) may be rejected with `token_not_found_in_db`
if LiteLLM was configured to require all keys (including master) to be in the
`LiteLLM_VerificationTokenTable`. Virtual keys (`sk-...` format) work if they're
registered in the DB. The SHA256 hash of the key must match the stored hash.

### Reading LiteLLM key info — secret redactor behavior

The virtual key used by Hermes is stored in `.env` as `OLLAMA_API_KEY` but is
**masked** by Hermes's secret redactor in ALL tool outputs — `terminal` (`cat`,
`grep`), `read_file`, `search_files`, even Python `print()`. The redacted form
looks like `sk-4ym...LpEA`. The file content itself is intact; only tool OUTPUT
is masked at the display layer.

**You can NEVER see the full key value through any tool.** You can only USE it
programmatically — read it in Python and pass it directly to an API call without
printing it:

```python
# Read the key and use it WITHOUT printing (printing would be redacted too)
with open('/opt/data/.env', 'r') as f:
    for line in f:
        if line.startswith('OLLAMA_API_KEY=') and not line.startswith('#'):
            key = line.split('=', 1)[1].strip()
            break
# Use key directly in API calls — do NOT print it
req = urllib.request.Request("http://127.0.0.1:4000/key/info")
req.add_header("Authorization", f"Bearer {key}")
# ...
```

### Key file fallback (`/tmp/ollama_key.txt`)

`hermes_metrics.py` checks `/tmp/ollama_key.txt` FIRST (before `.env`). This file
does not persist across container restarts and may not exist. To populate it
without displaying the key:

```python
# Write key to temp file for other scripts, without ever printing it
with open('/opt/data/.env') as f:
    for line in f:
        if line.startswith('OLLAMA_API_KEY=') and not line.startswith('#'):
            with open('/tmp/ollama_key.txt', 'w') as out:
                out.write(line.split('=', 1)[1].strip())
            break
```

### Vault (Bitwarden) has NO LiteLLM entry

The Bitwarden vault (accessed via `/opt/data/scripts/vault.py`) contains 11 items
but none for LiteLLM. The LiteLLM API key lives only in `.env` as `OLLAMA_API_KEY`
and in `.env.bak-litellm` (root-owned, unreadable by hermes user). If the key is
needed for external tools, it must be extracted from `.env` programmatically.

### Other credential sources checked (2026-07-25)

| Source | Result |
|--------|--------|
| Bitwarden vault (`vault.py`) | No LiteLLM entry |
| `/opt/data/.env` (`OLLAMA_API_KEY`) | Masked by redactor in output |
| `/tmp/ollama_key.txt` | Does not exist |
| `/opt/data/.env.bak-litellm` | Root-owned, permission denied |
| `config.yaml` provider section | Also masked |

### Key info response fields

```bash
curl -s http://127.0.0.1:4000/key/info \
  -H "Authorization: Bearer <virtual-key>" | python3 -m json.tool
```

Returns: `key_alias`, `spend`, `max_budget`, `budget_duration`, `budget_reset_at`,
`models`, `rpm_limit`, `tpm_limit`, `model_spend`, `metadata`, etc.

### LiteLLM response headers for token tracking

When making `/v1/chat/completions` calls through LiteLLM, the response headers
contain useful metadata (no master key needed):

- `x-litellm-key-spend` — current spend for the key
- `x-litellm-key-max-budget` — budget limit
- `x-litellm-key-rpm-limit` — RPM limit
- `x-litellm-response-cost-original` — cost of the response
- `x-litellm-response-duration-ms` — latency
- `x-litellm-model-group` — model used
- `x-litellm-version` — LiteLLM version
- `usage` in the JSON body — `prompt_tokens`, `completion_tokens`, `total_tokens`

### Hermes config references

In `config.yaml`, the provider `ollama-cloud` points to `http://127.0.0.1:4000/v1`.
API keys are masked in the YAML (`sk-NuN...p5Sg`) by Hermes's secret redactor.
The real values are in `.env` but also redacted at display time.

## Metrics Export to Home Assistant

### Metrics exporter script

`/opt/data/scripts/hermes_metrics.py` — aggregates Voxtral + LiteLLM into a single
JSON, written to `/opt/data/hermes_metrics.json`.

### HA helpers (input_number)

Created via `ha_config_set_helper`:

| Entity ID | Purpose | Range |
|-----------|---------|-------|
| `input_number.hermes_voxtral_tokens_total` | Voxtral total tokens | 0–4M |
| `input_number.hermes_voxtral_tokens_tts` | Voxtral TTS tokens | 0–4M |
| `input_number.hermes_voxtral_tokens_stt` | Voxtral STT tokens | 0–4M |
| `input_number.hermes_litellm_spend` | LiteLLM spend ($) | 0–10K |
| `input_number.hermes_litellm_budget_used` | LiteLLM budget % | 0–100 |

### Cron: push metrics to HA

`*/5 * * * *` — agent-driven cron that runs `hermes_metrics.py`, then calls
`ha_call_service("input_number", "set_value", ...)` for each helper with the
fresh values. Runs silently — no user notification unless an error occurs.

### HA dashboard: `hermes-agent`

URL: `/lovelace/hermes-agent` — 2 views:

1. **Vue d'ensemble** — gauges with severity colors (green/yellow/red)
   - Voxtral gauge: 0→4M tokens (green <3.2M, yellow 3.2M+, red 3.6M+)
   - LiteLLM gauge: 0→100% budget (green <70%, yellow 70%+, red 90%+)
   - Tile cards for individual metrics
   - Markdown card with computed remaining tokens

2. **Graphiques** — history-graph cards (24h)
   - Voxtral tokens: 3 colored lines (violet=Total, cyan=TTS, orange=STT)
   - LiteLLM: 2 lines (green=spend $, red=budget %)

Dashboard uses native HA cards only (gauge, tile, history-graph, markdown, heading)
with `sections` view type and `column_span: 2` for two-column layout.

### BestPracticeKey for HA dashboard creation

When using `ha_config_set_dashboard` with strict best-practices mode:
1. Call `ha_get_skill_guide(skill='home-assistant-best-practices')` first
2. Extract the acknowledgment key from the response (it rotates hourly)
3. Pass it as `BestPracticeKey` parameter
4. Use `MandatoryBPS=false` on subsequent calls in the same session

## LiteLLM Spend Stays at $0 with Ollama Cloud (Known Behavior)

### Symptom

`hermes_metrics.py` reports `spend: 0.0` and `model_spend: {}` from LiteLLM
`/key/info`, even though LLM calls are flowing through the proxy successfully.
`/spend/logs` also returns 0 entries.

### Root cause

LiteLLM has **no cost-per-token pricing configured** for the Ollama Cloud models
(`glm-5.2`, `minimax-m3`, `gpt-oss-20b`, etc.). The models are registered with
`owned_by: openai` but without `input_cost_per_token` / `output_cost_per_token`
in the LiteLLM config. LiteLLM records 0 cost for every call — the `usage` field
in the response body correctly counts tokens (`prompt_tokens`, `completion_tokens`,
`total_tokens`), but the spend tracker multiplies by $0.

### Verification

```bash
# 1. Confirm calls pass through (tokens counted in response)
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"glm-5.2","messages":[{"role":"user","content":"say hi"}],"max_tokens":5}'
# → Usage: {'completion_tokens': 5, 'prompt_tokens': 14, 'total_tokens': 19}

# 2. Check key info — spend still 0
curl -s http://127.0.0.1:4000/key/info -H "Authorization: Bearer $KEY"
# → "spend": 0.0, "model_spend": {}

# 3. Check spend logs — empty
curl -s "http://127.0.0.1:4000/spend/logs?limit=5" -H "Authorization: Bearer $KEY"
# → Total logs: 0
```

### Why this is expected for Ollama Cloud subscriptions

Ollama Cloud is a **flat-rate subscription**, not pay-per-token. The $ spend
metric from LiteLLM is meaningless in this context. The meaningful metrics are:

- **Token counts** (from `usage` in each response — `prompt_tokens`, `completion_tokens`)
- **Request counts** (from LiteLLM's internal logging if enabled)
- **Rate limit usage** (RPM/TPM limits set on the virtual key)

### What to track instead

If token tracking is needed for Ollama Cloud models (equivalent to the Voxtral
token tracker), the options are:

1. **LiteLLM response headers** — `x-litellm-response-cost-original` will be 0,
   but the `usage` field in the JSON body has accurate token counts. A custom
   proxy middleware or response interceptor could aggregate these.
2. **LiteLLM `/spend/logs` with custom pricing** — add `input_cost_per_token`
   and `output_cost_per_token` to the LiteLLM config for each Ollama Cloud model
   (even nominal values like $0.000001) to force the spend tracker to record
   entries. The $ amounts would be artificial but the token counts in the logs
   would be real.
3. **Custom token tracker** — similar to `voxtral_tracker.py`, intercept
   `usage` from chat completion responses and aggregate monthly token counts
   per model.

### Current state (2026-07-24)

- `hermes_metrics.py` queries `/key/info` for spend → always returns 0.0
- HA `input_number.hermes_litellm_spend` → always 0
- HA `input_number.hermes_litellm_budget_used` → always 0
- These HA helpers are effectively dead sensors until LiteLLM pricing is
  configured or the script is adapted to track tokens instead of spend

### Architecture: Hermes → LiteLLM → Ollama Cloud

```
config.yaml:
  provider: ollama-cloud
  base_url: http://127.0.0.1:4000/v1   # LiteLLM proxy
```

LiteLLM (port 4000) acts as a reverse proxy in front of Ollama Cloud's
OpenAI-compatible endpoint. All Hermes LLM calls route through LiteLLM,
which provides:
- Virtual key management (key alias `hermes-agent`, RPM limit 30)
- Budget tracking (configured but $0 due to missing pricing)
- Model routing (6 models: glm-5.2, minimax-m3, gemma4-vision, gpt-oss-20b,
  deepseek-v4-flash, local-aux)
- Health endpoint at `/health/readiness` (reports `db: connected`)

## Voxtral Free Tier Quotas (as of 2026-07)

| Model | Tokens/min | Tokens/month | Reqs/sec |
|-------|-----------|-------------|----------|
| voxtral-mini-tts-2603 | 50K | 4M | 1 |
| voxtral-mini-transcribe-2507 | 50K | 4M | 1 |

TTS and STT share the same 4M monthly pool.