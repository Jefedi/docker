---
name: jellyfin
description: >
  Jellyfin media server documentation expert. Covers Jellyfin (serveur multimédia, transcoding, reverse proxy), Jellyseerr (request management, discovery), Bazarr (subtitles, FR/EN/forced). Trigger words: jellyfin, jellyseerr, bazarr, subtitle, transcoding, hardware acceleration, media server, request, discovery, reverse proxy jellyfin.
---

# Jellyfin / Jellyseerr / Bazarr Documentation Skill

## Mental Model

Jellyfin = 3 services complémentaires:

- **Jellyfin** = serveur multimédia (scan library, transcode, stream to clients). Gère les bibliothèques de films/séries/musique, le hardware transcoding (Intel QuickSync / AMD VAAPI / NVIDIA NVENC), et le streaming vers clients web, mobiles, Apple TV (Streamyfin).
- **Jellyseerr** = portail de demande (users request films/séries via Jellyfin/Plex SSO). Les utilisateurs peuvent demander du contenu qui n'est pas encore dans la bibliothèque. Jellyseerr envoie les demandes à Sonarr/Radarr qui gèrent le download. Supporte l'authentification via Jellyfin (SSO).
- **Bazarr** = gestionnaire de sous-titres (auto-download FR/EN/forced pour Sonarr/Radarr). Récupère la liste des films/séries depuis Radarr/Sonarr via leur API, cherche et télécharge les sous-titres correspondants. Gère 3 types de sous-titres: regular (FR), forced (forced narrative), et EN.

Jellyseerr et Bazarr s'intègrent avec les *arr: Jellyseerr envoie les demandes à Sonarr/Radarr, Bazarr récupère les sous-titres pour les releases importées. Le tout en Docker avec accès au /data mount.

## Routing Table

Load the reference file that matches the question domain. Always open the file before answering.

### Jellyfin — Installation & Setup

| Question domain | Reference file |
|---|---|
| Quick start, overview | `jellyfin__quick-start.md`, `jellyfin__about.md` |
| Docker container install | `jellyfin__installation__container.md`, `jellyfin__installation___container-docker-cli.md`, `jellyfin__installation___container-docker-compose.md` |
| Podman install | `jellyfin__installation___container-podman.md` |
| Linux install | `jellyfin__installation__linux.md` |
| Windows install | `jellyfin__installation__windows.md` |
| macOS install | `jellyfin__installation__macos.md` |
| Kubernetes install | `jellyfin__installation__advanced__kubernetes.md` |
| Synology install | `jellyfin__installation__advanced__synology.md` |
| TrueNAS install | `jellyfin__installation__advanced__truenas.md` |
| Manual/source build | `jellyfin__installation__advanced__manual.md`, `jellyfin__installation__advanced__source.md` |
| Community builds | `jellyfin__installation__advanced__community.md` |
| Setup wizard (post-install) | `jellyfin__post-install__setup-wizard.md` |

### Jellyfin — Administration

| Question domain | Reference file |
|---|---|
| Configuration (server config) | `jellyfin__administration__configuration.md` |
| Troubleshooting | `jellyfin__administration__troubleshooting.md` |
| Backup and restore | `jellyfin__administration__backup-and-restore.md` |
| Storage (NFS, local, network) | `jellyfin__administration__storage.md` |
| Hardware selection (CPU/GPU) | `jellyfin__administration__hardware-selection.md` |
| Migration (from Emby) | `jellyfin__administration__migrate.md` |
| Server settings | `jellyfin__server__settings.md` |
| FAQ | `jellyfin__faq.md` |

### Jellyfin — Networking & Reverse Proxy

| Question domain | Reference file |
|---|---|
| Networking overview | `jellyfin__post-install__networking__index.md` |
| Reverse proxy overview | `jellyfin__post-install__networking__8_reverse-proxy__index.md` |
| Traefik reverse proxy | `jellyfin__post-install__networking__8_reverse-proxy__traefik.md` |
| Nginx reverse proxy | `jellyfin__post-install__networking__8_reverse-proxy__nginx.md` |
| Caddy reverse proxy | `jellyfin__post-install__networking__8_reverse-proxy__caddy.md` |
| Apache reverse proxy | `jellyfin__post-install__networking__8_reverse-proxy__apache.md` |
| HAProxy reverse proxy | `jellyfin__post-install__networking__8_reverse-proxy__haproxy.md` |
| Tailscale networking | `jellyfin__post-install__networking__2_tailscale.md` |
| DLNA | `jellyfin__post-install__networking__3_dlna.md` |
| fail2ban (security) | `jellyfin__post-install__networking__9_advanced__fail2ban.md` |
| IPBan (security) | `jellyfin__post-install__networking__9_advanced__ipban.md` |
| Let's Encrypt (TLS) | `jellyfin__post-install__networking__9_advanced__letsencrypt.md` |
| Monitoring | `jellyfin__post-install__networking__9_advanced__monitoring.md` |

### Jellyfin — Transcoding & Hardware Acceleration

| Question domain | Reference file |
|---|---|
| Hardware acceleration overview | `jellyfin__post-install__transcoding__hardware-acceleration__index.md` |
| Intel (QuickSync/VAAPI) | `jellyfin__post-install__transcoding__hardware-acceleration__intel.md` |
| AMD (AMF/VAAPI) | `jellyfin__post-install__transcoding__hardware-acceleration__amd.md` |
| NVIDIA (NVENC) | `jellyfin__post-install__transcoding__hardware-acceleration__nvidia.md` |
| Apple (VideoToolbox) | `jellyfin__post-install__transcoding__hardware-acceleration__apple.md` |
| Rockchip | `jellyfin__post-install__transcoding__hardware-acceleration__rockchip.md` |
| Known issues (HW accel) | `jellyfin__post-install__transcoding__hardware-acceleration__known-issues.md` |
| Audio downmix | `jellyfin__post-install__transcoding__downmix.md` |

### Jellyfin — Server, Media, Users

| Question domain | Reference file |
|---|---|
| Libraries setup | `jellyfin__server__libraries.md` |
| Devices management | `jellyfin__server__devices.md` |
| Media — movies | `jellyfin__server__media__movies.md` |
| Media — shows (TV) | `jellyfin__server__media__shows.md` |
| Media — music | `jellyfin__server__media__music.md` |
| Media — books | `jellyfin__server__media__books.md` |
| Media — music videos | `jellyfin__server__media__music-videos.md` |
| Mixed movies and shows | `jellyfin__server__media__mixed-movies-and-shows.md` |
| Excluding directories | `jellyfin__server__media__excluding-directory.md` |
| Metadata overview | `jellyfin__server__metadata__index.md` |
| NFO metadata | `jellyfin__server__metadata__nfo.md` |
| Metadata identifiers | `jellyfin__server__metadata__identifiers.md` |
| Chapter images | `jellyfin__server__metadata__chapter-images.md` |
| Media segments | `jellyfin__server__metadata__media-segments.md` |
| Users — adding & managing | `jellyfin__server__users__adding-managing-users.md` |
| Users overview | `jellyfin__server__users__index.md` |
| Quick Connect | `jellyfin__server__quick-connect.md` |
| Notifications | `jellyfin__server__notifications.md` |
| Scheduled tasks | `jellyfin__server__tasks.md` |
| OpenSubtitles plugin | `jellyfin__server__plugins__open-subtitles.md` |
| TVheadend plugin | `jellyfin__server__plugins__tvheadend.md` |
| Live TV setup | `jellyfin__server__live-tv__setup-guide.md`, `jellyfin__server__live-tv__index.md` |

### Jellyfin — Clients

| Question domain | Reference file |
|---|---|
| Codec support | `jellyfin__clients__codec-support.md` |
| Web config | `jellyfin__clients__web-config.md` |
| CSS customization | `jellyfin__clients__css-customization.md` |
| Jellyfin Vue | `jellyfin__clients__jellyfin-vue.md` |
| Kodi | `jellyfin__clients__kodi.md` |
| Mopidy | `jellyfin__clients__mopidy.md` |

### Jellyseerr — Installation & Setup

| Question domain | Reference file |
|---|---|
| Getting started overview | `jellyseerr__getting-started__index.md` |
| Docker install | `jellyseerr__getting-started__docker.md` |
| Build from source | `jellyseerr__getting-started__buildfromsource.md` |
| Kubernetes | `jellyseerr__getting-started__kubernetes.md` |
| Nix package | `jellyseerr__getting-started__nixpkg.md` |
| AUR (Arch) | `jellyseerr__getting-started__third-parties__aur.md` |
| Synology | `jellyseerr__getting-started__third-parties__synology.md` |
| TrueNAS | `jellyseerr__getting-started__third-parties__truenas.md` |
| Unraid | `jellyseerr__getting-started__third-parties__unraid.md` |
| Migration guide (Overseerr → Seerr) | `jellyseerr__migration-guide.md` |
| Troubleshooting | `jellyseerr__troubleshooting.md` |

### Jellyseerr — Settings & Configuration

| Question domain | Reference file |
|---|---|
| General settings | `jellyseerr__using-seerr__settings__general.md` |
| Media server (Jellyfin/Plex/Emby config) | `jellyseerr__using-seerr__settings__mediaserver.md` |
| Services (Sonarr/Radarr config) | `jellyseerr__using-seerr__settings__services.md` |
| Users settings | `jellyseerr__using-seerr__settings__users.md` |
| Network settings | `jellyseerr__using-seerr__settings__network.md` |
| Notifications settings | `jellyseerr__using-seerr__settings__notifications.md` |
| Jobs & cache | `jellyseerr__using-seerr__settings__jobs&cache.md` |
| Advanced settings | `jellyseerr__using-seerr__advanced__index.md` |
| Self-signed certificates | `jellyseerr__using-seerr__advanced__self-signed-certificates.md` |
| Verifying signed artifacts | `jellyseerr__using-seerr__advanced__verifying-signed-artifacts.md` |

### Jellyseerr — Users

| Question domain | Reference file |
|---|---|
| Adding users | `jellyseerr__using-seerr__users__adding-users.md` |
| Editing users | `jellyseerr__using-seerr__users__editing-users.md` |
| Deleting users | `jellyseerr__using-seerr__users__deleting-users.md` |
| Owner account | `jellyseerr__using-seerr__users__owner.md` |

### Jellyseerr — Notifications

| Question domain | Reference file |
|---|---|
| Notifications overview | `jellyseerr__using-seerr__notifications__index.md` |
| Discord | `jellyseerr__using-seerr__notifications__discord.md` |
| Telegram | `jellyseerr__using-seerr__notifications__telegram.md` |
| Email | `jellyseerr__using-seerr__notifications__email.md` |
| Gotify | `jellyseerr__using-seerr__notifications__gotify.md` |
| ntfy | `jellyseerr__using-seerr__notifications__ntfy.md` |
| Pushbullet | `jellyseerr__using-seerr__notifications__pushbullet.md` |
| Pushover | `jellyseerr__using-seerr__notifications__pushover.md` |
| Slack | `jellyseerr__using-seerr__notifications__slack.md` |
| Webhook | `jellyseerr__using-seerr__notifications__webhook.md` |
| Web Push | `jellyseerr__using-seerr__notifications__webpush.md` |

### Jellyseerr — Extending & Advanced

| Question domain | Reference file |
|---|---|
| Reverse proxy config | `jellyseerr__extending-seerr__reverse-proxy.md` |
| Database config | `jellyseerr__extending-seerr__database-config.md` |
| fail2ban | `jellyseerr__extending-seerr__fail2ban.md` |
| Terraform provider | `jellyseerr__extending-seerr__terraform-provider.md` |
| Backups | `jellyseerr__using-seerr__backups.md` |
| Plex settings | `jellyseerr__using-seerr__plex__index.md` |
| Plex watchlist auto-request | `jellyseerr__using-seerr__plex__watchlist-auto-request.md` |
| Blog posts & release notes | `jellyseerr__gen-docs__blog__2026-06-01__seerr-3-2-0-and-3-3-0-release-notes.md`, etc. |

### Bazarr — Installation & Setup

| Question domain | Reference file |
|---|---|
| Home / overview | `bazarr__home.md` |
| Installation guide | `bazarr__installation.md` |
| Synology install | `bazarr__installation-synology.md` |
| Setup guide | `bazarr__setup-guide.md` |
| First-time config | `bazarr__first-time-installation-configuration.md` |
| Autostart (Linux/Win/Mac/BSD) | `bazarr__autostart-on-linux-windows-macos-freebsd.md` |

### Bazarr — Configuration & Troubleshooting

| Question domain | Reference file |
|---|---|
| Settings (all options) | `bazarr__settings.md` |
| FAQ (forced subtitles, embedded, etc.) | `bazarr__faq.md` |
| Reverse proxy help | `bazarr__reverse-proxy-help.md` |
| Performance tuning | `bazarr__performance-tuning.md` |
| Logging & log files | `bazarr__logging-and-log-files.md` |
| Asking for help / reporting problems | `bazarr__asking-for-help-or-report-a-problem.md` |

### Jefe's Infrastructure (Gotchas)

| Question domain | Reference file |
|---|---|
| **Jefe's field knowledge (gotchas)** | `00-gotchas-jefe.md` |

## Behavior Rule

**Never answer from memory about a configuration option, default value, or API field.** Always open the corresponding reference file and cite the exact value. If the answer is not in the reference files or the gotchas file, say so explicitly. Do not invent.

## Validation Questions

### Q1: Comment configurer Jellyseerr pour utiliser Jellyfin comme authentification ?

Ouvrir `jellyseerr__using-seerr__settings__mediaserver.md` (section Jellyfin). Les points clés:
- Se connecter à Jellyseerr avec un compte administrateur Jellyfin (le premier login doit utiliser un compte admin Jellyfin).
- Configurer l'Internal URL (URL accessible depuis le conteneur Jellyseerr vers Jellyfin — ne pas utiliser `localhost` si en Docker bridged network; utiliser le container name ou l'IP locale).
- Configurer l'External URL (URL publique que les utilisateurs utilisent pour accéder à Jellyfin, ex: via reverse proxy Pangolin).
- Sélectionner les bibliothèques Jellyfin à scanner.
- Lancer un manual library scan la première fois.

Voir aussi `00-gotchas-jefe.md` (section "Jellyseerr + Jellyfin SSO") pour les TODO spécifiques à l'infra Jefe (URL exacte, admin user).

### Q2 (contre-intuitive): Pourquoi Bazarr ne trouve pas les sous-titres d'un film qui est dans Radarr ?

Bazarr ne scanne pas le filesystem. Il récupère la liste des films/séries **via l'API Radarr/Sonarr** (Settings > Services). Si un film n'est pas **importé** dans Radarr (c'est-à-dire downloaded ET imported dans la bibliothèque Radarr), Bazarr ne le verra pas, même si le fichier est sur le disque.

Étapes de diagnostic:
1. Vérifier que le film est marqué "Downloaded" dans Radarr (pas seulement "Wanted").
2. Vérifier Settings > Services > Radarr dans Bazarr: la connexion (URL, API key) doit être valide (cliquer "Test").
3. Lancer un sync manuel dans Bazarr (le sync automatique se fait périodiquement via l'API *arr).
4. Le film doit avoir un chemin de fichier valide dans Radarr pour que Bazarr puisse chercher les sous-titres.

Voir `bazarr__setup-guide.md` et `00-gotchas-jefe.md` (section "Bazarr et Sonarr/Radarr integration").

### Q3: Comment activer le hardware transcoding dans Jellyfin en Docker ?

Ouvrir `jellyfin__post-install__transcoding__hardware-acceleration__index.md` pour l'overview, puis le fichier spécifique au GPU:
- Intel QuickSync/VAAPI: `jellyfin__post-install__transcoding__hardware-acceleration__intel.md`
- AMD AMF/VAAPI: `jellyfin__post-install__transcoding__hardware-acceleration__amd.md`
- NVIDIA NVENC: `jellyfin__post-install__transcoding__hardware-acceleration__nvidia.md`

En Docker, le conteneur doit avoir accès au device GPU (`--device /dev/dri` pour Intel/AMD). Puis dans Jellyfin: Dashboard > Playback > Transcoding > sélectionner le type de Hardware Acceleration.

Voir aussi `jellyfin__post-install__transcoding__hardware-acceleration__known-issues.md` pour les problèmes connus, et `00-gotchas-jefe.md` (section "Jellyfin Hardware Transcoding") pour les TODO spécifiques au serveur AX42 (confirmation du GPU, config Docker exacte).