---
name: qbittorrent-mcp-server
title: MCP qBittorrent Natif — Read-Only 26 outils
description: Serveur MCP natif pour qBittorrent, read-only (private trackers). Login cookie automatique. 26 outils.
tags: [mcp, qbittorrent, fastmcp, python, torrent, read-only]
---

# MCP qBittorrent Natif — Read-Only

**⚠️ READ-ONLY uniquement. Private trackers — jefe gère les suppressions.**

## Connexion

- **URL** : `http://100.64.0.2:8090` (AX42 via Tailscale) — ❗ le port 8080 est refusé, le vrai service est sur 8090
- **Auth** : Login via API v2/auth/login (cookie SID)
- **Username** : `jefe`
- **Password** : stocké dans `~/.hermes/qb_password.txt` ou env `QB_PASSWORD`

## Fichier

`/root/.hermes/mcp/qbittorrent_server.py` — 26 outils

### App Info (4)
- `app_version` / `app_web_api_version`
- `app_preferences` / `app_build_info`

### Transfert (2)
- `transfer_info` — vitesses, ratios
- `transfer_speed_limits`

### Torrents (12)
- `torrents_info` — liste avec filtres (filter, category, tag, sort, limit)
- `torrent_properties` / `torrent_trackers` / `torrent_files`
- `torrent_piece_states` / `torrent_piece_hashes`
- `torrents_active` / `torrents_downloading`
- `torrents_completed` / `torrents_seeding`
- `torrents_paused` / `torrents_errored`

### Sync (1)
- `sync_maindata` — données complètes + incrémental

### Catégories & Tags (2)
- `list_categories` / `list_tags`

### Logs (2)
- `log_main` / `log_peers`

### RSS & Search (2)
- `rss_items` / `search_plugins`

### Catch-all (1)
- `api(path, query)` — tout endpoint read-only

## Enregistrement (commande correcte)

```bash
printf 'Y\nY\n' | hermes mcp add qbittorrent \
  --command "/usr/local/lib/hermes-agent/venv/bin/python3" \
  --env "QB_URL=http://100.64.0.2:8090" \
  --env "QB_USERNAME=jefe" \
  --args "/root/.hermes/mcp/qbittorrent_server.py" \
  --connect-timeout 30
```

> ❗ **NE PAS utiliser `hermes config set mcp_servers.qbittorrent.args ...`** — ça corrompt le format YAML (stocke la liste comme une string JSON au lieu d'une vraie liste YAML). Toujours utiliser `hermes mcp add` à la place.

## Pièges & Leçons

### 🚫 Port 8080 ≠ 8090
- qBittorrent tourne sur **8090** sur AX42, PAS 8080
- Si une config MCP existante a 8080, le login retourne la page HTML de login (pas "Ok.")
- Symptôme : `{'text': '<!DOCTYPE html>...', 'status': 200}` en retour d'appel

### 🔄 Gateway cache en mémoire
- Le Gateway **cache la config MCP au démarrage** — modifier `config.yaml` ne suffit pas
- Tuer le process MCP (`pkill -f qbittorrent_server`) ne résout rien : le Gateway re-spawne avec les vieux arguments
- **Solution 1** (recommandée) : restart le Gateway → `kill <gateway_pid>`
- **Solution 2** (si restart impossible) : modifier le script pour y hardcoder l'URL par défaut : `QB_URL = os.getenv("QB_URL") or "http://100.64.0.2:8090"`
- **Solution 3** : `hermes mcp remove qbittorrent` puis `hermes mcp add ...` (force re-registration)

### 🔑 Password
- Le serveur lit `QB_PASSWORD` depuis l'env var, OU depuis `~/.hermes/qb_password.txt`
- Le fichier de fallback est lu via `os.path.expanduser("~/.hermes/qb_password.txt")` — accessible depuis le process MCP
- Inclure `QB_PASSWORD` dans les `--env` si le fichier n'est pas trouvé

### 🧪 Test vs Réel
- `hermes mcp test qbittorrent` ✅ connexion + découverte des outils (ne teste PAS le login réel)
- Le login qBittorrent est testé seulement au premier appel d'outil via `_get_client()`
- Si le login échoue : vérifier URL, port, password dans cet ordre

### 🔒 Toujours read-only
- Les outils GET uniquement — aucune modification possible
- `_request()` ne supporte QUE les GET (private trackers)
- Le catch-all `api(path, query)` force aussi GET
