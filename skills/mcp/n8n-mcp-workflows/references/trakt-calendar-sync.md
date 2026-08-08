# Trakt API → Radicale Calendar Sync

Syncs upcoming TV episodes and movie releases from Trakt to Radicale, same
pattern as the Motorsport Calendar Sync. Trakt's calendar endpoints already
filter to content the user watches/collects/watchlists — no manual "is this
still in production?" check needed.

## Trakt API Authentication (Device Flow)

### Create an app
- Go to https://trakt.tv/oauth/applications/new
- Name: anything (e.g. "n8n Calendar Sync")
- Redirect URI: `urn:ietf:wg:oauth:2.0:oob` (or any placeholder)
- Save → get `client_id` and `client_secret`

### Device flow (no browser redirect needed)
```bash
# Step 1: Request device codes
curl -s -X POST https://api.trakt.tv/oauth/device/code \
  -H "Content-Type: application/json" \
  -d '{"client_id":"<client_id>"}'
# Returns: device_code, user_code, verification_url, expires_in, interval

# Step 2: User goes to verification_url (https://auth.trakt.tv/activate)
# and enters the user_code

# Step 3: Poll for access token (at `interval` seconds)
curl -s -X POST https://api.trakt.tv/oauth/token \
  -H "Content-Type: application/json" \
  -d '{"code":"<device_code>","client_id":"<client_id>","client_secret":"<client_secret>"}'
# Returns 200 with access_token + refresh_token when authorized
# Returns 400 while pending (keep polling)
```

### Required headers for all API calls
| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `trakt-api-version` | `2` |
| `trakt-api-key` | `<client_id>` |
| `Authorization` | `Bearer <access_token>` |

### Token refresh
access_token expires in 7 days. Refresh with:
```bash
curl -s -X POST https://api.trakt.tv/oauth/token \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>","client_id":"<client_id>","client_secret":"<client_secret>","grant_type":"refresh_token"}'
```

## Key API Endpoints for Calendar Sync

### User calendar — shows (upcoming episodes)
```
GET /calendars/my/shows/{start_date}/{days}
```
- `target`: `my` (authenticated user's watched/collected/watchlisted shows) or `all` (global)
- `start_date`: `YYYY-MM-DD` (use today)
- `days`: integer (e.g. 30 for next 30 days)
- `extended=full` for episode titles, `extended=full,images` for artwork
- Supports filters: `ignore_watched`, `ignore_collected`, `ignore_watchlisted`, `genres`, etc.
- Returns array of `{first_aired, episode: {season, number, title, ...}, show: {title, year, ids: {trakt, slug, imdb, tmdb}}}`

### User calendar — movies (upcoming releases)
```
GET /calendars/my/movies/{start_date}/{days}
```
- Same target/date/days params as shows
- Returns array of `{released, movie: {title, year, ids: {...}}}`

### User watchlist (all media)
```
GET /users/me/watchlist/movie,show/{sort}
```
- `sort`: `rank`, `added`, `title`, `released`, `popularity`, etc.
- Returns array of `{rank, id, listed_at, type, movie/show: {...}}`
- Can filter with `hide=ended` to exclude ended shows, or `hide=unreleased` for movies

## Pitfall: Trakt Free Tier App Connection Limit

**Free tier allows only 1 community app connection.** The user hit a 4/1 limit
(Trakii, mdblist.com, Sofa Time iOS, Simkl already connected). When the device
flow activation page shows "Limite de connexions atteinte", the user must:

1. Go to https://app.trakt.tv → Settings → Applications → Connected Applications
2. Revoke one existing app ("Révoquer l'accès")
3. Retry the device flow activation

VIP tier increases the limit. The limit is per-Trakt-account, not per-app.

## Workflow Design (n8n → Radicale)

Same multi-source pattern as Motorsport Calendar Sync:

```
[Schedule Trigger 6h]
  ├─ GET /calendars/my/shows/{today}/30  → Code: JSON → VEVENTs
  └─ GET /calendars/my/movies/{today}/90 → Code: JSON → VEVENTs
       └──────── Merge (append) ──────────┘
                     ↓
            Split in Batches → PUT Radicale (same collection)
```

### Code node: Trakt JSON → iCal VEVENTs

For shows, each item has `first_aired` (ISO datetime), `episode.title`,
`episode.season`, `episode.number`, `show.title`. Build a VEVENT:
```javascript
const items = $input.all().map(i => i.json);
const events = items.filter(item => item.first_aired).map(item => {
  const uid = `trakt-show-${item.show.ids.trakt}-S${item.episode.season}E${item.episode.number}`;
  const dtstart = item.first_aired.replace(/[-:]/g, '').split('.')[0] + 'Z'; // UTC basic
  const summary = `${item.show.title} S${item.episode.season}E${item.episode.number}`;
  const vevent = [
    `BEGIN:VEVENT`,
    `UID:${uid}`,
    `DTSTART:${dtstart}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${item.show.title} - ${item.episode.title || ''}`,
    `END:VEVENT`
  ].join('\n');
  return { json: { uid, icsContent: `BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//n8n//Trakt Sync//FR\n${vevent}\nEND:VCALENDAR\n` } };
});
return events;
```

For movies, each item has `released` (date), `movie.title`, `movie.year`:
```javascript
const items = $input.all().map(i => i.json);
const events = items.filter(item => item.released).map(item => {
  const uid = `trakt-movie-${item.movie.ids.trakt}`;
  const dtstart = item.released.replace(/-/g, ''); // YYYYMMDD (all-day event)
  const summary = `🎬 ${item.movie.title} (${item.movie.year || ''})`;
  const vevent = [
    `BEGIN:VEVENT`,
    `UID:${uid}`,
    `DTSTART;VALUE=DATE:${dtstart}`,
    `SUMMARY:${summary}`,
    `END:VEVENT`
  ].join('\n');
  return { json: { uid, icsContent: `BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//n8n//Trakt Sync//FR\n${vevent}\nEND:VCALENDAR\n` } };
});
return events;
```

### Same Radicale collection as Motorsport

Use the same collection UUID (`0feb942c-776d-cef4-18a5-cb0d8bccd798`) and
credential ("Radicale" httpBasicAuth) as the Motorsport Calendar Sync. This
keeps everything on one calendar visible on iPhone, HA, and PC.

### User preference: consolidate, don't multiply workflows

The user explicitly wants ONE calendar. Two options:
1. Add Trakt branches to the existing Motorsport workflow (preferred per user
   preference about consolidation)
2. Create a separate Trakt workflow pushing to the same Radicale collection

Option 1 means: add 2 more HTTP GET branches (shows + movies) to the existing
`A4F90ZXY7FGD4zop` workflow, update Merge node `numberInputs` from 3 to 5.

## User's Trakt Apps (as of 2026-07-26)

- Trakii (connected Jul 4, 2026)
- mdblist.com (connected Jun 17, 2026)
- Sofa Time iOS (connected Jul 2, 2026)
- Simkl (connected Jun 2, 2026)
- n8n Calendar Sync (pending — blocked by connection limit)