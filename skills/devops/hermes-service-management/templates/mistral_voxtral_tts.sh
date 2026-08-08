#!/bin/bash
# Mistral Voxtral TTS — Custom Command Provider for Hermes
# 
# Usage in config.yaml:
#   tts:
#     provider: mistral-voxtral
#     providers:
#       mistral-voxtral:
#         type: command
#         command: /opt/data/scripts/mistral_voxtral_tts.sh {input_path} {output_path}
#         format: mp3
#         voice_compatible: true
#
# Hermes calls this script with: script.sh {input_path} {output_path}
# Text is written to {input_path} (temp file), audio must be written to {output_path}
#
# Replace API_KEY with the real Mistral key (get from LiteLLM container:
#   docker exec litellm printenv MISTRAL_API_KEY)
# Replace VOICE_ID with the desired voice (see references/voxtral-voices.md)
#
# ⚠ IMPORTANT: The Voxtral TTS API returns JSON with base64-encoded audio
# in the "audio_data" field, NOT raw MP3. You MUST decode the base64.
# Using curl -o alone saves the JSON, not the audio — the output file
# will be invalid (0 channels, no duration, unreadable by ffprobe).

INPUT_PATH="$1"
OUTPUT_PATH="$2"
API_KEY="REPLACE_WITH_REAL_KEY"
VOICE_ID="5a271406-039d-46fe-835b-fbbb00eaf08d"  # Marie - Neutral (fr_fr)
MODEL="voxtral-mini-tts-latest"

# Read text from input file and call Mistral API, decoding base64 audio response.
# The API returns {"audio_data": "<base64>", ...} — we extract and decode it.
python3 -c "
import json, base64, urllib.request, sys

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

# Verify output is a valid audio file (not JSON error)
if [ -f "$OUTPUT_PATH" ] && [ $(stat -c%s "$OUTPUT_PATH" 2>/dev/null) -gt 100 ]; then
  exit 0
else
  echo "Error: TTS generation failed" >&2
  exit 1
fi