"""
Prowlarr MCP Server — Read-only API coverage via FastMCP
READ-ONLY ONLY — Indexer manager queries only, no modifications!
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Prowlarr")

PROWLARR_URL = os.getenv("PROWLARR_URL") or "http://100.64.0.2:9696"
REQUEST_TIMEOUT = float(os.getenv("PROWLARR_TIMEOUT", "15"))

# API key from env var or file
API_KEY = os.getenv("PROWLARR_API_KEY")
if not API_KEY:
    key_file = os.path.expanduser("~/.hermes/prowlarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            API_KEY = f.read().strip()
if not API_KEY:
    raise RuntimeError("PROWLARR_API_KEY env var or ~/.hermes/prowlarr_api_key.txt required")

_client = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=REQUEST_TIMEOUT)
    return _client


def _request(method: str, path: str, *, params: dict | None = None) -> Any:
    client = _get_client()
    url = f"{PROWLARR_URL.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {"X-Api-Key": API_KEY}
    resp = client.request(method, url, params=params, headers=headers)
    if resp.status_code == 401:
        raise RuntimeError(f"Prowlarr auth failed (401) — check API key")
    resp.raise_for_status()
    if not resp.content or resp.status_code == 204:
        return {"success": True}
    try:
        return resp.json()
    except (json.JSONDecodeError, Exception):
        return {"text": resp.text, "status": resp.status_code}


# ═══════════════════════════════════════
# SYSTEM
# ═══════════════════════════════════════

@mcp.tool
def system_status() -> dict[str, Any]:
    """Get Prowlarr system status (version, platform, DB, etc.). READ-ONLY."""
    return _request("GET", "system/status")


@mcp.tool
def system_routes() -> list[dict[str, Any]]:
    """Get all API routes registered in Prowlarr. READ-ONLY."""
    return _request("GET", "system/routes")


@mcp.tool
def system_tasks() -> list[dict[str, Any]]:
    """Get all system tasks and their status. READ-ONLY."""
    return _request("GET", "system/task")


@mcp.tool
def system_task(id: int) -> dict[str, Any]:
    """Get a specific system task by ID. READ-ONLY.

    Args:
        id: Task ID
    """
    return _request("GET", f"system/task/{id}")


# ═══════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════

@mcp.tool
def health() -> list[dict[str, Any]]:
    """Get all health checks. READ-ONLY."""
    return _request("GET", "health")


# ═══════════════════════════════════════
# INDEXERS
# ═══════════════════════════════════════

@mcp.tool
def indexers() -> list[dict[str, Any]]:
    """Get all configured indexers. READ-ONLY."""
    return _request("GET", "indexer")


@mcp.tool
def indexer(id: int) -> dict[str, Any]:
    """Get a specific indexer by ID. READ-ONLY.

    Args:
        id: Indexer ID
    """
    return _request("GET", f"indexer/{id}")


@mcp.tool
def indexer_schema() -> list[dict[str, Any]]:
    """Get available indexer definitions/schema. READ-ONLY."""
    return _request("GET", "indexer/schema")


@mcp.tool
def indexer_categories() -> dict[str, Any]:
    """Get default indexer categories. READ-ONLY."""
    return _request("GET", "indexer/categories")


@mcp.tool
def indexer_stats() -> dict[str, Any]:
    """Get indexer statistics (query counts, grabs, etc.). READ-ONLY."""
    return _request("GET", "indexerstats")


@mcp.tool
def indexer_status() -> list[dict[str, Any]]:
    """Get indexer connection status. READ-ONLY."""
    return _request("GET", "indexerstatus")


# ═══════════════════════════════════════
# APPLICATIONS (Sonarr/Radarr/Lidarr links)
# ═══════════════════════════════════════

@mcp.tool
def applications() -> list[dict[str, Any]]:
    """Get all configured applications (linked *arr services). READ-ONLY."""
    return _request("GET", "applications")


@mcp.tool
def application(id: int) -> dict[str, Any]:
    """Get a specific application by ID. READ-ONLY.

    Args:
        id: Application ID
    """
    return _request("GET", f"applications/{id}")


@mcp.tool
def application_schema() -> list[dict[str, Any]]:
    """Get available application provider schema. READ-ONLY."""
    return _request("GET", "applications/schema")


# ═══════════════════════════════════════
# DOWNLOAD CLIENTS
# ═══════════════════════════════════════

@mcp.tool
def download_clients() -> list[dict[str, Any]]:
    """Get all configured download clients. READ-ONLY."""
    return _request("GET", "downloadclient")


@mcp.tool
def download_client(id: int) -> dict[str, Any]:
    """Get a specific download client by ID. READ-ONLY.

    Args:
        id: Download client ID
    """
    return _request("GET", f"downloadclient/{id}")


@mcp.tool
def download_client_schema() -> list[dict[str, Any]]:
    """Get available download client provider schema. READ-ONLY."""
    return _request("GET", "downloadclient/schema")


# ═══════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════

@mcp.tool
def notifications() -> list[dict[str, Any]]:
    """Get all configured notifications. READ-ONLY."""
    return _request("GET", "notification")


@mcp.tool
def notification(id: int) -> dict[str, Any]:
    """Get a specific notification by ID. READ-ONLY.

    Args:
        id: Notification ID
    """
    return _request("GET", f"notification/{id}")


@mcp.tool
def notification_schema() -> list[dict[str, Any]]:
    """Get available notification provider schema. READ-ONLY."""
    return _request("GET", "notification/schema")


# ═══════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════

@mcp.tool
def history(
    page: int = 1,
    page_size: int = 50,
    sort_key: str = "date",
    sort_direction: str = "descending",
    event_type: list[str] | None = None,
    successful: bool | None = None,
    indexer_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Get paginated history. READ-ONLY.

    Args:
        page: Page number (default: 1)
        page_size: Results per page (default: 50)
        sort_key: Sort field (date, indexerId, etc.)
        sort_direction: ascending or descending
        event_type: Filter by event type(s) (e.g. ['1', '2', '3', '4'])
        successful: Filter by success status
        indexer_ids: Filter by indexer IDs
    """
    params: dict[str, Any] = {
        "page": page,
        "pageSize": page_size,
        "sortKey": sort_key,
        "sortDirection": sort_direction,
    }
    if event_type:
        params["eventType"] = ",".join(str(e) for e in event_type)
    if successful is not None:
        params["successful"] = str(successful).lower()
    if indexer_ids:
        params["indexerIds"] = ",".join(str(i) for i in indexer_ids)
    return _request("GET", "history", params=params)


@mcp.tool
def history_since(date: str, event_type: str | None = None) -> list[dict[str, Any]]:
    """Get history since a specific date. READ-ONLY.

    Args:
        date: ISO date string (e.g. '2026-01-01T00:00:00Z')
        event_type: Filter by event type
    """
    params: dict[str, Any] = {"date": date}
    if event_type:
        params["eventType"] = event_type
    return _request("GET", "history/since", params=params)


@mcp.tool
def history_by_indexer(
    indexer_id: int,
    event_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Get history for a specific indexer. READ-ONLY.

    Args:
        indexer_id: Indexer ID
        event_type: Filter by event type
        limit: Max results (default: 50)
    """
    params: dict[str, Any] = {"indexerId": indexer_id, "limit": limit}
    if event_type:
        params["eventType"] = event_type
    return _request("GET", "history/indexer", params=params)


# ═══════════════════════════════════════
# TAGS
# ═══════════════════════════════════════

@mcp.tool
def tags() -> list[dict[str, Any]]:
    """Get all tags. READ-ONLY."""
    return _request("GET", "tag")


@mcp.tool
def tag(id: int) -> dict[str, Any]:
    """Get a specific tag by ID. READ-ONLY.

    Args:
        id: Tag ID
    """
    return _request("GET", f"tag/{id}")


@mcp.tool
def tag_details() -> list[dict[str, Any]]:
    """Get tag details with label/usage info. READ-ONLY."""
    return _request("GET", "tag/detail")


@mcp.tool
def tag_detail(id: int) -> dict[str, Any]:
    """Get a specific tag detail by ID. READ-ONLY.

    Args:
        id: Tag detail ID
    """
    return _request("GET", f"tag/detail/{id}")


# ═══════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════

@mcp.tool
def commands() -> list[dict[str, Any]]:
    """Get all queued/completed commands. READ-ONLY."""
    return _request("GET", "command")


@mcp.tool
def command(id: int) -> dict[str, Any]:
    """Get a specific command by ID. READ-ONLY.

    Args:
        id: Command ID
    """
    return _request("GET", f"command/{id}")


# ═══════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════

@mcp.tool
def search_results(
    query: str,
    indexer_ids: list[int] | None = None,
    type: str = "search",
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search for releases across indexers. READ-ONLY.

    Args:
        query: Search query (e.g. 'Star Wars')
        indexer_ids: Filter by specific indexer IDs
        type: Search type (search, tvsearch, moviesearch, booksearch)
        limit: Max results (default: 100)
        offset: Results offset
    """
    params: dict[str, Any] = {
        "query": query,
        "type": type,
        "limit": limit,
        "offset": offset,
    }
    if indexer_ids:
        params["indexerIds"] = ",".join(str(i) for i in indexer_ids)
    return _request("GET", "search", params=params)


# ═══════════════════════════════════════
# BACKUPS
# ═══════════════════════════════════════

@mcp.tool
def backups() -> list[dict[str, Any]]:
    """Get all backups. READ-ONLY."""
    return _request("GET", "system/backup")


# ═══════════════════════════════════════
# LOG
# ═══════════════════════════════════════

@mcp.tool
def log(
    page: int = 1,
    page_size: int = 50,
    level: str | None = None,
) -> dict[str, Any]:
    """Get application log entries. READ-ONLY.

    Args:
        page: Page number (default: 1)
        page_size: Results per page (default: 50)
        level: Filter by log level (Info, Warn, Error, Debug, Trace)
    """
    params: dict[str, Any] = {"page": page, "pageSize": page_size}
    if level:
        params["level"] = level
    return _request("GET", "log", params=params)


@mcp.tool
def log_files() -> list[dict[str, Any]]:
    """Get list of log files. READ-ONLY."""
    return _request("GET", "log/file")


# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════

@mcp.tool
def host_config() -> dict[str, Any]:
    """Get Prowlarr host configuration. READ-ONLY."""
    return _request("GET", "config/host")


@mcp.tool
def ui_config() -> dict[str, Any]:
    """Get Prowlarr UI configuration. READ-ONLY."""
    return _request("GET", "config/ui")


@mcp.tool
def download_client_config() -> dict[str, Any]:
    """Get download client configuration. READ-ONLY."""
    return _request("GET", "config/downloadclient")


# ═══════════════════════════════════════
# APP PROFILES
# ═══════════════════════════════════════

@mcp.tool
def app_profiles() -> list[dict[str, Any]]:
    """Get all application profiles (sync levels). READ-ONLY."""
    return _request("GET", "appprofile")


@mcp.tool
def app_profile(id: int) -> dict[str, Any]:
    """Get a specific application profile by ID. READ-ONLY.

    Args:
        id: Profile ID
    """
    return _request("GET", f"appprofile/{id}")


@mcp.tool
def app_profile_schema() -> list[dict[str, Any]]:
    """Get application profile schema. READ-ONLY."""
    return _request("GET", "appprofile/schema")


# ═══════════════════════════════════════
# CUSTOM FILTERS
# ═══════════════════════════════════════

@mcp.tool
def custom_filters() -> list[dict[str, Any]]:
    """Get all custom filters. READ-ONLY."""
    return _request("GET", "customfilter")


@mcp.tool
def custom_filter(id: int) -> dict[str, Any]:
    """Get a specific custom filter by ID. READ-ONLY.

    Args:
        id: Filter ID
    """
    return _request("GET", f"customfilter/{id}")


# ═══════════════════════════════════════
# FILESYSTEM
# ═══════════════════════════════════════

@mcp.tool
def filesystem_list(
    path: str,
    include_files: bool = False,
    allow_folders_without_trailing_slashes: bool = False,
) -> list[dict[str, Any]]:
    """Browse filesystem. READ-ONLY.

    Args:
        path: Directory path to browse
        include_files: Include files in listing
        allow_folders_without_trailing_slashes: Allow folders without trailing /
    """
    params: dict[str, Any] = {
        "path": path,
        "includeFiles": str(include_files).lower(),
        "allowFoldersWithoutTrailingSlashes": str(allow_folders_without_trailing_slashes).lower(),
    }
    return _request("GET", "filesystem", params=params)


@mcp.tool
def filesystem_type(path: str) -> dict[str, Any]:
    """Get file type info. READ-ONLY.

    Args:
        path: File/directory path
    """
    return _request("GET", "filesystem/type", params={"path": path})


# ═══════════════════════════════════════
# UPDATES
# ═══════════════════════════════════════

@mcp.tool
def updates() -> list[dict[str, Any]]:
    """Get available updates. READ-ONLY."""
    return _request("GET", "update")


# ═══════════════════════════════════════
# RAW API (READ-ONLY CATCH-ALL)
# ═══════════════════════════════════════

@mcp.tool
def api(path: str, query: str = "{}") -> Any:
    """Catch-all read-only Prowlarr API call.

    WARNING: READ-ONLY. Only GET requests.
    Path examples: system/status, indexer, applications, history, health
    """
    params = json.loads(query) if query and query != "{}" else None
    return _request("GET", path, params=params)


if __name__ == "__main__":
    mcp.run()
