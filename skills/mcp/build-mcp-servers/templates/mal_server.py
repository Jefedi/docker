"""MyAnimeList MCP Server — FastMCP

8 tools: search/ranking/detail/recommendations for anime + manga.
Uses MAL v2 public API (Client ID header, no OAuth).
"""
import os, httpx
from fastmcp import FastMCP

mcp = FastMCP("MyAnimeList")
MAL_URL = "https://api.myanimelist.net/v2"
CLIENT_ID = os.getenv("MAL_CLIENT_ID", "")
HEADERS = {"X-MAL-CLIENT-ID": CLIENT_ID}

def _request(path, params=None):
    """Make a GET request to the MAL API."""
    url = f"{MAL_URL}/{path.lstrip('/')}"
    with httpx.Client(headers=HEADERS, timeout=20) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

FIELDS = "id,title,main_picture,mean,rank,popularity,num_episodes,status,synopsis,genres,studios,authors{first_name,last_name},media_type,start_season"

def _parse_nodes(data, limit=10):
    """Parse MAL search/ranking response nodes into flat dicts."""
    items = data.get("data", [])[:limit]
    out = []
    for item in items:
        node = item.get("node", item)
        entry = {
            "id": node.get("id"),
            "title": node.get("title"),
            "mean_score": node.get("mean"),
            "rank": node.get("rank") or item.get("ranking", {}).get("rank"),
            "popularity": node.get("popularity"),
            "num_episodes": node.get("num_episodes"),
            "status": node.get("status"),
            "synopsis": (node.get("synopsis") or "")[:500],
            "image_url": (node.get("main_picture") or {}).get("medium"),
            "genres": [g["name"] for g in (node.get("genres") or [])],
            "studios": [s["name"] for s in (node.get("studios") or [])],
            "media_type": node.get("media_type"),
        }
        out.append(entry)
    return out

@mcp.tool()
def mal_search_anime(query: str, limit: int = 10) -> list:
    """Search for anime by title on MyAnimeList."""
    data = _request("anime", {"q": query, "limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

@mcp.tool()
def mal_get_anime(anime_id: int) -> dict:
    """Get full details for a specific anime by its MyAnimeList ID."""
    data = _request(f"anime/{anime_id}", {"fields": FIELDS})
    return _parse_nodes({"data": [{"node": data}]})[0]

@mcp.tool()
def mal_get_anime_ranking(ranking_type: str = "all", limit: int = 10) -> list:
    """Get top anime ranking. Types: all, airing, upcoming, tv, movie, ova, ona."""
    data = _request("anime/ranking", {"ranking_type": ranking_type, "limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

@mcp.tool()
def mal_get_seasonal_anime(year: int | None = None, season: str | None = None, limit: int = 20) -> list:
    """Get anime from a specific season. Auto-detects current season if not specified."""
    import datetime
    if not year or not season:
        now = datetime.date.today()
        year = now.year
        m = now.month
        season = {1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
                  6: "summer", 7: "summer", 8: "summer", 9: "fall", 10: "fall", 11: "fall", 12: "winter"}[m]
    data = _request(f"anime/season/{year}/{season}", {"sort": "members", "limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

@mcp.tool()
def mal_get_anime_recommendations(anime_id: int, limit: int = 10) -> list:
    """Get anime recommendations based on a specific anime."""
    data = _request(f"anime/{anime_id}/recommendations", {"limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

@mcp.tool()
def mal_search_manga(query: str, limit: int = 10) -> list:
    """Search for manga/manhwa/manhua by title on MyAnimeList."""
    data = _request("manga", {"q": query, "limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

@mcp.tool()
def mal_get_manga(manga_id: int) -> dict:
    """Get full details for a specific manga by its MyAnimeList ID."""
    data = _request(f"manga/{manga_id}", {"fields": FIELDS})
    return _parse_nodes({"data": [{"node": data}]})[0]

@mcp.tool()
def mal_get_manga_ranking(ranking_type: str = "all", limit: int = 10) -> list:
    """Get top manga/manhwa/manhua ranking. Types: all, manga, manhwa, manhua, oneshot, doujin."""
    data = _request("manga/ranking", {"ranking_type": ranking_type, "limit": limit, "fields": FIELDS})
    return _parse_nodes(data, limit)

if __name__ == "__main__":
    mcp.run()
