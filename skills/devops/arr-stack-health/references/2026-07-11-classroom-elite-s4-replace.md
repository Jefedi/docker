# Classroom of the Elite S4 — Codec Audit & Replacement (2026-07-11)

## Situation

User reported that **Classroom of the Elite Season 4** episodes starting from E07 play with artifacts ("buguent comme les vieilles télés") in direct play on Jellyfin. Even x264 Tsundere-Raws releases (normally good) were reported as buggy.

## Initial File State (S4)

| Epi | Group | Codec | Size | Quality | Issue |
|-----|-------|-------|------|---------|-------|
| E01-E04 | MonoDiSC | **AV1** | ~180MB | WEBRip-1080p | ❌ AV1 unplayable on most clients |
| E05-E06 | Tsundere-Raws | x264 | ~1.4GB | WEBDL-1080p | ✅ Good |
| E07-E11 | Tsundere-Raws | x264 | ~1.4GB | WEBDL-1080p | Reported buggy despite x264 |
| E12-E16 | TLC | **x265** | ~300-600MB | WEBRip-1080p | ⚠️ x265 heavy on some clients |

## Action Taken

1. **Deleted files** for E07-E16 via Sonarr API (`DELETE /api/v3/episodefile/{fileId}`)
2. **Triggered EpisodeSearch** for all 10 episodes in one command via `POST /api/v3/command {"name":"EpisodeSearch","episodeIds":[...]}`
3. **Monitored command** via `GET /api/v3/command/{commandId}` — status goes `queued → started → completed`
4. **Found releases** from Tsundere-Raws CR (Crunchyroll source) in x264 for all episodes

## Stuck Queue Items

When monitoring `GET /api/v3/queue`:

| Episode | Status | Issue | Fix |
|---------|--------|-------|-----|
| E08-E10 | `warning` at 0% | Torrent had no seeders | `DELETE /api/v3/queue/{queueId}?removeFromClient=true&blocklist=false` then re-search |
| E13 | `completed` at 100% | "Unable to determine if file is a sample" | Same fix: remove from queue + re-search |

The re-search (`EpisodeSearch` command) found new seedable releases for E08-E09 immediately. E10 and E13 needed a bit more time but were found in the second pass.

## Result

14/16 episodes replaced with x264. Only E10 and E13 were still downloading when the user checked.

## Key API Endpoints Used

| Purpose | Endpoint |
|---------|----------|
| Find series | `GET /api/v3/series` |
| List episode files | `GET /api/v3/episodefile?seriesId=N` |
| List episodes (get IDs) | `GET /api/v3/episode?seriesId=N&seasonNumber=M` |
| Delete file | `DELETE /api/v3/episodefile/{fileId}` |
| Search for replacements | `POST /api/v3/command {"name":"EpisodeSearch","episodeIds":[...]}` |
| Monitor command | `GET /api/v3/command/{commandId}` |
| Monitor queue | `GET /api/v3/queue?includeSeries=true&includeEpisode=true` |
| Remove stuck queue item | `DELETE /api/v3/queue/{queueId}?removeFromClient=true&blocklist=false` |
| Check history | `GET /api/v3/history?page=1&pageSize=20&sortKey=date&sortDirection=descending&includeSeries=true&includeEpisode=true` |

## CF Scores Profile ("1080p Direct Play")

| CF | Score |
|----|-------|
| x264 / h264 (Direct Play) | +5000 |
| 1080p WEB-DL | +2000 |
| AAC | +3000 |
| AV1 | -5000 |
| x265 / h265 | -2000 |
| French Audio | +10000 |
| Multi French | +15000 |

The `AV1` -5000 penalty ensures x264 is preferred when both exist. But if ONLY AV1 exists for an episode (common right after airdate), Sonarr still grabs it. Solution: delete the AV1 file and re-search 24-48h later.

## Release Groups Found (Crunchyroll source)

| Group | Codec | Audio | Size |
|-------|-------|-------|------|
| Tsundere-Raws (AD) | x264 | MULTi AD (VF+VO) | ~1.45 GB |
| Tsundere-Raws (CR) | x264 | VOSTFR | ~1.37 GB |
