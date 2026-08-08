---
name: radarr
description: Gestionnaire de films (PVR). Organisation, téléchargement, renommage via Usenet et torrents.
category: media
---

# Radarr — Guide de référence

> **Image :** `lscr.io/linuxserver/radarr:latest`  
> **Port :** `7878`  
> **Tags :** `latest` (stable), `develop`, `nightly`  
> **Wiki :** https://wiki.servarr.com/en/radarr  
> **Site :** https://radarr.video

---

## 1. Docker Compose

```yaml
  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - ./configs/radarr:/config
      - "${COMMON_PATH}:/data"
    restart: unless-stopped
```

## 2. Variables d'environnement avancées (Servarr)

Format : `RADARR__CONFIGNAMESPACE__CONFIGITEM`

### Auth
| Variable | Description |
|---|---|
| `RADARR__AUTH__APIKEY` | Forcer une API key |
| `RADARR__AUTH__ENABLED` | `true` / `false` |
| `RADARR__AUTH__METHOD` | `Basic`, `Forms`, `External` |
| `RADARR__AUTH__REQUIRED` | `Disabled`, `Enabled`, `LanNetworks` |

### Server
| Variable | Description |
|---|---|
| `RADARR__SERVER__URLBASE` | Sous-chemin (ex: `/radarr`) |
| `RADARR__SERVER__BINDADDRESS` | IP d'écoute |
| `RADARR__SERVER__PORT` | Port (défaut: 7878) |
| `RADARR__SERVER__ENABLESSL` | `true` / `false` |

### PostgreSQL (optionnel)
| Variable | Description |
|---|---|
| `RADARR__POSTGRES__HOST` | Hôte PostgreSQL |
| `RADARR__POSTGRES__PORT` | Port |
| `RADARR__POSTGRES__USER` | Utilisateur |
| `RADARR__POSTGRES__PASSWORD` | Mot de passe |
| `RADARR__POSTGRES__MAINDB` | Nom BDD |

### Logs
| Variable | Description |
|---|---|
| `RADARR__LOG__LEVEL` | `info`, `debug`, `trace`, `warn`, `error` |
| `RADARR__LOG__DBENABLED` | Log SQL |

## 3. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 7878 à mapper dans Gluetun

## 4. Chemins recommandés (hardlinks)

```
/data/torrents  → downloads
/data/media/movies  → library
```

## 5. Intégrations

- **Indexers :** Prowlarr
- **Download clients :** qBittorrent
- **Custom Formats :** Profilarr
- **Sous-titres :** Bazarr
- **Nettoyage :** Janitorr
