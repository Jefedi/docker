---
name: prowlarr
description: Gestionnaire d'indexers. Miroir auto vers Sonarr/Radarr/Lidarr. Torznab, Newznab, Cardigann.
category: media
---

# Prowlarr — Guide de référence

> **Image :** `lscr.io/linuxserver/prowlarr:latest`  
> **Port :** `9696`  
> **Wiki :** https://wiki.servarr.com/en/prowlarr  
> **Site :** https://prowlarr.com

---

## 1. Docker Compose

```yaml
  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    container_name: prowlarr
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - ./configs/prowlarr:/config
    restart: unless-stopped
```

## 2. Variables d'environnement avancées (Servarr)

Format : `PROWLARR__CONFIGNAMESPACE__CONFIGITEM`

### Auth
| Variable | Description |
|---|---|
| `PROWLARR__AUTH__APIKEY` | Forcer une API key |
| `PROWLARR__AUTH__ENABLED` | `true` / `false` |
| `PROWLARR__AUTH__METHOD` | `Basic`, `Forms`, `External` |
| `PROWLARR__AUTH__REQUIRED` | `Disabled`, `Enabled`, `LanNetworks` |

### Server
| Variable | Description |
|---|---|
| `PROWLARR__SERVER__URLBASE` | Sous-chemin |
| `PROWLARR__SERVER__BINDADDRESS` | IP d'écoute |
| `PROWLARR__SERVER__PORT` | Port (défaut: 9696) |

### PostgreSQL (optionnel)
| Variable | Description |
|---|---|
| `PROWLARR__POSTGRES__HOST` | Hôte PostgreSQL |
| `PROWLARR__POSTGRES__PORT` | Port |
| `PROWLARR__POSTGRES__USER` | Utilisateur |
| `PROWLARR__POSTGRES__PASSWORD` | Mot de passe |
| `PROWLARR__POSTGRES__MAINDB` | Nom BDD |

### Logs
| Variable | Description |
|---|---|
| `PROWLARR__LOG__LEVEL` | `info`, `debug`, `trace`, `warn`, `error` |

## 3. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 9696 à mapper dans Gluetun

## 4. Fonctionnement

Prowlarr est l'unique point d'entrée pour les indexers. Il synchronise automatiquement les indexers vers :
- **Sonarr** (séries)
- **Radarr** (films)
- **Lidarr** (musique)

Les indexers sont configurés une seule fois puis propagés.

### Types d'indexers supportés
- **Torznab** (torrents)
- **Newznab** (usenet)
- **Cardigann** (YAML definitions pour indexers privés)

## 5. Intégrations

- **Apps synchronisées :** Sonarr, Radarr, Lidarr
- **Indexers :** Jackett, Torznab, Newznab
- **FlareSolverr :** configuré comme proxy pour indexers Cloudflare
