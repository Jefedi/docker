# SearXNG API Reference

SearXNG exposes a simple JSON search API at `/search?q=<query>&format=json`.

## Endpoint

```
GET /search?q=<query>&format=json
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | (required) | Search query |
| `format` | string | `html` | `json` for programmatic access |
| `categories` | string | — | Comma-separated: `general`, `news`, `images`, `videos`, `music`, `files`, `it`, `science`, `social media` |
| `language` | string | — | Language code: `fr`, `en`, `de`, etc. |
| `pageno` | int | `1` | Page number |
| `time_range` | string | — | `day`, `week`, `month`, `year` |

### Response Structure

```json
{
  "query": "search term",
  "results": [
    {
      "url": "https://...",
      "title": "Page Title",
      "content": "Snippet text...",
      "engine": "google",
      "template": "default.html",
      "parsed_url": ["https", "domain", "/path", "", "", ""],
      "img_src": "",
      "thumbnail": "",
      "priority": "",
      "engines": ["google", "wikipedia"],
      "positions": [1, 3],
      "score": 2.5,
      "category": "general",
      "publishedDate": null
    }
  ],
  "answers": [],
  "corrections": [],
  "infoboxes": [],
  "suggestions": ["related", "search", "terms"],
  "unresponsive_engines": [["brave", "too many requests"]]
}
```

### Key Fields

- `results[].score` — relevance score (higher = better). Normalized, range roughly 0-3.
- `results[].engine` — which search engine provided this result.
- `results[].engines` — all engines that returned this result (dedup).
- `results[].positions` — position in each engine's results.
- `unresponsive_engines` — engines that failed or were rate-limited.

## Auth

No authentication required when accessed internally (docker network or Pangolin proxy).
Public SearXNG instances may have rate limiting.

## Pangolin Private Resource Pattern

Jefe's SearXNG at `search.jefe.al` is a Pangolin Private Resource — only accessible
through the Newt tunnel. The MCP server routes via:

```
docker exec pangolin-cli curl -sk "https://search.jefe.al/search?q=...&format=json"
```

The pangolin-cli container runs the Newt client which maintains the WireGuard tunnel
to the private resources. Without this tunnel (or being on the same Docker network),
the domain returns a "Private Placeholder Screen" page.
