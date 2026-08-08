---
name: media-stack
description: >
  Media stack documentation expert. Covers TRaSH Guides (custom formats, quality
  profiles, naming schemes), Recyclarr (sync automatisé TRaSH -> Sonarr/Radarr),
  hardlinks (Docker mount unique /data, permissions PUID/PGID, NFS). Trigger words:
  trash guides, recyclarr, custom format, quality profile, naming scheme, hardlink,
  PUID, PGID, NFS, docker mount, media stack, CF group, trash id.
---

# Media Stack Documentation Skill

## Mental Model

Media stack = la couche de configuration qui orchestre la qualité des releases.
**TRaSH Guides** est la source de vérité (templates de Custom Formats, Quality
Profiles, naming schemes pour Sonarr/Radarr/Lidarr). **Recyclarr** est l'outil
qui synchronise ces templates automatiquement vers les instances *arr via leur
API. **Hardlinks** est le pattern Docker/NFS qui permet aux *arr de déplacer
les fichiers sans les copier (économie d'espace). Les trois sont liés: Recyclarr
pousse les CF de TRaSH Guides → les *arr filtrent les releases → qBittorrent
télécharge → les *arr importent via hardlink (pas de copie).

- **TRaSH Guides**: repo `TRaSH-Guides/Guides`, dossier `docs/`. Contient les
  guides par app (Sonarr, Radarr, Prowlarr, Bazarr) + guides Downloaders
  (qBittorrent, Deluge, SABnzbd, NZBGet) + Misc + Plex + Guide-Sync (CF groups).
- **Recyclarr**: repo `recyclarr/recyclarr`, dossier `docs/`. Architecture interne,
  ADRs (architecture decision records), et références sur les trash IDs et CF groups.
- **Hardlinks**: pas de dépôt dédié. Documenté dans le wiki Servarr
  (`docker-guide.md`, `permissions-and-networking.md`). Dépend du mount Docker
  et du filesystem sous-jacent (ext4 local ou NFS).

## Routing Table

Load the reference file that matches the question domain. Always open the file before answering.

| Question domain | Reference file |
|---|---|
| TRaSH Guides — index général | `trash__index.md` |
| TRaSH Guides — Sonarr CF (collection) | `trash__Sonarr__sonarr-collection-of-custom-formats.md` |
| TRaSH Guides — Sonarr quality profiles | `trash__Sonarr__sonarr-setup-quality-profiles.md` |
| TRaSH Guides — Sonarr quality profiles (FR) | `trash__Sonarr__sonarr-setup-quality-profiles-french-fr.md` |
| TRaSH Guides — Sonarr naming scheme | `trash__Sonarr__Sonarr-recommended-naming-scheme.md` |
| TRaSH Guides — Sonarr file size settings | `trash__Sonarr__Sonarr-Quality-Settings-File-Size.md` |
| TRaSH Guides — Sonarr import/update CF | `trash__Sonarr__sonarr-import-custom-formats.md`, `trash__Sonarr__sonarr-how-to-update-custom-formats.md` |
| TRaSH Guides — Sonarr tips (merge, order, rename, remote path) | `trash__Sonarr__Tips__Merge-quality.md`, `trash__Sonarr__Tips__How-to-order-Quality-Source.md`, `trash__Sonarr__Tips__Sonarr-rename-your-folders.md`, `trash__Sonarr__Tips__Sonarr-remote-path-mapping.md` |
| TRaSH Guides — Sonarr language CF | `trash__Sonarr__Tips__How-to-setup-language-custom-formats.md` |
| TRaSH Guides — Radarr CF (collection) | `trash__Radarr__Radarr-collection-of-custom-formats.md` |
| TRaSH Guides — Radarr quality profiles | `trash__Radarr__radarr-setup-quality-profiles.md` |
| TRaSH Guides — Radarr quality profiles (FR) | `trash__Radarr__radarr-setup-quality-profiles-french-fr.md` |
| TRaSH Guides — Radarr naming scheme | `trash__Radarr__Radarr-recommended-naming-scheme.md` |
| TRaSH Guides — Radarr file size settings | `trash__Radarr__Radarr-Quality-Settings-File-Size.md` |
| TRaSH Guides — Radarr import/update CF | `trash__Radarr__Radarr-import-custom-formats.md`, `trash__Radarr__Radarr-how-to-update-custom-formats.md` |
| TRaSH Guides — Radarr tips | `trash__Radarr__Tips__Merge-quality.md`, `trash__Radarr__Tips__Radarr-rename-your-folders.md`, `trash__Radarr__Tips__Radarr-remote-path-mapping.md` |
| TRaSH Guides — Radarr language CF | `trash__Radarr__Tips__How-to-setup-language-custom-formats.md` |
| TRaSH Guides — Prowlarr (FlareSolverr, proxy, limited API) | `trash__Prowlarr__prowlarr-setup-flaresolverr.md`, `trash__Prowlarr__prowlarr-setup-proxy.md`, `trash__Prowlarr__prowlarr-setup-limited-api.md` |
| TRaSH Guides — Bazarr setup + scoring | `trash__Bazarr__Setup-Guide.md`, `trash__Bazarr__Bazarr-suggested-scoring.md` |
| TRaSH Guides — qBittorrent setup + paths + categories | `trash__Downloaders__qBittorrent__Basic-Setup.md`, `trash__Downloaders__qBittorrent__Paths.md`, `trash__Downloaders__qBittorrent__How-to-add-categories.md` |
| TRaSH Guides — Downloaders index + port forwarding | `trash__Downloaders__index.md`, `trash__Downloaders__port-forwarding-troubleshooting.md` |
| TRaSH Guides — Deluge / SABnzbd / NZBGet | `trash__Downloaders__Deluge__Basic-Setup.md`, `trash__Downloaders__SABnzbd__Basic-Setup.md`, `trash__Downloaders__NZBGet__Basic-Setup.md` |
| TRaSH Guides — Guide-Sync (CF groups) | `trash__Guide-Sync__index.md`, `trash__Guide-Sync__sonarr-cf-groups.md`, `trash__Guide-Sync__radarr-cf-groups.md` |
| TRaSH Guides — Recyclarr configs | `trash__Recyclarr__recyclarr-configs.md` |
| TRaSH Guides — Misc (docker-compose, x265 4K) | `trash__Misc__how-to-provide-a-docker-compose.md`, `trash__Misc__x265-4k.md` |
| TRaSH Guides — Plex (transcoding, client settings) | `trash__Plex__Tips__4k-transcoding.md`, `trash__Plex__Tips__Optimal-plex-client-settings.md` |
| TRaSH Guides — SQP (Streaming Quality Presets) | `trash__SQP__index.md` |
| Recyclarr — architecture (sync pipeline, CF pipeline) | `recyclarr__architecture__sync-pipeline-architecture.md`, `recyclarr__architecture__custom-format-pipeline.md` |
| Recyclarr — quality profile pipeline + state resolution | `recyclarr__architecture__quality-profile-pipeline.md`, `recyclarr__architecture__quality-profile-state-resolution.md` |
| Recyclarr — trash ID state system | `recyclarr__architecture__trash-id-state-system.md` |
| Recyclarr — ADRs (architecture decisions) | `recyclarr__decisions__architecture__*.md` |
| Recyclarr — product decisions (CF groups, profile ordering) | `recyclarr__decisions__product__*.md` |
| Recyclarr — reference (CF groups patterns) | `recyclarr__reference__trash-guides-cf-group-patterns.md` |
| Hardlinks — Docker guide (mount, volumes, hardlinks) | `servarr__docker-guide.md` |
| Hardlinks — permissions & networking (PUID/PGID, NFS) | `servarr__permissions-and-networking.md` |
| Hardlinks — VPN + Docker networking | `servarr__vpn.md` |
| Hardlinks — install script | `servarr__install-script.md` |
| Hardlinks — useful tools | `servarr__useful-tools.md` |
| **Jefe's field knowledge (gotchas)** | `00-gotchas-jefe.md` |

## Behavior Rule

**Never answer from memory about a configuration option, default value, or API field.**
Always open the corresponding reference file and cite the exact value. If the answer
is not in the reference files or the gotchas file, say so explicitly. Do not invent.

## Validation Questions

### Q1: Comment synchroniser les Custom Formats TRaSH Guides vers Radarr avec Recyclarr ?

**Réponse**: Recyclarr utilise un fichier `recyclarr.yml` qui définit quelles
configurations synchroniser. Pour Radarr, on spécifie l'instance (URL + API key)
et les CF/quality profiles à synchroniser depuis TRaSH Guides via les trash IDs.
Voir `trash__Recyclarr__recyclarr-configs.md` pour les exemples de config et
`recyclarr__architecture__sync-pipeline-architecture.md` pour le fonctionnement
interne du pipeline de sync.

### Q2 (contre-intuitive): Pourquoi mes hardlinks ne fonctionnent pas alors que j'utilise le même filesystem en Docker ?

**Réponse**: Avoir le même filesystem ne suffit pas — il faut que **media et
downloads soient sur le MÊME point de montage Docker**. Si vous avez deux volumes
séparés (`/mnt/nfs/media:/media` et `/mnt/nfs/downloads:/downloads`), Docker
les voit comme deux filesystems différents, même si physiquement c'est le même
NFS export. La solution est un seul mount: `/mnt/nfs/data:/data` avec media et
downloads en sous-dossiers. Voir `servarr__docker-guide.md` et `00-gotchas-jefe.md`.

### Q3: Les CF Groups de Recyclarr permettent-ils de désactiver un ensemble de Custom Formats en une seule ligne ?

**Réponse**: Oui. Recyclarr v6+ supporte les CF Groups, qui permettent d'activer
ou désactiver un groupe entier de Custom Formats via un seul identifiant dans
`recyclarr.yml`. La sémantique est "opt-in" (il faut explicitement inclure un
groupe pour l'activer). Voir `recyclarr__decisions__product__005-cf-group-opt-in-semantics.md`
et `recyclarr__decisions__product__006-cf-group-auto-sync-contract.md` pour les
détails.