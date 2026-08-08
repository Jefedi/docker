# HA Assist Pipeline Configuration with LiteLLM

Configurer un pipeline HA Assist complet (STT + Conversation + TTS) via LiteLLM, en utilisant des custom integrations HACS.

## Contexte

HA Assist utilise des "pipelines" qui chainent 3 composants :
1. **STT** (Speech-to-Text) — transcription de la voix
2. **Conversation agent** — LLM qui comprend et exécute les commandes
3. **TTS** (Text-to-Speech) — synthèse vocale de la réponse

Par défaut, HA propose Google AI ou Wyoming local. Pour utiliser LiteLLM comme backend, il faut des custom integrations HACS.

## Prérequis

- LiteLLM accessible depuis HA (ex: `http://host.docker.internal:4000/v1` depuis un conteneur HA Docker)
- Clé API LiteLLM avec accès aux modèles conversation
- Clé API Mistral directe (`wtSi...`) pour STT et TTS — **LiteLLM ne sait PAS router l'audio Mistral** (voir Pièges ci-dessous)
- Modèles LiteLLM configurés : `glm-5.2` (conversation)
- Modèles Mistral directs : `voxtral-mini-latest` (STT), `voxtral-mini-tts-latest` (TTS)

## Architecture recommandée

| Composant | Backend | Pourquoi |
|-----------|---------|----------|
| STT | API Mistral directe (`https://api.mistral.ai/v1`) | LiteLLM `mode: audio_transcription` fonctionne mais est peu fiable |
| Conversation | LiteLLM (`http://host.docker.internal:4000/v1`) | Routing normal, glm-5.2 |
| TTS | API Mistral directe (`https://api.mistral.ai/v1/audio/speech`) | **LiteLLM ne supporte PAS `mode: audio_speech` pour Mistral** — erreur "Unable to map provider=mistral" |

⚠️ **CRITIQUE — LiteLLM ne peut pas router le TTS Mistral.** La config `mode: audio_speech` avec `model: mistral/voxtral-mini-tts-latest` échoue avec `APIConnectionError: Unable to map the custom llm provider=mistral to a known provider`. C'est un bug/limitation de LiteLLM. La solution : pointer HA directement vers l'API Mistral pour STT et TTS. Seule la conversation passe par LiteLLM.

## Étape 1 : Vérifier l'état actuel

```python
# Lister les intégrations OpenAI existantes
ha_get_integration(query="openai")
# → extended_openai_conversation entries (conversation agent)

# Lister les pipelines Assist existants
ha_manage_pipeline(action="list")
# → voir les pipelines, leur STT/TTS/conversation engine

# Chercher les entités STT/TTS disponibles
ha_search(query="stt", domain_filter="stt")
ha_search(query="tts", domain_filter="tts")
```

## Étape 2 : Installer les custom integrations HACS

HA n'a pas d'intégration OpenAI native pour STT/TTS (seulement `extended_openai_conversation` pour la conversation). Installer :

**STT :** `einToast/openai_stt_ha` (OpenAI Whisper via API compatible)
```python
ha_manage_hacs(action="download", repository_id="einToast/openai_stt_ha")
```

**TTS :** `sfortis/openai_tts` (OpenAI speech engine ou endpoint compatible, 203⭐, 4939 downloads)
```python
ha_manage_hacs(action="download", repository_id="sfortis/openai_tts")
```

## Étape 3 : Redémarrer HA

Les custom integrations nécessitent un redémarrage pour s'activer :

```python
ha_restart(confirm=True)  # ⚠️ confirm=True OBLIGATOIRE
```

Attendre 1-5 minutes pour le redémarrage complet.

## Étape 4 : Configurer les intégrations

### STT — config YAML (PAS de config flow !)

⚠️ **Important :** `openai_stt` (einToast/openai_stt_ha) n'a **PAS de config flow** (`config_flow: false`). Il se configure via `configuration.yaml` uniquement.

Écrire dans `/config/configuration.yaml` du conteneur HA :

```yaml
stt:
  - platform: openai_stt
    api_key: wtSi...              # ⚠️ clé API Mistral DIRECTE (pas LiteLLM)
    api_url: https://api.mistral.ai/v1   # ⚠️ API Mistral directe
    model: voxtral-mini-latest          # modèle Mistral Voxtral
```

⚠️ **Ne PAS utiliser `host.docker.internal` ni la clé LiteLLM pour le STT Mistral.** L'endpoint `audio/transcriptions` de LiteLLM peut fonctionser pour le STT (mode `audio_transcription`) mais le TTS via LiteLLM ne fonctionne pas du tout. Pour simplicité, pointer STT et TTS directement vers Mistral.

Pour écrire dans le fichier config du conteneur HA :
```bash
docker exec home-assistant bash -c 'cat >> /config/configuration.yaml << "EOF"

stt:
  - platform: openai_stt
    api_key: sk-...
    api_url: http://host.docker.internal:4000/v1
    model: gpt-4o-mini-transcribe
EOF'
```

⚠️ Le YAML ne peut pas être validé avec `python3 yaml.safe_load()` car HA utilise des tags `!include` non standards. Ne pas paniquer si la validation Python échoue sur `!include`.

### TTS — config flow avec sub-entry agent

L'intégration `openai_tts` (sfortis/openai_tts) a un config flow à 2 étapes :

**Étape 1 : Créer l'entry principal**
```python
ha_set_integration(domain="openai_tts", config={
    "name": "Mistral Voxtral",
    "api_key": "wtSi...",                                     # ⚠️ clé Mistral DIRECTE (pas LiteLLM)
    "url": "https://api.mistral.ai/v1/audio/speech"  # ⚠️ API Mistral directe avec /audio/speech
})
```

⚠️ **Pièges critiques TTS étape 1 :**
- Le champ s'appelle **`url`** (PAS `base_url`) — c'est l'endpoint complet `/audio/speech`
- Si l'API key est refusée (`invalid_api_key`), c'est que le backend n'est pas `api.openai.com` — l'API key devient optionnelle pour les custom backends, mais il faut quand la passer
- L'entry principale ne crée PAS d'entité TTS — il faut un **sub-entry agent**

**Étape 2 : Ajouter un sub-entry profile (TTS profile)**

Le subentry_type est **`profile`** (PAS `agent` — `agent` retourne 404 "Invalid handler").

```python
# ⚠️ BPS key obligatoire : d'abord lire le skill guide
ha_get_skill_guide(skill='home-assistant-best-practices', file='references/helper-selection.md')
# → retourne une clé comme "I-HAVE-READ-THE-BEST-PRACTICES-GUIDE-cdb0d479"

# Puis créer le sub-entry avec la clé BPS
ha_config_set_helper(
    helper_type="config_subentry",
    entry_id="<entry_id_de_l'étape_1>",
    subentry_type="profile",           # ⚠️ "profile" PAS "agent"
    config={
        "profile_name": "Marie FR",  # ⚠️ "profile_name" PAS "name"
        "model": "voxtral-mini-tts-latest"  # custom_value accepté — modèle Mistral direct
    },
    BestPracticeKey="I-HAVE-READ-THE-BEST-PRACTICES-GUIDE-..."  # clé rotative
)
```

⚠️ **Pièges critiques TTS étape 2 :**
- Le `subentry_type` est **`profile`** — si on met `"agent"`, on obtient 404 "Invalid handler"
- Le champ pour le nom est **`profile_name`** — si on met `"name"`, validation error "required key not provided"
- La clé `BestPracticeKey` est **obligatoire** — sans elle, refus avec "BPS_ACKNOWLEDGMENT_REQUIRED". La clé est rotative (horaire), la récupérer via `ha_get_skill_guide` à chaque session
- Le modèle doit être une des valeurs du dropdown : `tts-1`, `tts-1-hd`, `gpt-4o-mini-tts` (custom_value accepté)

### Conversation — extended_openai_conversation

Utiliser l'intégration `extended_openai_conversation` déjà existante (entry "litellm"). Vérifier qu'elle pointe bien vers `glm-5.2` via LiteLLM.

## Étape 5 : Créer le pipeline Assist

```python
ha_manage_pipeline(
    action="create",
    name="LiteLLM GLM-5.2",
    language="fr",
    stt_engine="stt.openai_stt",
    stt_language="fr-FR",
    conversation_engine="conversation.extended_openai_conversation",
    tts_engine="tts.openai_tts",
    tts_language="fr-FR",
    tts_voice="..."
)
```

Puis définir comme pipeline par défaut :

```python
ha_manage_pipeline(action="set_preferred", pipeline_id="<id_retourné>")
```

## Clés LiteLLM pour HA

- `ha-integration` (`sk-ZKd...`) — clé dédiée HA, budget $20/mois
- Utiliser cette clé pour STT, TTS, et conversation

## Modèles LiteLLM disponibles pour HA

| Usage | Modèle LiteLLM | Notes |
|-------|----------------|-------|
| Conversation | `glm-5.2` | Réponse en français |
| STT | `stt-mistral` ou `mistral/voxtral-mini-latest` | |
| TTS | `voxtral-tts` | |

## Pièges — STT YAML ignoré par default_config

⚠️ **CRITIQUE — `stt:` dans `configuration.yaml` est IGNORÉ silencieusement quand `default_config:` est actif.** HA `default_config` gère `stt` via config entries (Google AI STT), pas via YAML platforms. Conséquences :
- Le bloc `stt:` YAML est chargé mais **aucune entité `stt.openai_stt` n'est créée**
- `stt: !reset` avant le bloc custom **ne fonctionne pas non plus** — HA ne supporte pas `!reset` pour `stt`
- Aucune erreur dans les logs HA — le YAML est juste ignoré
- **Solution non trouvée ce session** — il faudrait soit exclure `stt` de `default_config` (risqué, non testé), soit utiliser une intégration STT avec config flow natif

## Pièges — TTS voix non configurable via MCP

⚠️ **Le config flow `openai_tts` a 2 étapes : (1) modèle, (2) voix+audio. Le MCP ne peut compléter que l'étape 1.**

- L'étape 1 (`profile_name` + `model`) fonctionne via `ha_config_set_helper` → crée le sub-entry
- L'étape 2 (`voice`, `speed`, `format`, `chime`, etc.) **n'est pas accessible via MCP** — le helper tool ne gère qu'une étape par appel
- Conséquence : la voix reste à `shimmer` (défaut OpenAI), qui donne **404 "Voice not found" sur l'API Mistral**
- L'entité TTS est créée (`tts.openai_tts_marie_fr`) mais ne fonctionne pas tant que la voix n'est pas `fr_marie_neutral`
- **Solution : configurer la voix depuis l'UI HA** — Settings → Devices & Services → OpenAI TTS → Configure le profil → voice = `fr_marie_neutral`

## Pièges — TTS entry non persistée

⚠️ **L'entry `openai_tts` peut disparaître de `/config/.storage/core.config_entries` après un restart HA.** L'entry est visible via MCP (`ha_get_integration`) mais pas dans le fichier de storage. Comportement non déterministe — parfois persistée, parfois perdue. Si l'entry disparaît, il faut la recréer via `ha_set_integration` + `ha_config_set_helper`.

## Pièges — API Mistral voices

⚠️ L'endpoint `GET /v1/audio/voices` retourne `{"items": [...]}` (PAS `{"data": [...]}`). Le paramètre `limit` max est 100 (pas 200). Exemple : `curl "https://api.mistral.ai/v1/audio/voices?limit=100&offset=0" -H "Authorization: Bearer $MISTRAL_API_KEY"`.

## Pièges

- **`ha_restart`** nécessite `confirm=True` — sans ça, refus avec "Restart not confirmed"
- **`host.docker.internal`** : depuis un conteneur HA Docker, utiliser cette URL pour atteindre LiteLLM sur l'hôte
- **Intégration native `openai`** : retourne 404 "Invalid handler" — elle n'est pas installée par défaut. Les custom integrations HACS sont la solution
- **Ordre des étapes** : installer HACS → redémarrer HA → configurer les intégrations → créer le pipeline. Impossible de configurer une intégration pas encore activée.
- **`hermes config set` pour MCP** : le `patch` tool refuse d'écrire `config.yaml` (sécurité). Utiliser `hermes config set mcp_servers.<name>.url ...` à la place.
- **STT `openai_stt` = YAML seulement** : `config_flow: false`. Pas de config flow. Écrire dans `configuration.yaml` via `docker exec`.
- **TTS `openai_tts` sub-entry = via MCP avec `profile`** : le subentry_type est `profile` (PAS `agent`). Le champ nom est `profile_name` (PAS `name`). BPS key obligatoire via `ha_get_skill_guide`. Voir Étape 2 ci-dessus pour le code exact.
- **STT `openai_stt` champ `api_url`** : le paramètre s'appelle `api_url` (PAS `base_url`). Utiliser l'URL complète `http://host.docker.internal:4000/v1`.
- **TTS `openai_tts` champ `url`** : le paramètre s'appelle `url` (PAS `base_url`). Doit être l'endpoint COMPLET avec `/audio/speech` (ex: `http://host.docker.internal:4000/v1/audio/speech`). Sans `/audio/speech`, l'API key est refusée (`invalid_api_key`).
- **HA restart depuis Hermes impossible** : `hermes gateway restart` est bloqué depuis l'intérieur du conteneur. `s6-svc` n'est pas dans le PATH. Il faut utiliser `ha_restart(confirm=True)` via MCP, ou `docker restart home-assistant` depuis l'hôte.
- **HA restart déconnecte le MCP** : pendant 1-5 min, tous les appels MCP HA retournent 502 Bad Gateway. Attendre le retour avant de continuer.
- **`hermes config set` vs `patch`** : le tool `patch` refuse d'écrire `config.yaml` (fichier sécurité). Toujours utiliser `hermes config set mcp_servers.<name>.<field> <value>`.
- **HACS ne crée pas `/config/custom_components/`** : si le dossier n'existe pas dans le conteneur HA, HACS dit "installed" mais les fichiers ne sont PAS présents. Solution : créer le dossier et télécharger les fichiers manuellement via `docker exec` + `wget` depuis GitHub. Voir "Installation manuelle des custom components" ci-dessous.
- **Voix Mistral TTS = slugs spécifiques** : les voix ne sont PAS `alloy`, `coral`, etc. (ça donne 404 "Voice not found"). Les voix Mistral utilisent des slugs comme `fr_marie_neutral`, `fr_marie_happy`, `fr_marie_excited`, `en_paul_neutral`, etc. Récupérer la liste via `curl "https://api.mistral.ai/v1/audio/voices?limit=100&offset=0" -H "Authorization: Bearer $MISTRAL_API_KEY"`. Les voix françaises sont toutes `fr_marie_*` (féminin, 30 ans, plusieurs émotions).
- **Configuration YAML du conteneur HA via Hermes** : `docker exec home-assistant` pour accéder au filesystem. Le volume HA est mappé sur `/var/lib/docker/volumes/ha_config/_data` côté hôte mais Hermes ne voit que le conteneur. Pour réécrire `configuration.yaml` entièrement, utiliser `docker exec home-assistant sh -c 'cat > /config/configuration.yaml << "EOF" ... EOF'` (le `sed -i` pour des remplacements ciblés fonctionne aussi, mais les clés API dans le fichier peuvent être redacted par Hermes — éviter `sed` pour les clés).
- **`hermes config set` pour MCP ha-mcp** : le `patch` tool refuse d'écrire `config.yaml` (sécurité). Utiliser `hermes config set mcp_servers.ha-mcp.url "https://ha-mcp.jefe.al/private_..." && hermes config set mcp_servers.ha-mcp.connect_timeout 30.0 && hermes config set mcp_servers.ha-mcp.enabled true`. Les outils MCP sont chargés automatiquement sans restart Hermes.

## Installation manuelle des custom components

Si HACS dit "installed" mais que `/config/custom_components/` n'existe pas dans le conteneur HA :

```bash
# Créer les dossiers
docker exec home-assistant mkdir -p /config/custom_components/openai_stt /config/custom_components/openai_tts

# Télécharger STT (einToast/openai_stt_ha)
docker exec home-assistant sh -c '
cd /config/custom_components/openai_stt
wget -q "https://raw.githubusercontent.com/einToast/openai_stt_ha/main/custom_components/openai_stt/__init__.py" -O __init__.py
wget -q "https://raw.githubusercontent.com/einToast/openai_stt_ha/main/custom_components/openai_stt/manifest.json" -O manifest.json
wget -q "https://raw.githubusercontent.com/einToast/openai_stt_ha/main/custom_components/openai_stt/stt.py" -O stt.py
'

# Télécharger TTS (sfortis/openai_tts)
docker exec home-assistant sh -c '
cd /config/custom_components/openai_tts
wget -q "https://raw.githubusercontent.com/sfortis/openai_tts/main/custom_components/openai_tts/__init__.py" -O __init__.py
wget -q "https://raw.githubusercontent.com/sfortis/openai_tts/main/custom_components/openai_tts/manifest.json" -O manifest.json
wget -q "https://raw.githubusercontent.com/sfortis/openai_tts/main/custom_components/openai_tts/tts.py" -O tts.py
wget -q "https://raw.githubusercontent.com/sfortis/openai_tts/main/custom_components/openai_tts/const.py" -O const.py
'
```

Puis redémarrer HA avec `ha_restart(confirm=True)`.

## Voix Mistral Voxtral TTS disponibles (FR)

| Slug | Nom | Genre | Émotion |
|------|-----|-------|---------|
| `fr_marie_neutral` | Marie - Neutral | Femme | Neutre |
| `fr_marie_happy` | Marie - Happy | Femme | Joyeuse |
| `fr_marie_sad` | Marie - Sad | Femme | Triste |
| `fr_marie_excited` | Marie - Excited | Femme | Excitée |
| `fr_marie_curious` | Marie - Curious | Femme | Curieuse |
| `fr_marie_angry` | Marie - Angry | Femme | En colère |

Pour lister toutes les voix : `curl -s "https://api.mistral.ai/v1/audio/voices?limit=100&offset=0" -H "Authorization: Bearer $MISTRAL_API_KEY"`

## HACS repository IDs

| Custom Integration | repository_id (owner/repo) | HACS numeric ID |
|--------------------|---------------------------|-----------------|
| openai_stt_ha (STT) | `einToast/openai_stt_ha` | `781375315` |
| openai_tts (TTS) | `sfortis/openai_tts` | `716917337` |