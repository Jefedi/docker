---
name: profilarr
description: Gestion de profils et Custom Formats pour Radarr/Sonarr. Build, test, déploiement de configurations.
category: media
---

# Profilarr — Guide de référence

> **Image :** `ghcr.io/dictionarry-hub/profilarr:latest`  
> **Port :** `6868`  
> **Version :** v2.0.9  
> **Stars :** 2.5k  
> **Site :** https://github.com/Dictionarry-Hub/profilarr  
> **Docs :** https://dictionarry.dev  

Profilarr est une plateforme de gestion de configuration pour Radarr et Sonarr. Elle permet de **construire, tester et déployer** des profils qualité et Custom Formats.

**Stack :** Deno 2 + SvelteKit 5 + Tailwind 4 + SQLite (WAL) + parser C#/.NET optionnel.

---

## 1. Docker Compose

```yaml
  profilarr:
    image: ghcr.io/dictionarry-hub/profilarr:latest
    container_name: profilarr
    ports:
      - "127.0.0.1:6868:6868"
      - "100.64.0.2:6868:6868"
    volumes:
      - ./configs/profilarr-v2:/config
    environment:
      - PUID=1000
      - PGID=1000
      - UMASK=022
      - TZ=Europe/Paris
      - ORIGIN=https://profilarr.jefe.ovh
    restart: unless-stopped
```

## 2. Variables d'environnement

| Variable | Description |
|---|---|
| `ORIGIN` | URL publique pour CORS (ex: `https://profilarr.jefe.ovh`) |
| `PUID` | User ID |
| `PGID` | Group ID |

## 3. Fonctionnalités (3 piliers)

### 🔨 Build
- **Link databases** : connexion à des bases PCD (Profilarr Compliant Database) :
  - [Dictionarry](https://github.com/Dictionarry-Hub/database) (recommandé)
  - [TRaSH Guides](https://github.com/Dictionarry-Hub/trash-pcd)
  - [Dumpstarr](https://github.com/Dumpstarr/Database)
- **Quality profiles** : groupement et ordre des qualités, scoring des CF par app
- **Custom Formats** : import depuis les bases liées

### 🧪 Test
- **Parser** : microservice C#/.NET optionnel (`ghcr.io/dictionarry-hub/profilarr-parser:latest`)
- **Preview** : visualise le matching des CF sur des release names réels
- **Validation** : vérifie la cohérence des profils avant déploiement

### 🚀 Deploy
- **Synchronisation API** : pousse les profils vers Radarr/Sonarr
- **Tags** : support des tags pour grouper les CF
- **Scores** : scoring par profil qualité

## 4. Prérequis

- **Linux kernel 3.17+** (pas de Synology kernel 3.10)
- Platforme Docker `linux/amd64` ou `linux/arm64`
- **Radarr v5+**
- **Sonarr v4+**

## 5. Intégrations

- **Radarr :** profils qualité et CF pour films
- **Sonarr :** profils qualité et CF pour séries
- **Parser (optionnel) :** service de test des release names via `ghcr.io/dictionarry-hub/profilarr-parser:latest`

## 6. Réseau

- **Pas derrière le VPN** (interface web, accessible via reverse proxy)
- Port 6868 exposé sur localhost + IP secondaire
- Pangolin/Newt : créer une ressource proxy → `http://127.0.0.1:6868`
