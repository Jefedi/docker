# Wistoria S2 Hardlink/Cross-Seed Block — June 29, 2026

## Problem

Wistoria: Wand & Sword S02 E06-12 files were corrupted (Tsundere-Raws x264 MULTi AD). After deleting the episode files from Sonarr and re-monitoring, Sonarr's SeasonSearch found nothing — even though Prowlarr confirmed the exact releases existed on Torr9 with 55-69 seeders.

## Root Cause

The old corrupted torrents were **still in qBittorrent** (seeding at 100%, category: `tv`). Even though Sonarr's hardlinks were deleted, qBittorrent's original files + Cross-seed hardlinks kept the data alive on disk. When Sonarr tried to grab the same infohash, it saw "already in client" and skipped.

## Affected qBittorrent Torrents

| Hash (full) | Name | State |
|---|---|---|
| `282cb86846b1a7150f0ee2673c9469ca8caf73e1` | Wistoria Wand and Sword S02E04 MULTi AD x264-Tsundere-Raws | stalledUP |
| `2ef02d388a0c6c0f9d3a9b94d76e9ad589f49e5b` | Wistoria Wand and Sword S02E07 MULTi AD x264-Tsundere-Raws | stalledUP |
| `f934a02134c2b3ab818f9ec772773645ae55c7d4` | Tsue.to.Tsurugi.no.Wistoria.S02E05.VOSTFR.x265-KAF | stalledUP |
| `def252ab9927be9ceb696398569d2921426c0dee` | Tsue.to.Tsurugi.no.Wistoria.S02E10.VOSTFR.x265-KAF | stalledUP |
| `ec32477b2aef288e89f923480e9a221ac06867a6` | Tsue to Tsurugi no Wistoria S02E10 VOSTFR x265 10bit AAC | stalledUP |
| `ba2120f0464fc437994106116382935bb6db9a75` | Wistoria S02E09 AV1 MonoDiSC | downloading 22% |

## Fix Applied

1. **Deleted from qBittorrent** via `POST /api/v2/torrents/delete` with `deleteFiles=false` (preserves cross-seed hardlinks)
2. **Episode files already removed** from Sonarr (were just hardlinks)
3. **Re-monitored episodes** (auto-unmonitored by Sonarr on file deletion)
4. **New SeasonSearch** triggered at 2026-06-29T19:54

## Related: Office Romance (Radarr) — x265 → x264 Replacement

### Current State
- **File:** `Office.Romance.2026.MULTi.VFF.1080p.WEB.HDR10.AAC.Atmos.H265-EAGLE.mkv`
- **Radarr profile:** 4KLight VFF (ID: 10) — x265 +300, VFF +1000, MULTI +500
- **Score with x265+VFF+MULTI:** 1800 (cutoffFormatScore=500, met ✅)
- **Problem:** x265 → transcoding on Firefox → very slow

### x264 Alternatives on Trackers

| Release | Tracker | Size | Seeders | Score (x264+VFF+MULTI) |
|---|---|---|---|---|
| FW | C411 | 5.96 GB | 123 | 1500 ✅ |
| THESYNDiCATE | C411 | 5.96 GB | 20 | 1500 ✅ |
| HiggsBoson | G3MINI | 5.4 GB | 5 | 1500 ✅ |

### x265 vs x264 Score Conflict
- x265 releases get +300 bonus → score 1800-1900
- x264 releases get no codec bonus → score ~1500
- Radarr **always prefers x265** even when x264 exits with same VFF+MULTI CFs
- **Workaround:** Delete x265 from qBittorrent + Radarr, add x264 torrent directly to qBittorrent via Prowlarr download URL
- **Longer fix:** Lower x265 score to 0 or negative in the Radarr quality profile

## Radarr Profile Values (4KLight VFF, ID: 10)

Same CF scoring as Sonarr FR-MULTi-VF-WEB-1080p:
- x265 (HD): +300
- VFF: +1000
- VOF: +900
- VFI: +800
- VF2: +700
- MULTI: +500
- VFQ: +200
- VQ/VFB: +100
- TrueHD ATMOS: +100
- DTS X: +100
- DD+ ATMOS: +100
- TrueHD: +50
- ATMOS (undefined): +50
- VOSTFR: -50
- LQ: -10000
- LQ (Release Title): -10000
- BR-DISK: -10000
- 3D: -10000
- Over 20 GB: -10000

## Confirmed x264-Only Rule (June 2026)

**All content** (films, séries, animés) must be x264 for cross-client compatibility:
- Firefox → NO x265 support
- Chrome/Edge → x265 partial, not everywhere
- Jellyfin native app → x265 OK
- Jelly TV (mobile) → depends on device
- Stream Film (iOS) → x265 OK on recent devices
- Multiple users with various browser setups

This applies to both Sonarr **and** Radarr profiles.

- `cutoffFormatScore`: 500
- `minFormatScore`: 0
- `minUpgradeFormatScore`: 1
- `cutoff`: 1004 (Bluray|WEB 1080p group)

### Custom Format Scores

| Format | ID | Score | 
|---|---|---|
| VFF | 545 | +1000 |
| VOF | 546 | +900 |
| VFI | 547 | +800 |
| VF2 | 548 | +700 |
| MULTI | 554 | +500 |
| x265 | 551 | +300 |
| VFQ | 549 | +200 |
| VQ | 550 | +100 |
| VOSTFR | 555 | -50 |
| LQ | 552 | -10000 |
| No-RlsGroup | 553 | -10000 |

**Note:** x265 is POSITIVE (+300) in this profile, not negative. The earlier "x265 rejected" assumption was wrong — the profile actually encourages x265 slightly.

### Title Scoring Examples

**Tsundere-Raws MULTi AD x264:** MULTI (+500) + no VOSTFR/x265/VFF CF match = score **500** (= cutoffFormatScore ✅)

**KAF x265 VOSTFR:** x265 (+300) + VOSTFR (-50) = score **250** (< cutoffFormatScore, but above minFormatScore=0 ✅)

## Release Stats on Nyaa.si (Public)

| Group | Format | Audio | Size | Seeders |
|---|---|---|---|---|
| Tsundere-Raws | x264 MULTi AD | VF+JA+VOSTFR | 1.4 GiB | 108-402 |
| Erai-raws | x265 HEVC MultiSub | JA + multi subs | 556 MiB | 159 |
| Anime Time | x265 10bit Dual-Audio | JA+EN + multi subs | 562 MiB | 59 |
| KAF (batch) | x265 10bit VOSTFR | JA + FR subs | ~300 MiB each | 41 |
| VARYG | x264 DUAL | JA+EN + multi subs | 1.4 GiB | varies |
