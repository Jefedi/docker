---
name: sonarr-mcp-server
title: MCP Sonarr Natif — Serveur FastMCP 100% API v3
description: Serveur MCP natif pour Sonarr, construit avec FastMCP, connexion directe via Tailscale. Couvre 47 outils + 1 catch-all pour 100% de l'API.
tags: [mcp, sonarr, fastmcp, python, tailscale, homelab]
---

# MCP Sonarr Natif — Serveur FastMCP

Serveur MCP natif remplaçant l'ancien MCP basé sur un workflow n8n. Connexion directe à Sonarr via Tailscale/Headscale (pas de wrapper n8n).

## Prérequis

```bash
pip install fastmcp httpx
```

Installer dans le venv Hermes :
```bash
/usr/local/lib/hermes-agent/venv/bin/pip install fastmcp httpx
```

## Connexion

- **URL Sonarr** : `http://100.64.0.2:8989/api/v3` (via Tailscale)
- **Auth** : Header `X-Api-Key`
- **Clé API** stockée dans `~/.hermes/sonarr_api_key.txt`

## Fichier du serveur

Chemin : `/root/.hermes/mcp/sonarr_server.py`

Le serveur expose **47 outils** couvrant tous les endpoints Sonarr v3 :

### Système
- `system_status` — Version, OS, DB, auth

### Séries (9 outils)
- `list_series` — Filtrer par TVDB ID optionnel
- `get_series` — Par Sonarr series ID
- `lookup_series` — Recherche TVDB par nom
- `add_series` — Ajouter avec tvdbId, qualityProfileId, rootFolderPath
- `update_series` — Modifier monitored, qualityProfileId, etc.
- `delete_series` — Supprimer (+ fichiers optionnel)
- `search_series` — Lancer une recherche
- `refresh_series` — Rafraîchir métadonnées TVDB

### Profils Qualité (5 outils)
- `list_quality_profiles` — Lister avec qualités autorisées
- `get_quality_profile` — Par ID
- `get_quality_profile_schema` — Structure par défaut
- `create_quality_profile` — Nouveau profil (structure clonée de "Any")
- `update_quality_profile` — Nom, cutoff, upgrade, language
- `delete_quality_profile` — Supprimer

### Épisodes (3 outils)
- `list_episodes` — Par seriesId + seasonNumber optionnel
- `get_episode` — Par ID
- `update_episode` — Toggle monitored

### Fichiers (2 outils)
- `list_episode_files` — Qualité, taille, chemin, codecs
- `get_episode_file` — Par ID

### Queue & Historique (4 outils)
- `list_queue` — Téléchargements actifs/en attente
- `list_history` — Historique des imports/grabs
- `list_wanted_missing` — Épisodes manquants
- `list_wanted_cutoff_unmet` — Sous le cutoff qualité

### Calendrier (1 outil)
- `get_calendar` — Épisodes à venir

### Commandes (2 outils)
- `list_commands` — Commandes récentes/running
- `send_command` — RssSync, RefreshSeries, EpisodeSearch, etc.

### Configuration (6 outils)
- `list_root_folders`
- `list_language_profiles`
- `list_tags` / `create_tag` / `get_tag`
- `list_indexers` / `get_indexer` / `test_indexer`
- `list_download_clients`
- `list_notifications`
- `list_custom_formats`
- `get_media_management_config`
- `get_naming_config` / `get_naming_examples`

### Releases (1 outil)
- `search_releases` — Recherche manuelle par episodeId

### Santé & Infos (3 outils)
- `get_health` — Checks de santé
- `get_disk_space` — Espace disque
- `get_logs` — Logs système
- `get_update_info` — MAJ disponibles

### Catch-all (1 outil)
- `api(method, path, query, body)` — Tout endpoint non couvert

## Enregistrement dans Hermes

```bash
printf 'Y\nY\n' | hermes mcp add sonarr \
  --command "/usr/local/lib/hermes-agent/venv/bin/python3" \
  --args "/root/.hermes/mcp/sonarr_server.py" \
  --env "SONARR_URL=http://100.64.0.2:8989" \
  --connect-timeout 30
```

### Suppression

```bash
hermes mcp remove sonarr
```

## Profil Qualité Recommandé

Pour du **Direct Play instantané** (1080p x264, pas de transcoding) :

```
Name: "1080p x264 Direct Play"
Autorisé : WEB 1080p, WEB 720p, Bluray-1080p, Bluray-720p
Bloqué : x265 (-10000), LQ (-10000), 4K, SD
Favorisé : MULTI (+500)
Cutoff : WEB 1080p
```

## Références

- `references/qualityprofile-creation.md` — Clone-Any-profile workaround for creating quality profiles via the API (bypasses `AllQualitiesValidator`).
- `references/episode-replacement.md` — Remplacer des épisodes corrompus ou de mauvaise qualité : delete file → re-monitor → SeasonSearch.

## Pièges Connus

- Le validateur Sonarr `AllQualitiesValidator` rejette les POST si des qualités obsolètes (IDs 23-31) sont incluses. Toujours utiliser la structure actuelle du profil "Any".
- La clé API est lue depuis `~/.hermes/sonarr_api_key.txt` comme fallback si `SONARR_API_KEY` n'est pas dans l'env.
- `fastmcp inspect` ne supporte pas les `**kwargs` — utiliser des paramètres explicites typés.
- Les outils MCP sont découverts au démarrage d'Hermes seulement — nécessite une nouvelle session.
- **Pas de profil par défaut serveur :** Le profil qualité "par défaut" est stocké en localStorage navigateur (Settings → UI), pas via l'API. Aucun endpoint ne permet de le définir. Passez `qualityProfileId` explicitement dans chaque `add_series`.
