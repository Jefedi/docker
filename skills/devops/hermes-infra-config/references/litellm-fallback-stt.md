# LiteLLM Fallback STT — Local faster-whisper → Mistral Voxtral

## Architecture

```
Hermes STT → LiteLLM /v1/audio/transcriptions (model=stt-local)
                    ↓
              faster-whisper (172.31.0.3:8000, réseau diction_default)
                    ↓ (si échec/timeout/connexion refusée)
              Mistral Voxtral (api.mistral.ai, fallback automatique)
```

Hermes envoie l'audio à LiteLLM avec `model=stt-local`. LiteLLM essaie d'abord
le faster-whisper local. Si le service est down (connexion refusée, timeout),
LiteLLM switch automatiquement vers `stt-mistral` (Mistral Voxtral).

## Configuration LiteLLM (config.yaml)

### Modèles STT dans model_list

```yaml
model_list:
  # STT Local (faster-whisper sur AX42)
  - model_name: stt-local
    litellm_params:
      model: openai/Systran/faster-whisper-medium
      api_base: http://172.31.0.3:8000/v1
      api_key: "none"

  # STT Mistral (fallback cloud)
  - model_name: stt-mistral
    litellm_params:
      model: mistral/voxtral-mini-latest
      api_key: os.environ/MISTRAL_API_KEY
```

### Fallback — format YAML correct

**⚠ PITFALL — le format du fallback doit être une LISTE de dicts, pas un dict simple.**

```yaml
# ✅ CORRECT — liste de dicts
router_settings:
  fallbacks:
    - stt-local: [stt-mistral]

# ❌ INCORRECT — dict simple (LiteLLM ignore silencieusement)
router_settings:
  fallbacks:
    stt-local:
      - stt-mistral
```

Avec le format incorrect, LiteLLM démarre sans erreur mais les logs montrent
`Available Model Group Fallbacks=None` quand le modèle primaire échoue.
Le fallback ne se déclenche JAMAIS.

### Où placer router_settings

`router_settings` est un **top-level key** dans le YAML (au même niveau que
`litellm_settings` et `general_settings`), PAS imbriqué dans `litellm_settings`.

```yaml
litellm_settings:
  drop_params: true
  num_retries: 2
  request_timeout: 600

router_settings:
  fallbacks:
    - stt-local: [stt-mistral]

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

## Cross-network Docker connectivity

**⚠ PITFALL** : LiteLLM (réseau `litellm_default`, 172.23.x.x) et faster-whisper
(réseau `diction_default`, 172.31.x.x) sont sur des réseaux Docker séparés.
LiteLLM ne peut PAS joindre faster-whisper par défaut (connection timeout).

**Fix** : Connecter le conteneur LiteLLM au réseau de faster-whisper :

```bash
docker network connect diction_default litellm
```

Cette commande doit être re-jouée après chaque recréation du conteneur litellm
(`docker stop && docker rm && docker run`). `docker restart` conserve les
networks, mais une recréation les perd.

**Alternative** : Exposer le port de faster-whisper sur l'hôte et utiliser
l'IP du gateway Docker (`172.23.0.1`) ou `host.docker.internal`.

**⚠ PITFALL — Drift d'IP Docker au restart** : Les IP Docker des conteneurs
sur des réseaux personnalisés (ex: `diction_default`) **changent** quand le
conteneur est recréé ou redémarré. Si `api_base` dans le config LiteLLM
hardcode une IP (ex: `http://172.31.0.3:8000/v1`), elle devient invalide
après un restart du conteneur Whisper (nouvelle IP: `172.31.0.4`). Symptôme :
les transcriptions échouent silencieusement (timeout sans erreur explicite),
et l'app externe (ex: Spokenly iOS) affiche "plantage" sans message d'erreur.

**Fix** : NE PAS hardcoder l'IP dans `api_base`. Solutions :
1. Utiliser le nom du conteneur (`http://diction-whisper-medium-1:8000/v1`)
   — fonctionne si les deux conteneurs sont sur le même réseau Docker.
2. Attacher une IP fixe via `--ip` dans le `docker run`.
3. Exposer le port sur l'hôte et utiliser l'IP du gateway Docker ou
   `host.docker.internal`.
4. Utiliser Docker Compose avec `networks:` et des `aliases:` définis.

**Diagnostic** : Comparer l'IP dans `api_base` du config LiteLLM avec l'IP
réelle du conteneur : `docker inspect <container> --format '{{range $net, $config := .NetworkSettings.Networks}}{{$net}}: {{$config.IPAddress}}{{end}}'`.
Si elles diffèrent, corriger le config et redémarrer LiteLLM
(`docker restart litellm` — le `docker exec sed` ne marche pas sur les
fichiers bind-mounted, il faut éditer sur l'hôte).

## Test du fallback

### Test 1 : local UP (devrait utiliser faster-whisper)

```bash
curl -s --max-time 15 http://127.0.0.1:4000/v1/audio/transcriptions \
  -H "Authorization: Bearer $HERMES_KEY" \
  -F "model=stt-local" \
  -F "file=@/tmp/test_audio.wav"
# → {"text":"you",...}
```

### Test 2 : local DOWN (devrait fallback vers Mistral)

```bash
# Arrêter faster-whisper
docker stop diction-whisper-medium-1

# Refaire le même appel — LiteLLM devrait fallback vers stt-mistral
curl -s --max-time 30 http://127.0.0.1:4000/v1/audio/transcriptions \
  -H "Authorization: Bearer $HERMES_KEY" \
  -F "model=stt-local" \
  -F "file=@/tmp/test_audio.wav"
# → {"text":"",...}  (vide car fichier silencieux, mais Mistral a répondu)

# Relancer faster-whisper
docker start diction-whisper-medium-1
```

### Créer un fichier WAV de test

```python
import struct, wave
with wave.open('/tmp/test_audio.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b'\x00\x00' * 16000)  # 1 seconde de silence
```

## Virtual keys — scope des modèles

**⚠ PITFALL** : Quand on crée une virtual key via `/key/generate`, la clé n'a
accès qu'aux modèles explicitement listés dans `models`. Si on ajoute de
nouveaux modèles au config.yaml (ex: `stt-local`, `stt-mistral`,
`mistral-small-latest`), la clé existante renverra `key not allowed to access
model` pour ces nouveaux modèles.

**Fix** : Supprimer et recréer la virtual key avec la liste complète :

```bash
# Supprimer toutes les clés (DB)
docker exec litellm-db psql -U litellm -d litellm -c \
  'DELETE FROM "LiteLLM_VerificationToken";'

# Recréer avec tous les modèles
curl -s -X POST http://127.0.0.1:4000/key/generate \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "Hermes-Agent",
    "models": [
      "glm-5.2", "minimax-m3", "gemma4-vision", "gpt-oss-20b", "deepseek-v4-flash",
      "local-aux",
      "stt-local", "stt-mistral",
      "mistral/voxtral-mini-latest", "voxtral-tts", "mistral-ocr", "mistral-small-latest",
      "ollama-cloud/glm-5.2", "ollama-cloud/minimax-m3", "ollama-cloud/gemma4:31b",
      "ollama-cloud/gpt-oss:20b", "ollama-cloud/deepseek-v4-flash"
    ]
  }'
```

## Configuration Hermes STT pour utiliser LiteLLM

Dans `config.yaml` :

```yaml
stt:
  enabled: true
  provider: openai
  openai:
    model: stt-local  # modèle LiteLLM (pas le modèle direct faster-whisper)
    language: fr      # forcer le français (sinon faster-whisper transcrit en anglais par défaut)
```

**⚠ PITFALL — faster-whisper transcrit en anglais par défaut** : Le serveur
`speaches` (fedirz/faster-whisper-server) n'a pas de variable d'environnement
pour forcer la langue. La langue est détectée automatiquement ou passée **par
requête** via le paramètre `language` de l'API OpenAI. Sans `language: fr`,
faster-whisper part sur l'anglais. Le paramètre est passé dans chaque requête
de transcription, que ce soit vers faster-whisper (local) ou Voxtral (Mistral
en fallback). Les deux le supportent.

Hermes utilise `VOICE_TOOLS_OPENAI_KEY` et `STT_OPENAI_BASE_URL` pour le
provider STT `openai`. Configurer dans `.env` :

```dotenv
VOICE_TOOLS_OPENAI_KEY=<virtual-key-litellm>
STT_OPENAI_BASE_URL=http://127.0.0.1:4000/v1
```

Ainsi, Hermes envoie l'audio à LiteLLM qui gère le fallback automatique.

## Créer une clé API pour une app externe (ex: app iOS Spokenly)

Pour créer une clé LiteLLM dédiée à une application externe avec un budget
limité (ex: 5€/mois pour STT) :

```bash
MASTER_KEY="<master_key_litellm>"

curl -s -X POST http://127.0.0.1:4000/key/generate \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "Spokenly-iOS",
    "models": ["stt-local", "stt-mistral", "mistral/voxtral-mini-latest"],
    "max_budget": 5.50,
    "budget_duration": "1mo"
  }'
```

L'app externe configure :
- **Model** : `stt-local` (utilise faster-whisper avec fallback Mistral automatique)
- **URL** : `http://127.0.0.1:4000/v1` (ou URL Pangolin pour accès externe)
- **API Key** : la clé générée ci-dessus
- **language** : `fr` (si l'app supporte le paramètre)

La clé n'a accès qu'aux modèles listés dans `models`. Le budget bloque les
appels quand `max_budget` est atteint (en USD, 5.50 ≈ 5€).

**⚠ Capturer la clé générée** : Hermes masque les `sk-*` dans la sortie.
Utiliser la technique base64 décrite dans `references/litellm-proxy-tracking.md`
→ section « Capturer les virtual keys créées ». Pour une app externe, afficher
la clé par parties (`key[:8]`, `key[8:16]`, `key[16:]`) pour contourner le
masquage, ou l'écrire dans un fichier et lire avec `od -c`.