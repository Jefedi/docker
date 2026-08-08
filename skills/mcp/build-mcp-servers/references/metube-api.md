# MeTube API Reference

MeTube is a self-hosted web UI for yt-dlp. It exposes a minimal REST API used by its Angular frontend.

## Source

https://github.com/alexta69/metube

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/add` | Add a download URL to the queue |
| POST | `/delete` | Remove a download from history |
| POST | `/start` | Start a queued download |
| GET  | `/history` | Get all downloads (done, queue, pending) |

## POST /add

Request body (JSON):
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "quality": "best",
  "format": "video",
  "playlist_start": 1,
  "playlist_end": 0
}
```

Parameters:
- `url` (required) — Video URL
- `quality` (optional) — "best", "720p", "1080p", "bestaudio", etc.
- `format` (optional) — "video", "audio", "video+audio"
- `playlist_start` (optional) — First playlist item index
- `playlist_end` (optional) — Last playlist item index (0 = unlimited)

Response: `{"status": "ok"}`

## GET /history

Response structure:
```json
{
  "done": [{...}],
  "queue": [{...}],
  "pending": [{...}]
}
```

Each item:
- `id` — Unique download ID
- `title` — Video title
- `url` — Original URL
- `quality` — Requested quality
- `status` — "finished", "downloading", "pending", "failed"
- `filename` — Output filename
- `size` — File size in bytes
- `percent` — Download progress (0-100, during download)
- `speed` — Download speed (during download)
- `eta` — Estimated time remaining (during download)
- `error` — Error message (if failed)
- `timestamp` — Unix timestamp in nanoseconds

## Authentication

MeTube has no authentication by default. If behind a reverse proxy (Pangolin), auth is handled at the proxy level.
