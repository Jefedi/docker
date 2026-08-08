# Jellyfin / Jellyseerr / Bazarr — Field Knowledge (Jefe's Infrastructure)

Savoir terrain absent de la doc officielle, compilé depuis l'infrastructure
Jefe (serveur AX42, jNas, Apple TV, Pangolin reverse proxy).

## Infrastructure Map

| Service | Docker container | Host | Storage | Reverse proxy |
|---------|-----------------|------|---------|---------------|
| Jellyfin | jellyfin/jellyfin | AX42 (Docker) | NFS mount (/data from jNas → AX42) | Pangolin (Traefik) |
| Jellyseerr | fallenbagel/jellyseerr | AX42 (Docker) | — | Pangolin (Traefik) |
| Bazarr | linuxserver/bazarr | AX42 (Docker) | — | Pangolin (Traefik) |

- Jellyfin: hardware transcoding activé sur AX42 (Intel QuickSync ou AMD VAAPI — TODO: confirmer).
- Jellyseerr: connecté à Jellyfin (SSO) + Radarr/Sonarr (demandes).
- Bazarr: connecté à Sonarr + Radarr (API), gère sous-titres FR/EN/forced.
- Apple TV Séjour: client Jellyfin via app Streamyfin.
- Stockage: migration jNas → AX42 en cours. NFS pour la bibliothèque multimédia.

## Jellyfin Hardware Transcoding

TODO — documenter la config hardware acceleration (Intel QuickSync / AMD VAAPI / NVIDIA NVENC) sur le serveur AX42.
Vérifier `--device /dev/dri` dans le conteneur Docker.

Points à confirmer:
- Quel GPU est disponible sur AX42 (Intel iGPU? AMD? NVIDIA?)
- Le conteneur Docker Jellyfin a-t-il `--device /dev/dri` mappé?
- Dans Jellyfin: Dashboard > Playback > Transcoding > Hardware Acceleration
- Voir `jellyfin__post-install__transcoding__hardware-acceleration__index.md` pour la doc officielle.
- Voir `jellyfin__post-install__transcoding__hardware-acceleration__intel.md` (QuickSync/VAAPI).
- Voir `jellyfin__post-install__transcoding__hardware-acceleration__amd.md` (AMD AMF/VAAPI).
- Voir `jellyfin__post-install__transcoding__hardware-acceleration__nvidia.md` (NVENC).

## Jellyseerr + Jellyfin SSO

Jellyseerr supporte l'authentification via Jellyfin (Settings > Services > Jellyfin).
L'utilisateur Jellyfin doit avoir le flag "Admin" pour que Jellyseerr accepte le login.

TODO: documenter la config exacte:
- URL Jellyfin (interne ou via reverse proxy?)
- API key (ou utiliser le login Jellyfin directement?)
- Admin user Jellyfin requis pour le premier login Jellyseerr
- Voir `jellyseerr__using-seerr__settings__mediaserver.md` pour la doc officielle.
- Voir `jellyseerr__using-seerr__settings__services.md` pour la config Sonarr/Radarr.
- Voir `jellyseerr__using-seerr__users__adding-users.md` pour la gestion des utilisateurs.

## Bazarr FR/EN/forced Subtitles

Bazarr gère 3 types de sous-titres:
- **regular** (FR): sous-titres complets en français pour le contenu VOSTFR.
- **forced** (forced narrative): sous-titres forcés pour les passages en langue étrangère dans un film VF.
- **EN**: sous-titres en anglais.

Pour les releases VOSTFR, Bazarr doit chercher FR + forced.
Pour les releases VF, chercher FR seulement (ou forced seulement pour les passages étrangers).

TODO: documenter les profiles de languages exacts dans Bazarr (Settings > Languages).
Voir `bazarr__settings.md` et `bazarr__faq.md` (section "What are Forced Subtitles").

## Bazarr et Sonarr/Radarr Integration

Bazarr récupère la liste des films/séries depuis Radarr/Sonarr (Settings > Services).
Si un film manque dans Bazarr, vérifier:
1. Le film est **importé** dans Radarr/Sonarr (pas juste "wanted" — il doit être downloaded + imported).
2. Bazarr a **synchronisé** sa bibliothèque (le sync se fait via l'API *arr, pas via filesystem scan).
3. Settings > Services > Radarr/Sonarr > vérifier la connexion (URL, API key, "Test" button).

Le sync se fait via l'API *arr, pas via filesystem scan. Donc un fichier qui est sur le disque
mais pas encore importé dans Radarr/Sonarr n'apparaîtra pas dans Bazarr.

Voir `bazarr__setup-guide.md` et `bazarr__settings.md` pour la doc officielle.

## Jellyfin Reverse Proxy

Jellyfin derrière un reverse proxy (Traefik/Pangolin) nécessite:
- Les headers `X-Forwarded-For`, `X-Forwarded-Proto`.
- Le path `/socket` pour les WebSockets (communication temps réel: notifications, sync playback).
- Configuration HTTPS pour que les clients fonctionnent correctement.

TODO: documenter la config Traefik exacte pour Jellyfin.
Voir `jellyfin__post-install__networking__8_reverse-proxy__traefik.md` pour la doc officielle.
Voir aussi `jellyfin__post-install__networking__8_reverse-proxy__nginx.md` et `index.md`.

## Jellyfin et NFS

Jellyfin peut avoir des problèmes de scan lent si la bibliothèque est sur NFS.
Symptômes: scan de bibliothèque qui prend des heures, métadonnées qui ne se chargent pas.

Solutions possibles:
- Utiliser `-disable-ffmpeg-concurrent` au démarrage de Jellyfin.
- Augmenter le `scanner.activityInterval` dans la configuration.
- Vérifier les options de mount NFS (`nfsvers=4`, `hard`, `tcp`, `rsize=32768`, `wsize=32768`).

TODO: vérifier la config exacte pour le jNas/AX42 (mount NFS, options, performance).

## Apple TV Client (Streamyfin)

Jellyfin sur Apple TV utilise l'app Streamyfin (client Jellyfin pour tvOS).

TODO: documenter:
- Installation de Streamyfin depuis l'App Store tvOS.
- Config: Jellyfin server URL (interne LAN ou via Pangolin reverse proxy?).
- Credentials: utilisateur Jellyfin (non-admin ou admin?).
- Le device est connu dans Home Assistant comme `media_player.apple_tv_sejour` avec remote.

## Jellyseerr Notifications

Jellyseerr supporte plusieurs canaux de notification (Discord, Telegram, email, etc.).
TODO: documenter quelle notification est configurée sur l'infra Jefe.
Voir `jellyseerr__using-seerr__notifications__discord.md`, `jellyseerr__using-seerr__notifications__telegram.md`, etc.

## Bazarr Reverse Proxy

Bazarr derrière un reverse proxy nécessite une config similaire à Sonarr/Radarr.
Voir `bazarr__reverse-proxy-help.md` pour la doc officielle.
TODO: documenter la config Traefik/Pangolin exacte pour Bazarr.

## Jellyseerr Reverse Proxy

Jellyseerr derrière un reverse proxy nécessite une config spécifique.
Voir `jellyseerr__extending-seerr__reverse-proxy.md` pour la doc officielle.
TODO: documenter la config Traefik/Pangolin exacte pour Jellyseerr.