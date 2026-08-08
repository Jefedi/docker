# Media Quality Audit

Auditing and improving the media library — detecting VOSTFR files in Sonarr that should be VF/VFF, analyzing movie format distribution, and triggering targeted re-searches.

## Prerequisites

- Hermes MCP servers: `sonarr-mcp-server`, `radarr-mcp-server`, `qbittorrent-mcp-server`
- Tools: `mcp_sonarr_list_episode_files`, `mcp_radarr_search_releases`, `mcp_qbittorrent_sync_maindata`

## TV Series: VOSTFR → VF Upgrade

Detect episodes downloaded in VOSTFR (English/VO audio, French subtitles) instead of VF (French dub), then re-search for MULTi/VFF releases.

**This is covered by Pattern F (Language Audit) in the main arr-stack-health SKILL.md.** See the parent skill for the full workflow, Sonarr custom format scoring table, and caveats.

### Additional notes

- **Jefe's preferred format:** 1080p x264 MULTi VFF EAC3/AC3 (direct play compatible)
- **Sonarr profile priority:** VFF=+1000, VOSTFR=-50
- **Age filter:** Only touch files > 70h old
- **Anime:** rarely have VF — only check mainstream titles (Jujutsu Kaisen, One Piece, etc.)

## Movies: Format & Seed Analysis

Analyze movie file formats against community seed counts to identify the best quality/size/playability trade-off.

### Workflow

1. **Get current distribution** from qBittorrent: `mcp_qbittorrent_sync_maindata(rid=0)`
   - Extract torrents by category (`movies`, `radarr`)
   - Analyze names for resolution (2160p/1080p), codec (x264/x265), size

2. **Sample release search** on popular movies:
   - `mcp_radarr_lookup_movie(term="Movie Name")` → get movie ID
   - `mcp_radarr_search_releases(movie_id=N)` → parse seed counts by format

3. **Interpret:** Most seeders + releases = community favorite format

### Best Format (from real data)

```
Movies → 2160p 4KLight HDR x265 MULTi VFF | 5-8 GB | Seeders: 50-236
```

This format dominates seed counts, has great 4K HDR quality, compact size, and French audio included.

### Jefe's Movie Preference

- **Format:** 4KLight x265 MULTi VFF
- Already using community-favorite format for movies

## References

- `sonarr-mcp-server` skill: Sonarr MCP tool documentation
- `radarr-mcp-server` skill: Radarr MCP tool documentation
- `qbittorrent-mcp-server` skill: qBittorrent MCP tool documentation

## Absorbed from

This file was absorbed from the `media-quality-audit` skill (archived). The `arr-stack-health` parent skill covers all arr-stack diagnostics; this reference adds the movie format analysis methodology that was unique to the older skill.
