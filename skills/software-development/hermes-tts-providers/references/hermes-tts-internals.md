# Hermes TTS Internals — Key Resolution & Command Providers

## Key Resolution Chain

`_resolve_provider_key()` → `resolve_provider_secret()` in `tools/tool_backend_helpers.py`:

1. **config_value** from `config.yaml` (explicit `tts.openai.api_key` etc.)
2. **env / .env** — `get_env_value()` checks `os.environ` FIRST, then `~/.hermes/.env`
3. **credential pool** — `hermes auth add <provider>` store

### The masking problem
- Hermes masks keys in `config.yaml` and `.env` as `sk-XXX...XXX` on write
- The real values are in the credential store, not the file
- `os.environ` is populated at process start from the OLD `.env`
- Updating `.env` mid-session → `os.environ` still has old value → 401
- **Fix**: use a command provider with the real key in the script

## Command Provider Architecture

Source: `/opt/hermes/tools/tts_tool.py`

### Config structure
```yaml
tts:
  provider: my-custom-voice
  providers:
    my-custom-voice:
      type: command
      command: /path/to/script.sh {input_path} {output_path}
      voice_compatible: true
      format: mp3
      timeout: 60
      max_text_length: 5000
```

### Execution flow
1. Hermes writes text to a temp UTF-8 file (`input.txt`)
2. Renders the command template with placeholders
3. Runs via `subprocess.Popen` with `shell=True`
4. Waits for the script to write audio to `{output_path}`
5. Verifies output file exists and is >0 bytes
6. If `voice_compatible=true`, converts to .ogg for Telegram voice bubbles

### Key functions
- `_is_command_provider_config()` — checks `type: command` and `command` field exists
- `_resolve_command_provider_config()` — rejects built-in provider names (can't override)
- `_generate_command_tts()` — main execution, creates temp dir, renders template, runs
- `_get_command_tts_output_format()` — determines mp3/wav/ogg/flac from config or path suffix
- `BUILTIN_TTS_PROVIDERS` — set of names that can't be used for custom providers

## Mistral Voxtral Voices

List all voices:
```bash
curl -s 'https://api.mistral.ai/v1/audio/voices?limit=30' \
  -H "Authorization: Bearer <API_KEY>"
```

### French voices (Marie)
| Name | voice_id | Tags |
|------|----------|------|
| Marie - Neutral | 5a271406-039d-46fe-835b-fbbb00eaf08d | composed, steady, neutral |
| Marie - Happy | 49d024dd-981b-4462-bb17-74d381eb8fd7 | warm, radiant, happy |
| Marie - Sad | 4adeb2c6-25a3-44bc-8100-5234dfc1193b | muted, heavy, sad |
| Marie - Excited | 2f62b1af-aea3-4079-9d10-7ca665ee7243 | vibrant, bubbly, excited |
| Marie - Curious | e0580ce5-e63c-4cbe-88c8-a983b80c5f1f | bright, probing, curious |
| Marie - Angry | a7c07cdc-1c35-4d87-a938-c610a654f600 | fierce, sharp, angry |

### API call format
```bash
curl -s https://api.mistral.ai/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"model":"voxtral-mini-tts-latest","input":"text","voice_id":"<id>","response_format":"mp3"}'
```

Response: JSON `{"audio_data": "<base64 mp3>"}` — must base64-decode, NOT raw audio.