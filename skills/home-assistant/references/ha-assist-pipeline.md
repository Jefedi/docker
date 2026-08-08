# HA Assist Pipeline — Conversation, STT, TTS

Configurer les pipelines Assist de Home Assistant : agent de conversation, speech-to-text, text-to-speech.

## Pipeline = STT + Conversation Agent + TTS

Un pipeline Assist chaîne trois éléments :
1. **STT** (speech-to-text) — transcription vocale → texte
2. **Conversation agent** — génère la réponse textuelle
3. **TTS** (text-to-speech) — texte → audio

Chaque élément est une intégration séparée. Le pipeline les assemble.

## Gestion des pipelines via MCP

```python
ha_manage_pipeline(action="list")
ha_manage_pipeline(action="get", pipeline_id="...")
ha_manage_pipeline(action="create", name="...", conversation_engine="conversation.xxx",
    stt_engine="stt.xxx", stt_language="fr-FR",
    tts_engine="tts.xxx", tts_language="fr-FR", tts_voice="...",
    make_preferred=True)
ha_manage_pipeline(action="update", pipeline_id="...", ...)
ha_manage_pipeline(action="set_preferred", pipeline_id="...")
```

## Connecter Ollama Cloud comme agent de conversation

### Problème : intégration Ollama native ≠ Ollama Cloud

L'intégration **Ollama** native de HA utilise l'API native Ollama (`/api/tags`, `/api/chat`). Elle attend un serveur Ollama local.

**Ollama Cloud** (`ollama.com`) expose uniquement l'**API OpenAI-compatible** (`/v1/`). L'endpoint `/api/tags` sur ollama.com retourne 404.

→ L'intégration Ollama native NE PEUT PAS se connecter à Ollama Cloud.

### Solution : Extended OpenAI Conversation (HACS)

Custom component HACS avec base URL personnalisable.

1. Installer via HACS : **Extended OpenAI Conversation**
2. Paramètres → Devices & Services → Ajouter → Extended OpenAI Conversation
3. Configurer : API Key (ollama.com/settings) + Base URL `https://ollama.com/v1` + Model

### Modèles Ollama Cloud

```
glm-5.2, glm-5.1, deepseek-v4-pro, deepseek-v4-flash,
kimi-k2.7-code, kimi-k2.6, kimi-k2.5,
gpt-oss:120b, gpt-oss:20b,
minimax-m3, minimax-m2.7, minimax-m2.5,
mistral-large-3:675b, nemotron-3-ultra, nemotron-3-super,
nemotron-3-nano:30b, qwen3.5:397b, gemma4:31b
```

### Piège : modèle par défaut = gpt-3.5-turbo

Si on ne change pas le modèle, les requêtes partent vers OpenAI → erreur 400/401. **Toujours** changer le modèle.

### Test

```python
ha_call_service(domain="conversation", service="process",
    entity_id="conversation.extended_openai_conversation",
    data={"text": "Bonjour"}, return_response=True)
```

## STT — Speech-to-Text

### Piège : HA STT = protocole Wyoming uniquement

HA ne peut PAS utiliser un endpoint OpenAI-compatible pour le STT. Un service externe (ex: Diction/dicter.jefe.al) ne peut PAS être utilisé directement. Il faut un add-on Whisper/Wyoming local.

```python
ha_get_addon(source="available", query="whisper")  # → core_whisper
ha_manage_addon(slug="core_whisper", action="install")
ha_manage_addon(slug="core_whisper", action="start")
```

## TTS — Text-to-Speech

| Intégration | Type | Voix FR |
|-------------|------|---------|
| Google AI TTS | Cloud | ✅ |
| Piper | Local | ✅ (add-on) |

### Piège : Voxtral = STT (Mistral), pas TTS

## Workflow complet

1. Agent → Extended OpenAI Conversation + Ollama Cloud
2. STT → Add-on Whisper ou Google AI STT
3. TTS → Google AI TTS ou Piper
4. Pipeline → `ha_manage_pipeline(action="create", ...)`
5. Test → `conversation.process` avec `return_response=True`

## Préférences Jefe

- STT : Diction (dicter.jefe.al) — pas compatible HA directement
- TTS : Voxtral en attente, fallback Google AI TTS
- Edge TTS : rejeté
- **Ne pas brûler les étapes** — configurer étape par étape