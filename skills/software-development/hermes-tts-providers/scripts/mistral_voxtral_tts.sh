#!/bin/bash
# Mistral Voxtral TTS - Marie Neutral voice
# Called by Hermes TTS command provider with: {input_path} {output_path}
#
# Setup in Hermes:
#   hermes config set tts.provider mistral-voxtral
#   hermes config set tts.providers.mistral-voxtral.type command
#   hermes config set tts.providers.mistral-voxtral.command '/opt/data/scripts/mistral_voxtral_tts.sh {input_path} {output_path}'
#   hermes config set tts.providers.mistral-voxtral.voice_compatible true
#   hermes config set tts.providers.mistral-voxtral.format mp3
#
# Available voices (list via API):
#   curl -s https://api.mistral.ai/v1/audio/voices?limit=30 \
#     -H "Authorization: Bearer <API_KEY>"
#
# French voices: Marie (Neutral/Happy/Sad/Excited/Curious/Angry)
# English voices: Paul (Neutral/Happy/Sad/etc), Oliver, Jane

INPUT_PATH="$1"
OUTPUT_PATH="$2"
API_KEY="${MISTRAL_API_KEY}"
VOICE_ID="5a271406-039d-46fe-835b-fbbb00eaf08d"  # Marie - Neutral
MODEL="voxtral-mini-tts-latest"

# Call Mistral API and decode base64 audio response
# Mistral returns JSON {"audio_data": "<base64>"} NOT raw audio bytes
python3 -c "
import json, base64, urllib.request

text = open('$INPUT_PATH', encoding='utf-8').read()
payload = json.dumps({
    'model': '$MODEL',
    'input': text,
    'voice_id': '$VOICE_ID',
    'response_format': 'mp3'
}).encode()

req = urllib.request.Request(
    'https://api.mistral.ai/v1/audio/speech',
    data=payload,
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $API_KEY'
    }
)

resp = urllib.request.urlopen(req)
body = resp.read().decode()
data = json.loads(body)
audio_b64 = data.get('audio_data', '')
audio_bytes = base64.b64decode(audio_b64)

with open('$OUTPUT_PATH', 'wb') as f:
    f.write(audio_bytes)
"

# Verify output
if [ -f "$OUTPUT_PATH" ] && [ $(stat -c%s "$OUTPUT_PATH" 2>/dev/null) -gt 100 ]; then
  exit 0
else
  echo "Error: TTS generation failed" >&2
  exit 1
fi