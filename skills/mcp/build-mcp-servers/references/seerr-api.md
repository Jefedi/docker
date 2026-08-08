# Seerr API Reference

Seerr is a fork of Overseerr/Jellyseerr. API v1 at `/api/v1/`.

## Authentication

Header-based: `X-Api-Key: <key>`

API key location: inside the Docker container at `/app/config/settings.json` → `main.apiKey`.

```bash
docker exec seerr cat /app/config/settings.json | python3 -c "import sys,json; print(json.load(sys.stdin)['main']['apiKey'])"
```

Public endpoints (status, settings/public) don't require auth.

## Key Endpoints

### Status
- `GET status` — server version, update available
- `GET status/appdata` — app data directory

### Requests
- `GET request?take=N&skip=N&filter=approved|pending|available|unavailable|processing|deleted&sort=added|modified`
- `GET request/count` — counts by status
- `GET request/{id}` — request details
- `POST request` — create request. Body: `{mediaType: "movie"|"tv", mediaId: <TMDB>, is4k: false, profileId?, serverId?, rootFolder?, tvdbId?, seasons?: [1,2]}`
- `POST request/{id}/approve` — approve pending
- `POST request/{id}/decline` — decline pending
- `POST request/{id}/retry` — retry failed
- `DELETE request/{id}` — delete request

### Search
- `GET search?query=X&page=N&language=fr`
- `GET search/keyword?query=X`
- `GET search/company?query=X`

### Discover
- `GET discover/movies?page=N`
- `GET discover/movies/upcoming?page=N`
- `GET discover/tv?page=N`
- `GET discover/tv/upcoming?page=N`
- `GET discover/trending?page=N`

### Movies
- `GET movie/{tmdbId}` — details
- `GET movie/{tmdbId}/recommendations`
- `GET movie/{tmdbId}/similar`
- `GET movie/{tmdbId}/ratings`

### TV
- `GET tv/{tmdbId}` — details
- `GET tv/{tmdbId}/season/{seasonNumber}`
- `GET tv/{tmdbId}/recommendations`
- `GET tv/{tmdbId}/similar`

### Media
- `GET media?take=N&skip=N&filter=available|processing|pending|partial|blacklisted&sort=added`
- `GET media/{mediaId}` — media details
- `DELETE media/{mediaId}` — delete
- `POST media/{mediaId}/{status}` — set status (available, processing, partial, pending, blacklisted, deleted)

### Watchlist
- `GET watchlist` — current user's watchlist
- `POST watchlist` — body: `{tmdbId: N}`
- `DELETE watchlist/{tmdbId}`

### Blocklist
- `GET blocklist`
- `POST blocklist` — body: `{mediaType, tmdbId, tvdbId?}`
- `DELETE blocklist/{tmdbId}`

### Issues
- `GET issue?take=N&skip=N&filter=open|resolved`
- `GET issue/{id}`
- `POST issue/{id}/comment` — body: `{message: "..."}`
- `POST issue/{id}/resolved`
- `POST issue/{id}/reopen`
- `DELETE issue/{id}`

### Services
- `GET service/radarr` — list Radarr instances
- `GET service/sonarr` — list Sonarr instances

### Users
- `GET user` — list users
- `GET user/{id}` — user details
- `GET user/{id}/requests` — user's requests
- `GET user/{id}/watchlist`

### Settings (admin)
- `GET settings/main` — main settings
- `GET settings/public` — public settings
- `GET settings/jobs` — scheduled jobs
- `POST settings/jobs/{jobId}/run` — run job manually

### Other
- `GET collection/{tmdbId}` — collection details
- `GET person/{tmdbId}` — person details
- `GET person/{tmdbId}/combined_credits`
- `GET genres/movie` — movie genres
- `GET genres/tv` — TV genres

## Docker

Container name: `seerr`
Local port: `5055`
Config path: `/app/config/settings.json`