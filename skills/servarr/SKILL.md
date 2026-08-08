---
name: servarr
description: >
  Servarr stack documentation expert. Covers Sonarr (TV), Radarr (films), Lidarr
  (musique), Prowlarr (indexers). Installation Docker, configuration, quality
  profiles, custom formats, API REST, permissions PUID/PGID, reverse proxy,
  hardlinks. Trigger words: sonarr, radarr, lidarr, prowlarr, servarr, arr,
  quality profile, custom format, indexer, PUID, PGID, hardlink.
---

# Servarr Documentation Skill

## Mental Model

Servarr = 4 apps PVR (Personal Video Recorder) built on the same .NET/ReactJS
base. **Sonarr** = TV series, **Radarr** = films, **Lidarr** = musique,
**Prowlarr** = indexers manager. Chaque app gère: metadata (sources TVDB/TMDB/
MusicBrainz), wanted list (search/download), library (rename/organize). Toutes
partagent la même API structure (V3 pour Radarr/Prowlarr, V1 pour Lidarr, V5
pour Sonarr v5), le pattern Docker (PUID/PGID, /data mount, hardlinks), et
l'UI ReactJS.

**Prowlarr** est le pivot: il gère les indexers (trackers/usenet) et les synchronise
vers les 3 autres via Settings > Applications. Sans Prowlarr, chaque app doit
gérer ses indexers individuellement.

**Recyclarr** (voir skill `media-stack`) pousse les Custom Formats TRaSH Guides
vers Sonarr/Radarr via leur API. Prowlarr gère les indexers, Recyclarr gère
la qualité, les *arr gèrent le workflow.

## Routing Table

Load the reference file that matches the question domain. Always open the file before answering.

| Question domain | Reference file |
|---|---|
| **Sonarr** — installation Docker | `sonarr__installation__docker.md` |
| Sonarr — installation Linux/Windows/macOS/Synology | `sonarr__installation__linux.md`, `sonarr__installation__windows.md`, `sonarr__installation__macos.md`, `sonarr__installation__synology.md` |
| Sonarr — reverse proxy | `sonarr__installation__reverse-proxy.md` |
| Sonarr — multiple instances | `sonarr__installation__multiple-instances.md` |
| Sonarr — quick start guide | `sonarr__quick-start-guide.md` |
| Sonarr — settings (all options) | `sonarr__settings.md` |
| Sonarr — library, importing | `sonarr__library.md`, `sonarr__importing-existing-library.md` |
| Sonarr — wanted, activity, calendar | `sonarr__wanted.md`, `sonarr__activity.md`, `sonarr__calendar.md` |
| Sonarr — system, environment vars | `sonarr__system.md`, `sonarr__environment-variables.md` |
| Sonarr — appdata directory | `sonarr__appdata-directory.md` |
| Sonarr — custom scripts, tips | `sonarr__custom-scripts.md`, `sonarr__tips-and-tricks.md` |
| Sonarr — FAQ, troubleshooting | `sonarr__faq.md`, `sonarr__faq-v4.md`, `sonarr__troubleshooting.md` |
| Sonarr — XEM guide | `sonarr__xem-guide.md` |
| Sonarr — Postgres setup | `sonarr__postgres-setup.md` |
| Sonarr — API (OpenAPI V5) | `sonarr-api-index.md` (index), `sonarr-openapi.json` (raw) |
| **Radarr** — installation Docker | `radarr__installation__docker.md` |
| Radarr — installation Linux/Windows/macOS | `radarr__installation__linux.md`, `radarr__installation__windows.md`, `radarr__installation__macos.md` |
| Radarr — reverse proxy, multiple instances | `radarr__installation__reverse-proxy.md`, `radarr__installation__multiple-instances.md` |
| Radarr — quick start guide | `radarr__quick-start-guide.md` |
| Radarr — settings, library, calendar | `radarr__settings.md`, `radarr__library.md`, `radarr__calendar.md` |
| Radarr — activity, system, env vars | `radarr__activity.md`, `radarr__system.md`, `radarr__environment-variables.md` |
| Radarr — appdata, custom scripts, tips | `radarr__appdata-directory.md`, `radarr__custom-scripts.md`, `radarr__tips-and-tricks.md` |
| Radarr — FAQ, troubleshooting | `radarr__faq.md`, `radarr__troubleshooting.md` |
| Radarr — Postgres setup | `radarr__postgres-setup.md` |
| Radarr — API (OpenAPI V3) | `radarr-api-index.md` (index), `radarr-openapi.json` (raw) |
| **Lidarr** — installation Docker | `lidarr__installation__docker.md` |
| Lidarr — installation Linux/Windows/macOS | `lidarr__installation__linux.md`, `lidarr__installation__windows.md`, `lidarr__installation__macos.md` |
| Lidarr — reverse proxy | `lidarr__installation__reverse-proxy.md` |
| Lidarr — quick start guide | `lidarr__quick-start-guide.md` |
| Lidarr — settings, library, wanted | `lidarr__settings.md`, `lidarr__library.md`, `lidarr__wanted.md` |
| Lidarr — calendar, activity, system | `lidarr__calendar.md`, `lidarr__activity.md`, `lidarr__system.md` |
| Lidarr — metadata, importing, naming | `lidarr__metadata-troubleshooting.md`, `lidarr__import-troubleshooting.md`, `lidarr__importing-existing-library.md`, `lidarr__naming-guide.md` |
| Lidarr — beets integration, plugins | `lidarr__beets-integration.md`, `lidarr__plugins.md` |
| Lidarr — env vars, appdata, concepts | `lidarr__environment-variables.md`, `lidarr__appdata-directory.md`, `lidarr__concepts.md` |
| Lidarr — FAQ, troubleshooting, tips | `lidarr__faq.md`, `lidarr__troubleshooting.md`, `lidarr__tips-and-tricks.md` |
| Lidarr — community guide, supported | `lidarr__community-guide.md`, `lidarr__supported.md` |
| Lidarr — API (OpenAPI V1) | `lidarr-api-index.md` (index), `lidarr-openapi.json` (raw) |
| **Prowlarr** — installation Docker | `prowlarr__installation__docker.md` |
| Prowlarr — installation Linux/Windows/macOS | `prowlarr__installation__linux.md`, `prowlarr__installation__windows.md`, `prowlarr__installation__macos.md` |
| Prowlarr — reverse proxy | `prowlarr__installation__reverse-proxy.md` |
| Prowlarr — quick start guide | `prowlarr__quick-start-guide.md` |
| Prowlarr — indexers, search, history | `prowlarr__indexers.md`, `prowlarr__search.md`, `prowlarr__history.md` |
| Prowlarr — settings, system, env vars | `prowlarr__settings.md`, `prowlarr__system.md`, `prowlarr__environment-variables.md` |
| Prowlarr — appdata, custom scripts | `prowlarr__appdata-directory.md`, `prowlarr__custom-scripts.md` |
| Prowlarr — Cardigann YML definition | `prowlarr__cardigann-yml-definition.md` |
| Prowlarr — supported indexers | `prowlarr__supported-indexers.md`, `prowlarr__supported.md` |
| Prowlarr — FAQ, troubleshooting | `prowlarr__faq.md`, `prowlarr__troubleshooting.md` |
| Prowlarr — Postgres setup | `prowlarr__postgres-setup.md` |
| Prowlarr — API (OpenAPI V1) | `prowlarr-api-index.md` (index), `prowlarr-openapi.json` (raw) |
| **Shared** — Docker guide (hardlinks, volumes) | `servarr__docker-guide.md` |
| Shared — permissions & networking (PUID/PGID, NFS) | `servarr__permissions-and-networking.md` |
| Shared — VPN + Docker networking | `servarr__vpn.md` |
| Shared — install script | `servarr__install-script.md` |
| Shared — useful tools | `servarr__useful-tools.md` |
| Shared — index | `servarr__index.md` |
| **Jefe's field knowledge (gotchas)** | `00-gotchas-jefe.md` |

## Behavior Rule

**Never answer from memory about a configuration option, default value, or API field.**
Always open the corresponding reference file and cite the exact value. If the answer
is not in the reference files or the gotchas file, say so explicitly. Do not invent.

## Validation Questions

### Q1: Comment configurer Prowlarr pour synchroniser un indexer vers Sonarr ?

**Réponse**: Prowlarr synchronise les indexers via Settings > Applications.
Il faut ajouter Sonarr comme Application avec son URL (ex: `http://sonarr:8989`)
et sa API key (trouvable dans `config.xml`). Une fois configuré, chaque indexer
ajouté à Prowlarr est automatiquement synchronisé vers Sonarr. Voir
`prowlarr__settings.md` et `prowlarr__indexers.md` pour les détails. Voir aussi
`00-gotchas-jefe.md` pour les notes spécifiques à l'infra de Jefe.

### Q2 (contre-intuitive): Pourquoi mes hardlinks ne fonctionnent pas alors que j'utilise le même filesystem en Docker ?

**Réponse**: Avoir le même filesystem ne suffit pas — il faut que **media et
downloads soient sur le MÊME point de montage Docker**. Si vous avez deux volumes
séparés (`/mnt/nfs/media:/media` et `/mnt/nfs/downloads:/downloads`), Docker
les voit comme deux filesystems différents, même si physiquement c'est le même
NFS export. La solution est un seul mount: `/mnt/nfs/data:/data` avec media et
downloads en sous-dossiers. Voir `servarr__docker-guide.md` et `00-gotchas-jefe.md`.

### Q3: Quelle est la différence entre l'API V3 et V5 de Sonarr ?

**Réponse**: Sonarr v5 introduit une nouvelle API V5 (`Sonarr.Api.V5`),
disponible dans `sonarr-api-index.md`. L'ancienne API V3 reste disponible mais
est deprecated. Radarr et Prowlarr utilisent toujours V3, Lidarr utilise V1.
Pour les nouveaux scripts, utiliser V5 pour Sonarr. Voir `00-gotchas-jefe.md`
section "Sonarr v4 vs v5".