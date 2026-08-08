---
name: lidarr
description: Gestionnaire de musique (PVR). Organisation, téléchargement, renommage de musique.
category: media
---

# Lidarr — Guide de référence

> **Image :** `lscr.io/linuxserver/lidarr:latest`  
> **Port :** `8686`  
> **Wiki :** https://wiki.servarr.com/en/lidarr  
> **Site :** https://lidarr.audio  
> **Base de données musique :** MusicBrainz

---

## 1. Docker Compose

```yaml
  lidarr:
    image: lscr.io/linuxserver/lidarr:latest
    container_name: lidarr
    network_mode: service:gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
    volumes:
      - ./configs/lidarr/config:/config
      - "${COMMON_PATH}:/data"
    restart: unless-stopped
```

## 2. Variables d'environnement avancées (Servarr)

Format : `LIDARR__CONFIGNAMESPACE__CONFIGITEM`

### Auth
| Variable | Description |
|---|---|
| `LIDARR__AUTH__APIKEY` | Forcer une API key |
| `LIDARR__AUTH__ENABLED` | `true` / `false` |
| `LIDARR__AUTH__METHOD` | `Basic`, `Forms`, `External` |
| `LIDARR__AUTH__REQUIRED` | `Disabled`, `Enabled`, `LanNetworks` |

### Server
| Variable | Description |
|---|---|
| `LIDARR__SERVER__URLBASE` | Sous-chemin |
| `LIDARR__SERVER__PORT` | Port (défaut: 8686) |

### PostgreSQL (optionnel)
| Variable | Description |
|---|---|
| `LIDARR__POSTGRES__HOST` | Hôte PostgreSQL |
| `LIDARR__POSTGRES__USER` | Utilisateur |
| `LIDARR__POSTGRES__PASSWORD` | Mot de passe |
| `LIDARR__POSTGRES__MAINDB` | Nom BDD |

### Logs
| Variable | Description |
|---|---|
| `LIDARR__LOG__LEVEL` | `info`, `debug`, `trace`, `warn`, `error` |

## 3. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 8686 à mapper dans Gluetun

## 4. Spécificités Lidarr

- Basé sur **MusicBrainz** pour les métadonnées artistes/albums
- Organisation par artiste → album → pistes
- Chemins : `./configs/lidarr/config:/config` (avec sous-dossier `config`)
- TZ : `Etc/UTC` recommandé

## 5. Intégrations

- **Indexers :** Prowlarr
- **Download clients :** qBittorrent
