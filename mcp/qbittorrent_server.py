"""
qBittorrent MCP Server — Read-only API coverage via FastMCP
READ-ONLY ONLY — Private trackers, NEVER delete/modify any torrent!
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("qBittorrent")

QB_URL = os.getenv("QB_URL") or "http://100.64.0.2:8090"
QB_USERNAME = os.getenv("QB_USERNAME", "jefe")
QB_PASSWORD = os.getenv("QB_PASSWORD")
if not QB_PASSWORD:
    pw_file = os.path.expanduser("~/.hermes/qb_password.txt")
    if os.path.exists(pw_file):
        with open(pw_file) as f:
            QB_PASSWORD = f.read().strip()
if not QB_PASSWORD:
    raise RuntimeError("QB_PASSWORD env var or ~/.hermes/qb_password.txt required")
REQUEST_TIMEOUT = float(os.getenv("QB_TIMEOUT", "15"))

_client = None

def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=REQUEST_TIMEOUT)
        # Login to get SID cookie
        login_resp = _client.post(
            f"{QB_URL.rstrip('/')}/api/v2/auth/login",
            data={"username": QB_USERNAME, "password": QB_PASSWORD},
        )
        if login_resp.status_code != 200 or login_resp.text != "Ok.":
            raise RuntimeError(f"qBittorrent login failed: {login_resp.text}")
    return _client


def _request(method: str, path: str, *, params: dict | None = None) -> Any:
    client = _get_client()
    url = f"{QB_URL.rstrip('/')}/api/v2/{path.lstrip('/')}"
    resp = client.request(method, url, params=params)
    if resp.status_code == 403:
        # Session expired, re-login
        global _client
        _client = None
        client = _get_client()
        resp = client.request(method, url, params=params)
    resp.raise_for_status()
    if not resp.content or resp.status_code == 204:
        return {"success": True}
    try:
        return resp.json()
    except (json.JSONDecodeError, Exception):
        return {"text": resp.text, "status": resp.status_code}


# ═══════════════════════════════════════
# APP INFO
# ═══════════════════════════════════════

@mcp.tool
def app_version() -> dict[str, Any]:
    """Get qBittorrent version."""
    return _request("GET", "app/version")


@mcp.tool
def app_web_api_version() -> dict[str, Any]:
    """Get qBittorrent Web API version."""
    return _request("GET", "app/webapiVersion")


@mcp.tool
def app_preferences() -> dict[str, Any]:
    """Get qBittorrent application preferences (settings)."""
    return _request("GET", "app/preferences")


@mcp.tool
def app_build_info() -> dict[str, Any]:
    """Get qBittorrent build info (Qt, libtorrent versions)."""
    return _request("GET", "app/buildInfo")


# ═══════════════════════════════════════
# TRANSFER INFO
# ═══════════════════════════════════════

@mcp.tool
def transfer_info() -> dict[str, Any]:
    """Get global transfer info (download/upload speed, ratios, etc.)."""
    return _request("GET", "transfer/info")


@mcp.tool
def transfer_speed_limits() -> dict[str, Any]:
    """Get current speed limits (global download/upload limit)."""
    return _request("GET", "transfer/speedLimits")


# ═══════════════════════════════════════
# TORRENTS — READ ONLY
# ═══════════════════════════════════════

@mcp.tool
def torrents_info(
    filter: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    sort: str | None = None,
    reverse: bool = False,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    """Get list of torrents. READ-ONLY.
    
    Args:
        filter: 'all', 'downloading', 'seeding', 'completed', 'paused', 'active', 'inactive', 'resumed', 'stalled', 'stalled_uploading', 'stalled_downloading', 'errored'
        category: Filter by category
        tag: Filter by tag
        sort: Sort field (name, size, ratio, added_on, etc.)
        reverse: Reverse sort
        limit: Max results
        offset: Pagination offset
    """
    params: dict[str, Any] = {}
    if filter:
        params["filter"] = filter
    if category:
        params["category"] = category
    if tag:
        params["tag"] = tag
    if sort:
        params["sort"] = sort
    if reverse:
        params["reverse"] = "true"
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    return _request("GET", "torrents/info", params=params or None)


@mcp.tool
def torrent_properties(hash: str) -> dict[str, Any]:
    """Get properties of a torrent by info hash. READ-ONLY."""
    return _request("GET", "torrents/properties", params={"hash": hash})


@mcp.tool
def torrent_trackers(hash: str) -> list[dict[str, Any]]:
    """Get trackers of a torrent by info hash. READ-ONLY."""
    return _request("GET", "torrents/trackers", params={"hash": hash})


@mcp.tool
def torrent_files(hash: str) -> list[dict[str, Any]]:
    """Get files inside a torrent by info hash. READ-ONLY."""
    return _request("GET", "torrents/files", params={"hash": hash})


@mcp.tool
def torrent_piece_states(hash: str) -> list[int]:
    """Get piece states of a torrent by info hash. READ-ONLY."""
    return _request("GET", "torrents/pieceStates", params={"hash": hash})


@mcp.tool
def torrent_piece_hashes(hash: str) -> list[str]:
    """Get piece hashes of a torrent by info hash. READ-ONLY."""
    return _request("GET", "torrents/pieceHashes", params={"hash": hash})


# ═══════════════════════════════════════
# SYNC
# ═══════════════════════════════════════

@mcp.tool
def sync_maindata(rid: int = 0) -> dict[str, Any]:
    """Get sync main data (torrents, categories, tags, server state).
    
    Args:
        rid: Response ID. 0 = full data, subsequent calls with previous response rid for incremental updates
    """
    return _request("GET", "sync/maindata", params={"rid": rid})


# ═══════════════════════════════════════
# TORRENT INFO BY STATUS
# ═══════════════════════════════════════

@mcp.tool
def torrents_active() -> list[dict[str, Any]]:
    """Get all active (downloading/seeding) torrents."""
    return _request("GET", "torrents/info", params={"filter": "active"})


@mcp.tool
def torrents_downloading() -> list[dict[str, Any]]:
    """Get all currently downloading torrents."""
    return _request("GET", "torrents/info", params={"filter": "downloading"})


@mcp.tool
def torrents_completed() -> list[dict[str, Any]]:
    """Get all completed torrents (finished downloading, may still seed)."""
    return _request("GET", "torrents/info", params={"filter": "completed"})


@mcp.tool
def torrents_seeding() -> list[dict[str, Any]]:
    """Get all seeding torrents."""
    return _request("GET", "torrents/info", params={"filter": "seeding"})


@mcp.tool
def torrents_paused() -> list[dict[str, Any]]:
    """Get all paused torrents."""
    return _request("GET", "torrents/info", params={"filter": "paused"})


@mcp.tool
def torrents_errored() -> list[dict[str, Any]]:
    """Get all errored torrents."""
    return _request("GET", "torrents/info", params={"filter": "errored"})


# ═══════════════════════════════════════
# CATEGORIES & TAGS — READ ONLY
# ═══════════════════════════════════════

@mcp.tool
def list_categories() -> dict[str, Any]:
    """Get all categories. READ-ONLY."""
    return _request("GET", "torrents/categories")


@mcp.tool
def list_tags() -> list[str]:
    """Get all tags. READ-ONLY."""
    return _request("GET", "torrents/tags")


# ═══════════════════════════════════════
# RSS
# ═══════════════════════════════════════

@mcp.tool
def rss_items() -> dict[str, Any]:
    """Get RSS items. READ-ONLY."""
    return _request("GET", "rss/items")


# ═══════════════════════════════════════
# LOG
# ═══════════════════════════════════════

@mcp.tool
def log_main(last_known_id: int | None = None) -> list[dict[str, Any]]:
    """Get main log entries. READ-ONLY.
    
    Args:
        last_known_id: Only return entries with ID > this
    """
    params = {}
    if last_known_id is not None:
        params["last_known_id"] = last_known_id
    return _request("GET", "log/main", params=params or None)


@mcp.tool
def log_peers(last_known_id: int | None = None) -> list[dict[str, Any]]:
    """Get peer log entries. READ-ONLY."""
    params = {}
    if last_known_id is not None:
        params["last_known_id"] = last_known_id
    return _request("GET", "log/peers", params=params or None)


# ═══════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════

@mcp.tool
def search_plugins() -> list[dict[str, Any]]:
    """Get search plugins. READ-ONLY."""
    return _request("GET", "search/plugins")


# ═══════════════════════════════════════
# RAW API (READ-ONLY CATCH-ALL)
# ═══════════════════════════════════════

@mcp.tool
def api(path: str, query: str = "{}") -> Any:
    """Catch-all read-only qBittorrent API call.
    
    WARNING: READ-ONLY. Only GET requests.
    Path examples: torrents/info, torrents/properties?hash=X, transfer/info, sync/maindata
    """
    params = json.loads(query) if query and query != "{}" else None
    return _request("GET", path, params=params)


if __name__ == "__main__":
    mcp.run()
