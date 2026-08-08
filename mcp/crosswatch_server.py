"""
MCP Server for CrossWatch API.

CrossWatch syncs watchlists, history, ratings, and progress between
media servers (Plex, Jellyfin, Emby) and trackers (Trakt, SIMKL, MDBList, AniList, TMDb).

Supports:
  - Direct HTTP access (CW_INTERNAL=true)
  - Pangolin Newt tunnel via docker exec (default)
  - Cookie/session-based auth via CW_COOKIE or CW_AUTH_TOKEN
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any

# fastmcp lives under mcp.server in mcp SDK 1.26+
_here = os.path.dirname(__file__)
_venv = os.path.join(_here, "..", ".hermes_venv", "lib", "python3.13", "site-packages")
# Try common venv paths
for _p in [
    "/opt/hermes/.venv/lib/python3.13/site-packages/mcp/server",
]:
    if os.path.isdir(os.path.dirname(_p)):
        sys.path.insert(0, _p)

from fastmcp import FastMCP

mcp = FastMCP("CrossWatch")

# ── Configuration ────────────────────────────────────────────────
BASE_URL = os.getenv("CW_BASE_URL", "http://localhost:8787").rstrip("/")
DOCKER_EXEC = os.getenv("CW_DOCKER_CMD", "docker exec pangolin-cli")
CW_INTERNAL = os.getenv("CW_INTERNAL", "false").lower() == "true"

# Auth: cookie string (e.g. "session=abc123") or Bearer token
CW_COOKIE = os.getenv("CW_COOKIE", "")
CW_AUTH_TOKEN = os.getenv("CW_AUTH_TOKEN", "")


def _req(method: str, path: str, **kwargs) -> dict:
    """Make an HTTP request to CrossWatch API.

    If CW_INTERNAL=true, uses direct HTTP via httpx.
    Otherwise routes through the Newt tunnel via docker exec pangolin-cli.
    """
    url = f"{BASE_URL}/{path.lstrip('/')}"

    # Build curl args
    curl_args = ["curl", "-sk", "--max-time", "30"]

    if CW_COOKIE:
        curl_args += ["-H", f"Cookie: {CW_COOKIE}"]
    if CW_AUTH_TOKEN:
        curl_args += ["-H", f"Authorization: Bearer {CW_AUTH_TOKEN}"]

    if method == "GET":
        # Handle query params
        params = kwargs.get("params", {})
        if params:
            qs = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None and v != ""}
            )
            url = f"{url}?{qs}"
        curl_args.append(url)
    else:
        curl_args += ["-X", method, "-H", "Content-Type: application/json"]
        # Handle query params for POST/etc
        params = kwargs.get("params", {})
        if params:
            qs = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None and v != ""}
            )
            url = f"{url}?{qs}"
        curl_args.append(url)

        json_body = kwargs.get("json")
        if json_body:
            curl_args += ["-d", json.dumps(json_body)]

    if CW_INTERNAL:
        import httpx
        headers = {"Content-Type": "application/json"}
        if CW_COOKIE:
            headers["Cookie"] = CW_COOKIE
        if CW_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {CW_AUTH_TOKEN}"
        resp = httpx.get(url, headers=headers, timeout=30) if method == "GET" else httpx.post(url, headers=headers, json=kwargs.get("json"), timeout=30)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": resp.status_code, "text": resp.text[:200]}
    else:
        cmd_parts = DOCKER_EXEC.split() + curl_args
        result = subprocess.run(
            cmd_parts, capture_output=True, text=True, timeout=35
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"CrossWatch API call failed (exit={result.returncode}): "
                f"{result.stderr[:500]}"
            )
        stdout = result.stdout.strip()
        if not stdout:
            return {"success": True}
        try:
            data = json.loads(stdout)
            # FastMCP v3 requires dict return, wrap lists
            if isinstance(data, list):
                return {"results": data}
            return data
        except json.JSONDecodeError:
            return {"status": "unknown", "text": stdout[:500]}


# ═══════════════════════════════════════════════════════════════════
#  AUTH TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def auth_status() -> dict:
    """Check current authentication status."""
    return _req("GET", "/api/app-auth/status")


@mcp.tool()
def auth_login(payload: dict = {}) -> dict:
    """Login to CrossWatch. Requires username/password in payload.

    Args:
        payload: JSON object with login credentials (e.g. {"username": "...", "password": "..."})
    """
    return _req("POST", "/api/app-auth/login", json=payload)


@mcp.tool()
def auth_logout() -> dict:
    """Logout from CrossWatch."""
    return _req("POST", "/api/app-auth/logout")


@mcp.tool()
def list_auth_providers() -> dict:
    """List available auth providers."""
    return _req("GET", "/api/auth/providers")


# ═══════════════════════════════════════════════════════════════════
#  INSIGHT TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_insights(limit_samples: int = 60, history: int = 3, runtime: int = 0) -> dict:
    """Get insights payload (aggregated dashboard data).

    Args:
        limit_samples: Max samples to include
        history: History depth
        runtime: Runtime override
    """
    return _req("GET", "/api/insights", params={
        "limit_samples": limit_samples, "history": history, "runtime": runtime
    })


@mcp.tool()
def get_stats_raw() -> dict:
    """Get raw stats."""
    return _req("GET", "/api/stats/raw")


@mcp.tool()
def get_stats() -> dict:
    """Get processed stats."""
    return _req("GET", "/api/stats")


# ═══════════════════════════════════════════════════════════════════
#  WATCHER / SCROBBLER TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def watch_status() -> dict:
    """Get watcher (scrobbler) status — routes + group status."""
    return _req("GET", "/api/watch/status")


@mcp.tool()
def watch_currently_watching() -> dict:
    """Get the currently playing / watching item."""
    return _req("GET", "/api/watch/currently_watching")


@mcp.tool()
def watch_logs(tail: int = 200, tag: str = "", tags: str = "") -> dict:
    """Tail watcher logs.

    Args:
        tail: Number of lines (1-3000)
        tag: Single tag filter (optional)
        tags: CSV of tags or '*' for all
    """
    params = {"tail": tail}
    if tag:
        params["tag"] = tag
    if tags:
        params["tags"] = tags
    return _req("GET", "/api/watch/logs", params=params)


@mcp.tool()
def watch_start(provider: str = "", sink: str = "") -> dict:
    """Start the watcher/scrobbler.

    Args:
        provider: Provider name to filter (optional)
        sink: Sink name to filter (optional)
    """
    params = {}
    if provider:
        params["provider"] = provider
    if sink:
        params["sink"] = sink
    return _req("POST", "/api/watch/start", params=params)


@mcp.tool()
def watch_stop() -> dict:
    """Stop the watcher/scrobbler."""
    return _req("POST", "/api/watch/stop")


# ═══════════════════════════════════════════════════════════════════
#  SYNCHRONIZATION TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def sync_providers() -> dict:
    """List available sync providers."""
    return _req("GET", "/api/sync/providers")


@mcp.tool()
def list_pairs() -> dict:
    """List all sync pairs."""
    return _req("GET", "/api/pairs")


@mcp.tool()
def sync_run(payload: dict = {}) -> dict:
    """Run a sync. Optionally pass a payload to configure the run.

    Args:
        payload: Optional JSON object to configure the sync run
    """
    return _req("POST", "/api/run", json=payload or None)


@mcp.tool()
def sync_run_summary() -> dict:
    """Get the latest sync run summary."""
    return _req("GET", "/api/run/summary")


@mcp.tool()
def provider_counts(max_age: int = 30, force: bool = False, source: str = "state") -> dict:
    """Get provider item counts.

    Args:
        max_age: Max age in days for cached counts
        force: Force refresh
        source: Source type ('state' or 'provider')
    """
    return _req("GET", "/api/sync/providers/counts", params={
        "max_age": max_age, "force": json.dumps(force), "source": source
    })


@mcp.tool()
def add_pair(source: str, target: str, mode: str = "",
             enabled: bool = True, features: dict = {}) -> dict:
    """Add a new sync pair.

    Args:
        source: Source provider name
        target: Target provider name
        mode: Sync mode (optional)
        enabled: Whether the pair is enabled
        features: Feature flags object
    """
    body = {"source": source, "target": target, "enabled": enabled}
    if mode:
        body["mode"] = mode
    if features:
        body["features"] = features
    return _req("POST", "/api/pairs", json=body)


@mcp.tool()
def delete_pair(pair_id: str, purge_state: bool = True) -> dict:
    """Delete a sync pair.

    Args:
        pair_id: Pair ID to delete
        purge_state: Also purge state
    """
    return _req("DELETE", f"/api/pairs/{pair_id}", params={"purge_state": json.dumps(purge_state)})


# ═══════════════════════════════════════════════════════════════════
#  MAINTENANCE TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def maintenance_provider_cache_status() -> dict:
    """Get provider cache status/info."""
    return _req("GET", "/api/maintenance/provider-cache")


@mcp.tool()
def maintenance_crosswatch_tracker_status() -> dict:
    """Inspect the CrossWatch tracker folder (.cw_provider)."""
    return _req("GET", "/api/maintenance/crosswatch-tracker")


@mcp.tool()
def maintenance_clear_state() -> dict:
    """Clear application state (forces full rebuild on next run)."""
    return _req("POST", "/api/maintenance/clear-state")


@mcp.tool()
def maintenance_clear_cache() -> dict:
    """Clear general application cache."""
    return _req("POST", "/api/maintenance/clear-cache")


@mcp.tool()
def maintenance_clear_metadata_cache() -> dict:
    """Clear metadata cache."""
    return _req("POST", "/api/maintenance/clear-metadata-cache")


@mcp.tool()
def maintenance_restart() -> dict:
    """Restart the CrossWatch application."""
    return _req("POST", "/api/maintenance/restart")


# ═══════════════════════════════════════════════════════════════════
#  PROVIDER INSTANCES TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def list_provider_instances(provider: str = "") -> dict:
    """List provider instances (profiles).

    Args:
        provider: Optional provider name to filter (e.g. 'trakt', 'plex')
    """
    path = "/api/provider-instances"
    if provider:
        path = f"{path}/{provider}"
    return _req("GET", path)


# ═══════════════════════════════════════════════════════════════════
#  MEDIA PROVIDER INFO TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def plex_status() -> dict:
    """Get Plex connection status and info."""
    return _req("GET", "/api/plex/pms")


@mcp.tool()
def plex_libraries() -> dict:
    """List Plex libraries."""
    return _req("GET", "/api/plex/libraries")


@mcp.tool()
def plex_users() -> dict:
    """List Plex users."""
    return _req("GET", "/api/plex/users")


@mcp.tool()
def jellyfin_libraries() -> dict:
    """List Jellyfin libraries."""
    return _req("GET", "/api/jellyfin/libraries")


@mcp.tool()
def jellyfin_users() -> dict:
    """List Jellyfin users."""
    return _req("GET", "/api/jellyfin/users")


@mcp.tool()
def emby_libraries() -> dict:
    """List Emby libraries."""
    return _req("GET", "/api/emby/libraries")


@mcp.tool()
def emby_users() -> dict:
    """List Emby users."""
    return _req("GET", "/api/emby/users")


# ═══════════════════════════════════════════════════════════════════
#  METADATA TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def metadata_providers() -> dict:
    """List available metadata providers."""
    return _req("GET", "/api/metadata/providers")


@mcp.tool()
def metadata_search(q: str, typ: str = "movie", year: int = 0, limit: int = 10) -> dict:
    """Search for movies/shows in metadata.

    Args:
        q: Search query (min 2 chars)
        typ: Media type ('movie' or 'tv')
        year: Release year filter (optional)
        limit: Max results (1-20)
    """
    params = {"q": q, "typ": typ, "limit": limit}
    if year:
        params["year"] = year
    return _req("GET", "/api/metadata/search", params=params)


@mcp.tool()
def tmdb_art(typ: str, tmdb_id: int, size: str = "w342", locale: str = "") -> dict:
    """Fetch TMDB artwork URL.

    Args:
        typ: Type of art ('poster', 'backdrop', 'logo', etc.)
        tmdb_id: TMDB ID of the movie/show
        size: Image size variant (e.g. 'w342', 'w500', 'original')
        locale: Locale for localized artwork (e.g. 'nl-NL')
    """
    params = {"size": size}
    if locale:
        params["locale"] = locale
    return _req("GET", f"/art/tmdb/{typ}/{tmdb_id}", params=params)


# ═══════════════════════════════════════════════════════════════════
#  EXPORT TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def export_options() -> dict:
    """Get available export options."""
    return _req("GET", "/api/export/options")


@mcp.tool()
def export_sample(provider: str = "", feature: str = "watchlist",
                  limit: int = 25, q: str = "") -> dict:
    """Get a sample export for preview.

    Args:
        provider: Provider name (TRAKT|PLEX|EMBY|JELLYFIN|SIMKL|MDBLIST|CROSSWATCH)
        feature: Feature type (watchlist|history|ratings)
        limit: Max items (1-250)
        q: Search filter (case-insensitive multi-token contains)
    """
    return _req("GET", "/api/export/sample", params={
        "provider": provider, "feature": feature, "limit": limit, "q": q
    })


@mcp.tool()
def export_file(provider: str = "", feature: str = "watchlist",
                export_format: str = "letterboxd", q: str = "", ids: str = "") -> dict:
    """Export data as a file.

    Args:
        provider: Provider name
        feature: Feature type (watchlist|history|ratings)
        export_format: Export format (letterboxd|imdb|justwatch|yamtrack|tmdb)
        q: Optional search filter
        ids: Optional CSV of keys to include (overrides q)
    """
    return _req("GET", "/api/export/file", params={
        "provider": provider, "feature": feature,
        "format": export_format, "q": q, "ids": ids
    })


# ═══════════════════════════════════════════════════════════════════
#  LOGGING TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def logs_dump(channel: str = "TRAKT", n: int = 50) -> dict:
    """Dump recent log entries for a channel.

    Args:
        channel: Log channel (e.g. TRAKT, SYNC, WATCH)
        n: Number of entries to retrieve
    """
    return _req("GET", "/api/logs/dump", params={"channel": channel, "n": n})


@mcp.tool()
def logs_stream(tag: str = "SYNC") -> dict:
    """Get initial log stream entries for a tag.

    Args:
        tag: Log tag (e.g. SYNC, WATCH)
    """
    return _req("GET", "/api/logs/stream", params={"tag": tag})


# ═══════════════════════════════════════════════════════════════════
#  CONFIG TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_config() -> dict:
    """Get the full CrossWatch configuration."""
    return _req("GET", "/api/config")


@mcp.tool()
def get_config_meta() -> dict:
    """Get config metadata."""
    return _req("GET", "/api/config/meta")


# ═══════════════════════════════════════════════════════════════════
#  ANALYZER TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def analyzer_state(pairs: str = "") -> dict:
    """Get analyzer state.

    Args:
        pairs: Optional pairs filter
    """
    params = {}
    if pairs:
        params["pairs"] = pairs
    return _req("GET", "/api/analyzer/state", params=params)


@mcp.tool()
def analyzer_problems(pairs: str = "") -> dict:
    """Get analyzer problems.

    Args:
        pairs: Optional pairs filter
    """
    params = {}
    if pairs:
        params["pairs"] = pairs
    return _req("GET", "/api/analyzer/problems", params=params)


@mcp.tool()
def analyzer_ratings_audit(pairs: str = "") -> dict:
    """Get ratings audit.

    Args:
        pairs: Optional pairs filter
    """
    params = {}
    if pairs:
        params["pairs"] = pairs
    return _req("GET", "/api/analyzer/ratings-audit", params=params)


# ═══════════════════════════════════════════════════════════════════
#  SNAPSHOTS TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def snapshots_manifest() -> dict:
    """Get snapshots manifest."""
    return _req("GET", "/api/snapshots/manifest")


@mcp.tool()
def snapshots_list() -> dict:
    """List all snapshots."""
    return _req("GET", "/api/snapshots/list")


@mcp.tool()
def snapshots_read(path: str) -> dict:
    """Read a specific snapshot.

    Args:
        path: Relative path under /config/snapshots
    """
    return _req("GET", "/api/snapshots/read", params={"path": path})


# ═══════════════════════════════════════════════════════════════════
#  PROBES / STATUS TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def status(fresh: int = 0) -> dict:
    """Get CrossWatch status.

    Args:
        fresh: Force fresh status (1) or use cached (0)
    """
    return _req("GET", "/api/status", params={"fresh": fresh})


# ═══════════════════════════════════════════════════════════════════
#  FILES TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def list_files(path: str) -> dict:
    """List files in a directory.

    Args:
        path: Directory path (absolute or config-relative)
    """
    return _req("GET", "/api/files", params={"path": path})


# ═══════════════════════════════════════════════════════════════════
#  EDITOR TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def editor_state_providers() -> dict:
    """List available state providers."""
    return _req("GET", "/api/editor/state/providers")


@mcp.tool()
def editor_pairs() -> dict:
    """List available editor pairs."""
    return _req("GET", "/api/editor/pairs")


if __name__ == "__main__":
    mcp.run()
