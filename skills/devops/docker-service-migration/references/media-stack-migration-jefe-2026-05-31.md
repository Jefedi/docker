# Media Stack Migration: JNas → AX42 — Session Reference

## Source Host (JNas — UGREEN NAS)
- **IP**: 100.64.0.4 (Headscale)
- **Storage path**: `/volume1/media center/media-center/` (note the space!)
- **Compose**: `/srv/docker/media-center/compose.yaml`
- **Services**: Gluetun (ProtonVPN), qBittorrent, Jackett, Flaresolverr, Sonarr, Radarr, Cross-seed, Prowlarr, Lidarr, Spotarr, Bazarr, Janitorr
- **Network mode**: All *arr + qbit behind `network_mode: service:gluetun`, Janitorr in `network_mode: host`

## Target Host (AX42 — Debian Trixie)
- **IP**: 100.64.0.2 (Headscale)
- **NFS mount**: `/mnt/media-center-nfs/media-center/` → JNas's `/volume1/media center/media-center/`
- **.env**: `COMMON_PATH=/mnt/media-center-nfs/media-center`
- **Existing compose**: `/srv/docker/media-center/compose.yaml` (Jellyfin, Wizarr, Seerr, Jellystat+PG)

## Storage Layout (on JNas, same via NFS on AX42)
```
/volume1/media center/media-center/
├── qbittorrent/downloads/   ← downloads
├── sonarr/                   ← TV series
├── radarr/                   ← Movies
├── lidarr/                   ← Music
├── media/                    ← Final media (read by Jellyfin)
│   ├── Movies/
│   ├── Series/
│   └── Music/
├── configs/                  ← Docker configs for ALL services
│   ├── gluetun/
│   ├── qbittorrent/
│   ├── sonarr/
│   ├── radarr/
│   ├── prowlarr/
│   ├── lidarr/
│   ├── spotarr/
│   ├── bazarr/
│   ├── cross-seed/
│   ├── janitorr/
│   ├── jackett/
│   └── flaresolverr/
```

## Migration Constraints
- **Zero data loss**: The prompt explicitly enforces "NE RIEN PERDRE"
- **Parallel validation**: Both stacks can run simultaneously against the same NFS storage
- **48h validation**: After migration, leave source running for 48h before cleanup
- **Rollback**: Stop target service → restart source service — instant rollback per service

## Compose Adaptation Rules
1. Replace `/volume1/media center/media-center:/data` → `/mnt/media-center-nfs/media-center:/data`
2. Bind Gluetun ports to `127.0.0.1:` on AX42 (was `0.0.0.0` on JNas)
3. Gluetun volumes: use NFS path instead of local `./configs/gluetun:/gluetun`
4. Janitorr stays `network_mode: host` — can reach Jellyfin (localhost:8096) and *arr (127.0.0.1 bound ports)

## Key Verification Steps
1. NFS mount active: `df -h /mnt/media-center-nfs/media-center/`
2. Hardlinks work over NFS: `touch a; ln a b; ls -li a b` — inodes must match
3. Each service responds: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>`
4. Sonarr/Radarr root folders point to `/data/sonarr`, `/data/radarr` and show existing content
5. qBittorrent WebUI shows existing torrents still seeding
6. Janitorr logs show clean connections to both Jellyfin and *arr services

## Claude Code Prompt Delivery
The full instruction prompt was written to `/root/.hermes/cache/prompt_migration_media.txt` and delivered to the user as a file attachment via Telegram.
