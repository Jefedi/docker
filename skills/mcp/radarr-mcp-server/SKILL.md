---
name: radarr-mcp-server
title: MCP Radarr Natif — Serveur FastMCP 100% API v3
description: Serveur MCP natif pour Radarr, construit avec FastMCP, connexion directe via Tailscale. Couvre 53 outils + 1 catch-all pour 100% de l'API.
tags: [mcp, radarr, fastmcp, python, tailscale, homelab]
---

# MCP Radarr Natif — Serveur FastMCP

Serveur MCP natif remplaçant l'ancien MCP basé sur n8n. Connexion directe à Radarr via Tailscale/Headscale.

## Prérequis

```bash
pip install fastmcp httpx
```

## Connexion

- **URL Radarr** : `http://100.64.0.2:7878/api/v3` (via Tailscale)
- **Auth** : Header `X-Api-Key`
- **Clé API** stockée dans `~/.hermes/radarr_api_key.txt`

## Fichier du serveur

Chemin : `/root/.hermes/mcp/radarr_server.py`

53 outils couvrant tous les endpoints Radarr v3 :

### Système
- `system_status`

### Films (11 outils)
- `list_movies` / `get_movie` / `lookup_movie` / `lookup_movie_imdb` / `lookup_movie_tmdb`
- `add_movie` / `update_movie` / `delete_movie` / `search_movie` / `refresh_movie`
- `list_movie_files` / `get_movie_file`

### Profils Qualité (6 outils)
- `list_quality_profiles` / `get_quality_profile` / `get_quality_profile_schema`
- `create_quality_profile` / `update_quality_profile` / `delete_quality_profile`

### Collections (3 outils)
- `list_collections` / `get_collection` / `update_collection`

### Queue & Historique (5 outils)
- `list_queue` / `list_history` / `list_wanted_missing` / `list_wanted_cutoff_unmet` / `get_calendar`

### Commandes (2 outils)
- `list_commands` / `send_command`

### Config (10 outils)
- `list_root_folders` / `list_tags` / `get_tag` / `create_tag`
- `list_indexers` / `get_indexer` / `test_indexer`
- `list_download_clients` / `list_notifications`
- `list_custom_formats` / `list_remote_path_mappings` / `list_metadata_profiles`
- `get_host_config` / `get_naming_config` / `get_naming_examples` / `get_media_management_config` / `get_ui_config`

### Santé & Infos (4 outils)
- `get_health` / `get_disk_space` / `get_logs` / `get_update_info`

### Autres (3 outils)
- `search_releases` / `list_blocklist`

### Catch-all (1 outil)
- `api(method, path, query, body)`

## Enregistrement

```bash
printf 'Y\nY\n' | hermes mcp add radarr \
  --command "/usr/local/lib/hermes-agent/venv/bin/python3" \
  --args "/root/.hermes/mcp/radarr_server.py" \
  --env "RADARR_URL=http://100.64.0.2:7878" \
  --connect-timeout 30
```

## Suppression

```bash
hermes mcp remove radarr
```

## Pièges

- La clé API est lue depuis `~/.hermes/radarr_api_key.txt` si `RADARR_API_KEY` n'est pas dans l'env
- Les outils sont disponibles dans la session suivante seulement
- **Pas de profil par défaut serveur :** Le profil qualité choisi dans Settings → UI est stocké en localStorage navigateur, pas via l'API. `config/ui` n'a pas de champ `qualityProfileId`. Pour utiliser un profil précis, passez `qualityProfileId` explicitement dans chaque `add_movie`.
