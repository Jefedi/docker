---
name: dispatcharr
description: Dispatcharr - IPTV stream manager, EPG proxy et HDHomeRun emulation. Docker, configuration, intégration Plex/Jellyfin/Emby
category: media
---

# Dispatcharr — Guide de référence

> **Site officiel :** https://dispatcharr.github.io/Dispatcharr-Docs/  
> **GitHub :** https://github.com/Dispatcharr/Dispatcharr  
> **Image :** `ghcr.io/dispatcharr/dispatcharr:latest`  
> **Port :** `9191`  
> **Licence :** GNU AGPL v3.0

Dispatcharr est un gestionnaire de flux IPTV / proxy de streaming. Il permet d'importer des playlists M3U, de gérer des guides EPG, de proxyfier des flux, et de les exposer via HDHomeRun, M3U, XMLTV ou Xtream Codes API vers Plex, Jellyfin, Emby, ChannelsDVR.

---

## 1. Déploiement Docker

### 1.1 Mode AIO (All-In-One) — Recommandé

Redis et PostgreSQL sont embarqués dans le conteneur. Simple, idéal pour la plupart des usages.

```yaml
services:
  dispatcharr:
    image: ghcr.io/dispatcharr/dispatcharr:latest
    container_name: dispatcharr
    restart: unless-stopped
    ports:
      - 9191:9191
    volumes:
      - dispatcharr_data:/data
    environment:
      - DISPATCHARR_ENV=aio
      - DISPATCHARR_LOG_LEVEL=info
      # Optionnel : legacy CPU (circa 2009)
      # - USE_LEGACY_NUMPY=true
      # Priorité process (lower = higher priority, -20 à 19)
      # - UWSGI_NICE_LEVEL=-5   # Streaming (défaut: 0)
      # - CELERY_NICE_LEVEL=5   # Tâches fond (défaut: 5)
    # Si UWSGI_NICE_LEVEL < 0 :
    # cap_add:
    #   - SYS_NICE
    # Accélération GPU Intel/AMD (VA-API) :
    # devices:
    #   - /dev/dri:/dev/dri
    # NVIDIA (require NVIDIA Container Toolkit) :
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

volumes:
  dispatcharr_data:
```

### 1.2 Mode AIO derrière Gluetun (VPN)

Pour du géo-déblocage, Dispatcharr peut être placé derrière Gluetun (partage de namespace réseau).

**⚠️ Attention :** En AIO, Redis/Postgres utilisent `localhost` interne. Avec `network_mode: service:gluetun`, le namespace réseau est partagé, la communication interne fonctionne car les processus partagent le même loopback.

```yaml
  dispatcharr:
    image: ghcr.io/dispatcharr/dispatcharr:latest
    container_name: dispatcharr
    network_mode: service:gluetun
    environment:
      - DISPATCHARR_ENV=aio
      - DISPATCHARR_LOG_LEVEL=info
    volumes:
      - ./configs/dispatcharr:/data
    restart: unless-stopped
```

**Ajouter dans Gluetun `ports` :**
```yaml
      - "127.0.0.1:9191:9191"
      - "100.64.0.2:9191:9191"
```

### 1.3 Mode Modulaire (web + celery + postgres + redis)

Quand on veut plus de contrôle (TLS, DB externe, scaling séparé).

```yaml
services:
  web:
    image: ghcr.io/dispatcharr/dispatcharr:latest
    container_name: dispatcharr_web
    restart: unless-stopped
    ports:
      - 9191:9191
    volumes:
      - ./data:/data
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      - DISPATCHARR_ENV=modular
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=dispatcharr
      - POSTGRES_USER=dispatch
      - POSTGRES_PASSWORD=secret
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DISPATCHARR_LOG_LEVEL=info

  celery:
    image: ghcr.io/dispatcharr/dispatcharr:latest
    container_name: dispatcharr_celery
    restart: unless-stopped
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
      web: { condition: service_started }
    volumes:
      - ./data:/data
    entrypoint: ["/app/docker/entrypoint.celery.sh"]
    environment:
      - DISPATCHARR_ENV=modular
      - DISPATCHARR_PORT=9191
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=dispatcharr
      - POSTGRES_USER=dispatch
      - POSTGRES_PASSWORD=secret
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DISPATCHARR_LOG_LEVEL=info
      - DJANGO_SETTINGS_MODULE=dispatcharr.settings
      - PYTHONUNBUFFERED=1

  db:
    image: postgres:17
    container_name: dispatcharr_db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=dispatcharr
      - POSTGRES_USER=dispatch
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dispatch -d dispatcharr"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:latest
    container_name: dispatcharr_redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

---

## 2. Variables d'environnement

| Variable | Description |
|---|---|
| `DISPATCHARR_ENV` | `aio` (défaut) ou `modular` |
| `DISPATCHARR_LOG_LEVEL` | `info`, `debug`, `warning`, `error` |
| `REDIS_HOST` | Hôte Redis (défaut: `localhost` en AIO) |
| `REDIS_PORT` | Port Redis (défaut: `6379`) |
| `CELERY_BROKER_URL` | URL broker Celery |
| `USE_LEGACY_NUMPY` | `true` pour CPU anciens |
| `UWSGI_NICE_LEVEL` | Priorité uWSGI/FFmpeg (-20 à 19, défaut: 0) |
| `CELERY_NICE_LEVEL` | Priorité Celery/EPG (-20 à 19, défaut: 5) |
| `POSTGRES_HOST/PORT/DB/USER/PASSWORD` | PostgreSQL (mode modular) |
| `DISPATCHARR_PORT` | Port pour communication Celery → web (modular) |
| `DJANGO_SETTINGS_MODULE` | `dispatcharr.settings` (modular) |
| `PYTHONUNBUFFERED` | `1` (modular) |

### TLS (mode modular uniquement)

#### Redis
| Variable | Description |
|---|---|
| `REDIS_SSL=true` | Active TLS |
| `REDIS_SSL_VERIFY=true/false` | Vérification serveur |
| `REDIS_SSL_CA_CERT` | Chemin CA cert |
| `REDIS_SSL_CERT` | Client cert (mTLS) |
| `REDIS_SSL_KEY` | Client key (mTLS) |

#### PostgreSQL
| Variable | Description |
|---|---|
| `POSTGRES_SSL=true` | Active TLS |
| `POSTGRES_SSL_MODE` | `verify-full`, `verify-ca`, `require` |
| `POSTGRES_SSL_CA_CERT` | Chemin CA cert |
| `POSTGRES_SSL_CERT` | Client cert (mTLS) |
| `POSTGRES_SSL_KEY` | Client key (mTLS) |

---

## 3. Accélération matérielle

### Intel/AMD (VA-API)
```yaml
devices:
  - /dev/dri:/dev/dri
```
Stream profile custom param : `-user_agent {userAgent} -hwaccel vaapi -hwaccel_output_format vaapi -hwaccel_device /dev/dri/renderD128 -i {streamUrl} -c:a aac -c:v h264_vaapi -f mpegts pipe:1`

### Intel QSV
Param : `-hwaccel qsv -user_agent {userAgent} -i {streamUrl} -c:v h264_qsv -c:a aac -f mpegts pipe:1`

### NVIDIA
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```
Param : `-user_agent {userAgent} -hwaccel cuda -i {streamUrl} -c:v h264_nvenc -c:a copy -f mpegts pipe:1`

---

## 4. Configuration reverse proxy

### 4.1 Pangolin

Créer une ressource dans Pangolin, IP locale du conteneur, port 9191.

**Bypass rules SSO (Path, Bypass Auth) :**
- `/player_api.php/*`
- `/get.php/*`
- `/xmltv.php/*`
- `/*/*/*.ts`
- `/proxy/ts/stream/*`
- `/proxy/vod/episode/*`
- `/proxy/vod/movie/*`
- `/api/channels/logos/*/cache/`
- `/live/*/*`
- `/movie/*/*`
- `/series/*/*`
- Optionnel (HDHR/M3U/EPG) : `/hdhr/*`, `/output/m3u/*`, `/output/epg/*`

### 4.2 Nginx (streams publics, WebUI privé)

```
location ~ ^(/proxy/(vod|ts)/(stream|movie|episode)/.*|/player_api\.php|/xmltv\.php|...) {
    allow all;
    proxy_pass http://dispatcharr:9191;
    ...
}
location / {
    allow 10.0.0.0/22;
    deny all;
    proxy_pass http://dispatcharr:9191;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    ...
}
```

---

## 5. Fonctionnalités clés

### Stream Profiles disponibles

| Profile | Proxy | Fallback | Stats | Ressources |
|---|---|---|---|---|
| ffmpeg | ✅ | ✅ | ✅ | Faible |
| Proxy | ✅ | ✅ | ✅ | Très faible |
| Redirect | ❌ | ❌ | ❌ | Très faible |
| streamlink | ✅ | ✅ | ✅ | Faible |
| VLC | ✅ | ✅ | ✅ | Faible |
| Custom ffmpeg/VLC | ✅ | ✅ | ✅ | Faible → Très élevé |
| yt-dlp | ✅ | ✅ | ✅ | Faible |

### Output Profiles

Transcodage à la volée avant livraison au client (AC3 → AAC pour navigateurs). Utilise `pipe:0` en input, `pipe:1` en output. Format MPEG-TS obligatoire.

Exemple : `-i pipe:0 -c:v libx264 -b:v 2000k -vf scale=-2:720 -c:a copy -f mpegts pipe:1`

### Proxy Settings

- **Buffering Timeout** : délai max avant failover
- **Buffering Speed** : seuil de détection buffer (1.0 = normal)
- **Channel Shutdown Delay** : délai après déconnexion du dernier viewer
- **New Client Buffer** : secondes de buffer pour nouveau client
- **Buffer Chunk TTL** : durée de cache des chunks
- **Channel Init Timeout** : timeout connexion + failover
- **Client Connect Grace Period** : temps d'attente avant arrêt canal sans viewer

### Types d'utilisateurs

1. **Admin** : accès total, XC si password défini
2. **Standard** : UI channels/guide/settings, restrictions par profile XC
3. **Streamer** : pas d'UI, XC uniquement

### Backups

Planification via cron. Rétention configurable.

### Network Access

Restriction par CIDR par endpoint (M3U, EPG, HDHR, XC API, UI, Streams).

---

## 6. Intégration media centers

### Jellyfin
- Source TV : HDHR ou M3U (copier l'URL depuis Channels → Links)
- Guide : XMLTV (copier l'URL EPG)

### Plex
- Source TV : HDHR uniquement (détection auto)
- Guide : Plex EPG ou XMLTV depuis Dispatcharr
- Astuce logos : `?cachedlogos=false` dans l'URL EPG

### Emby
- Source TV : HDHR ou M3U
- Guide : XMLTV depuis Dispatcharr ou Emby Guide Data

### ChannelsDVR
- Source : M3U Custom Channels, MPEG-TS, XMLTV Guide

---

## 7. DVR (Enregistrements)

- Comskip (suppression pubs) : activable
- Templates de chemin : `{show}`, `{season}`, `{episode}`, `{sub_title}`, `{channel}`, `{year}`, `{start}`, `{end}`
- Enregistrements dans `/data/recordings`
- Possibilité de bind mount pour stockage externe : `host_path/media:/data/recordings`

---

## 8. M3U & EPG Manager

### M3U Accounts
- Types : Standard (URL M3U) ou Xtream Codes (panel API)
- Server Groups : partage de limites de connexion entre comptes même fournisseur
- Filtres regex (include/exclude) sur Group, Stream Name, Stream URL
- Auto Channel Sync : création auto des chaînes pour un groupe
- Profiles : second jeu d'identifiants pour un même compte
- VOD Scanning pour comptes Xtream Codes

### EPGs
- Sources : XMLTV URL, Schedules Direct, ou Dummy EPG (regex custom)
- Auto-import depuis `/data/epgs/` (fichiers .xml, .gz, .zip)
- Priorité entre EPGs multiples

### Dummy EPG
Permet de générer un guide EPG à partir du nom des chaînes avec patterns regex :
- Title/Time/Date Patterns pour extraire les infos
- Output Templates pour formater l'affichage
- Upcoming/Ended Templates pour les programmes futurs/passés
- Fallback Templates

---

## 9. Stats

Page temps réel montrant :
- Connexions actives par chaîne
- Profil stream, uptime, programme en cours
- Stats flux (résolution, FPS, codec, bitrate)
- Watchers (IP, User-Agent, username)
- Force stop d'un stream
- System Events (refreshes, switches, auth, errors)

---

## 10. Dépannage

- **Port :** `9191`
- **Logs :** `docker logs dispatcharr`
- **Niveau de log :** `DISPATCHARR_LOG_LEVEL=debug` pour plus d'info
- **AIO derrière VPN :** vérifier que Redis/Postgres tournent bien (interne)
- **Si le container ne démarre pas :** checker les droits sur `/data`
- **Pangolin SSO :** toutes les bypass rules sont nécessaires pour XC
