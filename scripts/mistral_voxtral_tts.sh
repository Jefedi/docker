#!/bin/bash
# Mistral Voxtral TTS - Marie Neutral voice
# Called by Hermes with placeholders: {input_path} {output_path}

INPUT_PATH="$1"
OUTPUT_PATH="$2"
API_KEY="${MISTRAL_API_KEY}"
VOICE_ID="5a271406-039d-46fe-835b-fbbb00eaf08d"
MODEL="voxtral-mini-tts-latest"

# Read text from input file
TEXT=$(cat "$INPUT_PATH")

# Call Mistral API and decode base64 audio response
python3 -c "
import json, base64, sys, urllib.request

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

# Response is JSON with audio_data field (base64 encoded)
data = json.loads(body)
audio_b64 = data.get('audio_data', '')
audio_bytes = base64.b64decode(audio_b64)

with open('$OUTPUT_PATH', 'wb') as f:
    f.write(audio_bytes)
"

# Check if output is valid
if [ -f "$OUTPUT_PATH" ] && [ $(stat -c%s "$OUTPUT_PATH" 2>/dev/null) -gt 100 ]; then
  exit 0
else
  echo "Error: TTS generation failed" >&2
  exit 1
fi