#!/usr/bin/env python3
"""MCP server for Seerr (Overseerr/Jellyseerr fork) — exposes the full Seerr REST API.

Env vars:
  SEERR_URL       — Base URL (default: http://localhost:5055)
  SEERR_API_KEY   — API key from Seerr settings (settings.json → main.apiKey)

Registration:
  hermes config set mcp_servers.seerr.command /opt/hermes/.venv/bin/python3
  hermes config set mcp_servers.seerr.args "['/opt/data/mcp/seerr_server.py']"
  hermes config set mcp_servers.seerr.env.SEERR_URL http://localhost:5055
  hermes config set mcp_servers.seerr.env.SEERR_API_KEY <key>
  hermes config set mcp_servers.seerr.enabled true
  hermes config set mcp_servers.seerr.connect_timeout 30
  # Then: hermes gateway restart (from separate terminal)
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Seerr")

SEERR_URL = os.getenv("SEERR_URL", "http://localhost:5055")
SEERR_API_KEY = os.getenv("SEERR_API_KEY", "")

HEADERS = {"X-Api-Key": SEERR_API_KEY} if SEERR_API_KEY else {}


def _req(method: str, path: str, params: dict = None, json_body: dict = None) -> dict:
    url = f"{SEERR_URL.rstrip('/')}/api/v1/{path.lstrip('/')}"
    with httpx.Client(timeout=30) as c:
        r = c.request(method, url, params=params, json=json_body, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return {"results": data}
        return data


# ─── Status ───

@mcp.tool()
def seerr_status() -> dict:
    """Get Seerr server status (version, update available)."""
    return _req("GET", "status")


@mcp.tool()
def seerr_appdata() -> dict:
    """Get Seerr app data directory info."""
    return _req("GET", "status/appdata")


# ─── Requests ───

@mcp.tool()
def seerr_list_requests(take: int = 20, skip: int = 0, filter: str = "", sort: str = "added") -> dict:
    """List media requests. filter: approved|pending|available|unavailable|processing|deleted. sort: added|modified."""
    params = {"take": take, "skip": skip, "sort": sort}
    if filter:
        params["filter"] = filter
    return _req("GET", "request", params=params)


@mcp.tool()
def seerr_request_count() -> dict:
    """Get total request counts by status."""
    return _req("GET", "request/count")


@mcp.tool()
def seerr_get_request(request_id: int) -> dict:
    """Get details of a specific request by ID."""
    return _req("GET", f"request/{request_id}")


@mcp.tool()
def seerr_request_movie(media_id: int, is4k: bool = False, profile_id: int = None, server_id: int = None, root_folder: str = None) -> dict:
    """Submit a new movie request. media_id is the TMDB ID."""
    body = {"mediaType": "movie", "mediaId": media_id, "is4k": is4k}
    if profile_id is not None:
        body["profileId"] = profile_id
    if server_id is not None:
        body["serverId"] = server_id
    if root_folder:
        body["rootFolder"] = root_folder
    return _req("POST", "request", json_body=body)


@mcp.tool()
def seerr_request_tv(media_id: int, tvdb_id: int = None, seasons: list = None, is4k: bool = False, profile_id: int = None, server_id: int = None, root_folder: str = None) -> dict:
    """Submit a new TV show request. media_id is TMDB ID. seasons is list of season numbers (e.g. [1,2]). If None, requests all seasons."""
    body = {"mediaType": "tv", "mediaId": media_id, "is4k": is4k}
    if tvdb_id is not None:
        body["tvdbId"] = tvdb_id
    if seasons is not None:
        body["seasons"] = seasons
    if profile_id is not None:
        body["profileId"] = profile_id
    if server_id is not None:
        body["serverId"] = server_id
    if root_folder:
        body["rootFolder"] = root_folder
    return _req("POST", "request", json_body=body)


@mcp.tool()
def seerr_approve_request(request_id: int) -> dict:
    """Approve a pending request."""
    return _req("POST", f"request/{request_id}/approve")


@mcp.tool()
def seerr_decline_request(request_id: int) -> dict:
    """Decline a pending request."""
    return _req("POST", f"request/{request_id}/decline")


@mcp.tool()
def seerr_retry_request(request_id: int) -> dict:
    """Retry a failed request."""
    return _req("POST", f"request/{request_id}/retry")


@mcp.tool()
def seerr_delete_request(request_id: int) -> dict:
    """Delete a request."""
    return _req("DELETE", f"request/{request_id}")


# ─── Search ───

@mcp.tool()
def seerr_search(query: str, page: int = 1, language: str = "") -> dict:
    """Search for movies, TV shows, and people."""
    params = {"query": query, "page": page}
    if language:
        params["language"] = language
    return _req("GET", "search", params=params)


@mcp.tool()
def seerr_search_keyword(query: str) -> dict:
    """Search by keyword."""
    return _req("GET", "search/keyword", params={"query": query})


# ─── Discover ───

@mcp.tool()
def seerr_discover_movies(page: int = 1) -> dict:
    """Discover popular movies."""
    return _req("GET", "discover/movies", params={"page": page})


@mcp.tool()
def seerr_discover_tv(page: int = 1) -> dict:
    """Discover popular TV shows."""
    return _req("GET", "discover/tv", params={"page": page})


@mcp.tool()
def seerr_discover_upcoming_movies(page: int = 1) -> dict:
    """Discover upcoming movies."""
    return _req("GET", "discover/movies/upcoming", params={"page": page})


@mcp.tool()
def seerr_discover_upcoming_tv(page: int = 1) -> dict:
    """Discover upcoming TV shows."""
    return _req("GET", "discover/tv/upcoming", params={"page": page})


@mcp.tool()
def seerr_discover_trending(page: int = 1) -> dict:
    """Discover trending media."""
    return _req("GET", "discover/trending", params={"page": page})


# ─── Movies ───

@mcp.tool()
def seerr_get_movie(tmdb_id: int) -> dict:
    """Get movie details by TMDB ID."""
    return _req("GET", f"movie/{tmdb_id}")


@mcp.tool()
def seerr_movie_recommendations(tmdb_id: int) -> dict:
    """Get recommended movies for a movie."""
    return _req("GET", f"movie/{tmdb_id}/recommendations")


@mcp.tool()
def seerr_movie_similar(tmdb_id: int) -> dict:
    """Get similar movies."""
    return _req("GET", f"movie/{tmdb_id}/similar")


# ─── TV ───

@mcp.tool()
def seerr_get_tv(tmdb_id: int) -> dict:
    """Get TV show details by TMDB ID."""
    return _req("GET", f"tv/{tmdb_id}")


@mcp.tool()
def seerr_get_tv_season(tmdb_id: int, season_number: int) -> dict:
    """Get details for a specific season of a TV show."""
    return _req("GET", f"tv/{tmdb_id}/season/{season_number}")


@mcp.tool()
def seerr_tv_recommendations(tmdb_id: int) -> dict:
    """Get recommended TV shows."""
    return _req("GET", f"tv/{tmdb_id}/recommendations")


@mcp.tool()
def seerr_tv_similar(tmdb_id: int) -> dict:
    """Get similar TV shows."""
    return _req("GET", f"tv/{tmdb_id}/similar")


# ─── Media ───

@mcp.tool()
def seerr_list_media(take: int = 20, skip: int = 0, filter: str = "", sort: str = "added") -> dict:
    """List all media in Seerr library. filter: available|processing|pending|partial|blacklisted."""
    params = {"take": take, "skip": skip, "sort": sort}
    if filter:
        params["filter"] = filter
    return _req("GET", "media", params=params)


@mcp.tool()
def seerr_get_media(media_id: int) -> dict:
    """Get media details by Seerr media ID."""
    return _req("GET", f"media/{media_id}")


@mcp.tool()
def seerr_delete_media(media_id: int) -> dict:
    """Delete a media item from Seerr."""
    return _req("DELETE", f"media/{media_id}")


@mcp.tool()
def seerr_set_media_status(media_id: int, status: str) -> dict:
    """Set media status. status: available|processing|partial|pending|blacklisted|deleted."""
    return _req("POST", f"media/{media_id}/{status}")


# ─── Watchlist ───

@mcp.tool()
def seerr_get_watchlist() -> dict:
    """Get the current user's watchlist."""
    return _req("GET", "watchlist")


@mcp.tool()
def seerr_add_to_watchlist(tmdb_id: int) -> dict:
    """Add a movie or TV show to watchlist by TMDB ID."""
    return _req("POST", "watchlist", json_body={"tmdbId": tmdb_id})


@mcp.tool()
def seerr_remove_from_watchlist(tmdb_id: int) -> dict:
    """Remove from watchlist by TMDB ID."""
    return _req("DELETE", f"watchlist/{tmdb_id}")


# ─── Blocklist ───

@mcp.tool()
def seerr_get_blocklist() -> dict:
    """Get the blocklist."""
    return _req("GET", "blocklist")


@mcp.tool()
def seerr_add_to_blocklist(media_type: str, tmdb_id: int, tvdb_id: int = None) -> dict:
    """Add to blocklist. media_type: movie|tv."""
    body = {"mediaType": media_type, "tmdbId": tmdb_id}
    if tvdb_id is not None:
        body["tvdbId"] = tvdb_id
    return _req("POST", "blocklist", json_body=body)


@mcp.tool()
def seerr_remove_from_blocklist(tmdb_id: int) -> dict:
    """Remove from blocklist by TMDB ID."""
    return _req("DELETE", f"blocklist/{tmdb_id}")


# ─── Issues ───

@mcp.tool()
def seerr_list_issues(take: int = 20, skip: int = 0, filter: str = "") -> dict:
    """List media issues. filter: open|resolved."""
    params = {"take": take, "skip": skip}
    if filter:
        params["filter"] = filter
    return _req("GET", "issue", params=params)


@mcp.tool()
def seerr_get_issue(issue_id: int) -> dict:
    """Get issue details by ID."""
    return _req("GET", f"issue/{issue_id}")


@mcp.tool()
def seerr_comment_issue(issue_id: int, message: str) -> dict:
    """Comment on an issue."""
    return _req("POST", f"issue/{issue_id}/comment", json_body={"message": message})


@mcp.tool()
def seerr_resolve_issue(issue_id: int) -> dict:
    """Resolve an issue."""
    return _req("POST", f"issue/{issue_id}/resolved")


@mcp.tool()
def seerr_reopen_issue(issue_id: int) -> dict:
    """Reopen a resolved issue."""
    return _req("POST", f"issue/{issue_id}/reopen")


@mcp.tool()
def seerr_delete_issue(issue_id: int) -> dict:
    """Delete an issue."""
    return _req("DELETE", f"issue/{issue_id}")


# ─── Services (Radarr/Sonarr) ───

@mcp.tool()
def seerr_list_radarr() -> dict:
    """List configured Radarr instances."""
    return _req("GET", "service/radarr")


@mcp.tool()
def seerr_list_sonarr() -> dict:
    """List configured Sonarr instances."""
    return _req("GET", "service/sonarr")


# ─── Users ───

@mcp.tool()
def seerr_list_users() -> dict:
    """List all Seerr users."""
    return _req("GET", "user")


@mcp.tool()
def seerr_get_user(user_id: int) -> dict:
    """Get user details by ID."""
    return _req("GET", f"user/{user_id}")


@mcp.tool()
def seerr_get_user_requests(user_id: int) -> dict:
    """Get requests for a specific user."""
    return _req("GET", f"user/{user_id}/requests")


# ─── Collection ───

@mcp.tool()
def seerr_get_collection(tmdb_id: int) -> dict:
    """Get collection details by TMDB ID."""
    return _req("GET", f"collection/{tmdb_id}")


# ─── Person ───

@mcp.tool()
def seerr_get_person(tmdb_id: int) -> dict:
    """Get person details by TMDB ID."""
    return _req("GET", f"person/{tmdb_id}")


@mcp.tool()
def seerr_person_credits(tmdb_id: int) -> dict:
    """Get combined credits for a person."""
    return _req("GET", f"person/{tmdb_id}/combined_credits")


# ─── Settings ───

@mcp.tool()
def seerr_get_settings() -> dict:
    """Get Seerr main settings (admin)."""
    return _req("GET", "settings/main")


@mcp.tool()
def seerr_get_settings_public() -> dict:
    """Get public settings (no auth required)."""
    return _req("GET", "settings/public")


@mcp.tool()
def seerr_list_jobs() -> dict:
    """List scheduled jobs."""
    return _req("GET", "settings/jobs")


@mcp.tool()
def seerr_run_job(job_id: str) -> dict:
    """Run a scheduled job manually."""
    return _req("POST", f"settings/jobs/{job_id}/run")


# ─── Genres ───

@mcp.tool()
def seerr_list_movie_genres() -> dict:
    """List all movie genres."""
    return _req("GET", "genres/movie")


@mcp.tool()
def seerr_list_tv_genres() -> dict:
    """List all TV genres."""
    return _req("GET", "genres/tv")


if __name__ == "__main__":
    mcp.run()