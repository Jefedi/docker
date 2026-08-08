# Language Audit — VOSTFR → VFF Scan Results (2026-06-20)

## Context
Jefe noticed some series had VO-only audio (VOSTFR) instead of French dub (VFF). Scanned 1890 qBittorrent torrents + Sonarr episode files.

## Stats
- Total torrents: 1890
- < 1 month: 1282 (68%)
- \> 1 month: 608 (32%)
- TV torrents: 441 (135 recent, 306 old)

## Confirmed VOSTFR Series (needs VFF re-search)

### 1. Chicago PD (Sonarr ID=134)
- **Season 13** — 21 episodes (S13E01-E21)
- All `FASTSUB.VOSTFR` — English audio only, French subs
- Date range: April 2 → June 5, 2026 (all > 70h)
- Scene names: `Chicago.PD.S13E*.FASTSUB.VOSTFR.*`
- Custom formats: VOSTFR only (no VFF/MULTI)

### 2. FBI (Sonarr ID=81)
- **Season 8** — 19 episodes (S08E01-E19)
- All `FASTSUB.VOSTFR` — English audio only, French subs
- Date range: February 25 → April 30, 2026 (all > 70h)
- Scene names: `FBI.S08E*.FASTSUB.VOSTFR.*`
- Custom formats: VOSTFR only

### 3. The Rookie (Sonarr ID=87)
- **Season 8, partial** — 10 episodes in VOSTFR:
  - E01-E06, E09-E13 = VOSTFR (English only)
  - E07-E08, E14-E18 = MULTI ✅ (already has French)
- Date range: February → March 2026 (all > 70h)
- Season 7 is fully MULTI ✅

## Series confirmed OK (already MULTI/VFF)
- Tracker (ID=82) — all MULTI or MULTI VFF
- Blue Bloods (ID=222) — MULTI VFF
- Dutton Ranch (ID=228) — FRENCH VFF
- Landman (ID=57) — MULTI VFF
- The Rookie S07 — MULTI

## Animes with VOSTFR (VF unlikely for most)
Started identifying these but didn't complete the audit. These are typically VOSTFR because French dubs for anime are rare:
- One Piece (VOSTFR)
- Classroom of the Elite (VOSTFR)
- Jujutsu Kaisen (MULTI)
- Yomi no Tsugai (VOSTFR)
- That Time I Got Reincarnated as a Slime (VOSTFR)
- Frieren (MULTI)
- Witch Hat Atelier (MULTI AD)
- etc.

## Commands for re-search
```python
# Chicago PD S13 — season search
mcp_sonarr_send_command(name="SeasonsSearch", seriesId=134, seasonNumber=13)

# FBI S08 — season search
mcp_sonarr_send_command(name="SeasonsSearch", seriesId=81, seasonNumber=8)

# The Rookie S08 — episode search for VOSTFR episodes only
mcp_sonarr_send_command(name="EpisodeSearch", episodeIds=[8931, 8935, 8954, 8955, 11688, 11902, 14498, 15521, 15909, 17147, 17753])
```

## Sonarr Custom Format Reference (Jefe)
| ID | Name | Score | Meaning |
|---|---|---|---|
| 545 | VFF | +1000 | French dub |
| 554 | MULTI | +500 | Multi-audio (incl. French) |
| 555 | VOSTFR | -50 | VO + French subs |
| 553 | No-RlsGroup | -10000 | Missing group tag |
| 551 | x265 | +200 | HEVC bonus |
