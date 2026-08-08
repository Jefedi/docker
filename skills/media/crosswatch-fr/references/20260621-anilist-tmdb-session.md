# Session 2026-06-21 — Ajout AniList + TMDB dans CrossWatch

## Problème

L'utilisateur ajoute AniList et TMDB dans CrossWatch UI, puis demande de configurer les paires de sync. Le sync semble fonctionner (état CrossWatch montre 40 items sur AniList et TMDB), mais l'utilisateur ne voit rien sur les plateformes.

## Causes

1. **Token AniList expiré** : CrossWatch enregistre les items dans son état interne (`anilist_pre: 0 → anilist_post: 40`) MAIS les appels API GraphQL réels échouent avec "Invalid token". L'utilisateur voit 0 item sur AniList.
2. **TMDB ne supporte aucune feature** : `features: {}` dans le health check. Ni watchlist, ni history, ni ratings. TMDB est une base de données publique, pas un tracker personnel. Les 40 items "TMDB" dans l'état CrossWatch sont des items avec un ID TMDB, PAS des items poussés sur le compte TMDB de l'utilisateur.

## Actions

### 1. Ajout des paires (réussi)

```python
# AniList
add_pair(source="JELLYFIN", target="ANILIST", mode="two-way",
    features={
        "watchlist": {"enable": True, "add": True, "remove": True,
                      "use_anime_mapping": True, "anime_only_sync": True},
        "history": {"enable": True, "add": True, "remove": True}
    })
# → pair_e6fee8afb47e ✅

# TMDB
add_pair(source="JELLYFIN", target="TMDB", mode="two-way",
    features={
        "watchlist": {"enable": True, "add": True, "remove": True,
                      "use_anime_mapping": False, "anime_only_sync": False},
        "history": {"enable": True, "add": True, "remove": True}
    })
# → pair_f733003e22e8 ✅
```

### 2. Sync endpoint correct

```
POST /api/run  → ✅ OK (body: {"label": "...", "run_id": "..."})
POST /api/sync/run → ❌ 404 Not Found
```

### 3. Diagnostic — Pourquoi l'utilisateur voit rien

```python
# Voir les health checks des providers
logs_dump(channel="SYNC", n=500)
# Chercher les lignes "health" avec le champ "features"

# AniList: {"features": {"watchlist": true, "ratings": true, "history": false, "playlists": false}}
# TMDB:    {"features": {}}  → vide = rien supporté

# Vérifier si des API writes ont eu lieu
# api:totals → ANILIST ne montre que health:graphql (1 hit), pas de writes
```

### 4. Test du token AniList direct

```
POST https://graphql.anilist.co
Authorization: Bearer <token>
Query: { MediaListCollection(userId: 7241861, type: ANIME) { lists { name entries { media { id title { romaji } } } } } }

Réponse valide: {"data": {"MediaListCollection": {"lists": [...]}}}
Réponse expiré: {"data": null, "errors": [{"message": "Invalid token"}]}
```

### 5. Réparation

L'utilisateur reconnecte AniList via l'UI CrossWatch (Settings → AniList → re-auth OAuth).
Le token est rafraîchi → health check passe (GraphQL 200).
Un sync ultérieur confirme les 40 items sur AniList.

### 6. Watcher temps réel

Les routes watcher sont configurées dans l'UI CrossWatch (Settings → Scrobble → Watcher).
L'API config est READ-ONLY : `GET /api/config` ✅, `PUT /api/config` ❌ Method Not Allowed.
Ajouter une route watcher pour AniList nécessite l'UI, pas l'API.
Les paires de sync (`add_pair`) et les routes watcher sont INDÉPENDANTES — une paire ne crée pas automatiquement une route watcher.

## Récapitulatif final

| Paire | Features supportées | Fonctionne ? |
|-------|-------------------|-------------|
| JELLYFIN ↔ ANILIST | watchlist ✅, history ❌, ratings ✅ | ✅ watchlist (après re-auth) |
| JELLYFIN ↔ TMDB | Aucune ❌ | ❌ pas de write possible |
| JELLYFIN ↔ TRAKT | watchlist ✅, history ✅ | ✅ |
| JELLYFIN ↔ SIMKL | watchlist ✅, history ✅ | ✅ |
| JELLYFIN ↔ MDBLIST | watchlist ✅, history ✅ | ✅ |
