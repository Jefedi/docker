# CrossWatch API Reference

CrossWatch syncs watchlists, history, ratings, and progress between media servers (Plex, Jellyfin, Emby) and trackers (Trakt, SIMKL, MDBList, AniList, TMDb). Self-hosted FastAPI app (v0.1.0).

- Base URL: variable per instance (`http://localhost:8787` locally, `https://crosswatch.<domain>` behind proxy)
- Auth: App-auth login (cookie-based) or optional X-API-Key header
- All requests/responses JSON unless noted
- Interactive docs at `GET /docs` or `GET /openapi.json`

## Auth Flow

CrossWatch uses app-auth with cookie-based sessions:

1. `POST /api/app-auth/login` with `{"username": "...", "password": "..."}` sets a session cookie
2. Subsequent requests include the cookie for auth
3. `GET /api/app-auth/status` returns auth state (`authenticated: bool`)

Optional: Bearer token via `X-API-Key` header if configured server-side.

## MCP Server (v2)

Built at `/root/.hermes/mcp/crosswatch_server.py` (53 tools, June 2026).

### Env Vars

| Env Var | Default | Description |
|---------|---------|-------------|
| `CW_BASE_URL` | `http://localhost:8787` | CrossWatch instance URL |
| `CW_INTERNAL` | `false` | `true` = direct HTTP; `false` = via docker exec tunnel |
| `CW_DOCKER_CMD` | `docker exec pangolin-cli` | Docker exec command for tunnel |
| `CW_COOKIE` | `""` | Session cookie (e.g. `session=abc123`) |
| `CW_AUTH_TOKEN` | `""` | Bearer token for X-API-Key header |

### Pangolin Private Resource Pattern

CrossWatch is behind Pangolin → route through Newt tunnel:
```
docker exec pangolin-cli curl -sk https://crosswatch.jefe.ovh/api/...
```

Set `CW_INTERNAL=false` (default) → `_req()` spawns `docker exec pangolin-cli curl -sk ...` via subprocess.
Set `CW_INTERNAL=true` → uses direct `httpx` to the raw URL.

### Tool Categories (53 tools)

| Category | Tools |
|----------|-------|
| **Auth** | `auth_status`, `auth_login`, `auth_logout`, `list_auth_providers` |
| **Insight** | `get_insights`, `get_stats_raw`, `get_stats` |
| **Watcher** | `watch_status`, `watch_currently_watching`, `watch_logs`, `watch_start`, `watch_stop` |
| **Sync** | `sync_providers`, `list_pairs`, `add_pair`, `delete_pair`, `sync_run`, `sync_run_summary`, `provider_counts` |
| **Maintenance** | `maintenance_provider_cache_status`, `maintenance_crosswatch_tracker_status`, `maintenance_clear_state`, `maintenance_clear_cache`, `maintenance_clear_metadata_cache`, `maintenance_restart` |
| **Media Providers** | `plex_status/libraries/users`, `jellyfin_libraries/users`, `emby_libraries/users` |
| **Metadata** | `metadata_providers`, `metadata_search`, `tmdb_art` |
| **Export** | `export_options`, `export_sample`, `export_file` |
| **Logs** | `logs_dump`, `logs_stream` |
| **Config** | `get_config`, `get_config_meta` |
| **Analyzer** | `analyzer_state`, `analyzer_problems`, `analyzer_ratings_audit` |
| **Snapshots** | `snapshots_manifest`, `snapshots_list`, `snapshots_read` |
| **Other** | `list_provider_instances`, `status`, `list_files`, `editor_state_providers`, `editor_pairs` |

## Endpoint Reference

### App Auth

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/app-auth/status` | Auth status (enabled, configured, authenticated, session_expires_at) |
| POST | `/api/app-auth/login` | Login (JSON body: username + password) |
| POST | `/api/app-auth/logout` | Logout |
| POST | `/api/app-auth/credentials` | Set credentials |

### Auth (provider OAuth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/providers` | List auth providers |
| POST | `/api/plex/pin/new` | Create Plex PIN |
| POST | `/api/plex/token/delete` | Delete Plex token |
| POST | `/api/jellyfin/login` | Jellyfin login (JSON) |
| GET | `/api/jellyfin/status` | Jellyfin auth status |
| POST | `/api/jellyfin/token/delete` | Delete Jellyfin token |
| POST | `/api/emby/login` | Emby login (JSON) |
| GET | `/api/emby/status` | Emby auth status |
| POST | `/api/emby/token/delete` | Delete Emby token |
| POST | `/api/mdblist/save` | Store MDBList credentials |
| POST | `/api/mdblist/disconnect` | Disconnect MDBList |
| POST | `/api/tautulli/save` | Store Tautulli credentials |
| POST | `/api/tautulli/disconnect` | Disconnect Tautulli |
| POST | `/api/trakt/pin/new` | Start Trakt OAuth PIN |
| POST | `/api/trakt/token/delete` | Delete Trakt token |
| POST | `/api/anilist/authorize` | Authorize AniList (JSON) |
| POST | `/api/anilist/token/delete` | Delete AniList token |
| POST | `/api/simkl/authorize` | Authorize SIMKL (JSON) |
| POST | `/api/simkl/token/delete` | Delete SIMKL token |
| GET | `/callback/anilist` | AniList OAuth callback |
| GET | `/callback` | SIMKL OAuth callback |

### Editor

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/editor/state/providers` | --- | List state providers |
| GET | `/api/editor` | kind, snapshot, source, provider, pair, dataset | Get editor state |
| POST | `/api/editor` | --- (JSON body) | Save editor state |
| GET | `/api/editor/pairs` | --- | List pairs |
| GET | `/api/editor/pairs/datasets` | kind, pair | List datasets |
| GET | `/api/editor/snapshots` | kind | List snapshots |
| GET | `/api/editor/state/manual/export` | --- | Export manual state |
| POST | `/api/editor/state/manual/import` | mode (multipart file) | Import manual state |
| GET | `/api/editor/export` | --- | Export editor state |
| POST | `/api/editor/import` | --- (multipart file) | Import editor state |
| GET | `/api/editor/state/import/providers` | --- | List import providers |
| POST | `/api/editor/state/import` | --- (JSON body) | Import state via API |

### Export

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/export/options` | --- | Export options |
| GET | `/api/export/sample` | provider, feature, limit, q | Sample export preview |
| GET | `/api/export/file` | provider, feature, format, q, ids | Export as file |

Params: `feature` = `watchlist|history|ratings`, `format` = `letterboxd|imdb|justwatch|yamtrack|tmdb`, `provider` = `TRAKT|PLEX|EMBY|JELLYFIN|SIMKL|MDBLIST|CROSSWATCH`

### Analyzer

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analyzer/state` | Analyzer state (pairs filter opt) |
| GET | `/api/analyzer/problems` | Analyzer problems |
| GET | `/api/analyzer/ratings-audit` | Ratings audit |
| GET | `/api/analyzer/cw-state` | CW tracker state |

### Insight

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/stats/raw` | --- | Raw stats |
| GET | `/api/stats` | --- | Processed stats |
| GET | `/api/insights` | limit_samples, history, runtime | Dashboard insights payload |

### Logging

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/logs/dump` | channel, n | Dump recent log lines |
| GET | `/api/logs/stream` | tag | Initial log stream |
| GET | `/api/logs/watcher` | tail, tags | Tail watcher logs |

### Maintenance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/maintenance/clear-metadata-cache` | Clear metadata cache |
| GET | `/api/maintenance/crosswatch-tracker` | Inspect CW tracker folder |
| POST | `/api/maintenance/clear-state` | Clear state.json |
| POST | `/api/maintenance/crosswatch-tracker/clear` | Clear tracker (body: clear_state, clear_snapshots bools) |
| POST | `/api/maintenance/clear-cache` | Clear provider cache |
| GET | `/api/maintenance/provider-cache` | Provider cache status |
| POST | `/api/maintenance/restart` | Restart CrossWatch |
| POST | `/api/maintenance/reset-currently-watching` | Reset "now playing" |
| POST | `/api/maintenance/reset-stats` | Reset stats (body: recalc, purge_* bools) |

### Media Providers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/plex/users` | Plex users |
| GET | `/api/plex/inspect` | Plex server inspect |
| GET | `/api/plex/libraries` | Plex libraries |
| GET | `/api/plex/pms/probe` | Plex PMS probe (timeout param) |
| GET | `/api/plex/pickusers` | Plex user picker |
| GET | `/api/jellyfin/inspect` | Jellyfin inspect |
| GET | `/api/jellyfin/libraries` | Jellyfin libraries |
| GET | `/api/jellyfin/users` | Jellyfin users |
| GET | `/api/emby/inspect` | Emby inspect |
| GET | `/api/emby/libraries` | Emby libraries |
| GET | `/api/emby/users` | Emby users |

### Metadata

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/metadata/providers` | --- | List metadata providers |
| GET | `/api/metadata/search` | q, typ, year, limit | Search movies/shows |
| GET | `/art/tmdb/{typ}/{tmdb_id}` | size, locale | TMDB artwork |

### Scrobbler / Watcher

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/plex/server_uuid` | --- | Plex server UUID |
| GET | `/api/plex/pms` | --- | Plex PMS info |
| GET | `/api/watch/currently_watching` | --- | Currently playing item |
| GET | `/api/watch/logs` | tail, tag, tags | Watcher logs |
| GET | `/api/watch/status` | --- | Watcher status |
| POST | `/api/watch/start` | provider, sink | Start watcher |
| POST | `/api/watch/stop` | --- | Stop watcher |

### Snapshots

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/snapshots/manifest` | Snapshot manifest |
| GET | `/api/snapshots/list` | List snapshots |
| GET | `/api/snapshots/read` | Read snapshot (path param) |

### Synchronization

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sync/providers` | List sync providers |
| GET | `/api/pairs` | List all pairs |
| POST | `/api/pairs` | Add pair (PairIn: source, target + optional mode, enabled, features) |
| POST | `/api/pairs/reorder` | Reorder pairs (body: array of string IDs) |
| PUT | `/api/pairs/{pair_id}` | Update pair (PairPatch body) |
| DELETE | `/api/pairs/{pair_id}` | Delete pair (purge_state query bool) |
| GET | `/api/sync/providers/counts` | Provider counts (max_age, force, source) |
| POST | `/api/run` | Run sync (optional JSON body) |
| GET | `/api/run/summary` | Run summary |

### Provider Instances

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/provider-instances` | All instances |
| GET | `/api/provider-instances/{provider}` | Instances for one provider |

### Probes

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/status` | fresh (0/1) | Service status |

### Files

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/files` | path (required) | List files in directory |

### Config

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config/meta` | Config metadata |
| GET | `/api/config` | Full config |
| POST | `/api/config` | Save config (JSON body) |
