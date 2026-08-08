# Anime Watch History — Fallback Sources (quand CrossWatch est down)

Quand CrossWatch MCP est inaccessible (Pangolin tunnel cassé, MCP non chargé,
tools invisibles), trois sources directes permettent de récupérer l'historique
de visionnage des animes :

1. **CrossWatch API directe** via localhost (le service tourne sur le même host)
2. **Jellyfin API directe** (publique, pas derrière Pangolin)
3. **MyAnimeList API** (publique, read-only sans OAuth)

---

## 1. CrossWatch API directe (localhost:8787)

Le service CrossWatch écoute aussi sur `http://127.0.0.1:8787` depuis le
container Hermes. Ce endpoint contourne complètement le tunnel Pangolin.

**Cookie d'auth :** stocké dans la config MCP (`CW_COOKIE`) dans `config.yaml`.

```bash
CW="cw_auth=qtLymCxqhFylisH3i2Hr5sZRBzbrK3EX5jrW73QqZS0"
CW_URL="http://127.0.0.1:8787"
```

### Endpoints utiles

**Auth status :**
```bash
curl -sk "$CW_URL/api/app-auth/status" -H "Cookie: $CW"
```

**Provider counts (watchlist/history size par provider) :**
```bash
curl -sk "$CW_URL/api/sync/providers/counts" -H "Cookie: $CW"
```

**Analyzer state — chercher items par series_title, provider, feature :**
```bash
curl -sk "$CW_URL/api/analyzer/state?limit=200" -H "Cookie: $CW" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\"{i.get('provider','?'):10s} | S{i.get('season','?')}E{i.get('episode','?'):>3} | {i.get('feature','?'):10s} | {i.get('series_title','')} | key={i.get('key','')}\") for i in d.get('items',[]) if i.get('series_title') and 'classroom' in i['series_title'].lower()]"
```

**Activity history (scrobble events récents) :**
```bash
curl -sk "$CW_URL/api/activity/history?limit=100" -H "Cookie: $CW"
```

Chaque item a `timestamp` (unix epoch), `title`, `season`, `episode`, `source`, `target`, `event`.

**Exporter l'historique Trakt en CSV :**
```bash
# Format yamtrack (CSV avec season_number, episode_number, status, start_date, end_date, progressed_at)
curl -sk "$CW_URL/api/export/file?provider=TRAKT&kind=history&format=yamtrack" -H "Cookie: $CW"

# Format justwatch (CSV plus simple)
curl -sk "$CW_URL/api/export/file?provider=TRAKT&kind=history&format=justwatch" -H "Cookie: $CW"
```

Les exports sont paginés et peuvent être filtrés par `provider` (TRAKT, JELLYFIN,
CROSSWATCH, MDBLIST, SIMKL) et `kind` (history, watchlist, combined).

**OpenAPI spec complète :**
```bash
curl -sk "$CW_URL/openapi.json" -H "Cookie: $CW" | python3 -m json.tool
```

### API path mapping (MCP tool → HTTP endpoint)

| MCP tool | HTTP endpoint |
|---|---|
| `auth_status` | `GET /api/app-auth/status` |
| `get_config` | `GET /api/config` |
| `sync_providers` | `GET /api/sync/providers` |
| `provider_counts` | `GET /api/sync/providers/counts` |
| `list_pairs` | `GET /api/pairs` |
| `add_pair` | `POST /api/pairs` |
| `delete_pair` | `DELETE /api/pairs/{pair_id}` |
| `analyzer_state` | `GET /api/analyzer/state` |
| `analyzer_problems` | `GET /api/analyzer/problems` |
| `metadata_search` | `GET /api/metadata/search?q=...` |
| `logs_dump` | `GET /api/logs/dump?channel=TRAKT&n=50` |
| `health` | `GET /api/health` |
| `export_file` | `GET /api/export/file?provider=TRAKT&kind=history&format=yamtrack` |
| `activity_history` | `GET /api/activity/history` |
| `watch_status` | `GET /api/watcher/status` |
| `export_options` | `GET /api/export/options` |

---

## 2. Jellyfin API directe (public)

L'URL Jellyfin `https://jflix.jefe.al` **n'est pas** derrière Pangolin.

```bash
JF_TOKEN=$(cat /opt/data/jellyfin_token.txt)
JF_URL="https://jflix.jefe.al"
USER_ID="30174a9fab2b4664a1964a7a8e62aee3"  # Jefe
```

**Chercher une série :**
```bash
curl -sk "$JF_URL/Users/$USER_ID/Items?ParentId=<LIB_ID>&SearchTerm=<titre>&IncludeItemTypes=Series&Recursive=true&Fields=Name,Id" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"
```

**IDs des bibliothèques :**
- Anime : `0c41907140d802bb58430fed7e2cd79e`
- Séries : `d565273fd114d77bdf349a2896867069`
- Films : `db4c1708cbb5dd1676284a40f2950aba`

**Chercher dans toutes les bibliothèques (recursive, pas de ParentId) :**
```bash
curl -sk "$JF_URL/Users/$USER_ID/Items?SearchTerm=<titre>&IncludeItemTypes=Series&Fields=Name,Id,Path&Recursive=true&Limit=5" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"
```

⚠️ Sans `ParentId`, la recherche peut retourner les dossiers racine au lieu
des séries. Ajouter le `ParentId` de la bibliothèque pour une recherche précise.

**Obtenir les saisons :**
```bash
curl -sk "$JF_URL/Users/$USER_ID/Items?ParentId=<SERIES_ID>&IncludeItemTypes=Season&Fields=Name,Id,IndexNumber&SortBy=SortName" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"
```

**Obtenir les épisodes d'une saison avec dates de visionnage :**
```bash
curl -sk "$JF_URL/Users/$USER_ID/Items?ParentId=<SEASON_ID>&IncludeItemTypes=Episode&Fields=Name,IndexNumber,ParentIndexNumber,UserData,PlayedPercentage&SortBy=SortName" \
  -H "X-Emby-Token: $JF_TOKEN" -H "Accept: application/json"
```

Le champ `UserData.LastPlayedDate` donne la date précise du dernier visionnage.
`PlayCount` donne le nombre de fois que l'épisode a été regardé.
`UserData.PlayedPercentage` donne la progression (0 = pas commencé, 100 = fini).

**Limite :** Jellyfin n'a l'historique que pour les épisodes regardés SUR ce serveur.
Les saisons regardées ailleurs (Netflix, Crunchy, etc.) avant d'avoir Jellyfin n'apparaîtront pas.

---

## 3. MyAnimeList API (publique, read-only)

L'API MAL v2 avec client ID donne accès aux listes utilisateurs publiques
sans OAuth :

```python
import httpx
CLIENT_ID = "4c50b7151074f8c84520c91ed04010a1"
HEADERS = {"X-MAL-CLIENT-ID": CLIENT_ID}

# Liste de l'utilisateur
resp = httpx.get(
    "https://api.myanimelist.net/v2/users/jefe59/animelist",
    headers=HEADERS,
    params={
        "limit": 100,
        "offset": 0,  # paginer par 100
        "fields": "list_status{status,score,num_episodes_watched,start_date,finish_date}"
    },
    timeout=10
)
```

**Données disponibles par anime :**
- `status` : watching / completed / on_hold / dropped / plan_to_watch
- `num_episodes_watched` : total d'épisodes vus
- `score` : note donnée
- `start_date`, `finish_date` : dates globales (pas par épisode)

**Rechercher un anime par titre :**
```bash
curl -sk "https://api.myanimelist.net/v2/anime?q=Classroom+of+the+Elite&limit=5" \
  -H "X-MAL-CLIENT-ID: 4c50b7151074f8c84520c91ed04010a1" -H "Accept: application/json"
```

**MAL OAuth (non recommandé pour per-episode) :**
Pour faire du OAuth MAL, utiliser le flow PKCE. Mais même avec un token OAuth,
l'API MAL ne renvoie PAS de dates par épisode — seulement des agrégats par
série (start_date, finish_date, num_episodes_watched).

Le client ID `4c50b7151074f8c84520c91ed04010a1` est en mode "public" (read-only).
Pour OAuth, il faudrait créer une app sur https://myanimelist.net/apiconfig.
Le redirect URI OOB `urn:ietf:wg:oauth:2.0:oob` permet de récupérer le code
sur l'écran sans serveur de callback.

**IDs MAL des saisons de Youkoso Jitsuryoku Shijou Shugi no Kyoushitsu e :**
- S1 (2017, 12 eps) : `#35507`
- S2 (2022, 13 eps) : `#51096`
- S3 (2024, 13 eps) : `#51180`
- S4 : pas d'entrée MAL distincte (peut-être sous S3 sur certains trackers)
- S5 (pas encore diffusé) : `#64463`

**Username MAL de Jefe :** `jefe59`

**Limites de l'API MAL (même avec OAuth) :**
- Pas de dates épisode par épisode — seulement des agrégats par série
- `num_episodes_watched` donne le total, pas un timestamp
- Les `start_date` / `finish_date` sont des dates globales (ex: toute la S2 marquée "finished" le même jour)

---

## Stratégie : combiner les trois sources

| Source | Couvre | Limite |
|--------|--------|--------|
| CrossWatch localhost | Données Trakt/Jellyfin aggregées, export CSV | Pas de timestamp précis par épisode |
| Jellyfin API | Dates précises par épisode | Seulement si regardé sur ce serveur |
| MAL | Statut global + dates début/fin | Pas de dates par épisode |

→ **CrossWatch localhost** : exporter l'historique Trakt, compter les items, diagnostiquer
→ **Jellyfin** : dates précises des épisodes récents
→ **MAL** : statut global et dates des saisons plus anciennes

**Workflow de récupération complet :**

1. D'abord essayer CrossWatch localhost pour les exports
2. Puis Jellyfin pour les timestamps par épisode
3. Puis MAL pour le statut global des saisons non-Jellyfin

Exemple : Classroom of the Elite
- S4 → **Jellyfin** (dates par épisode du 09/07/2026)
- S1-S3 → **MAL** (marquées complètes en fév-mars 2025)
- Watchlist → **CrossWatch** (export Trakt au format CSV/yamtrack)
