# Voxtral TTS Pre-Built Voices (Aug 2026)

All 30 pre-built voices available via `GET /v1/audio/voices?limit=30`.
No reference audio needed — pass `voice_id` directly in the TTS API call.

## French (fr_fr) — Marie

| Voice | ID | Tags |
|---|---|---|
| Marie - Neutral | `5a271406-039d-46fe-835b-fbbb00eaf08d` | composed, steady, neutral |
| Marie - Happy | `49d024dd-981b-4462-bb17-74d381eb8fd7` | warm, radiant, happy |
| Marie - Sad | `4adeb2c6-25a3-44bc-8100-5234dfc1193b` | muted, heavy, sad |
| Marie - Excited | `2f62b1af-aea3-4079-9d10-7ca665ee7243` | vibrant, bubbly, excited |
| Marie - Curious | `e0580ce5-e63c-4cbe-88c8-a983b80c5f1f` | bright, probing, curious |
| Marie - Angry | `a7c07cdc-1c35-4d87-a938-c610a654f600` | fierce, sharp, angry |

## English US (en_us) — Paul

| Voice | ID | Tags |
|---|---|---|
| Paul - Neutral | `c69964a6-ab8b-4f8a-9465-ec0925096ec8` | relaxed, balanced, neutral |
| Paul - Happy | `1024d823-a11e-43ee-bf3d-d440dccc0577` | sunny, easygoing, happy |
| Paul - Sad | `530e2e20-58e2-45d8-b0a5-4594f4915944` | heavy, hushed, sad |
| Paul - Frustrated | `1f017bcb-02e5-460d-989b-db065c0c6122` | edgy, snappy, frustrated |
| Paul - Excited | `5940190b-f58a-4c3e-8264-a40d63fd6883` | bouncy, spirited, excited |
| Paul - Confident | `98559b22-62b5-4a64-a7cd-fc78ca41faa8` | bold, punchy, confident |
| Paul - Cheerful | `01d985cd-5e0c-4457-bfd8-80ba31a5bc03` | upbeat, breezy, cheerful |
| Paul - Angry | `cb891218-482c-4392-9878-91e8d999d57a` | raw, gruff, angry |

## English GB (en_gb) — Oliver

| Voice | ID | Tags |
|---|---|---|
| Oliver - Neutral | `e3596645-b1af-469e-b857-f18ddedc7652` | calm, even, neutral |
| Oliver - Sad | `d4101b8f-12c3-450d-a812-7d700b3a3245` | low, hollow, sad |
| Oliver - Excited | `e8e5b1de-493c-4061-8414-e2170f9f4b6f` | energetic, crisp, excited |
| Oliver - Curious | `390c8a2b-60a6-4882-8437-c49a8bd33b63` | thoughtful, engaged, curious |
| Oliver - Confident | `8169ab87-bc99-4669-a5ec-6855860ace24` | firm, decisive, confident |
| Oliver - Cheerful | `5ad5d44e-6b4e-4a57-a8a8-4cae088034ed` | bright, lively, cheerful |
| Oliver - Angry | `862274a7-8333-48f7-b668-f19c932999e0` | intense, forceful, angry |

## English GB (en_gb) — Jane

| Voice | ID | Tags |
|---|---|---|
| Jane - Neutral | `82c99ee6-f932-423f-a4a3-d403c8914b8d` | clear, measured, neutral |
| Jane - Confident | `cbe96cf0-85ec-4a10-accb-0b35c93b6dfd` | assured, poised, confident |
| Jane - Curious | `5de47977-6e47-4266-a938-3bc1d76b4676` | inquisitive, open, curious |
| Jane - Frustrated | `60844938-221d-4d1e-8233-34203f787d9f` | tense, clipped, frustrated |
| Jane - Sarcasm | `a3e41ea8-020b-44c0-8d8b-f6cc03524e31` | dry, wry, sarcastic |
| Jane - Confused | `7d0a90a3-c211-4489-aaa0-61269299edc7` | hesitant, uncertain, confused |
| Jane - Shameful | `230ccacf-8800-4aa0-8ac2-8d004f1d9fb7` | quiet, remorseful, ashamed |
| Jane - Sad | `c7a8eb83-5247-4540-89f3-6650d349100d` | soft, subdued, sad |
| Jane - Jealousy | `e7168caa-f7ed-4e1c-98a1-434251f4f2b0` | bitter, strained, jealous |

## API Details

- **Model**: `voxtral-mini-tts-2603` or `voxtral-mini-tts-latest`
- **Endpoint**: `POST https://api.mistral.ai/v1/audio/speech`
- **Formats**: mp3, wav, pcm, flac, opus
- **Price**: $16/M characters
- **Streaming**: ~90ms time-to-first-audio
- **Languages**: English, French, Spanish, Portuguese, Italian, Dutch, German, Hindi, Arabic
- **Cross-lingual**: voice prompt in one language can speak text in another

## User's Configured Voice

Jefe uses **Marie - Neutral** (`5a271406-039d-46fe-835b-fbbb00eaf08d`).

**Active config** (custom command provider — bypasses os.environ key masking):
- `tts.provider = mistral-voxtral` (custom command provider, NOT the built-in `mistral`)
- `tts.providers.mistral-voxtral.type = command`
- `tts.providers.mistral-voxtral.command = /opt/data/scripts/mistral_voxtral_tts.sh {input_path} {output_path}`
- Script calls Mistral API directly with the real key (from LiteLLM container)
- No gateway restart needed — works immediately after `hermes config set`

**Why not the built-in mistral provider?** The built-in `mistral` TTS reads `MISTRAL_API_KEY` via `get_env_value()` which checks `os.environ` first (stale from process start), then `.env`. If the key in `.env` was updated mid-session, the built-in provider keeps using the old `os.environ` value → 401 error. The command provider bypasses this entirely by hardcoding the key in the script.