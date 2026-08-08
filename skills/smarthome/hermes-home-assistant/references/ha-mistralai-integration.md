# HA_MistralAI — Intégration tout-en-un Mistral (STT + TTS + Conversation)

L'intégration `SnarfNL/HA_MistralAI` (domaine `mistral_conversation`) est la solution recommandée pour configurer Mistral Voxtral STT + TTS + Conversation dans Home Assistant. Elle remplace avantageusement les intégrations séparées `openai_stt_ha` + `openai_tts` qui souffraient de multiples problèmes (STT YAML ignoré, TTS voix non configurable via MCP, entry non persistée).

## Pourquoi HA_MistralAI au lieu de openai_stt + openai_tts

| Problème openai_stt/openai_tts | Solution HA_MistralAI |
|-------------------------------|----------------------|
| STT YAML ignoré par `default_config:` | STT via config flow natif — pas de YAML |
| TTS voix non configurable via MCP (étape 2 inaccessible) | Voix configurées automatiquement (récupérées via API Mistral) |
| TTS entry disparaît après restart | Entry persistée normalement dans `core.config_entries` |
| 2 intégrations séparées + YAML + sub-entries complexes | 1 intégration, 1 config flow, tout automatique |
| `stt: !reset` non supporté par HA | Pas besoin — pas de YAML STT |

## Installation

### Via HACS (depuis MCP)

```python
# 1. Ajouter le repo HACS
ha_manage_hacs(action="add_repository", repository="SnarfNL/HA_MistralAI", category="integration")

# HACS l'installe automatiquement (installed=True immédiatement)
# Le domaine est "mistral_conversation"
# Version minimum HA: 2025.10
```

⚠️ HACS peut dire "installed" sans créer `/config/custom_components/`. Si l'intégration n'apparaît pas après restart, installer manuellement :

```bash
docker exec home-assistant mkdir -p /config/custom_components/mistral_conversation
# Télécharger depuis GitHub
docker exec home-assistant sh -c '
  cd /config/custom_components/mistral_conversation
  for f in __init__.py conversation.py stt.py tts.py const.py manifest.json; do
    wget -q "https://raw.githubusercontent.com/SnarfNL/HA_MistralAI/main/custom_components/mistral_conversation/$f" -O "$f"
  done
'
```

### Restart HA

```python
ha_restart(confirm=True)  # ⚠️ confirm=True obligatoire
# Attendre 1-5 min — les appels MCP retournent 502 pendant le restart
```

## Configuration

### Ajouter l'intégration

```python
# ⚠️ Utiliser la clé API Mistral DIRECTE (pas la clé LiteLLM)
# L'intégration valide la clé auprès de l'API Mistral — une clé LiteLLM sera refusée (invalid_auth)
ha_set_integration(
    domain="mistral_conversation",
    config={"api_key": "${MISTRAL_API_KEY}"}  # clé Mistral directe
)
```

### Entités créées automatiquement

| Domaine | Entity ID | Friendly name |
|---------|-----------|---------------|
| STT | `stt.mistral_ai_stt_mistral_ai_stt_voxtral` | Mistral AI STT (Voxtral) |
| TTS | `tts.mistral_ai_tts_mistral_ai_tts` | Mistral AI TTS |
| Conversation | `conversation.mistral_ai_conversation` | Mistral AI Conversation |

### Options configurables (via Configure dans l'UI HA)

- **AI model** : `ministral-8b-latest` (défaut), `mistral-small-latest`, `mistral-large-latest`, etc.
- **System prompt** : Jinja2 templates (`{{ ha_name }}`, `{{ now() }}`)
- **Temperature**, **Max tokens**, **Control HA** (device control)
- **STT language** : Auto-detect ou fixe
- **TTS mode** : `Streaming` (SSE WAV) ou `Batch` (MP3)
- **TTS voice** : récupérée dynamiquement via `GET /v1/audio/voices` (voix custom incluses)

## Pipeline Assist avec LiteLLM pour la conversation

Pour garder la conversation via LiteLLM (glm-5.2) tout en utilisant Mistral pour STT/TTS :

```python
ha_manage_pipeline(
    action="update",
    pipeline_id="<id_du_pipeline>",
    name="LiteLLM GLM-5.2 + Mistral STT/TTS",
    language="fr",
    stt_engine="stt.mistral_ai_stt_mistral_ai_stt_voxtral",
    stt_language="fr-FR",
    conversation_engine="conversation.extended_openai_conversation",  # LiteLLM glm-5.2
    tts_engine="tts.mistral_ai_tts_mistral_ai_tts",
    tts_language="fr-FR"
)
```

⚠️ Le `conversation_engine` reste `conversation.extended_openai_conversation` (LiteLLM/glm-5.2), PAS `conversation.mistral_ai_conversation`. L'intégration HA_MistralAI crée sa propre entité conversation, mais on choisit d'utiliser extended_openai pour garder le routing via LiteLLM.

## Architecture finale

```
Voice Input → STT (Mistral Voxtral direct) → Conversation (LiteLLM → glm-5.2) → TTS (Mistral Voxtral direct) → Audio Output
```

| Composant | Backend | Pourquoi |
|-----------|---------|----------|
| STT | API Mistral directe | LiteLLM `mode: audio_transcription` peu fiable pour Mistral |
| Conversation | LiteLLM (`http://host.docker.internal:4000/v1`) | Routing glm-5.2, budget control |
| TTS | API Mistral directe | LiteLLM ne supporte pas `mode: audio_speech` pour Mistral |

## Correction config LiteLLM pour audio Mistral

Si on veut quand même router le TTS/STT via LiteLLM (testé et fonctionnel), remplacer `model: mistral/...` par `model: openai/...` avec `api_base` Mistral :

```yaml
# AVANT (ne marche pas — LiteLLM ne sait pas mapper "mistral" pour l'audio)
- model_name: voxtral-tts
  litellm_params:
    model: mistral/voxtral-mini-tts-latest
    api_key: os.environ/MISTRAL_API_KEY
  model_info:
    mode: audio_speech

# APRÈS (fonctionne — openai/ avec api_base Mistral)
- model_name: voxtral-tts
  litellm_params:
    model: openai/voxtral-mini-tts-latest
    api_base: https://api.mistral.ai/v1
    api_key: os.environ/MISTRAL_API_KEY
  model_info:
    mode: audio_speech
```

⚠️ Le conteneur LiteLLM peut avoir un bind mount `:ro` (read-only) sur `config.yaml`. Dans ce cas :
1. `docker stop litellm && docker rm litellm`
2. Recréer avec `-v /srv/docker/litellm/config.yaml:/app/config.yaml:rw` (sans `:ro`)
3. `docker exec -i litellm sh -c 'cat > /app/config.yaml' < new_config.yaml`
4. `docker restart litellm`

Test TTS via LiteLLM : `curl -X POST http://127.0.0.1:4000/v1/audio/speech -H "Authorization: Bearer sk-..." -H "Content-Type: application/json" -d '{"model":"voxtral-tts","input":"Bonjour","voice":"fr_marie_neutral"}' -o test.mp3`

## Pièges

- **Clé API Mistral obligatoire** : L'intégration `HA_MistralAI` valide la clé auprès de Mistral. Une clé LiteLLM sera refusée (`invalid_auth`). Utiliser la clé Mistral directe.
- **STT/TTS via Mistral direct, conversation via LiteLLM** : L'intégration crée sa propre entité conversation (`conversation.mistral_ai_conversation`), mais on peut utiliser `conversation.extended_openai_conversation` dans le pipeline pour garder glm-5.2 via LiteLLM.
- **HA_MistralAI requiert HA 2025.10+** : Vérifier la version avec `ha_get_overview()`.
- **HACS peut ne pas créer `/config/custom_components/`** : Voir installation manuelle ci-dessus.
- **Restart HA déconnecte le MCP 1-5 min** : Tous les appels MCP retournent 502 Bad Gateway. Attendre le retour.
- **LiteLLM bind mount read-only** : Si `docker exec` ne peut pas écrire `/app/config.yaml`, le conteneur a un bind `:ro`. Recréer le conteneur avec `:rw`.
- **Voix Mistral = slugs** : `fr_marie_neutral`, `fr_marie_happy`, etc. (PAS `alloy`, `shimmer`). Voir `references/ha-assist-pipeline-litellm.md` pour la liste complète.