# Sealed Venv Package Install Reference

In Docker deployments (`HERMES_DISABLE_LAZY_INSTALLS=1`, `HERMES_LAZY_INSTALL_TARGET` set in `.env`):

## Diagnostic checklist (ordered)

When STT/TTS with a lazy-installed provider is not working, check in this order:

1. **API key valid?** — Test directly against the provider's API. An expired key (401) is the most common and cheapest-to-check cause.
2. **`HERMES_LAZY_INSTALL_TARGET` set?** — Without it, no lazy packages are found. Check `.env`.
3. **Package installed in target dir?** — `ls /opt/data/.local/lib/python3.13/site-packages/mistralai/`
4. **Correct version?** — Must match the pin in `lazy_deps.py` exactly. Don't upgrade — newer versions have breaking API changes.
5. **Gateway restarted after install?** — `_HAS_*` flags are cached at module import time.
6. **Config set explicitly?** — `stt.provider: mistral` and `tts.provider: mistral` must be set in config.yaml. Auto-detect may skip Mistral.

## API key validity — check FIRST

Before debugging package installation, test the API key directly against the provider. An expired/revoked key gives the same end-user symptom ("STT/TTS doesn't work") but no amount of package reinstalling will fix it.

```bash
# Mistral API key test (TTS endpoint)
PYTHONPATH=/opt/data/.local/lib/python3.13/site-packages /opt/hermes/.venv/bin/python3 -c "
from mistralai.client import Mistral
client = Mistral(api_key='YOUR_KEY')
try:
    with client as c:
        r = c.audio.speech.complete(
            model='voxtral-mini-tts-2603',
            input='test',
            voice_id='Almes',
            response_format='mp3'
        )
        print('API key OK')
except Exception as e:
    print(f'API ERROR: {e}')
"
```

If you get `Status 401` or `Unauthorized`, the key is expired OR the provider quota is exhausted. Check both:
- **Expired key**: get a new one from https://console.mistral.ai/.
- **Quota exhausted**: Mistral's free tier has monthly usage limits. When at 100%, the API returns 401 until the quota resets (can be 6+ days). Check the provider's dashboard. Switch to free fallback providers until the quota resets.

## HERMES_LAZY_INSTALL_TARGET must be in .env

The env var must be set in `/opt/data/.env` (or the Docker environment). Without it, the lazy-deps bootstrap has no target directory and `find_spec()` returns `None` for all lazy packages.

```bash
echo "HERMES_LAZY_INSTALL_TARGET=/opt/data/.local/lib/python3.13/site-packages" >> /opt/data/.env
```

## Install command template

```bash
/usr/local/bin/uv pip install \
  --python /opt/hermes/.venv/bin/python3 \
  --target /opt/data/.local/lib/python3.13/site-packages \
  'package==exact.version'
```

## Version pin criticality — two failure modes

The `ensure()` function in `lazy_deps.py` calls `_is_satisfied(spec)` which checks `importlib.metadata.version(pkg)` against the pinned specifier. If the installed version differs from the lazy-deps pin:

1. **_is_satisfied failure:** triggers a pip install that fails in the sealed venv (uv → pip → ensurepip, all fail). The error shifts from "not available" to `FeatureUnavailable`, but the result is the same: no STT/TTS.
2. **Breaking API changes:** The `mistralai` SDK changed its API between versions. Hermes code targets `client.audio.speech.complete(model=..., input=..., voice_id=..., response_format=...)` for TTS (pinned 2.4.8). In mistralai >=2.5, the method name changed to `client.audio.speech.create(...)` with different parameter names. This is a **silent break** — the import succeeds, but calling the expected method raises `AttributeError`.

**Fix:** always match the pinned version exactly. Never upgrade a lazy-dep package beyond its pin without also patching the Hermes source code that calls it.

## Verification

```python
from hermes_bootstrap import activate_durable_lazy_target
activate_durable_lazy_target()
from importlib.util import find_spec
from importlib.metadata import version

# Check find_spec (used by _HAS_* module-level flags)
print(find_spec('mistralai'))

# Check version (used by _is_satisfied)
print(version('mistralai'))
```

## Free Fallback Providers

When the paid provider is unavailable (expired key, exhausted quota), switch to free alternatives:

### TTS: Edge TTS (free, no API key, no package install)

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice fr-FR-HenriNeural   # French male voice
```

### STT: Local faster-whisper (free, no API key)

```bash
uv pip install --target /opt/data/.local/lib/python3.13/site-packages faster-whisper
hermes config set stt.provider local
hermes config set stt.local.model base   # tiny|base|small|medium|large-v3
```

### STT: Dicter self-hosted (OpenAI-compatible, needs API key)

```bash
# In .env: STT_OPENAI_BASE_URL=https://dicter.example.com/v1
hermes config set stt.provider openai
hermes config set stt.openai.model Systran/faster-whisper-medium
```

Dicter requires its own API key. If the endpoint returns 401, fall back to local faster-whisper.

### After switching: restart the gateway

Provider changes require a gateway restart — module-level `_HAS_*` flags are cached at import time.

## Packages installed in this environment

| Package | Version | Pinned by | Installed for |
|---------|---------|-----------|---------------|
| mistralai | 2.4.8 | `lazy_deps.LAZY_DEPS["stt.mistral"]` and `["tts.mistral"]` | Mistral STT (Voxtral Transcribe) + TTS (Voxtral TTS) |
| fastmcp | latest | `lazy_deps.LAZY_DEPS` (via ensure) | Profilarr, Discord, DockHand, MyAnimeList MCP servers |
| faster-whisper | latest | `lazy_deps.LAZY_DEPS["stt.faster_whisper"]` | Local STT fallback (free, no API key) |