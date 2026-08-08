# Bazarr API Reference

Bazarr is a subtitle management companion for Sonarr and Radarr. It uses Flask-RESTX with an `X-API-KEY` header for auth.

**Base URL:** `http://100.64.0.2:6767` (internal Docker network)
**Auth:** `X-API-KEY` header
**API prefix:** `/api`
**Unauthenticated:** `GET /api/system/ping`

## Complete Endpoint Reference (64 endpoints, 11 namespaces)

### 1. Badges
| Method | Path | Description |
|--------|------|-------------|
| GET | `/badges` | Badge counts (missing subs, throttled providers, health) |

### 2. Episodes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/episodes` | List episode metadata |
| GET | `/episodes/wanted` | List episodes with missing subtitles (paginated) |
| GET | `/episodes/history` | Episode subtitle history (paginated) |
| GET | `/episodes/blacklist` | List blacklisted subtitles |
| POST | `/episodes/blacklist` | Add subtitle to blacklist |
| DELETE | `/episodes/blacklist` | Remove blacklist entry(ies) |
| PATCH | `/episodes/subtitles` | Download specific subtitle |
| POST | `/episodes/subtitles` | Upload subtitle file |
| DELETE | `/episodes/subtitles` | Delete subtitle |

### 3. Movies
| Method | Path | Description |
|--------|------|-------------|
| GET | `/movies` | List movie metadata (paginated) |
| POST | `/movies` | Update language profiles |
| PATCH | `/movies` | Run actions (scan-disk, search-missing, search-wanted, sync) |
| GET | `/movies/wanted` | List movies with missing subtitles |
| GET | `/movies/history` | Movie subtitle history |
| GET | `/movies/blacklist` | List blacklisted movie subtitles |
| POST | `/movies/blacklist` | Blacklist a subtitle |
| DELETE | `/movies/blacklist` | Remove blacklist entry |
| PATCH | `/movies/subtitles` | Download subtitle |
| POST | `/movies/subtitles` | Upload subtitle file |
| DELETE | `/movies/subtitles` | Delete subtitle |

### 4. Series
| Method | Path | Description |
|--------|------|-------------|
| GET | `/series` | List series metadata (paginated) |
| POST | `/series` | Update language profiles |
| PATCH | `/series` | Run actions (scan-disk, search-missing, search-wanted, sync) |

### 5. Subtitles (External Tools)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/subtitles` | Get audio tracks & subtitles for a media file |
| PATCH | `/subtitles` | Sync, translate, or modify subtitle |

### 6. Providers
| Method | Path | Description |
|--------|------|-------------|
| GET | `/providers` | Provider status / history stats |
| POST | `/providers` | Reset throttled providers |
| GET | `/providers/episodes` | Manual episode subtitle search |
| POST | `/providers/episodes` | Manual episode subtitle download |
| GET | `/providers/movies` | Manual movie subtitle search |
| POST | `/providers/movies` | Manual movie subtitle download |

### 7. Files
| Method | Path | Description |
|--------|------|-------------|
| GET | `/files` | Browse Bazarr filesystem |
| GET | `/files/sonarr` | Browse Sonarr-side filesystem |
| GET | `/files/radarr` | Browse Radarr-side filesystem |

### 8. History
| Method | Path | Description |
|--------|------|-------------|
| GET | `/history/stats` | History statistics (aggregated by day) |

### 9. System
| Method | Path | Auth? | Description |
|--------|------|-------|-------------|
| GET | `/system/ping` | No | Health check |
| GET | `/system/status` | Yes | Environment info & versions |
| GET | `/system/health` | Yes | Health issues list |
| GET | `/system/settings` | Yes | All system settings |
| POST | `/system/settings` | Yes | Save system settings |
| POST | `/system/webhooks/test` | Yes | Test webhook connection |
| GET | `/system/logs` | Yes | Log file entries |
| DELETE | `/system/logs` | Yes | Force log rotation |
| GET | `/system/tasks` | Yes | List scheduled tasks |
| POST | `/system/tasks` | Yes | Execute a task immediately |
| GET | `/system/jobs` | Yes | List job queue |
| POST | `/system/jobs` | Yes | Force start / move job |
| PATCH | `/system/jobs` | Yes | Empty job queue |
| DELETE | `/system/jobs` | Yes | Delete job from queue |
| POST | `/system` | Yes | Shutdown or restart |
| POST | `/system/account` | Yes | Login/logout |
| GET | `/system/announcements` | Yes | List announcements |
| POST | `/system/announcements` | Yes | Dismiss announcement |
| GET | `/system/backups` | Yes | List backup files |
| POST | `/system/backups` | Yes | Create backup |
| PATCH | `/system/backups` | Yes | Restore backup |
| DELETE | `/system/backups` | Yes | Delete backup |
| GET | `/system/releases` | Yes | GitHub releases cache |
| GET | `/system/searches` | Yes | Search series/movies by name |
| GET | `/system/languages` | Yes | List languages |
| GET | `/system/languages/profiles` | Yes | List language profiles |
| PATCH | `/system/notifications` | Yes | Send test notification |

### 10. Webhooks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/sonarr` | Sonarr webhook trigger |
| POST | `/webhooks/radarr` | Radarr webhook trigger |
| POST | `/webhooks/plex` | Plex webhook trigger |

### 11. Plex OAuth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/plex/oauth/pin` | Create Plex OAuth PIN |
| GET | `/plex/oauth/pin/<pin_id>` | Check PIN status |
| GET | `/plex/oauth/validate` | Validate Plex token |
| GET | `/plex/oauth/servers` | List owned Plex servers |

## MCP Server Template Pattern (FastMCP)

```python
import os, httpx
from fastmcp import FastMCP

mcp = FastMCP("Bazarr")

BAZARR_URL = os.getenv("BAZARR_URL", "http://100.64.0.2:6767")
BAZARR_API_KEY = os.getenv("BAZARR_API_KEY")
if not BAZARR_API_KEY:
    key_file = os.path.expanduser("~/.hermes/bazarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            BAZARR_API_KEY = f.read().strip()
if not BAZARR_API_KEY:
    raise RuntimeError("BAZARR_API_KEY env var or ~/.hermes/bazarr_api_key.txt required")

def _headers() -> dict[str, str]:
    return {"X-API-KEY": BAZARR_API_KEY, "Accept": "application/json"}

def _request(method: str, path: str, *, params: dict = None, json_body=None):
    url = f"{BAZARR_URL.rstrip('/')}/api/{path.lstrip('/')}"
    with httpx.Client(timeout=20, headers=_headers()) as client:
        resp = client.request(method, url, params=params, json=json_body)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"success": True}
        return resp.json()

# System
@mcp.tool
def system_ping() -> dict:
    """Check Bazarr availability (no auth needed)."""
    return _request("GET", "system/ping")

@mcp.tool
def system_status() -> dict:
    """Get Bazarr environment info & versions."""
    return _request("GET", "system/status")

@mcp.tool
def system_health() -> list:
    """List Bazarr health issues."""
    return _request("GET", "system/health")

# Series
@mcp.tool
def list_series(start: int = 0, length: int = -1) -> dict:
    """List series metadata with pagination."""
    return _request("GET", "series", params={"start": start, "length": length})

# Movies
@mcp.tool
def list_movies(start: int = 0, length: int = -1) -> dict:
    """List movie metadata with pagination."""
    return _request("GET", "movies", params={"start": start, "length": length})

# Episodes
@mcp.tool
def list_episodes_wanted(start: int = 0, length: int = -1) -> dict:
    """List episodes with missing/wanted subtitles."""
    return _request("GET", "episodes/wanted", params={"start": start, "length": length})

# Badges
@mcp.tool
def get_badges() -> dict:
    """Get badge counts for UI (missing subs, throttled providers, health)."""
    return _request("GET", "badges")

# ... continue with remaining endpoints following the same pattern
```

## Key Differences from Sonarr/Radarr MCP

- **Auth header**: Bazarr uses `X-API-KEY` (not `X-Api-Key`)
- **API prefix**: `/api/` (matches Sonarr/Radarr v3 pattern)
- **Flask-RESTX**: Responses are wrapped in an envelope; check for `data` key in list responses
- **Pagination**: `start` (offset) and `length` (limit, -1 = all)
- **Actions**: PATCH endpoints take `action` param (`scan-disk`, `search-missing`, `search-wanted`, `sync`)
- **No PUT endpoints**: Bazarr uses POST for updates, PATCH for actions
