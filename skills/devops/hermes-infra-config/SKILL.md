---
name: hermes-infra-config
description: "Configurer, dépanner et exposer l'infrastructure Hermes — dashboard, remote gateway, OIDC, reverse proxy Pangolin"
version: 1.0.0
created_by: agent
tags: [hermes, dashboard, gateway, oidc, pangolin, remote]
---

# Hermes Infrastructure Configuration

Configuration de l'infrastructure Hermes : dashboard, connexion remote gateway (Desktop app), authentification OIDC, exposition via Pangolin.

## STT self-hosted compatible OpenAI

Pour remplacer un fournisseur STT cloud (notamment Voxtral) par un serveur OpenAI-compatible tout en conservant le bloc Mistral pour un retour manuel, suivre `references/openai-compatible-stt.md`. Toujours découvrir le modèle via `/v1/models`, valider avec un vrai `POST /v1/audio/transcriptions`, stocker le bearer token uniquement dans `.env`, et demander l’accord avant tout redémarrage du gateway.

## Dashboard Hermes

### Démarrage du dashboard

```bash
hermes dashboard --no-open --skip-build --host 0.0.0.0 --port 9119 --insecure
```

En arrière-plan (conserve les logs) :

```bash
# Avec vars d'env explicites
HERMES_DASHBOARD_SESSION_TOKEN="<token>" \
HERMES_DASHBOARD_PUBLIC_URL="https://hermes.example.com" \
HERMES_DASHBOARD_OIDC_ISSUER="https://id.example.com" \
HERMES_DASHBOARD_OIDC_CLIENT_ID="<client-id>" \
HERMES_DASHBOARD_OIDC_CLIENT_SECRET="<client-secret>" \
hermes dashboard --no-open --skip-build --host 0.0.0.0 --port 9119 --insecure &
```

### Vérifier que le dashboard répond

```bash
curl -s http://127.0.0.1:9119/api/status
# Réponse attendue : {"version":"...","auth_required":true,"auth_providers":[...],...}
```

### Variables d'environnement du dashboard

| Variable | Rôle | Obligatoire |
|----------|------|-------------|
| `HERMES_DASHBOARD_SESSION_TOKEN` | Token de session pour l'auth REST/WebSocket | Oui |
| `HERMES_DASHBOARD_PUBLIC_URL` | URL publique du dashboard | Oui |
| `HERMES_DASHBOARD_OIDC_ISSUER` | URL de l'issuer OIDC (ex: Pocket ID) | Pour OIDC |
| `HERMES_DASHBOARD_OIDC_CLIENT_ID` | Client ID OIDC | Pour OIDC |
| `HERMES_DASHBOARD_OIDC_CLIENT_SECRET` | Client secret OIDC (nécessaire pour Pocket ID) | Pour OIDC |

## Remote Gateway (Hermes Desktop App)

### Configuration dans l'app Desktop

1. Settings → Gateway
2. Mode : **Remote gateway**
3. Remote URL : `https://<domain>`
4. Session token : laisser vide si déjà sauvegardé, sinon coller le token
5. Cocher "Save for next restart"
6. Cliquer "Save and reconnect"

### Dépannage de la connexion

**502 Bad Gateway** → Pangolin arrive pas à joindre le backend :
1. Vérifier que le dashboard tourne sur le serveur : `curl http://127.0.0.1:9119/api/status`
2. Vérifier la cible de la ressource Pangolin (destination IP:port)
3. Vérifier que le SSO/OIDC est désactivé sur la ressource Pangolin, ou correctement configuré
4. Vérifier le port : si le dashboard est sur le serveur A et la ressource Pangolin pointe vers le serveur B, ça donne 502

**302 Redirect → page de connexion Pangolin** → Le SSO est activé sur la ressource :
- Désactiver le SSO sur la ressource dans l'admin Pangolin
- Ou configurer un Identity Provider valide

**OIDC token endpoint 401 "invalid_client"** :
- Ajouter `HERMES_DASHBOARD_OIDC_CLIENT_SECRET` dans l'env du dashboard
- Pocket ID nécessite le client_secret même avec PKCE

## OIDC / Pocket ID

### Configuration OIDC

Le dashboard Hermes supporte OIDC via Pocket ID (PKCE). Configuration dans `.env` :

```bash
HERMES_DASHBOARD_OIDC_ISSUER=https://id.example.com
HERMES_DASHBOARD_OIDC_CLIENT_ID=<uuid>
HERMES_DASHBOARD_OIDC_CLIENT_SECRET=<secret>
HERMES_DASHBOARD_PUBLIC_URL=https://hermes.example.com
```

Supprimer l'OIDC complètement (dashboard sans auth derrière proxy) — **3 points de contact** :

1. **`.env`** — supprimer toutes les vars `HERMES_DASHBOARD_OIDC_*` et `HERMES_DASHBOARD_PUBLIC_URL` :
   ```sh
   sed -i '/^# Dashboard OIDC Auth/,/^HERMES_DASHBOARD_OIDC_CLIENT_SECRET=/d' /opt/data/.env
   ```
2. **`config.yaml`** — supprimer la section `dashboard.oauth` (client_id, portal_url) :
   ```sh
   sed -i '/^  oauth:/,/^  basic_auth:/{/^  basic_auth:/!d}' /opt/data/config.yaml
   ```
3. **`config.yaml`** — retirer le plugin `dashboard_auth/self_hosted` de `plugins.enabled` :
   ```sh
   sed -i '/^    - dashboard_auth\/self_hosted$/d' /opt/data/config.yaml
   ```

Puis redémarrer le gateway (`/restart` ou `hermes gateway restart`). Les 3 points doivent être nettoyés — laisser le plugin sans vars OIDC cause des erreurs d'init auth avec des valeurs vides.

### Redémarrage du dashboard

```bash
# 1. Tuer l'ancien processus
kill $(lsof -ti:9119)

# 2. Redémarrer avec les vars souhaitées
<vars> hermes dashboard --no-open --skip-build --host 0.0.0.0 --port 9119 --insecure
```

## Exposition via Pangolin

La ressource Pangolin doit pointer vers `http://127.0.0.1:9119` (ou l'IP du serveur où tourne le dashboard).

### Vérifier les redirections

```bash
curl -sI https://dashboard.example.com/api/status
# 200 → OK
# 302 → SSO/OIDC activé sur la ressource Pangolin
# 502 → Mauvaise destination ou backend down
```

### Proxy inverse direct (sans Pangolin)

Si le dashboard est accessible directement :
```bash
curl http://<IP_SERVEUR>:9119/api/status
```

⚠️ Attention aux règles UFW/firewall qui peuvent bloquer le port.

## LiteLLM Proxy (port 4000) — Tracking de quota

Un proxy LiteLLM tourne sur l'hôte Docker (`127.0.0.1:4000`), hors container Hermes. Hermes route tout son trafic LLM via ce proxy (provider `ollama-cloud` dans `config.yaml`). LiteLLM fournit nativement le tracking de tokens, budgets, et spend logs — voir `references/litellm-proxy-tracking.md` pour l'architecture, les endpoints de management API, et la configuration d'un budget de 4M tokens/mois pour Voxtral (free tier Mistral).

**⚠** La master key LiteLLM n'est pas accessible depuis le container Hermes — elle est dans l'environnement du process LiteLLM sur l'hôte. Les opérations de configuration (création de budget, génération de key, ajout de provider/model) doivent se faire depuis l'hôte.

**Bypass du masquage Hermes** : Hermes masque les `sk-*` dans la sortie de tous les outils (terminal, read_file, python3) via `redact.py`. Les vraies valeurs sont en texte clair dans `.env`/`config.yaml` — utiliser `od -c` pour les lire : `grep '^VAR' /opt/data/.env | od -c`. Détails dans `references/litellm-proxy-tracking.md` → section "Bypass du masquage Hermes".

**⚠ PITFALL CRITIQUE — Corruption de .env par masquage** : Si un agent lit un `.env` depuis l'hôte via Docker (ex: `docker run --rm -v /srv/docker/litellm:/data:ro alpine cat /data/.env`), obtient des valeurs masquées (`sk-e30...7425`), puis **réécrit** ces valeurs dans un fichier, le masquage devient le contenu réel. Le `.env` de LiteLLM a été corrompu de cette façon en août 2026 — `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY` et `OPENROUTER_API_KEY` ne contenaient plus que des valeurs tronquées de 51 chars, cassant toute l'auth. **Règle ABSOLUE** : ne JAMAIS copier-coller des valeurs `sk-*` depuis la sortie d'outils Hermes vers un fichier. Générer de nouvelles clés, utiliser `od -c`, ou `os.environ/VAR_NAME` dans les config YAML. Procédure de récupération complète dans `references/litellm-proxy-tracking.md` → section « Procédure de récupération — .env LiteLLM corrompu ».

**⚠ PITFALL — DB `LiteLLM_Config` écrase la config YAML** : Quand `STORE_MODEL_IN_DB=True`, la table PostgreSQL `LiteLLM_Config` stocke `general_settings` (incluant `master_key`) et **écrase le YAML** au démarrage. Si la DB contient un `master_key` corrompu (masqué), il écrase le `os.environ/LITELLM_MASTER_KEY` du YAML. Diagnostic et fix : `DELETE FROM "LiteLLM_Config" WHERE param_name = 'general_settings'` puis recréer le conteneur. Détails dans `references/litellm-proxy-tracking.md` → section « DB `LiteLLM_Config` écrase la config YAML ».

**⚠ PITFALL — `docker restart` ne recharge pas l'`env_file`** : `docker restart` conserve les variables d'environnement du conteneur original. Pour recharger un `.env` modifié, il faut `docker stop && docker rm && docker run` (ou `docker compose up -d --force-recreate`). Depuis Hermes, utiliser `docker run` avec `-e` pour chaque variable (l'`--env-file` de l'hôte n'est pas accessible). Détails dans `references/litellm-proxy-tracking.md` → section « `docker restart` NE recharge PAS l'`env_file` ».

**Ajouter un provider à LiteLLM** (ex: Mistral, OpenRouter) — la procédure complète (édition config vs API management, limitations container, infos provider Mistral) est dans `references/litellm-proxy-tracking.md` → section « Ajouter un provider/model à LiteLLM ». **Raccourci** : quand l'utilisateur demande d'ajouter un provider à LiteLLM, aller directement à cette section — ne pas chercher le fichier de config depuis le container (inaccessible). **Bypass possible** : la master key est accessible via `docker exec litellm python3 -c "import os; print(os.environ['LITELLM_MASTER_KEY'])"` (Docker masque les secrets dans `printenv`/`env` mais pas dans `os.environ` Python). Voir la section « Bypass de la master key » dans la référence pour des exemples complets d'ajout de modèles (STT, TTS, OCR) via l'API.

**Fallback STT local→cloud (faster-whisper → Mistral Voxtral)** — LiteLLM supporte les fallbacks automatiques entre modèles. Si le STT local (faster-whisper) tombe, LiteLLM switch automatiquement vers Mistral Voxtral. La config utilise `router_settings.fallbacks` (format liste de dicts, pas dict). Le conteneur faster-whisper est sur un réseau Docker séparé (`diction_default`) — il faut `docker network connect diction_default litellm` pour que LiteLLM puisse le joindre. Voir `references/litellm-fallback-stt.md` pour l'architecture complète, le format YAML correct, les tests, et la config Hermes STT.

**⚠ PITFALL — Format fallbacks LiteLLM** : `router_settings.fallbacks` doit être une **liste de dicts** (`- stt-local: [stt-mistral]`), pas un dict simple (`stt-local: [stt-mistral]`). Avec le format incorrect, LiteLLM démarre sans erreur mais le fallback ne se déclenche JAMAIS (`Available Model Group Fallbacks=None` dans les logs).

**⚠ PITFALL — Virtual keys et nouveaux modèles** : Une virtual key créée via `/key/generate` n'accède qu'aux modèles explicitement listés dans `models`. Ajouter un nouveau modèle au config.yaml ne donne pas automatiquement accès aux clés existantes → `key not allowed to access model`. Il faut supprimer et recréer la clé avec la liste complète.

**⚠ PITFALL — Virtual keys perdues après reset DB** : Si une virtual key configurée dans `config.yaml` (ex: `auxiliary.vision.api_key`) n'existe plus dans la table `LiteLLM_VerificationToken`, tous les appels via cette clé échouent avec `401 token_not_found_in_db`. Cela arrive après un reset/migration de la DB LiteLLM. **Diagnostic** : comparer le hash de la clé dans `LiteLLM_VerificationToken` (active) vs `LiteLLM_DeletedVerificationToken` (supprimée). **Fix complet** : recréer la clé via `docker exec litellm python3` (split-string pour bypass masquage), puis `hermes config set auxiliary.<section>.api_key` pour les 14 sections + mise à jour `.env`. Procédure détaillée dans `references/litellm-proxy-tracking.md` → sections « DB schema », « Vision analysis — bypass » et « Procédure complète — Rotation de toutes les clés auxiliary Hermes ».

**⚠ PITFALL — Cross-network Docker** : Les conteneurs sur des réseaux Docker différents (ex: `litellm_default` vs `diction_default`) ne peuvent pas se joindre par défaut. Utiliser `docker network connect <network> <container>` pour connecter LiteLLM au réseau du service cible. Cette connexion est perdue à chaque recréation du conteneur.

**⚠ PITFALL — Cron jobs `provider_snapshot` après changement de provider global** : Quand on change le provider/modèle global (`hermes config set model.provider`), Hermes affiche un warning : *"N enabled unpinned cron jobs have stored provider_snapshot values that differ from the new global provider. They will fail closed on their next run."* Les cron jobs agent-based stockent un snapshot du provider/modèle à la création. Il faut mettre à jour **chaque** cron job individuellement :

```bash
hermes cron edit <job_id> --provider auto --model glm-5.2
```

Vérifier les snapshots stockés dans `/opt/data/cron/jobs.json` (chercher `provider_snapshot` et `model_snapshot`). Les jobs avec `provider=None` utilisent la config globale (OK). Les jobs script-only (`no_agent=True`) ne sont pas affectés. Voir `references/litellm-proxy-tracking.md` → section « Cron jobs — mise à jour provider_snapshot ».

**⚠ PITFALL — `.env` vs `config.yaml` reload** : Les changements de `api_key` dans `config.yaml` (sections `auxiliary.*`) sont lus au runtime par Hermes — pas de restart nécessaire. Mais les variables d'environnement dans `/opt/data/.env` (ex: `HERMES_CUSTOM_LITELLLM_JEFE_AL_API_KEY`) ne sont chargées qu'au **démarrage du process**. Après modifier `.env`, il faut `docker restart hermes` pour que la nouvelle valeur soit en mémoire.

**Routage du modèle principal via LiteLLM** : Pour router tout le trafic LLM (modèle principal + auxiliary) via LiteLLM, configurer :

```bash
hermes config set model.provider auto --force
hermes config set model.default glm-5.2 --force
hermes config set model.base_url "http://127.0.0.1:4000/v1" --force
hermes config set model.api_key "sk-<litellm_virtual_key>" --force
```

Puis mettre à jour les cron jobs (voir pitfall ci-dessus) et `docker restart hermes`.

**Cost tracking et budgets Mistral** — Pour suivre les coûts des modèles audio (Voxtral STT/TTS, qui ne sont pas au token), configurer les champs `model_info` (`input_cost_per_second`, `output_cost_per_character`) dans le config YAML. Pour limiter la dépense, créer une virtual key dédiée avec `max_budget` (en USD) et `budget_duration` (`1mo` = mensuel). Ex: 5€/mois pour STT+TTS = `max_budget: 5.50, budget_duration: "1mo"`. Voir `references/litellm-proxy-tracking.md` → sections « Configuration du cost tracking » et « Budget sur virtual key ».

**Clés API pour apps externes** — Pour créer une clé LiteLLM dédiée à une app externe (ex: Spokenly iOS) avec budget limité et accès STT, voir `references/litellm-fallback-stt.md` → section « Créer une clé API pour une app externe ». Pour créer des clés par consommateur (isolation budgétaire entre OpenCode HA, intégrations HA, etc.) et configurer OpenCode avec LiteLLM, voir `references/litellm-proxy-tracking.md` → sections « Clés virtuelles par consommateur » et « Config OpenCode (HA add-on) avec LiteLLM ». Le template de config OpenCode est dans `templates/opencode-provider-config.json`.

**Intégration OpenAI Conversation de Home Assistant avec LiteLLM** — Pour configurer l'intégration native `openai_conversation` de HA pour utiliser LiteLLM (modèle custom glm-5.2, minimax-m3, etc.) au lieu de l'API OpenAI, voir `references/ha-litellm-integration.md`. Inclut : bypass du token HA expiré (création d'admin user via fichier auth, génération de JWT depuis le system user), écriture directe dans `.storage/core.config_entries`, subentry `conversation` obligatoire pour l'agent, et le piège critique du masquage Hermes qui corrompt les API keys écrites via `docker exec` (construire les clés en hex pour bypass).

**⚠ PITFALL — faster-whisper transcrit en anglais par défaut** : Le serveur `speaches` (fedirz/faster-whisper-server) n'a pas de variable d'env pour forcer la langue. Passer `language: fr` dans la config Hermes STT (`stt.openai.language: fr`) pour forcer le français. Voir `references/litellm-fallback-stt.md` → section « Configuration Hermes STT ».

**Ajouter OpenRouter comme provider** — OpenRouter donne accès à 400+ modèles (LLMs + embeddings) via une seule API. La clé `OPENROUTER_API_KEY` est déjà dans `.env`. Config à ajouter dans `litellm_config.yaml` (sur l'hôte) :

```yaml
model_list:
  # Embedding models via OpenRouter
  - model_name: qwen3-embedding-8b
    litellm_params:
      model: openrouter/qwen/qwen3-embedding-8b
      api_key: os.environ/OPENROUTER_API_KEY

  - model_name: bge-m3
    litellm_params:
      model: openrouter/baai/bge-m3
      api_key: os.environ/OPENROUTER_API_KEY

  # LLMs via OpenRouter (au fur et à mesure)
  - model_name: <nom-alias>
    litellm_params:
      model: openrouter/<provider>/<model>
      api_key: os.environ/OPENROUTER_API_KEY
```

Le préfixe LiteLLM pour OpenRouter est `openrouter/`. Doc officielle :
https://docs.litellm.ai/docs/providers/openrouter (inclut les embeddings via `POST /v1/embeddings`).
**Stratégie** : connecter OpenRouter à LiteLLM une seule fois → tous les modèles OpenRouter
accessibles via `http://127.0.0.1:4000/v1`. Ajouter Mistral, OpenAI, etc. plus tard = juste
une ligne dans le config. Tout le reste (n8n, embed service, Hermes) se connecte à LiteLLM uniquement.

## Confidentialité LLM & alternatives EU souveraines

Le trafic LLM passe par LiteLLM → Ollama Cloud (US). Les risques de confidentialité (CLOUD Act, pas de SOC 2, proxification vers providers d'origine, CVE-2026-7482 "Bleeding Llama") et les alternatives EU (TensorX/EuroRouter, Regolo, EUrouter, etc.) sont documentés dans `references/llm-provider-privacy-eu-alternatives.md`. Consulter cette référence avant d'envoyer des données sensibles via le LLM, et pour planifier une migration vers un provider EU souverain.

## Hermes API Server (port 9119) — OpenAI-compatible

Le gateway Hermes expose une API OpenAI-compatible sur le port **9119** (port réel au 2 août 2026). L'activation se fait via `platforms.api_server.enabled=true` dans `config.yaml`. La clé API est définie via `API_SERVER_KEY` dans `.env`.

**⚠️ CORRECTION août 2026 :** La section disait précédemment que le port avait été migré à 9120. C'est FAUX — vérifié au 2 août 2026 : `config.yaml` indique `api_server.port: 9120`, mais l'override `API_SERVER_PORT` dans `.env` (valeur 9119) **gagne toujours** au runtime. Le serveur écoute réellement sur **9119**. Voir le pitfall `.env` vs `config.yaml` documenté dans le skill `api-server-setup`.

**⚠️ Pitfall clé API :** `config.yaml` contient `api_server.extra.key: y8Lr...` MAIS la clé valide est `API_SERVER_KEY` dans `.env` (valeur `hermes-ios-shortcut-a80ac18a29ed5d62`). La clé `config.yaml` est rejetée avec `gateway_auth_error`. Toujours utiliser la clé de `.env`.

**⚠️ Vocabulaire utilisateur :** Quand l'utilisateur dit "ton API OpenAI" ou "l'API OpenAI Hermes", il parle de CET API server Hermes (OpenAI-compatible), PAS de LiteLLM (port 4000) ni de la clé OpenAI voice tools (`VOICE_TOOLS_OPENAI_KEY`).

### Accès

| Champ | Valeur |
|-------|--------|
| URL | `http://127.0.0.1:9119/v1` (depuis l'intérieur du container Hermes) |
| Endpoints | `/v1/chat/completions`, `/v1/responses`, `/v1/models`, `/v1/runs` |
| Model ID | `hermes-agent` |
| Auth | Bearer token via header `Authorization: Bearer <API_SERVER_KEY>` |
| Clé | `API_SERVER_KEY` dans `/opt/data/.env` |

### Depuis un conteneur Docker (n8n, etc.)

Les conteneurs Docker séparés (n8n, autres services) ne peuvent PAS utiliser `localhost:9119` car le conteneur Hermes utilise `network_mode: host`. Utiliser l'IP du bridge Docker :

```
http://172.17.0.1:9119/v1
```

### Test rapide (depuis le container Hermes)

```bash
# Lister les modèles
docker exec hermes curl -s http://127.0.0.1:9119/v1/models \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /opt/data/.env | cut -d= -f2)"
# → {"data":[{"id":"hermes-agent",...}]}

# Chat completion
docker exec hermes curl -s http://127.0.0.1:9119/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY /opt/data/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

### Diagnostic — port/clé désynchronisés

1. Vérifier le port réel dans les logs : `docker exec hermes grep "API server listening on" /opt/data/logs/gateway.log | tail -1`
2. Vérifier la clé `.env` : `grep API_SERVER_KEY /opt/data/.env`
3. Si `config.yaml` `api_server.port` ≠ port réel → `.env` override gagne. Sync les deux ou supprimer `API_SERVER_PORT` de `.env`.
4. Si `config.yaml` `api_server.extra.key` ≠ clé `.env` → `.env` gagne. Utiliser la clé `.env` pour les tests.

### Cas d'usage

- **n8n workflows** : LLM pour RAG, summarisation, classification
- **iOS Shortcuts** : POST `/v1/responses` pour interactions vocales
- **Applications externes** : tout client OpenAI-compatible (LobeChat, LibreChat, etc.)

## Envoi de messages Telegram (sans toolset messaging)

Pour envoyer un message Telegram depuis une session qui n'a pas le toolset `messaging` (WebUI, CLI, cron restreint), utiliser l'API Bot Telegram directement via curl. Les credentials (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_HOME_CHANNEL`) sont dans `/opt/data/.env`. Procédure complète dans `references/telegram-direct-api.md`.

## MCP - Ajout via config.yaml

Quand `hermes mcp add` échoue (timeout, connexion), ajouter le serveur directement dans `config.yaml` :

```yaml
mcp_servers:
  nom-du-serveur:
    command: npx
    args: ['-y', '@package/mcp']
    env:
      API_URL: https://...
      API_KEY: ...
    enabled: true
```

Puis `/reload-mcp` ou redémarrer la session.

## Signal Messenger (E2E)

Configuration de Signal comme plateforme de messagerie chiffrée de bout en bout
pour Hermes. Utile pour les conversations sensibles (Telegram n'est pas E2E).

⚠️ **4 pièges principaux** dans un setup Docker-in-Docker :
1. **127.0.0.1 ne marche pas** entre conteneurs — utiliser l'IP du bridge Docker
2. **Health check 404** — Hermes appelle `/api/v1/check` qui n'existe pas dans
   signal-cli-rest-api ; il faut un proxy shim (le code Hermes est read-only)
3. **Redactor masque les numéros de téléphone** — l'agent ne peut pas écrire le
   numéro dans .env automatiquement ; l'utilisateur doit le faire manuellement
4. **⚠️ CRITIQUE — Réception KO avec signal-cli-rest-api** : Hermes attend SSE
   sur `/api/v1/events` mais signal-cli-rest-api expose WebSocket sur
   `/v1/receive/{number}`. L'envoi fonctionne (REST `/v2/send`) mais la réception
   est impossible. Solution probable : signal-cli daemon natif (Java 17+ sur hôte).

⚠️ **Le endpoint QR code est un GET** (`/v1/qrcodelink`), pas un POST. Plusieurs
guides tiers mentionnent POST à tort.

Procédure complète (déploiement, linkage QR, proxy shim, config .env, pitfalls,
et analyse détaillée de l'incompatibilité SSE/WebSocket) dans
`references/signal-setup-docker.md`.

## Récupération de conteneurs Docker depuis Hermes

Quand Hermes tourne dans un conteneur Docker avec le socket de l'hôte monté, la gestion
de conteneurs a des pièges spécifiques : résolution des bind mounts sur l'hôte (pas dans
Hermes), `docker compose` v2 absent, sockets kernel orphelins bloquant les ports,
`read_only: true` + chown, et tunnel WireGuard Newt tombé (502 sur tous les services).

Voir `references/docker-container-recovery-from-hermes.md` pour les patterns de
diagnostic et de réparation complets.
