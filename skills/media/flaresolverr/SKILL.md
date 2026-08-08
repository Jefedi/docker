---
name: flaresolverr
description: Proxy pour contourner Cloudflare et autres challenges anti-bot. Utilisé par les indexers.
category: media
---

# Flaresolverr — Guide de référence

> **Image :** `ghcr.io/flaresolverr/flaresolverr:latest`  
> **Port :** `8191`  
> **Site :** https://github.com/FlareSolverr/FlareSolverr

---

## 1. Docker Compose

```yaml
  flaresolverr:
    image: ghcr.io/flaresolverr/flaresolverr:latest
    container_name: flaresolverr
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - LOG_LEVEL=info
      - TZ=Europe/Paris
    restart: unless-stopped
```

## 2. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 8191 à mapper dans Gluetun

## 3. Intégration

Configuré comme proxy dans Prowlarr ou Jackett pour les indexers protégés par Cloudflare.
