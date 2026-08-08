---
name: crosswatch-fr
description: >
  Utiliser CrossWatch (MCP) pour gérer le sync entre Jellyfin et Trakt/SIMKL/MDBList/AniList/TMDB
  (dans les deux directions : Jellyfin→tracker OU tracker→Jellyfin). OBLIGATOIRE quand
  l'utilisateur parle de CrossWatch, sync, suivi, watcher, problèmes, historique, scrobble,
  suivi de films/séries, ou tracker. TOUJOURS en français.
---

# CrossWatch FR — Guide complet en français

Charge le MCP `crosswatch` (si pas déjà fait) avant d'utiliser les outils.
L'URL est configurée sur `https://crosswatch.jefe.ovh` avec le cookie de session.
**TOUJOURS répondre en français.**

## Commandes principales

### 📡 État du watcher temps réel
```
watch_status()
```
Voir si le watcher tourne, quelles routes sont actives.

### 📊 Résumé du dernier sync
```
sync_run_summary()
```
Voir le résultat du dernier run : combien d'items ajoutés/supprimés/modifiés.

### 🚀 Lancer un sync manuel
```
sync_run()
```
Lance une synchro complète. Attention : prend du temps (30+ min pour ~1200 items).

### 🔍 Problèmes (analyzer)
```
analyzer_problems()
```
Voir les items qui ont pas pu être sync (missing IDs, missing peers, etc.)

### 📋 Voir les paires de sync
```
list_pairs()
```
Liste tous les sync actifs.

### 🖥 Voir la config complète
```
get_config()
```

### 📜 Logs du watcher
```
watch_logs(tail=50)
```
Dernières lignes des logs temps réel.

### 👁 Ce qui est en cours
```
watch_currently_watching()
```
Voir ce que l'utilisateur regarde en ce moment.

### 📈 Insights / Stats
```
get_insights(limit_samples=60, history=3)
get_stats()
```

## Installer ou modifier la config du MCP

```bash
printf 'Y\nY\n' | hermes mcp add crosswatch \
  --command "/opt/hermes/.venv/bin/python3" \
  --args "/opt/data/mcp/crosswatch_server.py" \
  --env "CW_BASE_URL=https://crosswatch.jefe.ovh" \
  --env "CW_COOKIE=cw_auth=..." \
  --env "CW_INTERNAL=true"
```

Le cookie peut expirer — si `auth_status()` retourne `authenticated: false`, il faut refaire un login.

### Modifier les env vars du MCP (sans `hermes mcp configure`)

`hermes mcp configure` ne gère pas les ENV vars. Pour modifier les variables d'env d'un MCP server existant :
```bash
hermes --accept-hooks mcp remove crosswatch && \
printf 'Y\nY\n' | hermes mcp add crosswatch \
  --command /opt/hermes/.venv/bin/python3 \
  --args /opt/data/mcp/crosswatch_server.py \
  --env "CW_BASE_URL=..." \
  --env "CW_COOKIE=..." \
  --env "CW_INTERNAL=true"
```

## Ajouter une paire de sync

**Rappel sur la direction :** `source` → `target`. Si tu veux importer depuis Trakt vers Jellyfin, `source="TRAKT", target="JELLYFIN"`. L'inverse pour pousser depuis Jellyfin vers Trakt.

```python
# Pousser Jellyfin → Trakt (ce que l'utilisateur a regardé sur Jellyfin va sur Trakt)
add_pair(source="JELLYFIN", target="TRAKT", mode="one-way")

# OU importer Trakt → Jellyfin (ce que l'utilisateur a regardé ailleurs remonte sur Jellyfin)
add_pair(source="TRAKT", target="JELLYFIN", mode="one-way")

# Les deux directions PEUVENT coexister (paires séparées)
# JELLYFIN → TRAKT (un watcher)
# TRAKT → JELLYFIN (l'autre watcher)
```

```python

### Avec profil source/target spécifique (multi-user)

```python
# JELLYFIN avec un profil dédié (ex: "JELLYFIN-P01" pour Réfé) → TRAKT
add_pair(
    source="JELLYFIN", target="TRAKT", mode="one-way",
    source_instance="JELLYFIN-P01",
    target_instance="default"
)
```

Les champs `source_instance` / `target_instance` ne sont pas dans le schema OpenAPI `PairIn` affiché sur la doc, mais ils sont bien supportés côté API (documentés dans le wiki). Par défaut, les deux valent `"default"`.
```

### Avec features avancées (anime-only pour AniList)

```python
# AniList → anime uniquement
add_pair(
    source="JELLYFIN", target="ANILIST", mode="two-way",
    features={
        "watchlist": {"enable": True, "add": True, "remove": True,
                      "use_anime_mapping": True, "anime_only_sync": True},
        "history": {"enable": True, "add": True, "remove": True}
    }
)

# TMDB → tout (pas de filtre anime)
add_pair(
    source="JELLYFIN", target="TMDB", mode="two-way",
    features={
        "watchlist": {"enable": True, "add": True, "remove": True,
                      "use_anime_mapping": False, "anime_only_sync": False},
        "history": {"enable": True, "add": True, "remove": True}
    }
)

# Avec progress (comme pour la paire crosswatch locale)
features_with_progress = {
    "watchlist": {"enable": True, "add": True, "remove": True,
                  "use_anime_mapping": False, "anime_only_sync": False},
    "history": {"enable": True, "add": True, "remove": True},
    "progress": {"enable": True, "add": True, "remove": True,
                 "min_seconds": 60, "delta_seconds": 30, "max_percent": 95.0,
                 "propagate_timestamp_updates": False}
}
```

## Supprimer une paire

```python
delete_pair(pair_id="pair_...")
```

## Workflows rapides

### "Montre moi l'état de CrossWatch"
1. `watch_status()` → watcher
2. `sync_run_summary()` → dernier sync
3. `analyzer_problems()` → problèmes

### "Nettoie les problèmes"
Quand le sync laisse des milliers d'erreurs :
1. `maintenance_clear_state()` → vide l'état
2. `maintenance_clear_cache()` → vide le cache
3. `maintenance_clear_metadata_cache()` → vide le cache metadata
4. `sync_run()` → sync complet
5. Attendre la fin
6. `analyzer_problems()` → vérifier les problèmes restants
Résultat typique : les `missing_peer` (10k+) tombent à ~0.

### "Ma série sync pas — pas de TMDB ID"
1. `analyzer_problems()` → voir les `missing_ids` / `key_missing_ids`
2. Chercher le TMDB ID via `metadata_search(q="titre série", typ="tv", year=YYYY)`
3. Si pas trouvé, essayer variantes (titre anglais, année -1, type movie)
4. Le prochain sync résoudra automatiquement avec le metadata resolver

### "Active le watcher temps réel"
1. Configurer les routes dans l'UI CrossWatch → Settings → Scrobble → Watcher
   (⚠️ L'API config est read-only : GET fonctionne, PUT/PATCH retourne Method Not Allowed)
2. Les routes watcher sont indépendantes des paires de sync. Ajouter une paire `add_pair()` ne crée PAS automatiquement une route watcher — les deux sont distincts.
3. `watch_start()` → démarre le watcher avec les routes déjà configurées dans l'UI
4. `watch_status()` → vérifier que les routes sont running

### "Lance un sync"
1. `sync_run()` → démarre (HTTP endpoint: `POST /api/run`, pas `/api/sync/run`)
2. Attendre, puis `sync_run_summary()` → résultat

### "Limite le sync à un seul user Jellyfin" (multi-user)

Quand CrossWatch est connecté à Jellyfin avec un token admin, il lit **tous les users** — et pousse tout vers les trackers. Pour limiter à un seul user :

> ⚠️ **One-way recommandé** : en multi-user, préfère le mode `one-way` (Jellyfin → tracker). Le two-way ramène aussi le contenu des trackers vers Jellyfin, ce qui pollue l'historique des autres users. Si l'utilisateur se plaint de contenu non-regardé sur ses trackers, c'est le signe N°1 d'un multi-user non filtré.

1. **UI CrossWatch → Settings → Connections → Authentication → Jellyfin**
2. Créer un **nouveau profil/instance** dédié à l'user voulu (ex: "Réfé")
   - Renseigner son username + password → CrossWatch génère un token scopé à cet user
3. **Settings → Synchronization → Pairs**
4. Éditer chaque paire → changer le profil source Jellyfin de `default` vers le nouveau profil
5. Run les paires → seules les données de cet user sont sync

📎 Voir `references/multi-user-jellyfin.md` pour le détail complet.

### "Ajoute AniList et TMDB comme sync targets"
1. Vérifier que les provider instances existent : `list_provider_instances()` ou `GET /api/provider-instances`
   - AniList et TMDB ont déjà une instance `default` quand Jefe les ajoute côté app
2. Ajouter JELLYFIN → ANILIST avec `anime_only_sync=True` + `use_anime_mapping=True`
3. Ajouter JELLYFIN → TMDB avec `anime_only_sync=False` (tout sync)
4. Lancer `sync_run()` pour démarrer le sync vers les nouveaux targets

## ⚠️ Direction du sync — Jellyfin comme cible (Tracker → Jellyfin)

**Le piège le plus fréquent :** par défaut, le skill et l'UI montrent tout comme `JELLYFIN → Traktor`. Mais l'utilisateur peut vouloir **l'inverse** : que les trackers (Trakt, SIMKL, etc.) poussent leur contenu **vers Jellyfin**.

**Quand c'est nécessaire :** l'utilisateur regarde ailleurs que sur Jellyfin (Trakt, autre serveur, cinéma) et veut que **Jellyfin reflète tout son historique**, pas l'inverse.

**Les paires actuelles vers Jellyfin :**

| Source → Target | Mode | Watchlist | History |
|----------------|------|-----------|---------|
| TRAKT → JELLYFIN | one-way | ❌ | ✅ |
| SIMKL → JELLYFIN | ❌ Existe pas | ❌ | ❌ |
| MDBLIST → JELLYFIN | ❌ Existe pas | ❌ | ❌ |

**Ce qu'il faut ajouter/modifier :**

```python
# Ajouter watchlist à la paire TRAKT → JELLYFIN
httpx.put(f"{base}/api/pairs/pair_7dcd62406e01", headers=headers, json={
    "features": {
        "watchlist": {"enable": True, "add": True, "remove": True},
        "history": {"enable": True, "add": True, "remove": True}
    }
})

# Ajouter la paire SIMKL → JELLYFIN
httpx.post(f"{base}/api/pairs", headers=headers, json={
    "source": "SIMKL", "target": "JELLYFIN", "mode": "one-way",
    "features": {
        "watchlist": {"enable": True, "add": True, "remove": True},
        "history": {"enable": True, "add": True, "remove": True}
    }
})

# Ajouter la paire MDBLIST → JELLYFIN
httpx.post(f"{base}/api/pairs", headers=headers, json={
    "source": "MDBLIST", "target": "JELLYFIN", "mode": "one-way",
    "features": {
        "watchlist": {"enable": True, "add": True, "remove": True},
        "history": {"enable": True, "add": True, "remove": True}
    }
})
```

**Contexte du diagnostic :** quand l'utilisateur dit "il me sync Jellyfin" mais que l'inverse est nécessaire, ou "j'ai regardé autre part", le problème est presque toujours la **direction** des paires. Vérifier :
1. `list_pairs()` ou `GET /api/pairs` → regarder la colonne `source`
2. Si toutes les paires sont `JELLYFIN → Traktor` mais que l'utilisateur veut l'inverse, il faut **soit inverser, soit ajouter des paires Traktor → JELLYFIN**
3. Les deux directions peuvent coexister (JELLYFIN→TRAKT + TRAKT→JELLYFIN en paires séparées)
4. Le `PUT /api/pairs/{id}` supporte les mises à jour **partielles** — envoyer juste `{"features": {...}}` sans respecifier mode/source/target suffit pour modifier les features d'une paire existante

## Diagnostiquer les problèmes utilisateur 👤

### "J'ai du contenu que j'ai pas regardé qui apparaît sur mes trackers"

**Symptôme typique :** l'utilisateur voit sur Trakt/SIMKL/AniList des films ou épisodes qu'il n'a **jamais** regardés, marqués comme vus. Ça arrive quand d'autres membres de la famille utilisent le même serveur Jellyfin.

**Cause la plus probable :** CrossWatch est connecté à Jellyfin avec un **token admin** qui voit **tous les utilisateurs**. Le sync pousse l'historique de tout le monde vers les trackers perso de l'utilisateur.

**Solution rapide :**
1. Créer un nouveau user Jellyfin **non-admin** dédié à CrossWatch (voir [multi-user-jellyfin.md → Alternative B](references/multi-user-jellyfin.md))
2. Mettre à jour le profil Jellyfin dans CrossWatch avec ce nouveau compte
3. Passer toutes les paires en **one-way**
4. **Backfill** l'historique des trackers vers le nouveau compte (voir [Backfill workflow](references/multi-user-jellyfin.md#backfill--copier-lhistorique-des-trackers-vers-le-nouveau-user-jellyfin))

### Autres problèmes courants

| Type | Nb typique | Signification |
|------|-----------|---------------|
| `missing_peer` | 0-10000+ après 1er sync | Items en cours sur un côté mais pas l'autre. Normal après premier sync. Disparaît après clear state + resync. |
| `missing_ids` | 20-100 | Items avec IMDb/TVDB mais sans TMDB. Le metadata resolver les résout tout seul au prochain sync. |
| `key_missing_ids` | 5-30 | Items avec juste un ID Jellyfin. Pas de cross-provider. |
| `key_ids_mismatch` | 0-20 | Incohérence entre la clé et les IDs stockés (épisodes d'une série avec IMDb IDs différents). |
| `history_show_normalization` | 2-5 | Séries qui existent d'un côté mais pas de l'autre. Normal, se résout avec le temps. |
| `cw_state_*` (unresolved, blackbox, flap, shadow) | 0-20 | Artéfacts d'état. Disparaissent après clear state. |

## Pitfalls

> 💡 Voir `references/req-pattern-terminal.md` pour le pattern terminal `_req` quand les MCP tools ne sont pas directement accessibles.

### ⚠️ MCP tools non chargés (silent failure)

Le serveur MCP CrossWatch est configuré dans `mcp_servers.crosswatch` du `config.yaml` avec `enabled: true`, mais ses outils peuvent ne **pas apparaître** dans la session Hermes (échec silencieux de découverte).

**Causes possibles :**
- **Timeout de découverte** — `mcp_discovery_timeout: 1.5` peut rater un serveur lent à démarrer
- **Module `fastmcp` introuvable** — le chemin d'import a changé selon la version du SDK `mcp`
- **Python système vs Hermes venv** — `/usr/bin/python3` n'a pas les dépendances, utiliser `/opt/hermes/.venv/bin/python3`
- **Docker socket inaccessible** — sans `CW_INTERNAL=true`, le serveur utilise `docker exec pangolin-cli curl` ; certains profils Hermes (s6, profils externes) n'ont pas `/var/run/docker.sock`
- **DNS/Olm cassé** dans le tunnel

**Diagnostic :**
```bash
# Config existe ?
grep -A 10 "crosswatch:" /opt/data/config.yaml | grep -E "enabled|command|CW_"

# Test MCP
hermes mcp test crosswatch

# Voir les logs gateway
journalctl -u hermes-gateway --no-pager -n 50 2>/dev/null | grep -i "mcp\\\\|crosswatch"
```

**Solutions :**
- **fastmcp pas importable** (mcp SDK ≥1.26) : le SDK a déplacé `fastmcp` sous `mcp.server.fastmcp`. Les scripts qui font `from fastmcp import FastMCP` échouent. Le test `hermes mcp test` passe (le serveur démarre et liste 53 outils) mais les appels API réels retournent du HTML Pangolin placeholder. Fix : ajouter `sys.path.insert(0, "/opt/hermes/.venv/lib/python3.13/site-packages/mcp/server")` avant `from fastmcp import FastMCP` dans le script. Voir le début de `/opt/data/mcp/crosswatch_server.py` pour un exemple.
- **Python système** (`/usr/bin/python3`) : changer pour `/opt/hermes/.venv/bin/python3` via `hermes mcp remove` + `hermes mcp add --command /opt/hermes/.venv/bin/python3`
- **Docker socket manquant** : ajouter `- /var/run/docker.sock:/var/run/docker.sock` au docker-compose
- **Ré-enregistrer proprement** : `hermes --accept-hooks mcp remove crosswatch && printf 'Y\\nY\\n' | hermes mcp add crosswatch --command /opt/hermes/.venv/bin/python3 --args /opt/data/mcp/crosswatch_server.py --env CW_INTERNAL=true --env CW_COOKIE=cw_auth=... --env CW_BASE_URL=https://crosswatch.jefe.ovh`
- **Workaround sans MCP** : utiliser les appels API directs via `docker exec pangolin-cli curl` (pattern `_req` dans `references/req-pattern-terminal.md`)

### ⚠️ CrossWatch API inaccessible depuis Hermes (Pangolin tunnel)

Même avec le MCP qui démarre correctement, les appels API réels vers `crosswatch.jefe.ovh` peuvent échouer depuis l'environnement Hermes (container s6). Symptôme : `hermes mcp test crosswatch` retourne `✓ Connected` mais tout appel d'outil retourne la page "Private Placeholder" de Pangolin.

**Causes :**
- `CW_INTERNAL=true` → appel HTTP direct → DNS public résout vers l'IP du proxy Pangolin → bloqué
- `CW_INTERNAL=false` → `docker exec pangolin-cli curl` → Docker socket inaccessible (profil s6)
- Le service CrossWatch tourne dans une stack Docker derrière Pangolin, inaccessible sans accès au tunnel

**Fix #1 — Accès direct via localhost:8787 (recommandé)**

Le service CrossWatch écoute sur `http://127.0.0.1:8787` depuis le même hôte — ça contourne complètement le tunnel Pangolin.

**⚠️ Nuance CW_BASE_URL + CW_INTERNAL=true** : quand `CW_INTERNAL=true`, le serveur utilise httpx (pas Docker) mais il appelle **toujours l'URL dans CW_BASE_URL**. Si CW_BASE_URL pointe vers le domaine externe (`https://crosswatch.jefe.ovh`), la requête traverse Pangolin et est bloquée. **Il faut mettre CW_BASE_URL à `http://localhost:8787` quand on est en mode interne.**

**⚠️ Problème connu — les `--env` dans `config.yaml` peuvent ne pas être lus comme vraies env vars** : dans la config YAML, les `--env` sont listés comme des arguments (`args:`), pas comme des `env:` réelles. Si le MCP server utilise encore Docker (erreur "Cannot connect to the Docker daemon") alors que tu as mis `CW_INTERNAL=true`, c'est que les `--env` ne sont pas transmis correctement. **Workaround** : faire les appels API directs en Python avec httpx :

```python
import httpx
h = {"Content-Type": "application/json", "Cookie": "cw_auth=..."}
b = "http://localhost:8787"

# Lire les paires
pairs = httpx.get(f"{b}/api/pairs", headers=h, timeout=5).json()

# Modifier une paire en one-way
httpx.put(f"{b}/api/pairs/pair_ID", headers=h, json={"mode": "one-way"}, timeout=5)

# Lancer un sync
httpx.post(f"{b}/api/run", headers=h, json={"label": "Sync description"}, timeout=10)

# Clear state + cache
httpx.post(f"{b}/api/maintenance/clear-state", headers=h, timeout=10)
httpx.post(f"{b}/api/maintenance/clear-cache", headers=h, timeout=10)
```

```bash
# Auth status
curl -sk "http://127.0.0.1:8787/api/app-auth/status" \
  -H "Cookie: cw_auth=..."

# Export Trakt history
curl -sk "http://127.0.0.1:8787/api/export/file?provider=TRAKT&kind=history&format=yamtrack" \
  -H "Cookie: cw_auth=..."

# Analyzer state (trouver items par series_title)
curl -sk "http://127.0.0.1:8787/api/analyzer/state?limit=200" \
  -H "Cookie: cw_auth=..."

# Activity history (scrobbles récents)
curl -sk "http://127.0.0.1:8787/api/activity/history?limit=100" \
  -H "Cookie: cw_auth=..."

# Provider counts (watchlist/history size par provider)
curl -sk "http://127.0.0.1:8787/api/sync/providers/counts" \
  -H "Cookie: cw_auth=..."

# Full config (pairs, instances configurées)
curl -sk "http://127.0.0.1:8787/api/config" \
  -H "Cookie: cw_auth=..."
```

**⚠️ API path mapping (MCP tool ≠ HTTP endpoint)**

Les chemins d'API Réels diffèrent de ceux utilisés par le MCP server :

| MCP tool | HTTP endpoint réel |
|---|---|
| `auth_status` | `GET /api/app-auth/status` |
| `auth_login` | `POST /api/app-auth/login` |
| `get_config` | `GET /api/config` |
| `sync_providers` | `GET /api/sync/providers` |
| `provider_counts` | `GET /api/sync/providers/counts` |
| `list_pairs` | `GET /api/pairs` |
| `add_pair` | `POST /api/pairs` |
| `delete_pair` | `DELETE /api/pairs/{pair_id}` |
| `activity_history` | `GET /api/activity/history` |
| `export_file` | `GET /api/export/file?provider=X&kind=history&format=yamtrack` |
| `analyzer_state` | `GET /api/analyzer/state` |
| `analyzer_problems` | `GET /api/analyzer/problems` |
| `metadata_search` | `GET /api/metadata/search?q=...` |
| `logs_dump` | `GET /api/logs/dump?channel=TRAKT&n=50` |
| `health` | `GET /api/health` |

**Fix #2 — Workaround : utiliser Jellyfin API directement (et MAL comme source complémentaire)**

Quand CrossWatch est down, les données d'historique de visionnage sont disponibles via l'API Jellyfin (publique, PAS derrière Pangolin) et l'API MAL (publique, pas d'OAuth nécessaire).

📎 Voir `references/anime-watch-history-fallback.md` pour les commandes complètes Jellyfin + MAL et la stratégie de combinaison des deux sources.

- **URL Jellyfin** : `https://jflix.jefe.al`
- **Token** : `/opt/data/jellyfin_token.txt`
- **User ID Jefe** : `30174a9fab2b4664a1964a7a8e62aee3`

```bash
JF_TOKEN=$(cat /opt/data/jellyfin_token.txt)
JF_URL="https://jflix.jefe.al"
USER_ID="30174a9fab2b4664a1964a7a8e62aee3"

# Rechercher une série
curl -sk "$JF_URL/Users/$USER_ID/Items?ParentId=<LIB_ID>&SearchTerm=<titre>&IncludeItemTypes=Series&Recursive=true" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"

# Obtenir les épisodes d'une saison avec historique
curl -sk "$JF_URL/Users/$USER_ID/Items?ParentId=<SEASON_ID>&IncludeItemTypes=Episode&Fields=Name,IndexNumber,UserData,PlayedPercentage&SortBy=SortName" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"
```

Les bibliothèques Jellyfin sont dans `/Anime`, `/Films`, `/Séries`. Leurs IDs se trouvent via :
```bash
curl -sk "$JF_URL/Users/$USER_ID/Items?SearchTerm=Anime&IncludeItemTypes=CollectionFolder" \
  -H "X-Emby-Token: $JF_TOKEN"
```

- Le premier sync massif peut prendre 30+ minutes (452+ items historiques)
- Les `missing_peer` en grand nombre (10000+) sont normaux après un premier sync — les réduire à ~0 en faisant clear state + cache + resync
- `missing_ids` sans TMDB ID → chercher sur TMDB et laisser le metadata resolver faire
- Si `watch_start()` ne démarre pas, vérifier que les routes sont configurées dans la config
- Tailscale doit être down pour que le tunnel pangolin-cli fonctionne
- Pour trouver des TMDB IDs de séries récentes/obscures : chercher avec `metadata_search` d'abord, puis `web_search("site:themoviedb.org nom_série année")` si pas trouvé
- `auth_status()` doit retourner `authenticated: true` avant d'utiliser les autres outils
- **Sync endpoint** : le HTTP endpoint direct est `POST /api/run`, **pas** `/api/sync/run` (qui retourne 404)
- **AniList** : ne supporte pas le progress sync (pas de feature progress dans les paires vers AniList)
- **AniList anime_only** : toujours mettre `anime_only_sync: True` ET `use_anime_mapping: True` pour la paire AniList, sinon il va tenter de sync des séries non-anime qui échoueront
- **⚠️ AniList ne supporte PAS l'historique** : le health check CrossWatch retourne `features: {"watchlist": true, "ratings": true, "history": false, "playlists": false}`. L'historique (épisodes regardés) ne peut PAS être synced vers AniList. Seulement la watchlist et les ratings passent. Voir `references/provider-capabilities.md`.
- **⚠️ TMDB Sync (provider) ne supporte AUCUNE feature** : le health check retourne `features: {}` (vide). Ni watchlist, ni history, ni ratings ne peuvent être poussés vers TMDB via CrossWatch. TMDB n'est utilisé que comme source de metadata (affiches, descriptions, IDs). Si tu vois `"TMDB": {"watchlist": 40}` dans l'état CrossWatch, c'est 40 items qui ont un ID TMDB — PAS 40 items poussés vers le compte TMDB de l'utilisateur. Ces items existent dans l'état interne parce que CrossWatch les tracke via leur ID TMDB.
- **⚠️ Token OAuth expiré = échec silencieux** : quand le token OAuth d'un provider expire (AniList, Trakt, etc.), CrossWatch enregistre les items dans son état interne (ex: `anilist_pre: 0 → anilist_post: 40`) mais les appels API réels échouent. L'utilisateur voit 0 item sur son compte. Les logs SYNC montreront `feature:unsupported` pour les features qui ne fonctionnent pas, mais les tokens expirés ne sont pas toujours explicites. Pour diagnostiquer : faire un appel API direct vers le provider avec le token stocké dans la config. Pour réparer : reconnecter le provider via l'UI CrossWatch → Settings → [provider] → reconnecter OAuth.
- **Diagnostic provider capabilities** : utiliser `logs_dump(channel="SYNC", n=500)` et chercher les lignes `health` qui contiennent `"features"`. Chaque provider a ses propres features supportées. Exemple AniList : `"features":{"watchlist":true,"ratings":true,"history":false}`. TMDB : `"features":{}`. Voir aussi `api:totals` pour vérifier si des appels API write ont vraiment été faits (count > 0 dans `by_endpoint`).
- **⚠️ Panne DNS tunnel Pangolin** : le MCP server utilise `docker exec pangolin-cli curl` pour joindre `crosswatch.jefe.ovh`. Le DNS Olm (100.96.128.1) à l'intérieur du tunnel peut tomber. Symptômes : le MCP exit code 7 (connection refused), DNS time out. Workaround : forcer `CW_INTERNAL=true` dans la config MCP pour que le serveur fasse un appel HTTP direct plutôt que de passer par le tunnel. Si le problème persiste, redémarrer le container `pangolin-cli` avec `docker restart pangolin-cli` pour rétablir le DNS. Source : session du 5 juillet 2026.
- **⚠️ Env vars MCP** : les variables d'env doivent être passées via l'option `--env` de `hermes mcp add` (qui crée la section `env:` dans `config.yaml`). Ne pas les mettre dans `--args` (la config résultante met les `--env` dans `args:` et les vraies env vars ne sont jamais lues par le script). Voir le workflow de ré-enregistrement ci-dessus.
- **⚠️ Backfill speed** : l'écriture d'historique dans Jellyfin via l'API CrossWatch tourne à ~5 items/seconde (~20s par 100 items). Pour 3173 items, compter 10-15 minutes de apply phase. Le compteur dans `_phase.apply.done` peut rester à 0 pendant toute la phase snapshot — c'est normal, les logs SYNC montrent le vrai progrès. De même, `provider_counts` (JELLYFIN) reste à 0 tant que tout le sync n'est pas fini.
- **⚠️ Orchestrateur séquentiel** : le sync `orchestrator` traite toutes les paires une par une. Après backfill TRAKT→JELLYFIN, le sync continue avec JELLYFIN→TRAKT, JELLYFIN→SIMKL, etc. Les apply counters changent à chaque paire. **Ne pas relancer un sync tant que le précédent n'est pas fini.**
