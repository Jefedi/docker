---
name: janitorr
description: Nettoyage de médias. Supprime orphelins, fichiers jamais regardés ou trop vieux dans Radarr/Sonarr/Jellyfin/Emby.
category: media
---

# Janitorr — Guide de référence

> **Image :** `ghcr.io/schaka/janitorr:jvm-stable`  
> **Version :** v2.1.1  
> **Port health :** `8081` (THC)  
> **Mode réseau :** `host`  
> **Repo :** https://github.com/Schaka/janitorr  
> **Langage :** Kotlin/Spring Boot

Janitorr nettoie les médias jamais regardés ou trop vieux sur votre serveur Jellyfin/Emby en se basant sur l'historique des *arr (Radarr/Sonarr). Pas de GUI — tout se fait via fichier `application.yml`.

---

## 1. Docker Compose

```yaml
  janitorr:
    image: ghcr.io/schaka/janitorr@sha256:6becfbed9098d27e6bf81a114976394a091d095ee5aba3ae8d86a4fd94af8e7a
    container_name: janitorr
    network_mode: host
    user: 1000:1000
    mem_limit: 256M
    mem_swappiness: 0
    environment:
      - TZ=Europe/Paris
      - THC_PATH=/health
      - THC_PORT=8081
    volumes:
      - ./configs/janitorr/application.yml:/config/application.yml
      - ./configs/janitorr/logs:/logs
      - "${COMMON_PATH}:/data"
    healthcheck:
      test: ["CMD", "/workspace/health-check"]
      start_period: 30s
      interval: 30s
      retries: 3
    restart: unless-stopped
```

## 2. Fichier `application.yml`

```yaml
application:
  # --- CONNEXION *arr ---
  sonarr:
    base-url: http://localhost:8989
    api-key: ""
  radarr:
    base-url: http://localhost:7878
    api-key: ""
  
  # --- CONNEXION MEDIA SERVER ---
  # Jellyfin OU Emby (pas les deux)
  jellyfin:
    base-url: http://localhost:8096
    api-key: ""
  # emby:
  #   base-url: http://localhost:8096
  #   api-key: ""

  # --- STATS (optionnel) ---
  # Jellystat OU Streamystats (pas les deux)
  # janitorr-stats peut être utilisé seul ou en fallback

  # --- DRY-RUN (défaut: true) ---
  dry-run: true

  # --- MODES DE NETTOYAGE ---

  # 1. MEDIA DELETION - Suppression basée sur espace disque
  media-deletion:
    minimum-free-disk-percent: 5
    # Films : seuil disque → délai
    lookup-table-movie:
      - free-disk-percent: 5
        expire-after-days: 15
      - free-disk-percent: 10
        expire-after-days: 30
      - free-disk-percent: 20
        expire-after-days: 90
    # Séries : seuil disque → délai  
    lookup-table-series:
      - free-disk-percent: 5
        expire-after-days: 15
      - free-disk-percent: 10
        expire-after-days: 30

  # 2. TAG-BASED DELETION - Suppression par tags
  tag-based-deletion:
    minimum-free-disk-percent: 5
    schedule:
      - tag: "janitorr_delete_soon"
        expire-after-days: 30
      - tag: "janitorr_old"
        expire-after-days: 90

  # 3. EPISODE DELETION - Talk-shows, infos quotidiennes
  episode-deletion:
    tag: janitorr_daily
    keep-last: 5  # Garde les N derniers épisodes
    ignore-jellystat: true

  # --- CONFIG EXCLUSION ---
  # Tag "janitorr_keep" (configurable) dans Sonarr/Radarr = exclure
  keep-tag: janitorr_keep
```

## 3. Modes de nettoyage détaillés

| Mode | Condition | Action |
|---|---|---|
| **Media Deletion** | Espace disque < seuil | Supprime films/saisons selon tableau âge |
| **Tag-based Deletion** | Espace disque < seuil + tag présent | Supprime médias tagués expirés |
| **Episode Deletion** | Tag `janitorr_daily` | Garde N derniers épisodes, supprime le reste |

## 4. Intégrations

- **Radarr :** films
- **Sonarr :** séries
- **Jellyfin :** serveur média
- **Emby :** serveur média (alternative)
- **Jellystat / Streamystats :** stats (optionnel)
- **janitorr-stats :** fallback stats intégré

## 5. Spécificités

- `network_mode: host` nécessaire pour accéder aux services en localhost
- **Pas de GUI** — monitoring via logs
- **dry-run: true** par défaut (sécurité)
- Symlinks "Leaving Soon" créés dans le système de fichiers
- Exclure un média : tag `janitorr_keep` dans Sonarr/Radarr
- Utilise `/:health` pour les healthchecks
