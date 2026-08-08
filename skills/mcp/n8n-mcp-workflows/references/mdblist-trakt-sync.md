# MDBList API as Trakt Proxy — Calendar Sync to Radicale

When the user's Trakt account has reached its community app connection limit (free tier = 1 app),
MDBList.com (already OAuth-connected to Trakt) serves as a proxy with a simple API key.

## Why MDBList Instead of Trakt API Directly

- Trakt free tier limits community app connections to **1** (user had 4/1)
- Creating a new Trakt OAuth app requires revoking an existing connection
- MDBList is likely already connected (user had it since before)
- MDBList API uses a simple **API key** (no OAuth flow needed)
- API key from: https://mdblist.com/preferences/ → section API Key
- Free tier: 1000 API requests/day (sufficient for hourly sync)

## Key Endpoints

### `/calendar/events` — Upcoming + Recent Episodes
```
GET https://api.mdblist.com/calendar/events?apikey=KEY&days=30
```
Returns `{ events: [...] }` where each event has:
- `id` — unique event ID (e.g. `"episode-7436557-2026-07-29"`)
- `type` — always `"episode"` (NO movie events in this endpoint)
- `start` — date string `"YYYY-MM-DD"`
- `title` — show title
- `episode_title` — episode title or `"Episode N"`
- `season_number`, `episode_number` — integers
- `is_watched` — boolean (filter `false` for upcoming only)
- `is_watchlist` — boolean
- `release_type` — `"episode"` (upcoming) or `"watched"` (past)
- `description` — nullable string
- `poster`, `image`, `backdrop` — TMDB image paths

**Filter logic**: `!is_watched && start >= today` gives upcoming unwatched episodes.

### `/watchlist/items/movie` — Watchlist Movies
```
GET https://api.mdblist.com/watchlist/items/movie?apikey=KEY
```
Returns `{ movies: [...], pagination: { total, has_more } }` where each movie has:
- `id` — TMDB ID
- `title`, `release_year`, `release_date` (`"YYYY-MM-DD"`)
- `status` — `"released"`, `"Released"`, or upcoming status
- `runtime`, `rating`, `last_watched_at`

**Filter logic**: `release_date >= today` gives upcoming/unreleased movies only.
Note: most watchlist movies are already released — the future-date filter is critical.

### `/watchlist/items/show` — Watchlist Shows
Returns `{ shows: [...] }` with `status` field: `"Returning Series"`, `"Ended"`, `"Canceled"`.

### `/upnext` — Next Episodes to Watch
Returns shows with progress info (`watched_episode_count`, `total_episode_count`).

### `/upnext/upcoming` — Shows with Upcoming New Episodes
Returns only shows with unaired future episodes (e.g. a show returning for season 2).

### `/upnext/watchlist` — Watchlist Shows with Next Episode Info
Returns watchlist shows with their first episode air date.

## User Information
```
GET https://api.mdblist.com/user?apikey=KEY
```
Returns username, API limits, rate limit info. Useful for verifying the key works.

## Workflow Architecture: Trakt Calendar Sync

**Workflow ID**: `6DfjzsWXe4I0u5os`
**Name**: "Trakt Calendar Sync"
**Schedule**: every 1 hour
**Target**: Radicale collection `0feb942c-776d-cef4-18a5-cb0d8bccd798` (SAME as Motorsport Calendar Sync — single unified calendar)

### Structure
```
[Schedule Trigger 1h]
  ├─ GET /calendar/events?days=30  → Code: filter unwatched+future → VEVENTs
  └─ GET /watchlist/items/movie    → Code: filter future release_date → VEVENTs
       └──── Merge (append) ───────┘
                     ↓
            Split in Batches → PUT to Radicale (same collection as motorsport)
```

### Key Differences from Motorsport Calendar Sync
- **Data source**: JSON API (MDBList) instead of iCal feed
- **Parsing**: Code node filters JSON events → builds VEVENTs manually (no regex parsing)
- **Two branches**: episodes + movies (motorsport has 3 iCal feeds)
- **Same Radicale collection**: user wants ONE calendar for everything (motorsport + Trakt)
- **Event UIDs**: `trakt-{event.id}` for episodes, `trakt-movie-{tmdb_id}` for movies

### VEVENT Format
Episodes use `📺` prefix, movies use `🎬` prefix in SUMMARY field.
All-day events (`DTSTART;VALUE=DATE:YYYYMMDD` — no time component).

### Code Node: Parse Episodes (key logic)
```javascript
const events = data.events || [];
const today = new Date().toISOString().split('T')[0];
const items = events
  .filter(e => !e.is_watched && e.start >= today)
  .map(e => {
    const uid = 'trakt-' + e.id;
    const summary = e.title + ' - ' + (e.episode_title || 'S' + e.season_number + 'E' + e.episode_number);
    // ... build ICS content
    return { json: { uid, icsContent, title: summary, date: e.start } };
  });
```

### Code Node: Parse Movies (key logic)
```javascript
const movies = data.movies || [];
const today = new Date().toISOString().split('T')[0];
const items = movies
  .filter(m => m.release_date && m.release_date >= today)
  .map(m => {
    const uid = 'trakt-movie-' + m.id;
    const summary = '🎬 ' + m.title + ' (' + (m.release_year || '') + ')';
    // ... build ICS content
    return { json: { uid, icsContent, title: summary, date: m.release_date } };
  });
```

## Pitfall: jsonQuery with expr() produces [object Object]

When using `specifyQuery: "json"` with `jsonQuery: '={{ { apikey: "..." } }}'` in an
HTTP Request node, n8n evaluates the expression to a JS object but then stringifies it
as `[object Object]` instead of valid JSON. Error at runtime:
```
The value in the "JSON Query Parameters" field is not valid JSON
"[object Object]" is not valid JSON
```

**Fix:** Put query params directly in the URL instead:
```
url: "https://api.mdblist.com/calendar/events?apikey=XXX&days=30"
```
Then use `updateNodeParameters` with `replace: true` to wipe ALL query-related params
(`sendQuery`, `specifyQuery`, `jsonQuery`). If you only set `sendQuery: false` without
`replace: true`, the stale `specifyQuery` and `jsonQuery` fields persist and cause
`INVALID_PARAMETER` warnings.

## Pitfall: CalDAV ATTACH for images — user rejected

The iCal `ATTACH;FMTTYPE=image/jpeg:<url>` property is valid per RFC 5545 but:
- **iOS Calendar**: shows as attachment link, NOT as inline thumbnail/icon in the grid
- **HA calendar card**: does not display images at all
- The iCal standard has no "thumbnail" or "icon" property — only `ATTACH` (attachment)

**User preference:** Don't add ATTACH for images — user explicitly said
"retire le alors je veux pas de piece joint". Keep VEVENTs clean with just
SUMMARY, DTSTART, UID, and optional DESCRIPTION.

## Credential Assignment

The `PUT to Radicale` node uses `httpBasicAuth` credential named "Radicale" — same credential
as the Motorsport Calendar Sync workflow. Must be assigned manually in n8n UI after creation
(the API cannot auto-assign generic credential types).

## Reusable for Other MDBList Data

The same API key + Radicale PUT pattern can sync:
- `/upnext` — "continue watching" reminders
- `/upnext/upcoming` — show return dates
- Any MDBList list items with dates

Just change the endpoint and adjust the Code node parsing logic.