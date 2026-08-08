# CrossWatch Provider Capabilities

Matrice des features supportées par chaque provider CrossWatch.
Basée sur le health check (`"features": {...}`) retourné par chaque provider lors du sync.

## Feature Matrix

| Provider | Watchlist | History | Ratings | Progress | Playlists |
|----------|-----------|---------|---------|----------|-----------|
| TRAKT    | ✅ | ✅ | ✅ | ❌ | ❌ |
| SIMKL    | ✅ | ✅ | ✅ | ❌ | ❌ |
| MDBLIST  | ✅ | ✅ | ✅ | ❌ | ❌ |
| **ANILIST** | ✅ | **❌** | ✅ | ❌ | ❌ |
| **TMDB** | **❌** | **❌** | **❌** | ❌ | ❌ |
| CROSSWATCH | ✅ | ✅ | ❌ | ✅ | ❌ |
| JELLYFIN | ✅ | ✅ | ✅ | ✅ | ❌ |
| PLEX     | ✅ | ✅ | ✅ | ✅ | ❌ |
| EMBY     | ✅ | ✅ | ✅ | ✅ | ❌ |
| PUBLICMETADB | ❌ | ❌ | ❌ | ❌ | ❌ |

## Détails importants

### AniList
- Watchlist items bien poussés (avec anime_only_sync + use_anime_mapping)
- History **NON supporté** → les épisodes regardés ne seront jamais marqués sur AniList
- Ratings supportés
- Utilise le système de listes AniList (Planning/Current/Completed/Dropped/Paused)
- Token OAuth2 peut expirer → re-auth via UI CrossWatch Settings

### TMDB (Sync)
- NE supporte AUCUNE feature d'écriture utilisateur
- TMDB n'est PAS un tracker personnel — c'est une base de données publique
- Le provider `TMDB` dans CrossWatch sert uniquement pour la METADATA (affiches, descriptions)
- Si l'état CrossWatch montre `TMDB: 40 items`, c'est 40 items qui existent avec un ID TMDB, PAS 40 items poussés chez TMDB
- TMDB nécessiterait une session OAuth utilisateur pour écrire des listes/watchlists, non implémenté dans CrossWatch actuellement

### Trakt / SIMKL / MDBList
- Support complet de watchlist + history
- Pas de progress (sauf via le watcher temps réel pour Trakt)

## Diagnostiquer un provider qui ne sync pas

1. Vérifier les logs SYNC : `logs_dump(channel="SYNC", n=500)`
2. Chercher `"provider":"ANILIST"` (ou autre) dans les lignes `health`
3. Lire le champ `"features": {...}` pour voir ce qui est supporté
4. Vérifier les `"api:totals"` → compter les appels API write réels
5. Si le token est expiré, l'appel API direct retourne "Invalid token"
   - AniList GraphQL: `POST https://graphql.anilist.co` avec `Authorization: Bearer <token>`
- Le sync endpoint correct est `POST /api/run` (PAS `/api/sync/run`)
- Si le nombre d'items AniList/TMDB dans l'état CrossWatch ne correspond pas à ce que l'utilisateur voit sur le site, le token est probablement expiré → voir `references/anilist-debug.md`
