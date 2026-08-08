---
name: spotify-library-management
category: media
description: "Dedup and clean up Spotify liked tracks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [spotify, library, dedup, cleanup, n8n, data-table]
    related_skills: [spotify, n8n-mcp-local-config]
---

# Spotify Library Management

Manage the user's Spotify liked tracks library: find and remove duplicates, bulk unlike, and synchronize state with n8n Data Tables. Use when user asks to remove duplicate songs, clean up liked tracks, or sync library state.

## When to use

- User asks to find/remove duplicates in their liked tracks (same song but live/concert/remix/best-of version)
- User wants to clean up their liked songs library
- User wants to bulk-remove tracks from their library
- User references their n8n Spotify backup/sync workflow or Data Table
- Spotify API is rate-limited but the user has an n8n Data Table backup of their library

## Prerequisites

- Hermes Spotify toolset (spotify_library, spotify_search, etc.)
- n8n MCP tools (mcp__n8n_mcp__search_workflows, mcp__n8n_mcp__execute_workflow, etc.)
- n8n REST API key at `/opt/data/.n8n_api_key` (header `X-N8N-API-KEY`)
- Load the `spotify` skill for basic tool reference

## Finding duplicates in liked tracks

### Step 1: Fetch all liked tracks
Paginate `spotify_library` with offset (50 per page) until a page returns < 50 items.

If Spotify is rate-limited (429 with long retry), **fall back to the n8n Data Table** (see below).

### Step 2: Normalize titles and artists
Strip variant suffixes to identify true duplicates. See `references/dedup-normalization.md` for the exact regex set. Key rules:
- Remove `(Live)`, `(Remix)`, `(Acoustic)`, `(Radio Edit)`, `(Remastered)`, `(Session)`, `(Deluxe)`, `(Version)` etc. from titles
- Remove `- Live`, `- Acoustic`, `- Remix` style suffixes
- Strip `feat`/`ft`/`featuring` from artist names
- Group by `normalized_artist + normalized_title`

### Step 3: Pick which version to keep
Priority order (highest first):
1. **Original studio album** — the album whose name matches the single/EP name, or the earliest studio release
2. **Standard edition** over Deluxe/Extended/Complete editions
3. **Earliest `added_at`** when albums are identical

Never keep best-of/compilation/greatest-hits/soundtrack versions when an original album version exists.

### Step 4: Present to user for validation
Always show the duplicate list with artist, title, album, and which version will be kept vs removed. **Do not delete without user confirmation.**

## Removing duplicates

### Rate-limit strategy
Spotify `429` with `Retry after N seconds` where N > 1800s means: **don't block the conversation, schedule a cron job**. Create a one-shot cron (~N minutes out) that:
1. Calls `spotify_library({kind: "tracks", "action": "remove", "ids": [...]})` with the duplicate track IDs
2. Triggers the n8n sync workflow to propagate deletions to the Data Table
3. Sends a report to the user

### Unlike call
```python
spotify_library({"kind": "tracks", "action": "remove", "ids": ["trackId1", "trackId2", ...]})
```
The `ids` parameter accepts bare Spotify track IDs (not full URIs).

## n8n Data Table as read cache

This user has an n8n workflow "Spotify Backup - Daily Sync" (ID: `IDq7NyfY6iXAdvzj`, active, schedule trigger at 8h) that syncs liked tracks and followed artists into n8n Data Tables. The workflow has 2 branches from the trigger:
1. **Liked Tracks**: Get Liked Tracks → Transform → Store (upsert to `spotify_saved_tracks`) → Get All Backup Tracks → Find Orphaned Tracks → Delete Orphaned Tracks (bidirectional sync)
2. **Followed Artists**: Get Followed Artists → Transform → Store (upsert to `spotify_followed_artists`)

The Data Table `spotify_saved_tracks` (ID: `JLXkrFmxTDYWcnNv`, project `saK2AvuDBGWYH4hl`) has columns: `track_id`, `track_name`, `artists`, `album`, `added_at`, `duration_ms`, `popularity`.

**Note**: The workflow previously had a Playlists branch (3rd parallel branch) that was removed on 2026-07-29 because a 403 Forbidden on the "Hermest ❤️" collaborative playlist killed the entire workflow. The `spotify_playlists` and `spotify_playlist_tracks` Data Tables still exist but are no longer populated.

### Reading tracks from the Data Table
The API path is `/api/v1/data-tables` (hyphenated), not `/api/v1/datatables`.

```
GET http://localhost:5678/api/v1/data-tables/JLXkrFmxTDYWcnNv/rows
```

**Cursor-based pagination** (not limit/offset):
- Default page size: 100 rows
- `?limit=N` does NOT work — returns 404. Use cursor pagination instead.
- Response: `{"data": [...rows], "nextCursor": "eyJ..."}`
- Loop: fetch with no params, then `?cursor={nextCursor}` until `nextCursor` is null

**Always use `localhost:5678`**, never the Pangolin-proxied URL — the proxy returns 403 on many endpoints.

See `references/n8n-datatable-api-quirks.md` for full API details.

### Critical: n8n Data Table REST API cannot DELETE rows
The n8n public REST API returns **404** on `DELETE /api/v1/data-tables/{id}/rows/{rowId}` — row deletion is not supported via REST. The MCP tools also lack a delete-rows operation.

**Workaround**: the sync workflow has a "Find Orphaned Tracks" → "Delete Orphaned Tracks" chain (using the internal `deleteRows` dataTable node operation) that removes Data Table rows for tracks no longer liked on Spotify. So the correct flow is:
1. Unlike on Spotify
2. Trigger the sync workflow via MCP: `mcp__n8n_mcp__execute_workflow({workflowId: "IDq7NyfY6iXAdvzj"})`
3. The workflow automatically cleans up the Data Table

### Triggering the sync workflow on demand
```
mcp__n8n_mcp__execute_workflow({ workflowId: "IDq7NyfY6iXAdvzj" })
```
Don't wait for the daily 8h schedule — trigger immediately after unlike operations.

## Pitfalls

- **Pangolin proxy blocks n8n API calls** — `n8n.jefe.ovh` returns 403 for many REST endpoints (DELETE, sometimes GET). Always use `http://localhost:5678` for n8n REST API calls.
- **Data Table row IDs are sequential integers** (1, 2, 3...) but DELETE still returns 404 — the endpoint simply doesn't exist in n8n CE.
- **The sync workflow IS bidirectional**: Spotify → Data Table (upsert liked tracks) AND Data Table → cleanup (delete orphaned rows for tracks no longer liked). Always unlike on Spotify first, then trigger the sync workflow to propagate the deletion to the Data Table.
- **Spotify rate limits can be very long** (54+ minutes). Don't block — use a cron job.
- **`spotify_library` `action: "remove"` uses `ids` not `uris`** — pass bare track IDs, not full URIs.
- **Workflow 403 on "Get Playlist Tracks" kills liked-tracks sync**: the workflow previously had 3 parallel branches from the schedule trigger (Playlists, Liked Tracks, Followed Artists). If the Playlists branch hit a 403 on a specific playlist (e.g., collaborative/restricted playlist "Hermest ❤️"), n8n killed the ENTIRE workflow before the Liked Tracks branch finished. **Resolved on 2026-07-29**: the entire Playlists branch was removed from the workflow (9 nodes deleted: Get User Playlists, Transform Playlists, Store Playlists, Loop Each Playlist, Set Playlist ID, Get Playlist Tracks, Transform Tracks, Store Playlist Tracks, Playlists Done). The workflow now has only 2 branches: Liked Tracks (upsert + orphan cleanup) and Followed Artists. The `spotify_playlists` and `spotify_playlist_tracks` Data Tables are now orphaned/unused. If playlist tracking is needed again, set `continueOnFail: true` on the Get Playlist Tracks node before re-adding the branch. See `references/n8n-datatable-api-quirks.md` for the workflow PUT API update procedure.
- **DT can be stale vs Spotify**: if the sync workflow has been erroring, the Data Table count will be HIGHER than the actual Spotify liked tracks count (tracks unliked since last successful sync remain as orphans in the DT). Always cross-check the DT count against Spotify's actual library count before treating the DT as source of truth.

## User preferences for this task

- **Always keep original studio albums**, never best-of/compilation/deluxe/single versions
- Present duplicates in a clear table format before deleting
- Respond in French for infra/media tasks
- Schedule automated cleanup via cron when rate-limited, don't make the user wait
- **Don't create cron jobs for short-fuse dedup/sync tasks** — the user finds cron jobs scheduled <1h out pointless. Instead, fix the sync workflow directly so it self-heals on its existing schedule. If a one-shot action is needed (e.g., wait for Spotify rate limit to pass), just use `sleep` in terminal rather than scheduling a cron job.

## n8n API access notes

- **REST API base**: `http://localhost:5678/api/v1/` (NOT `n8n.jefe.ovh` — Pangolin proxy returns 403 on many endpoints)
- **Data Tables endpoint**: `/api/v1/data-tables` (hyphenated, NOT `/api/v1/datatables`)
- **Workflow execution via MCP**: requires `executionMode: "production"` or `"manual"` (required param)
- See `references/n8n-datatable-api-quirks.md` for full API details and update procedures