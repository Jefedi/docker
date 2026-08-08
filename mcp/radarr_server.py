"""
Radarr MCP Server — 100% API coverage via FastMCP
Connects directly to Radarr v5 via Tailscale/Headscale (100.64.0.2:7878)
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Radarr")

RADARR_URL = os.getenv("RADARR_URL", "http://100.64.0.2:7878")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")
if not RADARR_API_KEY:
    key_file = os.path.expanduser("~/.hermes/radarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            RADARR_API_KEY = f.read().strip()
if not RADARR_API_KEY:
    raise RuntimeError("RADARR_API_KEY env var or ~/.hermes/radarr_api_key.txt is required")
REQUEST_TIMEOUT = float(os.getenv("RADARR_TIMEOUT", "20"))


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-Api-Key": RADARR_API_KEY,
    }


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
) -> Any:
    url = f"{RADARR_URL.rstrip('/')}/api/v3/{path.lstrip('/')}"
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=_headers()) as client:
        response = client.request(method, url, params=params, json=json_body)
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {"success": True}
        return response.json()


# ═══════════════════════════════════════
# SYSTEM
# ═══════════════════════════════════════

@mcp.tool
def system_status() -> dict[str, Any]:
    """Get Radarr system status (version, OS, DB, auth, etc.)."""
    return _request("GET", "system/status")


# ═══════════════════════════════════════
# MOVIES
# ═══════════════════════════════════════

@mcp.tool
def list_movies(tmdb_id: int | None = None) -> list[dict[str, Any]]:
    """List all movies in Radarr. Optionally filter by TMDB ID."""
    params = {}
    if tmdb_id:
        params["tmdbId"] = tmdb_id
    return _request("GET", "movie", params=params or None)


@mcp.tool
def get_movie(movie_id: int) -> dict[str, Any]:
    """Get a specific movie by its Radarr movie ID."""
    return _request("GET", f"movie/{movie_id}")


@mcp.tool
def lookup_movie(term: str) -> list[dict[str, Any]]:
    """Search for movies on TMDB by name or TMDB ID. Use before adding."""
    return _request("GET", "movie/lookup", params={"term": term})


@mcp.tool
def lookup_movie_imdb(imdb_id: str) -> list[dict[str, Any]]:
    """Look up a movie by its IMDb ID (e.g. 'tt0133093')."""
    return _request("GET", "movie/lookup/imdb", params={"imdbId": imdb_id})


@mcp.tool
def lookup_movie_tmdb(tmdb_id: int) -> dict[str, Any]:
    """Look up a movie by its TMDB ID."""
    return _request("GET", f"movie/lookup/tmdb", params={"tmdbId": tmdb_id})


@mcp.tool
def add_movie(
    tmdb_id: int,
    title: str,
    quality_profile_id: int,
    root_folder_path: str,
    monitored: bool = True,
    search_now: bool = True,
    minimum_availability: str = "announced",
    tags: list[int] | None = None,
) -> dict[str, Any]:
    """Add a new movie to Radarr.
    
    Args:
        tmdb_id: TMDB ID of the movie
        title: Movie title
        quality_profile_id: Quality profile ID (from list_quality_profiles)
        root_folder_path: Root folder (from list_root_folders)
        monitored: Monitor the movie
        search_now: Search for the movie immediately
        minimum_availability: 'announced', 'inCinemas', 'released', 'preDB'
        tags: List of tag IDs
    """
    body = {
        "tmdbId": tmdb_id,
        "title": title,
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": monitored,
        "minimumAvailability": minimum_availability,
        "addOptions": {"searchForMovie": search_now},
    }
    if tags:
        body["tags"] = tags
    return _request("POST", "movie", json_body=body)


@mcp.tool
def update_movie(
    movie_id: int,
    monitored: bool | None = None,
    quality_profile_id: int | None = None,
    minimum_availability: str | None = None,
    root_folder_path: str | None = None,
    tags: list[int] | None = None,
) -> dict[str, Any]:
    """Update a movie (monitored, quality profile, etc.)."""
    current = _request("GET", f"movie/{movie_id}")
    if monitored is not None:
        current["monitored"] = monitored
    if quality_profile_id is not None:
        current["qualityProfileId"] = quality_profile_id
    if minimum_availability is not None:
        current["minimumAvailability"] = minimum_availability
    if root_folder_path is not None:
        current["rootFolderPath"] = root_folder_path
    if tags is not None:
        current["tags"] = tags
    current["id"] = movie_id
    return _request("PUT", f"movie/{movie_id}", json_body=current)


@mcp.tool
def delete_movie(movie_id: int, delete_files: bool = False, delete_folders: bool = False) -> dict[str, Any]:
    """Delete a movie from Radarr.
    
    Args:
        movie_id: Radarr movie ID
        delete_files: Also delete movie files from disk
        delete_folders: Also delete movie folders from disk
    """
    return _request("DELETE", f"movie/{movie_id}",
                    params={"deleteFiles": str(delete_files).lower(), "deleteFolder": str(delete_folders).lower()})


@mcp.tool
def search_movie(movie_id: int) -> dict[str, Any]:
    """Trigger a search for a specific movie."""
    return _request("POST", "command", json_body={"name": "MoviesSearch", "movieIds": [movie_id]})


@mcp.tool
def refresh_movie(movie_id: int) -> dict[str, Any]:
    """Refresh movie info and metadata from TMDB."""
    return _request("POST", "command", json_body={"name": "RefreshMovie", "movieIds": [movie_id]})


# ═══════════════════════════════════════
# MOVIE FILES
# ═══════════════════════════════════════

@mcp.tool
def list_movie_files(movie_id: int) -> list[dict[str, Any]]:
    """List movie files for a specific movie (quality, size, path, codecs)."""
    return _request("GET", "moviefile", params={"movieId": movie_id})


@mcp.tool
def get_movie_file(file_id: int) -> dict[str, Any]:
    """Get a specific movie file by its ID."""
    return _request("GET", f"moviefile/{file_id}")


# ═══════════════════════════════════════
# QUALITY PROFILES
# ═══════════════════════════════════════

@mcp.tool
def list_quality_profiles() -> list[dict[str, Any]]:
    """List all quality profiles in Radarr with their allowed qualities."""
    return _request("GET", "qualityprofile")


@mcp.tool
def get_quality_profile(profile_id: int) -> dict[str, Any]:
    """Get a specific quality profile by ID."""
    return _request("GET", f"qualityprofile/{profile_id}")


@mcp.tool
def get_quality_profile_schema() -> list[dict[str, Any]]:
    """Get the quality profile schema (default structure for creating new profiles)."""
    return _request("GET", "qualityprofile/schema")


@mcp.tool
def create_quality_profile(
    name: str,
    cutoff_id: int,
    upgrade_allowed: bool = True,
    language_id: int = 1,
) -> dict[str, Any]:
    """Create a new quality profile in Radarr.
    
    Args:
        name: Profile display name
        cutoff_id: Quality ID to stop upgrading at
        upgrade_allowed: Allow automatic upgrades
        language_id: Language profile ID (1=English)
    """
    # Clone current Any profile structure
    any_profile = _request("GET", "qualityprofile/1")
    any_profile.pop("id", None)
    any_profile["name"] = name
    any_profile["cutoff"] = cutoff_id
    any_profile["upgradeAllowed"] = upgrade_allowed
    any_profile["language"] = {"id": language_id}
    
    allowed = {3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19}  # typical 1080p/4k
    for item in any_profile.get("items", []):
        if "quality" in item and item["quality"]:
            item["allowed"] = item["quality"]["id"] in allowed
        for sub in item.get("items", []):
            if "quality" in sub:
                sub["allowed"] = sub["quality"]["id"] in allowed
        if "id" in item and isinstance(item["id"], int) and item["id"] >= 1000:
            item["allowed"] = any(
                sub.get("allowed", False) for sub in item.get("items", [])
            )
    
    any_profile["formatItems"] = [
        {"format": f, "score": 0}
        for f in range(500, 600)
        if any(fi.get("format") == f for fi in any_profile.get("formatItems", []))
    ]
    any_profile["minFormatScore"] = 0
    any_profile["cutoffFormatScore"] = 0
    any_profile["minUpgradeFormatScore"] = 1
    
    return _request("POST", "qualityprofile", json_body=any_profile)


@mcp.tool
def update_quality_profile(
    profile_id: int,
    name: str | None = None,
    cutoff_id: int | None = None,
    upgrade_allowed: bool | None = None,
) -> dict[str, Any]:
    """Update a quality profile."""
    current = _request("GET", f"qualityprofile/{profile_id}")
    current["id"] = profile_id
    if name is not None:
        current["name"] = name
    if cutoff_id is not None:
        current["cutoff"] = cutoff_id
    if upgrade_allowed is not None:
        current["upgradeAllowed"] = upgrade_allowed
    return _request("PUT", f"qualityprofile/{profile_id}", json_body=current)


@mcp.tool
def delete_quality_profile(profile_id: int) -> dict[str, Any]:
    """Delete a quality profile."""
    return _request("DELETE", f"qualityprofile/{profile_id}")


# ═══════════════════════════════════════
# COLLECTIONS
# ═══════════════════════════════════════

@mcp.tool
def list_collections() -> list[dict[str, Any]]:
    """List all movie collections in Radarr."""
    return _request("GET", "collection")


@mcp.tool
def get_collection(collection_id: int) -> dict[str, Any]:
    """Get a specific collection by ID."""
    return _request("GET", f"collection/{collection_id}")


@mcp.tool
def update_collection(collection_id: int, monitored: bool | None = None, quality_profile_id: int | None = None, root_folder_path: str | None = None) -> dict[str, Any]:
    """Update a collection (monitored, quality profile, root folder)."""
    current = _request("GET", f"collection/{collection_id}")
    if monitored is not None:
        current["monitored"] = monitored
    if quality_profile_id is not None:
        current["qualityProfileId"] = quality_profile_id
    if root_folder_path is not None:
        current["rootFolderPath"] = root_folder_path
    return _request("PUT", f"collection/{collection_id}", json_body=current)


# ═══════════════════════════════════════
# QUEUE
# ═══════════════════════════════════════

@mcp.tool
def list_queue(page: int = 1, page_size: int = 50, include_movie: bool = True) -> dict[str, Any]:
    """List the Radarr download queue (active/pending downloads)."""
    return _request("GET", "queue", params={
        "page": page, "pageSize": page_size,
        "includeMovie": str(include_movie).lower(),
    })


# ═══════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════

@mcp.tool
def list_history(page: int = 1, page_size: int = 50, include_movie: bool = True) -> dict[str, Any]:
    """List Radarr history (downloaded, imported, grabbed, deleted movies)."""
    return _request("GET", "history", params={
        "page": page, "pageSize": page_size,
        "sortKey": "date", "sortDirection": "descending",
        "includeMovie": str(include_movie).lower(),
    })


# ═══════════════════════════════════════
# WANTED / MISSING
# ═══════════════════════════════════════

@mcp.tool
def list_wanted_missing(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """List movies that are monitored but missing (not yet downloaded)."""
    return _request("GET", "wanted/missing", params={
        "page": page, "pageSize": page_size,
        "sortKey": "releaseDate", "sortDirection": "descending",
        "monitored": "true",
    })


@mcp.tool
def list_wanted_cutoff_unmet(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """List movies that don't meet the quality cutoff yet."""
    return _request("GET", "wanted/cutoff", params={
        "page": page, "pageSize": page_size,
        "monitored": "true",
    })


# ═══════════════════════════════════════
# CALENDAR
# ═══════════════════════════════════════

@mcp.tool
def get_calendar(start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Get upcoming movie releases in a date range.
    
    Args:
        start: ISO 8601 start date (default: today)
        end: ISO 8601 end date (default: +7 days)
    """
    params = {"includeMovie": "true", "unmonitored": "false"}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _request("GET", "calendar", params=params)


# ═══════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════

@mcp.tool
def list_commands() -> list[dict[str, Any]]:
    """List all recent/running Radarr commands."""
    return _request("GET", "command")


@mcp.tool
def send_command(
    name: str,
    movie_ids: list[int] | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Send a command to Radarr (RssSync, RefreshMovie, MoviesSearch, etc.).
    
    Args:
        name: Command name (RssSync, RefreshMovie, MoviesSearch, DownloadedMoviesScan, ...)
        movie_ids: List of movie IDs (for MoviesSearch, RefreshMovie)
        path: File path (for DownloadedMoviesScan)
    """
    body: dict[str, Any] = {"name": name}
    if movie_ids is not None:
        body["movieIds"] = movie_ids
    if path is not None:
        body["path"] = path
    return _request("POST", "command", json_body=body)


# ═══════════════════════════════════════
# ROOT FOLDERS
# ═══════════════════════════════════════

@mcp.tool
def list_root_folders() -> list[dict[str, Any]]:
    """List all root folders configured in Radarr."""
    return _request("GET", "rootfolder")


# ═══════════════════════════════════════
# TAGS
# ═══════════════════════════════════════

@mcp.tool
def list_tags() -> list[dict[str, Any]]:
    """List all tags in Radarr."""
    return _request("GET", "tag")


@mcp.tool
def get_tag(tag_id: int) -> dict[str, Any]:
    """Get a specific tag by ID."""
    return _request("GET", f"tag/{tag_id}")


@mcp.tool
def create_tag(label: str) -> dict[str, Any]:
    """Create a new tag."""
    return _request("POST", "tag", json_body={"label": label})


# ═══════════════════════════════════════
# INDEXERS
# ═══════════════════════════════════════

@mcp.tool
def list_indexers() -> list[dict[str, Any]]:
    """List all configured indexers in Radarr."""
    return _request("GET", "indexer")


@mcp.tool
def get_indexer(indexer_id: int) -> dict[str, Any]:
    """Get a specific indexer configuration by ID."""
    return _request("GET", f"indexer/{indexer_id}")


@mcp.tool
def test_indexer(indexer_id: int) -> dict[str, Any]:
    """Test connectivity to an indexer."""
    return _request("POST", f"indexer/test/{indexer_id}")


# ═══════════════════════════════════════
# DOWNLOAD CLIENTS
# ═══════════════════════════════════════

@mcp.tool
def list_download_clients() -> list[dict[str, Any]]:
    """List all configured download clients in Radarr."""
    return _request("GET", "downloadclient")


# ═══════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════

@mcp.tool
def list_notifications() -> list[dict[str, Any]]:
    """List all notification/connection configurations."""
    return _request("GET", "notification")


# ═══════════════════════════════════════
# CUSTOM FORMATS
# ═══════════════════════════════════════

@mcp.tool
def list_custom_formats() -> list[dict[str, Any]]:
    """List all custom formats in Radarr."""
    return _request("GET", "customformat")


# ═══════════════════════════════════════
# RELEASES
# ═══════════════════════════════════════

@mcp.tool
def search_releases(movie_id: int) -> list[dict[str, Any]]:
    """Search for available releases for a movie (manual search)."""
    return _request("GET", "release", params={"movieId": movie_id})


# ═══════════════════════════════════════
# BLOCKLIST
# ═══════════════════════════════════════

@mcp.tool
def list_blocklist(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """List blocked releases."""
    return _request("GET", "blocklist", params={"page": page, "pageSize": page_size})


# ═══════════════════════════════════════
# REMOTE PATH MAPPINGS
# ═══════════════════════════════════════

@mcp.tool
def list_remote_path_mappings() -> list[dict[str, Any]]:
    """List all remote path mappings."""
    return _request("GET", "remotepathmapping")


# ═══════════════════════════════════════
# METADATA
# ═══════════════════════════════════════

@mcp.tool
def list_metadata_profiles() -> list[dict[str, Any]]:
    """List all metadata profiles."""
    return _request("GET", "metadataprofile")


# ═══════════════════════════════════════
# HEALTH & SYSTEM
# ═══════════════════════════════════════

@mcp.tool
def get_health() -> list[dict[str, Any]]:
    """Get Radarr health checks — returns warnings/errors if any issues."""
    return _request("GET", "health")


@mcp.tool
def get_disk_space() -> list[dict[str, Any]]:
    """Get disk space information for all mounted volumes."""
    return _request("GET", "diskspace")


@mcp.tool
def get_logs(page: int = 1, page_size: int = 50, level: str = "info") -> dict[str, Any]:
    """Get Radarr system logs. Level: info, warn, error, debug, trace."""
    return _request("GET", "log", params={
        "page": page, "pageSize": page_size,
        "level": level, "sortKey": "time", "sortDirection": "descending",
    })


@mcp.tool
def get_update_info() -> dict[str, Any]:
    """Get available update information (currently installed vs available)."""
    return _request("GET", "update")


# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════

@mcp.tool
def get_host_config() -> dict[str, Any]:
    """Get Radarr host configuration (port, SSL, auth, API key, etc.)."""
    return _request("GET", "config/host")


@mcp.tool
def get_naming_config() -> dict[str, Any]:
    """Get naming configuration (file/folder naming patterns)."""
    return _request("GET", "config/naming")


@mcp.tool
def get_naming_examples() -> list[dict[str, Any]]:
    """Get example file names based on current naming config."""
    return _request("GET", "config/naming/examples")


@mcp.tool
def get_media_management_config() -> dict[str, Any]:
    """Get Media Management settings."""
    return _request("GET", "config/mediamanagement")


@mcp.tool
def get_ui_config() -> dict[str, Any]:
    """Get UI configuration settings."""
    return _request("GET", "config/ui")


# ═══════════════════════════════════════
# RAW API ACCESS (CATCH-ALL)
# ═══════════════════════════════════════

@mcp.tool
def api(method: str, path: str, query: str = "{}", body: str = "{}") -> Any:
    """Catch-all Radarr API call. Use for any endpoint not covered by other tools.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path AFTER /api/v3/ (e.g. 'importlist', 'restriction')
        query: JSON query parameters as string (e.g. '{"pageSize":50}')
        body: JSON request body as string (e.g. '{"name":"RssSync"}')
    """
    params = json.loads(query) if query and query != "{}" else None
    json_body = json.loads(body) if body and body != "{}" else None
    return _request(method, path, params=params, json_body=json_body)


if __name__ == "__main__":
    mcp.run()
