"""
Sonarr MCP Server — 100% API coverage via FastMCP
Connects directly to Sonarr v4 via Tailscale/Headscale (100.64.0.2:8989)
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Sonarr")

SONARR_URL = os.getenv("SONARR_URL", "http://100.64.0.2:8989")
SONARR_API_KEY = os.getenv("SONARR_API_KEY")
if not SONARR_API_KEY:
    key_file = os.path.expanduser("~/.hermes/sonarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            SONARR_API_KEY = f.read().strip()
if not SONARR_API_KEY:
    raise RuntimeError("SONARR_API_KEY env var or ~/.hermes/sonarr_api_key.txt is required")
REQUEST_TIMEOUT = float(os.getenv("SONARR_TIMEOUT", "20"))


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-Api-Key": SONARR_API_KEY,
    }


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
) -> Any:
    url = f"{SONARR_URL.rstrip('/')}/api/v3/{path.lstrip('/')}"
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
    """Get Sonarr system status (version, OS, DB, auth, etc.)."""
    return _request("GET", "system/status")


# ═══════════════════════════════════════
# SERIES
# ═══════════════════════════════════════

@mcp.tool
def list_series(tvdb_id: int | None = None) -> list[dict[str, Any]]:
    """List all series in Sonarr. Optionally filter by TVDB ID."""
    params = {}
    if tvdb_id:
        params["tvdbId"] = tvdb_id
    return _request("GET", "series", params=params or None)


@mcp.tool
def get_series(series_id: int) -> dict[str, Any]:
    """Get a specific series by its Sonarr series ID."""
    return _request("GET", f"series/{series_id}")


@mcp.tool
def lookup_series(term: str) -> list[dict[str, Any]]:
    """Search for a series on TVDB by name or TVDB ID. Use before adding."""
    return _request("GET", "series/lookup", params={"term": term})


@mcp.tool
def add_series(
    tvdb_id: int,
    title: str,
    quality_profile_id: int,
    root_folder_path: str,
    monitored: bool = True,
    season_folder: bool = True,
    series_type: str = "standard",
    seasons: list[dict[str, Any]] | None = None,
    tags: list[int] | None = None,
    language_profile_id: int = 1,
) -> dict[str, Any]:
    """Add a new series to Sonarr.
    
    Args:
        tvdb_id: TheTVDB ID of the series
        title: Series title
        quality_profile_id: Quality profile ID (from list_quality_profiles)
        root_folder_path: Root folder path (from list_root_folders)
        monitored: Monitor the series
        season_folder: Create season folders
        series_type: 'standard', 'daily', or 'anime'
        seasons: List of {seasonNumber, monitored} dicts. Auto-generated if None
        tags: List of tag IDs
        language_profile_id: Language profile ID (default 1)
    """
    body = {
        "tvdbId": tvdb_id,
        "title": title,
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": monitored,
        "seasonFolder": season_folder,
        "seriesType": series_type,
        "languageProfileId": language_profile_id,
        "addOptions": {"searchForMissingEpisodes": True},
    }
    if seasons:
        body["seasons"] = seasons
    if tags:
        body["tags"] = tags
    return _request("POST", "series", json_body=body)


@mcp.tool
def update_series(
    series_id: int,
    monitored: bool | None = None,
    quality_profile_id: int | None = None,
    season_folder: bool | None = None,
    series_type: str | None = None,
    root_folder_path: str | None = None,
    tags: list[int] | None = None,
) -> dict[str, Any]:
    """Update a series (monitored, quality profile, type, etc.)."""
    current = _request("GET", f"series/{series_id}")
    if monitored is not None:
        current["monitored"] = monitored
    if quality_profile_id is not None:
        current["qualityProfileId"] = quality_profile_id
    if season_folder is not None:
        current["seasonFolder"] = season_folder
    if series_type is not None:
        current["seriesType"] = series_type
    if root_folder_path is not None:
        current["rootFolderPath"] = root_folder_path
    if tags is not None:
        current["tags"] = tags
    current["id"] = series_id
    return _request("PUT", f"series/{series_id}", json_body=current)


@mcp.tool
def delete_series(series_id: int, delete_files: bool = False, delete_folders: bool = False) -> dict[str, Any]:
    """Delete a series from Sonarr.
    
    Args:
        series_id: Sonarr series ID
        delete_files: Also delete episode files from disk
        delete_folders: Also delete series folders from disk
    """
    return _request("DELETE", f"series/{series_id}",
                    params={"deleteFiles": str(delete_files).lower(), "deleteFolder": str(delete_folders).lower()})


@mcp.tool
def search_series(series_id: int) -> dict[str, Any]:
    """Trigger a search for all monitored episodes of a series."""
    return _request("POST", "command", json_body={"name": "SeriesSearch", "seriesId": series_id})


@mcp.tool
def refresh_series(series_id: int) -> dict[str, Any]:
    """Refresh series info and metadata from TVDB."""
    return _request("POST", "command", json_body={"name": "RefreshSeries", "seriesId": series_id})


# ═══════════════════════════════════════
# QUALITY PROFILES
# ═══════════════════════════════════════

@mcp.tool
def list_quality_profiles() -> list[dict[str, Any]]:
    """List all quality profiles in Sonarr with their allowed qualities."""
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
    allowed_quality_ids: list[int] | None = None,
    upgrade_allowed: bool = True,
    language_id: int = 1,
) -> dict[str, Any]:
    """Create a new quality profile in Sonarr.
    
    IMPORTANT: Due to Sonarr's strict item validator, this creates the profile
    by cloning the 'Any' profile structure and modifying it.
    
    Args:
        name: Profile display name
        cutoff_id: Quality ID to stop upgrading at (3=WEBDL-1080p, 7=Bluray-1080p, etc.)
        allowed_quality_ids: List of quality IDs to allow. None = allow 1080p variants
        upgrade_allowed: Allow automatic upgrades
        language_id: Language profile ID (1=English)
    """
    if allowed_quality_ids is None:
        allowed_quality_ids = [3, 5, 6, 7, 14, 15]  # 1080p + 720p x264
    
    # Build full items list matching Sonarr's validation
    all_qualities = [
        (0, False), (24, False), (25, False), (26, False), (27, False),
        (29, False), (28, False), (20, False), (21, False), (1, False),
        (2, False), (23, False), (4, False), (9, False), (10, False),
        (30, False), (16, False), (19, False), (31, False), (22, False),
        (5, True, 14, True, 1001, "WEB 720p"),
        (6, False),
        (7, False),
        (3, True, 15, True, 1002, "WEB 1080p"),
        (18, False, 17, False, 1003, "WEB 2160p"),
        (8, False, 12, False, 1000, "WEB 480p"),
    ]
    
    items = []
    for entry in all_qualities:
        if len(entry) == 2:
            qid, allowed = entry
            allowed_final = qid in allowed_quality_ids or allowed
            items.append({"quality": {"id": qid}, "items": [], "allowed": allowed_final})
        elif len(entry) == 6:
            parent_id, parent_allowed, child_id, child_allowed, group_id, group_name = entry
            items.append({
                "name": group_name,
                "items": [
                    {"quality": {"id": child_id}, "items": [], "allowed": child_allowed or child_id in allowed_quality_ids},
                    {"quality": {"id": parent_id}, "items": [], "allowed": parent_allowed or parent_id in allowed_quality_ids},
                ],
                "allowed": parent_allowed or parent_id in allowed_quality_ids,
                "id": group_id,
            })
    
    body = {
        "name": name,
        "upgradeAllowed": upgrade_allowed,
        "cutoff": cutoff_id,
        "items": items,
        "formatItems": [
            {"format": 551, "name": "x265", "score": -10000},
            {"format": 552, "name": "LQ", "score": -10000},
            {"format": 553, "name": "No-RlsGroup", "score": -10000},
            {"format": 554, "name": "MULTI", "score": 500},
            {"format": 555, "name": "VOSTFR", "score": -50},
            {"format": 545, "name": "VFF", "score": 0},
            {"format": 546, "name": "VOF", "score": 0},
            {"format": 547, "name": "VFI", "score": 0},
            {"format": 548, "name": "VF2", "score": 0},
            {"format": 549, "name": "VFQ", "score": 0},
            {"format": 550, "name": "VQ", "score": 0},
        ],
        "minFormatScore": 0,
        "cutoffFormatScore": 0,
        "minUpgradeFormatScore": 1,
        "language": {"id": language_id},
    }
    return _request("POST", "qualityprofile", json_body=body)


@mcp.tool
def update_quality_profile(
    profile_id: int,
    name: str | None = None,
    cutoff_id: int | None = None,
    upgrade_allowed: bool | None = None,
    language_id: int | None = None,
) -> dict[str, Any]:
    """Update a quality profile (name, cutoff, upgrade, language)."""
    current = _request("GET", f"qualityprofile/{profile_id}")
    current["id"] = profile_id
    if name is not None:
        current["name"] = name
    if cutoff_id is not None:
        current["cutoff"] = cutoff_id
    if upgrade_allowed is not None:
        current["upgradeAllowed"] = upgrade_allowed
    if language_id is not None:
        current["language"] = {"id": language_id}
    del current["id"]  # Remove id before returning
    return _request("PUT", f"qualityprofile/{profile_id}", json_body=current)


@mcp.tool
def delete_quality_profile(profile_id: int) -> dict[str, Any]:
    """Delete a quality profile."""
    return _request("DELETE", f"qualityprofile/{profile_id}")


# ═══════════════════════════════════════
# EPISODES
# ═══════════════════════════════════════

@mcp.tool
def list_episodes(series_id: int, season_number: int | None = None) -> list[dict[str, Any]]:
    """List episodes for a series. Optionally filter by season number."""
    params: dict[str, Any] = {"seriesId": series_id}
    if season_number is not None:
        params["seasonNumber"] = season_number
    return _request("GET", "episode", params=params)


@mcp.tool
def get_episode(episode_id: int) -> dict[str, Any]:
    """Get a specific episode by its ID."""
    return _request("GET", f"episode/{episode_id}")


@mcp.tool
def update_episode(episode_id: int, monitored: bool | None = None) -> dict[str, Any]:
    """Update an episode (e.g. toggle monitored status)."""
    current = _request("GET", f"episode/{episode_id}")
    if monitored is not None:
        current["monitored"] = monitored
    return _request("PUT", f"episode/{episode_id}", json_body=current)


# ═══════════════════════════════════════
# EPISODE FILES
# ═══════════════════════════════════════

@mcp.tool
def list_episode_files(series_id: int) -> list[dict[str, Any]]:
    """List episode files for a series (quality, size, path, codecs)."""
    return _request("GET", "episodefile", params={"seriesId": series_id})


@mcp.tool
def get_episode_file(file_id: int) -> dict[str, Any]:
    """Get a specific episode file by its ID."""
    return _request("GET", f"episodefile/{file_id}")


# ═══════════════════════════════════════
# QUEUE
# ═══════════════════════════════════════

@mcp.tool
def list_queue(page: int = 1, page_size: int = 50, include_series: bool = True, include_episode: bool = True) -> dict[str, Any]:
    """List the Sonarr download queue (active/pending downloads)."""
    return _request("GET", "queue", params={
        "page": page, "pageSize": page_size,
        "includeSeries": str(include_series).lower(),
        "includeEpisode": str(include_episode).lower(),
    })


# ═══════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════

@mcp.tool
def list_history(page: int = 1, page_size: int = 50, include_series: bool = True, include_episode: bool = True) -> dict[str, Any]:
    """List Sonarr history (downloaded, imported, grabbed, deleted episodes)."""
    return _request("GET", "history", params={
        "page": page, "pageSize": page_size,
        "sortKey": "date", "sortDirection": "descending",
        "includeSeries": str(include_series).lower(),
        "includeEpisode": str(include_episode).lower(),
    })


# ═══════════════════════════════════════
# WANTED / MISSING
# ═══════════════════════════════════════

@mcp.tool
def list_wanted_missing(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """List episodes that are monitored but missing (not yet downloaded)."""
    return _request("GET", "wanted/missing", params={
        "page": page, "pageSize": page_size,
        "sortKey": "airDateUtc", "sortDirection": "descending",
        "monitored": "true",
    })


@mcp.tool
def list_wanted_cutoff_unmet(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """List episodes that don't meet the quality cutoff yet."""
    return _request("GET", "wanted/cutoff", params={
        "page": page, "pageSize": page_size,
        "monitored": "true",
    })


# ═══════════════════════════════════════
# CALENDAR
# ═══════════════════════════════════════

@mcp.tool
def get_calendar(start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    """Get upcoming/scheduled episodes in a date range.
    
    Args:
        start: ISO 8601 start date (default: today)
        end: ISO 8601 end date (default: +7 days)
    """
    params = {"includeSeries": "true", "includeEpisodeFile": "true"}
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
    """List all recent/running Sonarr commands."""
    return _request("GET", "command")


@mcp.tool
def send_command(
    name: str,
    series_id: int | None = None,
    episode_ids: list[int] | None = None,
    season_number: int | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Send a command to Sonarr (RssSync, RefreshSeries, EpisodeSearch, etc.).
    
    Args:
        name: Command name (RssSync, RefreshSeries, SeriesSearch, EpisodeSearch, SeasonsSearch, ...)
        series_id: Series ID (for RefreshSeries, SeriesSearch, SeasonsSearch)
        episode_ids: List of episode IDs (for EpisodeSearch)
        season_number: Season number (for SeasonsSearch)
        path: File path (for DownloadedEpisodesScan)
    """
    body: dict[str, Any] = {"name": name}
    if series_id is not None:
        body["seriesId"] = series_id
    if episode_ids is not None:
        body["episodeIds"] = episode_ids
    if season_number is not None:
        body["seasonNumber"] = season_number
    if path is not None:
        body["path"] = path
    return _request("POST", "command", json_body=body)


# ═══════════════════════════════════════
# ROOT FOLDERS
# ═══════════════════════════════════════

@mcp.tool
def list_root_folders() -> list[dict[str, Any]]:
    """List all root folders configured in Sonarr."""
    return _request("GET", "rootfolder")


# ═══════════════════════════════════════
# LANGUAGE PROFILES
# ═══════════════════════════════════════

@mcp.tool
def list_language_profiles() -> list[dict[str, Any]]:
    """List all language profiles in Sonarr."""
    return _request("GET", "languageprofile")


# ═══════════════════════════════════════
# TAGS
# ═══════════════════════════════════════

@mcp.tool
def list_tags() -> list[dict[str, Any]]:
    """List all tags in Sonarr."""
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
    """List all configured indexers in Sonarr."""
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
    """List all configured download clients in Sonarr."""
    return _request("GET", "downloadclient")


# ═══════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════

@mcp.tool
def list_notifications() -> list[dict[str, Any]]:
    """List all notification/connection configurations."""
    return _request("GET", "notification")


# ═══════════════════════════════════════
# RELEASES
# ═══════════════════════════════════════

@mcp.tool
def search_releases(episode_id: int) -> list[dict[str, Any]]:
    """Search for available releases for an episode (manual search)."""
    return _request("GET", "release", params={"episodeId": episode_id})


# ═══════════════════════════════════════
# CUSTOM FORMATS
# ═══════════════════════════════════════

@mcp.tool
def list_custom_formats() -> list[dict[str, Any]]:
    """List all custom formats in Sonarr."""
    return _request("GET", "customformat")


# ═══════════════════════════════════════
# MEDIA MANAGEMENT CONFIG
# ═══════════════════════════════════════

@mcp.tool
def get_media_management_config() -> dict[str, Any]:
    """Get Media Management settings (naming, root folders, etc.)."""
    return _request("GET", "config/mediamanagement")


@mcp.tool
def get_naming_config() -> dict[str, Any]:
    """Get naming configuration (file/folder naming patterns)."""
    return _request("GET", "config/naming")


@mcp.tool
def get_naming_examples() -> list[dict[str, Any]]:
    """Get example file names based on current naming config."""
    return _request("GET", "config/naming/examples")


# ═══════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════

@mcp.tool
def get_health() -> list[dict[str, Any]]:
    """Get Sonarr health checks — returns warnings/errors if any issues."""
    return _request("GET", "health")


# ═══════════════════════════════════════
# DISK SPACE
# ═══════════════════════════════════════

@mcp.tool
def get_disk_space() -> list[dict[str, Any]]:
    """Get disk space information for all mounted volumes."""
    return _request("GET", "diskspace")


# ═══════════════════════════════════════
# LOGS
# ═══════════════════════════════════════

@mcp.tool
def get_logs(page: int = 1, page_size: int = 50, level: str = "info") -> dict[str, Any]:
    """Get Sonarr system logs. Level: info, warn, error, debug, trace."""
    return _request("GET", "log", params={
        "page": page, "pageSize": page_size,
        "level": level, "sortKey": "time", "sortDirection": "descending",
    })


# ═══════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════

@mcp.tool
def get_update_info() -> dict[str, Any]:
    """Get available update information (currently installed vs available)."""
    return _request("GET", "update")


# ═══════════════════════════════════════
# RAW API ACCESS (CATCH-ALL)
# ═══════════════════════════════════════

@mcp.tool
def api(method: str, path: str, query: str = "{}", body: str = "{}") -> Any:
    """Catch-all Sonarr API call. Use for any endpoint not covered by other tools.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path AFTER /api/v3/ (e.g. 'releaseprofile', 'metadata')
        query: JSON query parameters as string (e.g. '{"pageSize":50}')
        body: JSON request body as string (e.g. '{"name":"RssSync"}')
    """
    params = json.loads(query) if query and query != "{}" else None
    json_body = json.loads(body) if body and body != "{}" else None
    return _request(method, path, params=params, json_body=json_body)


if __name__ == "__main__":
    mcp.run()
