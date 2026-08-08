---
name: arr-library-cleanup
title: Arrr Library Cleanup (Sonarr and Radarr)
description: Identify and remove media entries without actual files from Sonarr and Radarr libraries via MCP tools. Covers monitored-but-empty series (Sonarr) and films-without-files (Radarr).
tags: [sonarr, radarr, media-library, cleanup, monitoring]
---

# Arrr Library Cleanup

Inspect and clean up media entries in Sonarr and Radarr that are monitored but have no files on disk. The user Jefe prefers quick, decisive bulk action — present the list, then execute on confirmation.

## Workflow

### 1. List All Items

**Sonarr:**
```python
# Use mcp_sonarr_sonarr_list_series() — returns ALL series in one response (~500KB)
# Parse the response via Python:
import json
data = json.loads(raw_response)
series_list = json.loads(data['result'])
```

**Radarr:**
```python
# Use mcp_radarr_radarr_api(method='GET', path='movie', query={"pageSize": 100})
# Radarr returns paginated results — loop with page param
```

### 2. Filter Empty Items

**Sonarr** — check `statistics.episodeFileCount`:
```python
empty_series = [s for s in series_list 
    if s.get('monitored') 
    and s.get('statistics', {}).get('episodeFileCount', 0) == 0
    and s.get('statistics', {}).get('totalEpisodeCount', 0) > 0
    and any(se.get('monitored') for se in s.get('seasons', []))]
```

**Radarr** — check `hasFile` and/or `sizeOnDisk`:
```python
empty_movies = [m for m in movies if not m.get('hasFile', True)]
```

### 3. Present to User

List the candidates grouped by category, ask for confirmation. Jefe prefers a compact title list — no long descriptions. Confirm before executing.

### 4. Delete on Confirmation

**Sonarr:** `mcp_sonarr_sonarr_api(method='DELETE', path=f'series/{id}', body='{}', query='{}')`
**Radarr:** `mcp_radarr_radarr_api(method='DELETE', path=f'movie/{id}', body='{}', query='{}')`

No disk space freed (0 files). Reversible only by re-adding.

## Reference Files

- `references/sonarr-api-fields.md` — detailed Sonarr API statistics fields
- `references/radarr-api-fields.md` — detailed Radarr API fields

## Pitfalls

- Sonarr `list_series` returns ALL series in one ~500KB response — parse with Python, don't read manually
- `statistics` is embedded in the list response only
- `monitored=True` at series level ≠ monitored seasons — check season-level too
- Upcoming series (status: "upcoming") may have `totalEpisodeCount: 1` — confirm before deleting
- Radarr `hasFile` may be absent on some entries — treat missing as false
- Always ask confirmation; Jefe confirms with a simple "oui"

### ⚠️ Private Trackers — CRITICAL
Jefe is on private trackers (C411, Torr9, Generation-Free, G3MINI). **NEVER delete, remove, stop, unmonitor, or modify any torrent** via API operations (DELETE, POST to queue/remove, unmonitor, etc.). This includes:
- Removing items from Sonarr/Radarr queue
- Deleting movie/series from library
- Removing or stopping torrents in qBittorrent
- Any destructive action against tracked/downloaded content

**Allowed:** read-only diagnostic operations only (GET queues, GET history, GET wanted/missing, GET torrents/info). Always confirm with user before any action that could affect tracker ratio.
