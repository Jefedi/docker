---
name: jackett
description: Proxy d'indexers torrent. Traduit les API propriétaires en Torznab/Newznab pour les *arr. 350+ indexers supportés.
category: media
---

# Jackett — Guide de référence

> **Image :** `lscr.io/linuxserver/jackett:latest`  
> **Port :** `9117`  
> **Site :** https://github.com/Jackett/Jackett  
> **Doc LSIO :** https://docs.linuxserver.io/images/docker-jackett/

---

## 1. Docker Compose

```yaml
  jackett:
    image: lscr.io/linuxserver/jackett:latest
    container_name: jackett
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
      - AUTO_UPDATE=true  # Permet la màj dans le conteneur
      # - RUN_OPTS=       # Arguments supplémentaires optionnels
    volumes:
      - ./configs/jackett:/config
    restart: unless-stopped
```

## 2. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 9117 à mapper dans Gluetun

## 3. Utilisation

Jackett sert de bridge entre les indexers privés (API propriétaires HTML) et les *arr qui comprennent uniquement Torznab.

**Avec Prowlarr :** Jackett n'est plus nécessaire si les indexers sont directement supportés par Prowlarr. Garder Jackett pour les indexers obselètes ou non supportés par Prowlarr/Cardigann.

## 4. Notes

- Supporte 350+ indexers
- Auto-update disponible via `AUTO_UPDATE=true`
- Configuration via WebUI à `http://<ip>:9117`
