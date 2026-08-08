---
name: qbittorrent
description: Client torrent léger avec WebUI. linuxserver.io, version 5.1.4. Configuration derrière VPN, port forwarding.
category: media
---

# qBittorrent — Guide de référence

> **Image :** `lscr.io/linuxserver/qbittorrent:5.1.4`  
> **Port WebUI interne :** `8080`  
> **Ports :** TCP `6881`, DHT `6881`, UDP `6881`

---

## 1. Docker Compose

```yaml
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:5.1.4
    container_name: qbittorrent
    network_mode: service:gluetun
    depends_on:
      gluetun:
        condition: service_healthy
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
      - WEBUI_PORT=8080
    volumes:
      - ./configs/qbittorrent:/config
      - "${COMMON_PATH}:/data"
    restart: unless-stopped
```

## 2. Variables d'environnement (linuxserver.io)

| Variable | Description |
|---|---|
| `PUID` | User ID |
| `PGID` | Group ID |
| `TZ` | Fuseau horaire |
| `WEBUI_PORT` | Port de l'interface web (défaut: 8080) |
| `UMASK` | Umask (optionnel) |
| `DOCKER_MODS` | Mods optionnels |

## 3. Ports

- **WebUI :** 8080 (interne). Derrière Gluetun, mapper ce port dans Gluetun.
- **Torrent :** Port à configurer dans le fichier qBittorrent.conf (`Session\Port`). Doit correspondre au port forwardé par le VPN.

## 4. Répertoires

- `/config` : Configuration qBittorrent
- `/data/torrents` : Torrents en cours
- `/data/media` : Fichiers complets (hardlinks)

## 5. Intégration

- **Radarr/Sonarr/Lidarr :** connexion via l'API WebUI
- **cross-seed :** accès au dossier `BT_backup` via `./configs/qbittorrent/qBittorrent/BT_backup:/torrent_files:ro`
