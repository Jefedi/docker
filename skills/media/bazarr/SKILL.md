---
name: bazarr
description: Gestionnaire de sous-titres. Téléchargement automatique et synchronisation pour Sonarr/Radarr. FR/EN/forced.
category: media
---

# Bazarr — Guide de référence

> **Image :** `lscr.io/linuxserver/bazarr:latest`  
> **Port :** `6767`  
> **Tags :** `latest` (stable), `development` (pre-release)  
> **Site :** https://www.bazarr.media  
> **Wiki :** https://wiki.bazarr.media

---

## 1. Docker Compose

```yaml
  bazarr:
    image: lscr.io/linuxserver/bazarr:latest
    container_name: bazarr
    network_mode: service:gluetun
    depends_on:
      - gluetun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - ./configs/bazarr:/config
      - "${COMMON_PATH}:/data"
    restart: unless-stopped
```

## 2. Docker networking

- Derrière VPN via `network_mode: service:gluetun`
- Port 6767 à mapper dans Gluetun

## 3. Fonctionnalités

- **Recherche automatique** des sous-titres manquants
- **Recherche manuelle** avec sélection
- **Upgrade** automatique vers une meilleure version
- **Langues :** Français, Anglais, et toutes les langues disponibles
- **Sous-titres forcés** (foreign/forced) pour les parties non-traduites

## 4. Providers supportés

OpenSubtitles, Podnapisi, Subscene, Addic7ed, et bien d'autres selon la configuration dans le WebUI.

## 5. Intégration

- **Sonarr :** connexion API pour les séries TV
- **Radarr :** connexion API pour les films
- Les paths médias doivent correspondre entre Bazarr et les *arr (hardlinks)
