# Mistral Voxtral TTS via Hermes Command Provider

## Problem

The built-in `mistral` TTS provider in Hermes reads `MISTRAL_API_KEY` from `os.environ` at process start. If the key in `.env` is updated mid-session (e.g., the old key was invalid), the running Hermes process keeps the stale value and all TTS calls fail with `Status 401: Invalid API Key`. Restarting Hermes fixes it, but may not be desirable mid-session.

## Solution: Custom Command Provider

Create a shell script that calls the Mistral API directly (bypassing Hermes' env resolution), and register it as a custom TTS command provider.

### 1. Create the script

```bash
#!/bin/bash
# /opt/data/scripts/mistral_voxtral_tts.sh
# Args: {input_path} {output_path}

INPUT_PATH="$1"
OUTPUT_PATH="$2"
API_KEY="${MISTRAL_API_KEY}"
VOICE_ID="5a271406-039d-46fe-835b-fbbb00eaf08d"  # Marie - Neutral
MODEL="voxtral-mini-tts-latest"

python3 -c "
import json, base64, urllib.request
text = open('$INPUT_PATH', encoding='utf-8').read()
payload = json.dumps({'model':'$MODEL','input':text,'voice_id':'$VOICE_ID','response_format':'mp3'}).encode()
req = urllib.request.Request('https://api.mistral.ai/v1/audio/speech', data=payload,
    headers={'Content-Type':'application/json','Authorization':'Bearer $API_KEY'})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode())
with open('$OUTPUT_PATH', 'wb') as f:
    f.write(base64.b64decode(data.get('audio_data','')))
"
[ -f "$OUTPUT_PATH" ] && [ $(stat -c%s "$OUTPUT_PATH" 2>/dev/null) -gt 100 ] && exit 0 || exit 1
```

### 2. Register in Hermes config

```bash
hermes config set tts.provider mistral-voxtral
hermes config set tts.providers.mistral-voxtral.type command
hermes config set tts.providers.mistral-voxtral.command '/opt/data/scripts/mistral_voxtral_tts.sh {input_path} {output_path}'
hermes config set tts.providers.mistral-voxtral.voice_compatible true
hermes config set tts.providers.mistral-voxtral.format mp3
```

### 3. Key details

- **Mistral TTS API returns JSON** with `audio_data` field (base64-encoded audio), NOT raw MP3. Must decode base64. Using `curl -o` without decoding produces a malformed file.
- **Hermes command provider placeholders**: `{input_path}`, `{output_path}`, `{format}`, `{voice}`, `{model}`, `{speed}`.
- **`voice_compatible: true`** → Hermes sends as Telegram voice bubble (ogg/opus via ffmpeg).
- **Validation warnings** about unrecognized config keys are non-blocking.

## Pre-built Voxtral Voices (30 total)

- **French**: Marie (Neutral `5a271406-039d-46fe-835b-fbbb00eaf08d`, Happy, Sad, Excited, Curious, Angry)
- **English US**: Paul (8 modes)
- **English UK**: Oliver, Jane

List: `GET https://api.mistral.ai/v1/audio/voices?limit=30` with `Authorization: Bearer <key>`

## Finding the real Mistral API key

The `.env` file may have an outdated key. The real key is in the LiteLLM container:
```bash
docker exec litellm printenv MISTRAL_API_KEY
```