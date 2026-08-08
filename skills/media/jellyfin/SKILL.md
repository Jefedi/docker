---
name: jellyfin
description: Installer, configurer et dépanner Jellyfin — serveur multimédia libre. Couvre l'installation Docker, les réglages de transcodage, l'accès via reverse proxy, et les problèmes spécifiques aux clients (navigateurs, TV, apps).
---

# Jellyfin — serveur multimédia

Jellyfin est un serveur multimédia open-source. Ce skill couvre la configuration côté serveur et les problèmes de lecture côté client.

## Accès web

Une fois installé, accessible sur `http://IP:8096` ou via un sous-domaine Pangolin.

## Transcodage

### Réglages généraux (Dashboard → Playback → Transcoding)

- **Hardware acceleration** : à activer si le serveur a un GPU Intel QuickSync, NVIDIA NVENC, ou AMD VAAPI
- **Video codec** : laisser sur `Auto` par défaut
- **Allow encoding in MP4 container** : ✅ recommandé pour la compatibilité

### Problème : VIDAA OS (Hisense / Qilive / Toshiba)

Les TV sous **VIDAA OS** (Hisense, Sharp, Toshiba, Qilive par Auchan) ont un navigateur intégré avec des limitations :

| Problème | Cause | Solution |
|---|---|---|
| Vidéo lancée mais écran noir + pas de son | Le navigateur VIDAA ne supporte **pas le conteneur MKV** | Forcer le transcodage en H.264 MP4 |
| Transcodage CPU trop élevé | HEVC en MKV nécessite un transcodage complet | Activer le hardware acceleration si dispo |

**Solution rapide** (Dashboard → Playback → Transcoding) :

| Option | Valeur |
|---|---|
| Video codec | `H.264` (forcer au lieu de Auto) |
| Allow encoding in MP4 container | ✅ coché |
| Throttle transcode | ❌ décoché |

→ Jellyfin transcode alors tout le contenu en H.264 MP4, lisible par le navigateur VIDAA.

> **Alternative plus fiable** : utiliser un Chromecast / Fire Stick (~30€) avec l'app Jellyfin officielle du Play Store.

## Installation Docker

```yaml
services:
  jellyfin:
    image: lscr.io/linuxserver/jellyfin:latest
    container_name: jellyfin
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
    volumes:
      - ./config:/config
      - /path/to/media:/media:ro
    ports:
      - 8096:8096
      - 8920:8920  # (optional, HTTPS)
    devices:
      - /dev/dri:/dev/dri  # (optional, Intel QuickSync)
    restart: unless-stopped
```

## Exposition via Pangolin

Créer une ressource HTTP dans Pangolin avec SSL :

```bash
# Resource
PUT /v1/org/{orgId}/resource
{"name":"Jellyfin", "domainId":"...", "subdomain":"jflix", "http":true, "protocol":"tcp"}

# Target
PUT /v1/resource/{resourceId}/target
{"ip":"127.0.0.1", "port":8096, "siteId":6, "priority":100}
```

## Vérification

```bash
curl -I http://localhost:8096/web/
# Devrait retourner 200 ou 302
```

## Optimisation Direct Play & Formats

### Principe

Le **Direct Play** est l'objectif : le fichier est envoyé tel quel, 0% CPU, démarrage instantané. Si le client ne supporte pas le format, Jellyfin transcode (re-encode) à la volée → CPU + latence.

### Causes de transcodage

1. **Codec vidéo non supporté** — H.265 (HEVC) sur Firefox → transcode complet
2. **Bitrate limit** trop bas sur le client → transcode
3. **Sous-titres PGS/VobSub (image)** → burn-in = transcode (SRT passent en direct)
4. **Audio non supporté** (TrueHD/DTS sur navigateur) → transcode audio
5. **HDR → SDR** → transcode + tone mapping (très lourd sans GPU)

### Compatibilité codecs

| Codec | Chrome | Edge | Firefox | Safari | Android TV | Jelly TV | Stream Film (iOS) | Kodi/JMP |
|---|---|---|---|---|---|---|---|---|
| **H.264 (x264)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **H.265 (HEVC)** | ⚠️ | ✅* | ❌ (sauf 137+) | ✅ MP4 | ✅ | ⚠️ | ⚠️ | ✅ |
| AAC/AC3/EAC3 | ✅ | ✅ | ✅ | ✅ | ✅ |
| DTS/TrueHD | ❌ | ❌ | ❌ | Passthrough | Passthrough |

**Règle** : H.264 + AAC/AC3 = Direct Play sur **tous les clients**.

### Diagnostiquer

1. Dashboard → **Active Sessions** → Direct Play ou Transcode avec raison
2. Logs → chercher `TranscodingJob` ou consulter la config encoding :
   `GET /System/Configuration/encoding`
3. Vérifier `HardwareDecodingCodecs` — souvent "hevc" manque par défaut

### Hardware Acceleration (Intel VAAPI)

```
HardwareAccelerationType: vaapi
VaapiDevice: /dev/dri/renderD128
HardwareDecodingCodecs: h264, hevc, vc1, mpeg2video, vp9
  → Ajouter "hevc" si le GPU Intel le supporte !
EnableHardwareEncoding: true
AllowHevcEncoding: false  (force transcodage en x264 → meilleure compatibilité)
```

⚠️ **NE PAS oublier** "hevc" dans HardwareDecodingCodecs — sinon décode HEVC en **software** (très lent en 4K).

### Format par type de contenu

| Usage | Format | Audio | Taille |
|---|---|---|---|
| **Séries live** | **1080p WEB-DL x264** | EAC3/AC3/AAC | ~1-2 Go/ép |
| **Animés** | **1080p x264 MULTi AD** (VF si dispo) | AAC 2.0 | ~1.4 Go/ép |
| **Animés** (pas de Firefox) | **1080p x265 10bit** (Judas, ASW) | AAC 2.0 | ~300-500 Mo/ép |
| **Films** | 1080p x264 ou 2160p x265 (si GPU > 2Go) | EAC3/DTS/TrueHD | 3-15 Go |

**Pourquoi x264 pour les séries sur petit GPU Intel :**
- HEVC absent du HW decode → software = CPU saturé
- Firefox sans HEVC → transcode obligatoire
- x264 = HW decode + direct play = instantané

**Priorité audio :** EAC3 > AC3 > AAC > DTS > TrueHD (compromis qualité/compatibilité)

### Intégration Sonarr/Radarr

Profil "1080p x264 Direct Play" :
- ✅ Autoriser : WEBRip-1080p, WEBDL-1080p, Bluray-1080p (ou une sélection)
- ❌ Refuser : SDTV, DVD, 720p, 2160p, Remux, HEVC/x265
- Format custom (optionnel) : x264 scorage > 0
- Cutoff : WEB 1080p ou Bluray 1080p

API : `GET/POST /api/v3/qualityprofile`. Attention : le catch-all MCP Sonarr peut avoir un bug (URL mal construite) — utiliser les endpoints spécifiques.

### Références

- https://jellyfin.org/docs/general/clients/codec-support/
- https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/intel/
- https://jellywatch.app/blog/jellyfin-direct-play-vs-transcoding-explained-2026
- **`references/format-guide-by-content-type.md`** — format recommendations per content type (movies, series, anime) with TRaSH/Dictionarry/community consensus, including anime-specific x265 10bit rationale and decision tree for which format to pick given client constraints.

## Export & library queries

Use the Jellyfin API to export your full library for external trackers (Sofa, Letterboxd, Trakt):

→ **`references/export-library-csv.md`** — complete workflow: paginate all movies + episodes, extract ProviderIds (IMDb/TMDB), build a Sofa-compatible CSV. Key insight: export episodes only (not series-level rows) to avoid duplicates in Sofa.

Access via `skill_view('jellyfin', 'references/export-library-csv.md')`.

## Pièges

- **Don't trust that sample data = full library** — when a user pastes JSON, query the live API instead. Jellyfin's `GET /Items` with pagination is authoritative.
- **Anime x265 10bit n'est PAS un mauvais encode** contrairement aux x265 de séries live. Les groupes anime (Judas, ASW) font du vrai bon travail. Le problème c'est la compatibilité client (Firefox), pas la qualité. TRaSH lui-même ne bloque pas x265 pour l'anime.
- **Ne pas mélanger profil Sonarr série et anime** — les x265 anime sont légitimes, les x265 live action souvent des micro-encodes pourris. Faire deux profils distincts.
- Le navigateur VIDAA **ne lit pas le MKV** — forcer H.264 MP4
- HEVC pas dans HardwareDecodingCodecs par défaut → vérifier et ajouter
- Firefox ne supporte PAS le HEVC natif (sauf FF 137+ Linux avec ffmpeg)
- 4K HDR tone mapping sans GPU = serveur inutilisable (100% CPU)
- Bitrate client réglé trop bas = cause #1 de transcodage accidentel
- PGS sous-titres = transcode obligatoire (utiliser SRT)
- Vérifier format audio : TrueHD/DTS sur navigateur = transcode audio
