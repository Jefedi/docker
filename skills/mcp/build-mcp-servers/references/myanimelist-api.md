# MyAnimeList API Reference for MCP

## API Basics
- Base URL: `https://api.myanimelist.net/v2`
- Auth: `X-MAL-CLIENT-ID` header (Client ID only — no OAuth needed for read-only)
- Rate limits: reasonable for personal use
- Client ID is free: register at https://myanimelist.net/apiconfig

## Key Endpoints

### Search Anime
```
GET /anime?q={query}&limit={n}&fields={fields}
```
Fields to include: `id,title,main_picture,mean,rank,popularity,num_episodes,status,synopsis,genres,authors{first_name,last_name}` (anime) or `authors,serialization` (manga)

### Anime Detail
```
GET /anime/{id}?fields={fields}
```

### Anime Ranking
```
GET /anime/ranking?ranking_type={type}&limit={n}&fields={fields}
```
ranking_type: `all`, `airing`, `upcoming`, `tv`, `movie`, `ova`, `ona`

### Seasonal Anime
```
GET /anime/season/{year}/{season}?sort={sort}&limit={n}&fields={fields}
```
season: `winter`, `spring`, `summer`, `fall`
sort: `score`, `members`, `id`

### Anime Recommendations
```
GET /anime/{id}/recommendations?limit={n}&fields={fields}
```

### Search Manga
```
GET /manga?q={query}&limit={n}&fields={fields}
```

### Manga Detail
```
GET /manga/{id}?fields={fields}
```

### Manga Ranking
```
GET /manga/ranking?ranking_type={type}&limit={n}&fields={fields}
```

## Response Structure Quirks

### Search responses
```json
{
  "data": [
    {
      "node": {
        "id": 52299,
        "title": "Solo Leveling",
        "main_picture": { "medium": "...", "large": "..." },
        "mean": 8.16,
        "rank": 504,
        "popularity": 149,
        "num_episodes": 12,
        "status": "finished_airing",
        "synopsis": "..."
      }
    }
  ]
}
```

### Ranking responses
```json
{
  "data": [
    {
      "node": {
        "id": 52299,
        "title": "Solo Leveling",
        "mean": 8.16,
        "rank": 504,
        ...
      },
      "ranking": {
        "rank": 504,
        "previous_rank": 123
      }
    }
  ]
}
```

## Field Name Mapping (API → MCP tool output)
| API field | MCP output key | Notes |
|-----------|----------------|-------|
| `mean` | `mean_score` | NOT `score` — common pitfall |
| `num_episodes` | `num_episodes` | NOT `episode_count` |
| `main_picture.medium` | `image_url` | Thumbnail URL |
| `genres[].name` | `genres` | Array of genre name strings |
| `studios[].name` | `studios` | Array of studio name strings |
| `rank` | `rank` | From `ranking.rank` in ranking endpoint, from `node.rank` in search |
| `popularity` | `popularity` | Direct numeric field |

## Real-World Server
Full working server at `/root/myanimelist-mcp/mal_server.py` (8 tools). Registered via `hermes mcp add myanimelist`. Requires env var `MAL_CLIENT_ID`.

## Pitfalls
- The `mean` field (average score) is `null` for unrated anime — handle this in MCP tool output
- Ranking uses `ranking.rank` nested object; search/detail use direct `node.rank`
- Genre/studio data only available when explicitly requested in the `fields` parameter
- Some titles use Japanese names (e.g. "Ore dake Level Up na Ken" for "Solo Leveling") — always search in both languages
