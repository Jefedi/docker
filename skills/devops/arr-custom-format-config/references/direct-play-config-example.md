# Direct-Play x264 Config — Example from Jefe's Arr Stack

## Custom Formats

### x264 (created via API)

```json
{
  "name": "x264",
  "includeCustomFormatWhenRenaming": false,
  "specifications": [{
    "name": "x264 Codec",
    "implementation": "ReleaseTitleSpecification",
    "negate": false,
    "required": true,
    "fields": [{
      "value": "\\b(x264|h\\.?264|avc)\\b"
    }]
  }]
}
```

### x265/HEVC (already existed — TRaSH guide)

Radarr: `"x265 (HD)"` id:571 — regex `[xh][ ._-]?265|\bHEVC(\b|\d)` (excludes 2160p)
Sonarr: `"x265"` id:551 — same regex, excludes BlurayRaw source

## Profile: "1080p Direct Play"

| Property | Radarr (id:16) | Sonarr (id:20) |
|---|---|---|
| Qualities enabled | HDTV-1080p, Bluray-1080p, WEB-1080p | Same |
| Qualities disabled | All 720p, 480p, DVD, 4K, Remux, Raw-HD | Same |
| Cutoff | WEB-1080p (group 1002) | Same |
| Language | French (id:2) | French (id:2) |

### Format scores

| CF | Score | Purpose |
|---|---|---|
| x264 (Radarr:584 / Sonarr:556) | +200 | Prefer H.264 native |
| x265 (Radarr:571 / Sonarr:551) | -10000 | Reject HEVC, fallback only |
| MULTI (Radarr:581 / Sonarr:554) | +500 | French multi-audio preferred |
| VFF | +1000 | TrueFrench |
| VOF | +900 | Original French |
| VFI | +800 | French international |
| VF2 | +700 | Dual French |
| VFQ | +200 | Canadian French |
| VQ / VFB | +100 | Québécois / French Belgian |
| VOSTFR | -50 | Subtitled-only penalty |
| LQ | -10000 | Low quality groups |
| Over 20 GB (Radarr only) | -10000 | Oversized |
| BR-DISK / 3D | -10000 | Unwanted formats |
| TrueHD / TrueHD ATMOS / DTS X / DD+ ATMOS / ATMOS | +50 to +100 | Audio bonus (minor) |

## API key files

```bash
RADARR_KEY=$(cat ~/.hermes/radarr_api_key.txt)
SONARR_KEY=$(cat ~/.hermes/sonarr_api_key.txt)
```

## Result behaviour

```
x264 1080p MULTi FR  → x264+200 + MULTI+500 + VFF+1000  = +1700 ✅ GRAB
x265 1080p MULTi FR  → x265-10000 + MULTI+500 + VFF+1000 = -8500  ❌ Blocked
x264 1080p ENGLISH   → x264+200                            = +200   ✅ Fallback GRAB
x265 1080p ENGLISH   → x265-10000                          = -10000 ❌ Last resort fallback
```
