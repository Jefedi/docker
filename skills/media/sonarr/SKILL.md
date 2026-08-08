---
name: sonarr
description: Gestionnaire de séries TV (PVR). Organisation, téléchargement, renommage via Usenet et torrents.
category: media
---

# Sonarr — Guide de référence

> **Image :** `lscr.io/linuxserver/sonarr:latest`  
> **Port :** `8989`  
> **Tags :** `latest` (stable), `develop` (dev)  
> **Wiki :** https://wiki.servarr.com/en/sonarr  
> **Site :** https://sonarr.tv

---

## 1. Docker Compose

```yaml
  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - ./configs/sonarr:/config
      - "${COMMON_PATH}:/data"
    restart: unless-stopped
```

## 2. Variables d'environnement avancées (Servarr)

Les *arr supportent les variables d'environnement pour surcharger `config.xml`. Format : `SONARR__CONFIGNAMESPACE__CONFIGITEM`

### Auth
| Variable | Description |
|---|---|
| `SONARR__AUTH__APIKEY` | Forcer une API key |
| `SONARR__AUTH__ENABLED` | `true` / `false` |
| `SONARR__AUTH__METHOD` | `Basic`, `Forms`, `External` |
| `SONARR__AUTH__REQUIRED` | `Disabled`, `Enabled`, `LanNetworks` |

### Server
| Variable | Description |
|---|---|
| `SONARR__SERVER__URLBASE` | Sous-chemin (ex: `/sonarr`) |
| `SONARR__SERVER__BINDADDRESS` | IP d'écoute (`*` = toutes) |
| `SONARR__SERVER__PORT` | Port (défaut: 8989) |
| `SONARR__SERVER__ENABLESSL` | `true` / `false` |
| `SONARR__SERVER__SSLPORT` | Port SSL |

### PostgreSQL (optionnel, SQLite par défaut)
| Variable | Description |
|---|---|
| `SONARR__POSTGRES__HOST` | Hôte PostgreSQL |
| `SONARR__POSTGRES__PORT` | Port (défaut: 5432) |
| `SONARR__POSTGRES__USER` | Utilisateur |
| `SONARR__POSTGRES__PASSWORD` | Mot de passe |
| `SONARR__POSTGRES__MAINDB` | Nom BDD principale |

### Logs
| Variable | Description |
|---|---|
| `SONARR__LOG__LEVEL` | `info`, `debug`, `trace`, `warn`, `error` |
| `SONARR__LOG__DBENABLED` | Log les requêtes SQL |
| `SONARR__LOG__SYSLOGSERVER` | Serveur syslog distant |

## 3. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 8989 à mapper dans Gluetun

## 4. Chemins recommandés (hardlinks)

```
/data/torrents  → downloads
/data/media/tv  → library
```

Les paths doivent être **identiques** entre tous les conteneurs pour permettre les hardlinks. Voir https://wiki.servarr.com/docker-guide#consistent-and-well-planned-paths

## 5. Intégrations

- **Indexers :** Prowlarr (synchronisation native)
- **Download clients :** qBittorrent (via API)
- **Custom Formats :** Profilarr
- **Sous-titres :** Bazarr (connexion API)
- **Nettoyage :** Janitorr
