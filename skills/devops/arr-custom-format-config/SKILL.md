---
name: arr-custom-format-config
description: Configure Radarr/Sonarr custom formats and quality profiles via REST API when MCP tools are insufficient. Covers x264/x265 scoring, backup-before-edit workflow, and payload construction for CF and profile creation.
tags: [radarr, sonarr, custom-format, quality-profile, api, arr-stack]
---

# Arr Custom Format & Quality Profile Configuration

Configure Radarr/Sonarr to prefer x264 1080p for direct-play compatibility across all devices, without transcoding.

## When to use

- User wants to change grab preferences (x264 > x265, 1080p > 4K)
- User wants to create/update custom formats or quality profiles
- MCP tools lack `createCustomFormat` — fallback to REST API via curl
- User asks about direct-play optimization for Jellyfin/Emby/Plex

## Workflow

### 1. Dump current state

Before any changes, read both apps in parallel to understand the current setup:

```bash
# Custom Formats
curl -s http://100.64.0.2:7878/api/v3/customFormat?apiKey=$RADARR_KEY | jq '.[] | {id, name}'

# Quality Profiles
curl -s http://100.64.0.2:7878/api/v3/qualityProfile?apiKey=$RADARR_KEY
```

For Sonarr, same pattern on port 8989.

### 2. Backup before modification

```bash
curl -s "http://100.64.0.2:7878/api/v3/qualityProfile?apiKey=$RADARR_KEY" > backup_radarr_profiles.json
curl -s "http://100.64.0.2:8989/api/v3/qualityProfile?apiKey=$SONARR_KEY" > backup_sonarr_profiles.json
curl -s "http://100.64.0.2:8989/api/v3/customFormat?apiKey=$SONARR_KEY" > backup_sonarr_customformats.json
```

### 3. Check if CF already exists

TRaSH guide formats may already be installed (e.g. Radarr "x265 (HD)" id:571, or Sonarr "x265" id:551). **Do not create duplicates** — reuse existing CF IDs.

### 4. Create custom formats via REST API

**MCP limitation**: `mcp_radarr_list_custom_formats` exists but there is NO `mcp_radarr_create_custom_format` tool. Use curl directly:

```bash
curl -s -X POST "http://100.64.0.2:7878/api/v3/customFormat?apiKey=$KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "x264",
    "includeCustomFormatWhenRenaming": false,
    "specifications": [{
      "name": "x264 Codec",
      "implementation": "ReleaseTitleSpecification",
      "implementationName": "Release Title",
      "infoLink": "https://wiki.servarr.com/radarr/settings#custom-formats-2",
      "negate": false,
      "required": true,
      "fields": [{
        "order": 0,
        "name": "value",
        "label": "Regular Expression",
        "helpText": "Custom Format RegEx is Case Insensitive",
        "value": "\\b(x264|h\\.?264|avc)\\b",
        "type": "textbox",
        "advanced": false,
        "privacy": "normal",
        "isFloat": false
      }]
    }]
  }'
```

For Sonarr, change port to 8989.

### 5. Create quality profile with format scores

**MCP limitation**: `mcp_radarr_create_quality_profile` only sets name, cutoff, upgrade_allowed, and language. It does NOT set formatItems (CF scores) or allowed qualities. Use REST API for full control.

Write the full payload to a temp file, then POST:

```bash
# Write payload
cat > /tmp/profile.json << 'JSONEOF'
{
  "name": "1080p Direct Play",
  "upgradeAllowed": true,
  "cutoff": 1002,
  "items": [
    {"quality": {"id": 9, "name": "HDTV-1080p", "source": "tv", "resolution": 1080}, "items": [], "allowed": true},
    {"quality": {"id": 7, "name": "Bluray-1080p", "source": "bluray", "resolution": 1080}, "items": [], "allowed": true},
    {"name": "WEB 1080p", "items": [
      {"quality": {"id": 3, "name": "WEBDL-1080p"}, "items": [], "allowed": true},
      {"quality": {"id": 15, "name": "WEBRip-1080p"}, "items": [], "allowed": true}
    ], "allowed": true, "id": 1002}
    # ... all other qualities set to allowed: false
  ],
  "formatItems": [
    {"format": 584, "name": "x264", "score": 200},
    {"format": 571, "name": "x265 (HD)", "score": -10000},
    {"format": 581, "name": "MULTI", "score": 500}
  ],
  "language": {"id": 2, "name": "French"}
}
JSONEOF

curl -s -X POST "http://100.64.0.2:7878/api/v3/qualityProfile?apiKey=$KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/profile.json
```

### 6. Update existing profiles

```bash
curl -s -X PUT "http://100.64.0.2:7878/api/v3/qualityProfile/$PROFILE_ID?apiKey=$KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/updated_profile.json
```

## Scoring strategy for direct-play

| Format | Score | Purpose |
|---|---|---|
| x264 | **+200** | Strongly prefer H.264 — direct play compatible |
| x265 / HEVC | **-10000** | Reject unless no x264 alternative exists (fallback) |
| MULTI / VFF / VOF | +500 to +1000 | Language preference (French) |
| VOSTFR | -50 | Slight penalty for subtitled-only |
| LQ / BR-DISK / 3D | -10000 | Block low-quality and unwanted types |

The -10000 on x265 is aggressive enough to be last-resort fallback: if **only** x265 exists, Radarr/Sonarr takes what has the best available score (still negative, but nothing better exists). Raise to -100000 to block x265 entirely.

## Key API details

| Service | Port | Auth |
|---|---|---|
| Radarr | 7878 | `?apiKey=` |
| Sonarr | 8989 | `?apiKey=` |

**Quality group IDs (standard)**:
- WEB 480p: 1000 / WEB 720p: 1001 / WEB 1080p: 1002 / WEB 2160p: 1003
- Radarr only: additional groups like "1080p Compact" use different IDs (check via GET)

**Individual quality IDs**:
- HDTV-1080p: 9
- Bluray-1080p: 7
- WEBDL-1080p: 3, WEBRip-1080p: 15

## Pitfalls

- **No MCP create-CF tool**: `list_custom_formats` exists but `create_custom_format` does not in the MCP plugin. Always use REST API for CF creation.
- **Quality profile MCP tool is too limited**: `create_quality_profile` via MCP only sets name/cutoff/language. For format scores and allowed qualities, use REST API with full payload.
- **New CF auto-added to existing profiles**: Creating a CF automatically adds it to ALL quality profiles with score 0. This is harmless (0 = neutral) but can confuse diff inspection.
- **Sonarr uses different quality source names**: `television` not `tv`, `webRip` not `webrip`, `blurayRaw` not `remux` — Radarr and Sonarr have subtle differences in quality source enums.
- **Cutoff vs cutoffFormatScore**: `cutoff` is the quality ID to stop upgrading at (e.g. 1002 for WEB-1080p). `cutoffFormatScore` is a separate score threshold for format-based cutoff — set to 0 if not needed.
- **Language field differs**: Radarr uses `"language": {"id": 2, "name": "French"}` while Sonarr language works differently (check actual API response).
