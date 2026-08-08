# Spotify Backup Verification

Pattern for verifying that an n8n Spotify backup workflow is correctly capturing all liked tracks with valid IDs.

## Verification Approach

When the user asks "check my n8n backup is working for liked tracks", the verification has two sides:

### 1. Live Spotify Data (from Hermes Spotify plugin)

```python
# Fetch all liked tracks via Spotify API
# spotify_library(action="list", kind="tracks", limit=50)
# Paginate through all results — the API returns `total` and `next` URLs
# Key fields per track: track.id, track.name, track.artists[].name, track.album.name, added_at
```

The Spotify plugin returns up to 50 tracks per call. For a full library (e.g. 321 tracks), you need 7 pages (offset 0, 50, 100, 150, 200, 250, 300).

### 2. n8n Backup Data (from n8n Data Tables API)

This requires n8n API access (see `references/n8n-access-from-hermes.md`). Without n8n API access, you can only report the live Spotify side and tell the user what to check.

#### Listing Data Table names and IDs

```bash
curl -sk "http://localhost:5678/api/v1/data-tables" \
  -H "X-N8N-API-KEY: <key>" -H "Accept: application/json"
# Returns: [{"name": "spotify_saved_tracks", "id": "JLXkrFmxTDYWcnNv"}, ...]
```

#### Fetching rows with cursor pagination

The Data Tables API uses **cursor-based pagination**, NOT offset. Max limit per page is 250.

```bash
# Page 1
curl -sk "http://localhost:5678/api/v1/data-tables/<table_id>/rows?limit=250" \
  -H "X-N8N-API-KEY: <key>"
# Returns: {"data": [...250 rows...], "nextCursor": "eyJsaW...}

# Page 2+
curl -sk "http://localhost:5678/api/v1/data-tables/<table_id>/rows?limit=250&cursor=<nextCursor>" \
  -H "X-N8N-API-KEY: <key>"
# Repeat until nextCursor is null
```

⚠️ **Do NOT use `offset` parameter** — returns HTTP 400 "must match format nanoid".
⚠️ **Table name does NOT work as ID** — the API requires the nanoid ID from the table listing.

### Comparison Checklist

When both sides are available, verify:

| Check | How |
|-------|-----|
| **Track count match** | `spotify_total` == `n8n_table_row_count` |
| **All track IDs present** | Set difference: `spotify_ids - n8n_ids` should be empty |
| **No orphan IDs in backup** | `n8n_ids - spotify_ids` should be empty (or explained by unliking) |
| **ID format valid** | Each ID is a 22-char base62 string, URI format `spotify:track:<id>` |
| **No null/empty IDs** | Filter for `track_id == ''` or `track_id == null` in backup |
| **Recent tracks captured** | Compare most recent `added_at` timestamps — if the latest like isn't in the backup, the workflow hasn't run recently |
| **Track names not fallback** | Check for "N/A", "Unknown", "inconnu" — indicates silent failure (see n8n-workflow-doctor silent failure pattern) |

### Common Issues Found During Verification

1. **Workflow hasn't run recently** — last execution is days/weeks old. Check if the schedule trigger is active.
2. **Pagination incomplete** — workflow fetches only first 50 tracks but library has 300+. The Spotify node needs `returnAll: true` or a pagination loop.
3. **Track IDs missing** — usually caused by the Loop Gotcha (see `spotify-backup-pattern.md`): playlist_id or track_id lost between nodes.
4. **Silent failures** — workflow status is "success" but rows contain empty/fallback values. See n8n-workflow-doctor silent failure diagnosis.
5. **OAuth credential expired** — workflow fails with 401 on the Spotify node. Re-authenticate in n8n UI.

## Spotify API Pagination (from Hermes plugin)

```python
# First call
result = spotify_library(action="list", kind="tracks", limit=50)
total = result["total"]  # e.g. 321
items = result["items"]

# Subsequent calls use offset
# spotify_library(action="list", kind="tracks", limit=50, offset=50)
# ... repeat until offset >= total
```

Key fields to extract per track:
- `track.id` — the Spotify track ID (22 chars)
- `track.name` — track name
- `track.uri` — full URI (`spotify:track:xxxxx`)
- `track.artists[].name` — artist names (join with ", ")
- `track.album.name` — album name
- `added_at` — when the track was liked (ISO datetime)
- `track.external_ids.isrc` — ISRC code (useful for cross-platform matching)