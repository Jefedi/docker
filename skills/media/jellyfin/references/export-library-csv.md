# Export Jellyfin Library to Sofa / Tracker CSV

Export your full Jellyfin library (movies, series, episodes) as a CSV compatible with **Sofa** (ex-Sofa Time), Letterboxd, Trakt, or any generic tracker import.

## Prerequisites

- Jellyfin API token (`~/.hermes/jellyfin_token.txt` or `JELLYFIN_TOKEN` env var)
- Jellyfin server URL (e.g. `https://jflix.jefe.al`)
- A user ID (admin user with `EnableAllFolders: true` to see everything)

## Technique

### 1. Get user ID

```
GET /Users
Header: X-Emby-Token: <token>
Pick the admin user (IsAdministrator: true)
```

### 2. Paginate through all items

Jellyfin's API paginates at 200 items max per call. Loop with `StartIndex`:

```
Movies:   GET /Items?userId={id}&Recursive=true&IncludeItemTypes=Movie&Fields=ProviderIds,ProductionYear&Limit=200&StartIndex={offset}
Episodes: GET /Items?userId={id}&Recursive=true&IncludeItemTypes=Episode&Fields=ProviderIds,ProductionYear,SeriesName,ParentIndexNumber,IndexNumber&Limit=200&StartIndex={offset}
```

### 3. Key API fields

| Field | Where | Purpose |
|-------|-------|---------|
| `Name` | item root | Movie title / series name |
| `ProductionYear` | item root | Release year |
| `ProviderIds.Imdb` | `ProviderIds` | IMDb ID (`tt...`) for matching |
| `ProviderIds.Tmdb` | `ProviderIds` | TMDB ID alternative |
| `SeriesName` | episode | Links episodes to parent series |
| `ParentIndexNumber` | episode | Season number |
| `IndexNumber` | episode | Episode number |

### 4. Sofa CSV format

```
Title,Year,Type,Season,Episode,IMDb ID,TMDB ID,Status
```

**Key rules for Sofa import:**
- **Movies**: one row per movie → `Movie` type
- **Series**: do NOT include series-level rows — only episode rows. Each episode row auto-creates the series in Sofa and marks that episode watched. Series + episode rows together create duplicates.
- **Status**: `Watched` for everything on the server

### 5. Python script template

```python
import json, csv, urllib.request, urllib.parse

TOKEN="your..."
BASE = "https://jflix.jefe.al"
USER_ID = "user_id_here"

def jellyfin_get(path, params=None):
    url = f"{BASE}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "X-Emby-Token": TOKEN, "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

# Get all movies
movies, offset = [], 0
while True:
    data = jellyfin_get("Items", {"userId": USER_ID, "Recursive": "true",
        "IncludeItemTypes": "Movie", "Fields": "ProviderIds,ProductionYear",
        "Limit": 200, "StartIndex": offset})
    items = data.get("Items", [])
    movies.extend(items)
    if len(items) < 200: break
    offset += 200

# Get all episodes
eps, offset = [], 0
while True:
    data = jellyfin_get("Items", {"userId": USER_ID, "Recursive": "true",
        "IncludeItemTypes": "Episode",
        "Fields": "ProviderIds,ProductionYear,SeriesName,ParentIndexNumber,IndexNumber",
        "Limit": 200, "StartIndex": offset})
    items = data.get("Items", [])
    eps.extend(items)
    if len(items) < 200: break
    offset += 200

# Write CSV
with open("jellyfin-export.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Title","Year","Type","Season","Episode","IMDb ID","TMDB ID","Status"])
    for m in movies:
        p = m.get("ProviderIds", {})
        w.writerow([m["Name"], m.get("ProductionYear",""), "Movie","","",
                     p.get("Imdb",""), p.get("Tmdb",""), "Watched"])
    for e in eps:
        p = e.get("ProviderIds", {})
        w.writerow([e.get("SeriesName",""), e.get("ProductionYear",""), "TV Show",
                     e.get("ParentIndexNumber",""), e.get("IndexNumber",""),
                     p.get("Imdb",""), p.get("Tmdb",""), "Watched"])
```

## Pitfalls

- **Don't assume inline JSON is complete** — when a user shares sample data, query the live API instead. Sample data may be truncated.
- **Series-level + episode-level duplicate** in CSV → Sofa creates duplicate series entries. Export episodes ONLY.
- **Large libraries**: for 3500+ episodes, expect ~18 paginated calls. Use timeout=60.
- **ProviderIds may be empty** for some items — Sofa still imports them as custom entries.
- **UTF-8 required**: French/special chars → ensure `encoding="utf-8"` on file write.

## Related

- Sofa import docs: https://www.sofahq.com/support/data-management/import-from-other-services
- Jellyfin API: instance swagger at `https://your-host/swagger`
