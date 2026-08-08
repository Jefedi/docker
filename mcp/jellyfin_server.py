"""
Jellyfin MCP Server — Full API coverage via FastMCP
Connects to jFlix (jellyfin.jefe.ovh) via HTTPS/Pangolin
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Jellyfin")

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "https://jflix.jefe.al")
JELLYFIN_TOKEN = os.getenv("JELLYFIN_TOKEN")
if not JELLYFIN_TOKEN:
    token_file = os.path.expanduser("~/.hermes/jellyfin_token.txt")
    if os.path.exists(token_file):
        with open(token_file) as f:
            JELLYFIN_TOKEN = f.read().strip()
if not JELLYFIN_TOKEN:
    raise RuntimeError("JELLYFIN_TOKEN env var or ~/.hermes/jellyfin_token.txt is required")
REQUEST_TIMEOUT = float(os.getenv("JELLYFIN_TIMEOUT", "30"))


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-Emby-Token": JELLYFIN_TOKEN,
    }


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
) -> Any:
    url = f"{JELLYFIN_URL.rstrip('/')}/{path.lstrip('/')}"
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
def get_system_info() -> dict[str, Any]:
    """Get Jellyfin system information (version, server name, OS, etc.)."""
    return _request("GET", "System/Info")


@mcp.tool
def get_system_info_public() -> dict[str, Any]:
    """Get public system info (no auth needed)."""
    return _request("GET", "System/Info/Public")


@mcp.tool
def get_system_configuration() -> dict[str, Any]:
    """Get Jellyfin server configuration."""
    return _request("GET", "System/Configuration")


@mcp.tool
def get_activity_log(limit: int = 30) -> dict[str, Any]:
    """Get recent activity log entries."""
    return _request("GET", "System/ActivityLog/Entries", params={"Limit": limit})


# ═══════════════════════════════════════
# USERS
# ═══════════════════════════════════════

@mcp.tool
def list_users() -> list[dict[str, Any]]:
    """List all Jellyfin users."""
    return _request("GET", "Users")


@mcp.tool
def get_user(user_id: str) -> dict[str, Any]:
    """Get a specific user by ID."""
    return _request("GET", f"Users/{user_id}")


@mcp.tool
def get_user_views(user_id: str) -> dict[str, Any]:
    """Get views (libraries) accessible to a user."""
    return _request("GET", f"Users/{user_id}/Views")


# ═══════════════════════════════════════
# LIBRARIES / VIEWS
# ═══════════════════════════════════════

@mcp.tool
def list_libraries() -> list[dict[str, Any]]:
    """List all media libraries (virtual folders / views)."""
    return _request("GET", "Library/MediaFolders")


@mcp.tool
def get_virtual_folders() -> list[dict[str, Any]]:
    """List virtual folders (library definitions with paths)."""
    return _request("GET", "Library/VirtualFolders")


# ═══════════════════════════════════════
# ITEMS (generic browsing/search)
# ═══════════════════════════════════════

@mcp.tool
def get_items(
    user_id: str,
    parent_id: str | None = None,
    include_types: str = "Movie,Series,Episode",
    limit: int = 50,
    start_index: int = 0,
    recursive: bool = True,
    sort_by: str = "SortName",
    sort_order: str = "Ascending",
    fields: str = "Overview,UserData,SeriesName,ParentIndexNumber,IndexNumber,ProductionYear",
) -> dict[str, Any]:
    """Browse/get items in the library.
    
    Args:
        user_id: User ID
        parent_id: Parent folder/item ID (optional)
        include_types: Comma-separated item types
        limit: Max results
        start_index: Pagination offset
        recursive: Search recursively in subfolders
        sort_by: Sort field (SortName, DateCreated, PremiereDate, etc.)
        sort_order: Ascending or Descending
        fields: Comma-separated fields to include
    """
    params = {
        "userId": user_id, "Recursive": str(recursive).lower(),
        "IncludeItemTypes": include_types, "Limit": limit,
        "StartIndex": start_index, "SortBy": sort_by,
        "SortOrder": sort_order, "Fields": fields,
    }
    if parent_id:
        params["ParentId"] = parent_id
    return _request("GET", "Items", params=params)


@mcp.tool
def get_item(item_id: str, user_id: str | None = None) -> dict[str, Any]:
    """Get a specific item by ID."""
    params = {}
    if user_id:
        params["userId"] = user_id
    return _request("GET", f"Items/{item_id}", params=params or None)


@mcp.tool
def search_items(query: str, user_id: str, include_types: str = "Movie,Episode,Series", limit: int = 20) -> dict[str, Any]:
    """Search for items by name.
    
    Args:
        query: Search term
        user_id: User ID
        include_types: Types to search (Movie, Series, Episode, Audio, Person, etc.)
        limit: Max results
    """
    return _request("GET", "Items", params={
        "userId": user_id, "searchTerm": query,
        "Recursive": "true", "IncludeItemTypes": include_types,
        "Limit": limit, "Fields": "Overview,SeriesName,ProductionYear",
    })


@mcp.tool
def get_items_latest(user_id: str, include_types: str = "Movie,Episode", limit: int = 20) -> list[dict[str, Any]]:
    """Get most recently added items.
    
    Args:
        user_id: User ID
        include_types: Types (Movie, Episode, Series, etc.)
        limit: Max results
    """
    return _request("GET", f"Users/{user_id}/Items/Latest", params={
        "Limit": limit, "IncludeItemTypes": include_types,
        "GroupItems": "true", "Fields": "Overview,UserData,SeriesName,ProductionYear",
    })


@mcp.tool
def get_resume_items(user_id: str, limit: int = 20) -> dict[str, Any]:
    """Get items that the user has partially watched (resume playback)."""
    return _request("GET", f"Users/{user_id}/Items/Resume", params={
        "Limit": limit, "Fields": "Overview,UserData,SeriesName,ParentIndexNumber,IndexNumber",
    })


@mcp.tool
def get_next_up(user_id: str, limit: int = 20) -> dict[str, Any]:
    """Get next unwatched episodes for shows the user watches."""
    return _request("GET", "Shows/NextUp", params={
        "userId": user_id, "Limit": limit,
        "Fields": "Overview,SeriesName,ParentIndexNumber,IndexNumber",
    })


@mcp.tool
def get_play_history(user_id: str, include_types: str = "Movie,Episode", limit: int = 50) -> dict[str, Any]:
    """Get recently played/watched items (play history).
    
    Args:
        user_id: User ID
        include_types: Types (Movie, Episode, Audio, MusicVideo)
        limit: Max results
    """
    return _request("GET", f"Users/{user_id}/Items", params={
        "Filters": "IsPlayed", "SortBy": "DatePlayed",
        "SortOrder": "Descending", "Recursive": "true",
        "IncludeItemTypes": include_types, "Limit": limit,
        "Fields": "Overview,UserData,SeriesName,ParentIndexNumber,IndexNumber,ProductionYear",
    })


# ═══════════════════════════════════════
# GENRES, STUDIOS, PERSONS
# ═══════════════════════════════════════

@mcp.tool
def list_genres(user_id: str, limit: int = 100) -> dict[str, Any]:
    """List all genres in the library."""
    return _request("GET", "Genres", params={"userId": user_id, "Limit": limit})


@mcp.tool
def list_studios(user_id: str) -> dict[str, Any]:
    """List all studios."""
    return _request("GET", "Studios", params={"userId": user_id})


@mcp.tool
def list_persons(user_id: str, limit: int = 50) -> dict[str, Any]:
    """List all persons (actors, directors, etc.)."""
    return _request("GET", "Persons", params={"userId": user_id, "Limit": limit})


# ═══════════════════════════════════════
# SESSIONS & PLAYBACK
# ═══════════════════════════════════════

@mcp.tool
def get_now_playing(active_within_seconds: int = 60) -> list[dict[str, Any]]:
    """Get currently active sessions (what's being played right now)."""
    return _request("GET", "Sessions", params={"activeWithinSeconds": active_within_seconds})


@mcp.tool
def get_sessions() -> list[dict[str, Any]]:
    """Get all active sessions."""
    return _request("GET", "Sessions")


@mcp.tool
def send_playback_command(session_id: str, command: str) -> dict[str, Any]:
    """Send a remote control command to a session.
    
    Commands: Mute, Unmute, ToggleMute, VolumeUp, VolumeDown, SetVolume,
    TogglePause, Pause, Unpause, Stop, NextTrack, PreviousTrack, Seek,
    Rewind, FastForward, SetSubtitleStreamIndex, SetAudioStreamIndex,
    ToggleFullscreen, GoHome, GoToSettings
    """
    return _request("POST", f"Sessions/{session_id}/Command/{command}")


@mcp.tool
def play_remote(session_id: str, item_ids: str, mode: str = "PlayNow") -> dict[str, Any]:
    """Play media on a remote session.
    
    Args:
        session_id: Active session ID
        item_ids: Comma-separated item IDs to play
        mode: PlayNow, PlayNext, PlayLast, or Queue
    """
    params = {"itemIds": item_ids, "playCommand": mode}
    return _request("POST", f"Sessions/{session_id}/Playing", params=params)


# ═══════════════════════════════════════
# WATCH STATUS
# ═══════════════════════════════════════

@mcp.tool
def mark_played(user_id: str, item_id: str) -> dict[str, Any]:
    """Mark an item as played/watched."""
    return _request("POST", f"Users/{user_id}/PlayedItems/{item_id}")


@mcp.tool
def mark_unplayed(user_id: str, item_id: str) -> dict[str, Any]:
    """Mark an item as unplayed/unwatched."""
    return _request("DELETE", f"Users/{user_id}/PlayedItems/{item_id}")


@mcp.tool
def mark_favorite(user_id: str, item_id: str) -> dict[str, Any]:
    """Mark an item as favorite."""
    return _request("POST", f"Users/{user_id}/FavoriteItems/{item_id}")


@mcp.tool
def unmark_favorite(user_id: str, item_id: str) -> dict[str, Any]:
    """Unmark an item as favorite."""
    return _request("DELETE", f"Users/{user_id}/FavoriteItems/{item_id}")


# ═══════════════════════════════════════
# LIBRARY MANAGEMENT
# ═══════════════════════════════════════

@mcp.tool
def refresh_library() -> dict[str, Any]:
    """Trigger a full library refresh."""
    return _request("POST", "Library/Refresh")


@mcp.tool
def refresh_item(item_id: str) -> dict[str, Any]:
    """Refresh metadata for a specific item."""
    return _request("POST", f"Items/{item_id}/Refresh")


# ═══════════════════════════════════════
# ITEM DETAILS
# ═══════════════════════════════════════

@mcp.tool
def get_item_ancestors(item_id: str, user_id: str | None = None) -> list[dict[str, Any]]:
    """Get parent items (ancestors) of an item."""
    params = {}
    if user_id:
        params["userId"] = user_id
    return _request("GET", f"Items/{item_id}/Ancestors", params=params or None)


@mcp.tool
def get_item_similar(item_id: str, limit: int = 20) -> dict[str, Any]:
    """Get similar items (recommendations)."""
    return _request("GET", f"Items/{item_id}/Similar", params={"Limit": limit})


@mcp.tool
def get_item_playback_info(item_id: str, user_id: str) -> dict[str, Any]:
    """Get playback info for an item (streams, codecs, direct play info)."""
    return _request("GET", f"Items/{item_id}/PlaybackInfo", params={"userId": user_id})


# ═══════════════════════════════════════
# COLLECTIONS / SEASONS / EPISODES
# ═══════════════════════════════════════

@mcp.tool
def get_seasons(series_id: str, user_id: str) -> dict[str, Any]:
    """Get all seasons for a series."""
    return _request("GET", f"Shows/{series_id}/Seasons", params={"userId": user_id})


@mcp.tool
def get_episodes(series_id: str, season_id: str, user_id: str) -> dict[str, Any]:
    """Get all episodes in a season."""
    return _request("GET", f"Shows/{series_id}/Episodes", params={
        "userId": user_id, "seasonId": season_id,
    })


# ═══════════════════════════════════════
# MUSIC
# ═══════════════════════════════════════

@mcp.tool
def list_artists(user_id: str, limit: int = 50) -> dict[str, Any]:
    """List all music artists."""
    return _request("GET", "Artists", params={"userId": user_id, "Limit": limit})


@mcp.tool
def list_album_artists(user_id: str, limit: int = 50) -> dict[str, Any]:
    """List all album artists."""
    return _request("GET", "AlbumArtists", params={"userId": user_id, "Limit": limit})


# ═══════════════════════════════════════
# LIVE TV
# ═══════════════════════════════════════

@mcp.tool
def get_live_tv_channels(user_id: str) -> dict[str, Any]:
    """Get Live TV channels."""
    return _request("GET", "LiveTv/Channels", params={"userId": user_id})


@mcp.tool
def get_live_tv_guide(user_id: str, limit: int = 50) -> dict[str, Any]:
    """Get Live TV guide/programs."""
    return _request("GET", "LiveTv/Programs", params={"userId": user_id, "Limit": limit})


# ═══════════════════════════════════════
# PLUGINS
# ═══════════════════════════════════════

@mcp.tool
def list_plugins() -> list[dict[str, Any]]:
    """List installed plugins."""
    return _request("GET", "Plugins")


# ═══════════════════════════════════════
# SCHEDULED TASKS
# ═══════════════════════════════════════

@mcp.tool
def list_scheduled_tasks() -> list[dict[str, Any]]:
    """List scheduled tasks."""
    return _request("GET", "ScheduledTasks")


# ═══════════════════════════════════════
# DEVICES
# ═══════════════════════════════════════

@mcp.tool
def list_devices() -> list[dict[str, Any]]:
    """List all devices that have connected."""
    return _request("GET", "Devices")


# ═══════════════════════════════════════
# SUGGESTIONS
# ═══════════════════════════════════════

@mcp.tool
def get_suggestions(user_id: str, limit: int = 20) -> dict[str, Any]:
    """Get suggested items for a user."""
    return _request("GET", "Users", params={
        "userId": user_id, "Limit": limit,
    })


# ═══════════════════════════════════════
# ITEM COUNTS
# ═══════════════════════════════════════

@mcp.tool
def get_item_counts(user_id: str) -> dict[str, Any]:
    """Get counts of items by type (movies, series, episodes, etc.)."""
    return _request("GET", "Items/Counts", params={"userId": user_id})


# ═══════════════════════════════════════
# IMAGES
# ═══════════════════════════════════════

@mcp.tool
def get_item_images(item_id: str) -> list[dict[str, Any]]:
    """Get image info for an item (posters, backdrops, etc.)."""
    return _request("GET", f"Items/{item_id}/Images")


# ═══════════════════════════════════════
# RAW API ACCESS (CATCH-ALL)
# ═══════════════════════════════════════

@mcp.tool
def read_api(path: str, query: str = "{}") -> Any:
    """Catch-all GET for Jellyfin API endpoints not covered by other tools.
    
    Examples: Search/Hints, Persons, Studios, Years, Users/{id}/Policy,
    System/Ping, System/Logs, Notifications/Admin, Channels, Trickplay/{id}
    """
    params = json.loads(query) if query and query != "{}" else None
    return _request("GET", path, params=params)


@mcp.tool
def write_api(method: str, path: str, query: str = "{}", body: str = "{}") -> Any:
    """Catch-all write operation for Jellyfin API.
    DANGEROUS: Can modify/delete items, rescan libraries, etc.
    
    Examples: Items/{id}/Refresh (POST), Users/New (POST),
    Library/VirtualFolders (POST/DELETE), System/Restart (POST)
    """
    params = json.loads(query) if query and query != "{}" else None
    json_body = json.loads(body) if body and body != "{}" else None
    return _request(method, path, params=params, json_body=json_body)


if __name__ == "__main__":
    mcp.run()
