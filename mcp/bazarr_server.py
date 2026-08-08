"""
Bazarr MCP Server — Full API coverage via FastMCP
Connects directly to Bazarr (Tailscale 100.64.0.2:6767)
Bazarr manages and downloads subtitles for Sonarr/Radarr.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
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
    raise RuntimeError("BAZARR_API_KEY env var or ~/.hermes/bazarr_api_key.txt is required")
REQUEST_TIMEOUT = float(os.getenv("BAZARR_TIMEOUT", "20"))


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-API-KEY": BAZARR_API_KEY,
    }


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    data: dict[str, Any] | None = None,
) -> Any:
    url = f"{BAZARR_URL.rstrip('/')}/api/{path.lstrip('/')}"
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=_headers()) as client:
        response = client.request(method, url, params=params, json=json_body, data=data)
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {"success": True}
        return response.json()


# ═══════════════════════════════════════
# SYSTEM
# ═══════════════════════════════════════

@mcp.tool
def system_ping() -> dict[str, Any]:
    """Check Bazarr availability (unauthenticated)."""
    return _request("GET", "system/ping")


@mcp.tool
def system_status() -> dict[str, Any]:
    """Get Bazarr system status (env info, versions, OS, Python, DB)."""
    return _request("GET", "system/status")


@mcp.tool
def system_health() -> list[dict[str, Any]]:
    """List health issues in Bazarr."""
    return _request("GET", "system/health")


@mcp.tool
def system_settings() -> dict[str, Any]:
    """Get all Bazarr system settings (languages, profiles, notifications)."""
    return _request("GET", "system/settings")


@mcp.tool
def system_tasks(task_id: str | None = None) -> list[dict[str, Any]]:
    """List scheduled tasks in Bazarr.

    Args:
        task_id: Optional task ID to get a single task.
    """
    return _request("GET", "system/tasks", params={"taskid": task_id} if task_id else None)


@mcp.tool
def system_execute_task(task_id: str) -> dict[str, Any]:
    """Execute a scheduled task immediately.

    Args:
        task_id: Task ID to execute.
    """
    return _request("POST", "system/tasks", data={"taskid": task_id})


@mcp.tool
def system_jobs(job_id: int | None = None, status: str | None = None) -> list[dict[str, Any]]:
    """List jobs in the Bazarr job queue.

    Args:
        job_id: Optional job ID to filter.
        status: Optional status filter (pending, running, failed, completed).
    """
    params = {}
    if job_id is not None:
        params["id"] = job_id
    if status:
        params["status"] = status
    return _request("GET", "system/jobs", params=params or None)


@mcp.tool
def system_logs() -> list[dict[str, Any]]:
    """List log file entries."""
    return _request("GET", "system/logs")


@mcp.tool
def system_languages(history: str | None = None) -> list[dict[str, Any]]:
    """List available languages.

    Args:
        history: Optional - if provided, returns history stats instead.
    """
    return _request("GET", "system/languages", params={"history": history} if history else None)


@mcp.tool
def system_language_profiles() -> list[dict[str, Any]]:
    """List all language profiles in Bazarr."""
    return _request("GET", "system/languages/profiles")


@mcp.tool
def system_backups() -> list[dict[str, Any]]:
    """List available backup files."""
    return _request("GET", "system/backups")


@mcp.tool
def system_create_backup() -> dict[str, Any]:
    """Create a new backup."""
    return _request("POST", "system/backups")


@mcp.tool
def system_search(query: str) -> list[dict[str, Any]]:
    """Search for series or movies by name.

    Args:
        query: Search term for series or movies.
    """
    return _request("GET", "system/searches", params={"query": query})


# ═══════════════════════════════════════
# BADGES
# ═══════════════════════════════════════

@mcp.tool
def badges() -> dict[str, Any]:
    """Get badge counts (missing subs, throttled providers, health issues)."""
    return _request("GET", "badges")


# ═══════════════════════════════════════
# SERIES
# ═══════════════════════════════════════

@mcp.tool
def list_series(
    start: int = 0,
    length: int = -1,
    series_ids: list[int] | None = None,
) -> dict[str, Any]:
    """List series metadata in Bazarr.

    Args:
        start: Pagination offset.
        length: Pagination limit (-1 = all).
        series_ids: Optional list of Sonarr series IDs to filter.
    """
    params = {"start": start, "length": length}
    if series_ids:
        for sid in series_ids:
            # Bazarr expects seriesid[] param repeated
            pass  # handled via multiple params
    # httpx params dict handles repeated keys via list values
    if series_ids:
        params["seriesid[]"] = series_ids
    return _request("GET", "series", params=params)


@mcp.tool
def update_series_profile(series_ids: list[int], profile_ids: list[str]) -> dict[str, Any]:
    """Update language profiles for one or more series.

    Args:
        series_ids: List of Sonarr series IDs.
        profile_ids: List of language profile IDs (or "none" to clear), one per series.
    """
    return _request("POST", "series", data={
        "seriesid": series_ids,
        "profileid": profile_ids,
    })


@mcp.tool
def series_action(series_id: int, action: str) -> dict[str, Any]:
    """Run an action on a specific series.

    Args:
        series_id: Sonarr series ID.
        action: Action to run (scan-disk, search-missing, search-wanted, sync).
    """
    return _request("PATCH", "series", params={
        "seriesid": series_id,
        "action": action,
    })


# ═══════════════════════════════════════
# EPISODES
# ═══════════════════════════════════════

@mcp.tool
def list_episodes(
    series_ids: list[int] | None = None,
    episode_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """List episode metadata for specific series or episodes.

    Args:
        series_ids: Optional list of Sonarr series IDs.
        episode_ids: Optional list of episode IDs.
    """
    params = {}
    if series_ids:
        params["seriesid[]"] = series_ids
    if episode_ids:
        params["episodeid[]"] = episode_ids
    return _request("GET", "episodes", params=params or None)


@mcp.tool
def wanted_episodes(
    start: int = 0,
    length: int = 50,
    episode_ids: list[int] | None = None,
) -> dict[str, Any]:
    """List episodes with missing/wanted subtitles.

    Args:
        start: Pagination offset.
        length: Pagination limit.
        episode_ids: Optional episode IDs to filter.
    """
    params = {"start": start, "length": length}
    if episode_ids:
        params["episodeid[]"] = episode_ids
    return _request("GET", "episodes/wanted", params=params)


@mcp.tool
def episode_history(
    start: int = 0,
    length: int = 50,
    episode_id: int | None = None,
) -> dict[str, Any]:
    """List episode subtitle download history.

    Args:
        start: Pagination offset.
        length: Pagination limit.
        episode_id: Optional episode ID to filter.
    """
    params = {"start": start, "length": length}
    if episode_id is not None:
        params["episodeid"] = episode_id
    return _request("GET", "episodes/history", params=params)


@mcp.tool
def episode_blacklist(
    start: int = 0,
    length: int = 50,
) -> dict[str, Any]:
    """List blacklisted episode subtitles.

    Args:
        start: Pagination offset.
        length: Pagination limit.
    """
    return _request("GET", "episodes/blacklist", params={"start": start, "length": length})


@mcp.tool
def download_episode_subtitle(
    series_id: int,
    episode_id: int,
    language: str,
    forced: bool = False,
    hi: bool = False,
) -> dict[str, Any]:
    """Download a specific subtitle for an episode.

    Args:
        series_id: Sonarr series ID.
        episode_id: Episode ID.
        language: Language code (e.g. 'fre', 'eng').
        forced: Forced subtitles only.
        hi: Hearing impaired subtitles.
    """
    return _request("PATCH", "episodes/subtitles", data={
        "seriesid": series_id,
        "episodeid": episode_id,
        "language": language,
        "forced": forced,
        "hi": hi,
    })


@mcp.tool
def delete_episode_subtitle(
    series_id: int,
    episode_id: int,
    language: str,
    forced: bool = False,
    hi: bool = False,
    path: str = "",
) -> dict[str, Any]:
    """Delete a subtitle from an episode.

    Args:
        series_id: Sonarr series ID.
        episode_id: Episode ID.
        language: Language code.
        forced: Forced subtitles.
        hi: Hearing impaired subtitles.
        path: Subtitle file path.
    """
    return _request("DELETE", "episodes/subtitles", data={
        "seriesid": series_id,
        "episodeid": episode_id,
        "language": language,
        "forced": forced,
        "hi": hi,
        "path": path,
    })


@mcp.tool
def blacklist_episode_subtitle(
    series_id: int,
    episode_id: int,
    provider: str,
    subs_id: str,
    language: str,
    subtitles_path: str,
) -> dict[str, Any]:
    """Add episode subtitle to blacklist, delete file, trigger re-download.

    Args:
        series_id: Sonarr series ID.
        episode_id: Episode ID.
        provider: Subtitle provider name.
        subs_id: Subtitle ID from provider.
        language: Language code.
        subtitles_path: Path to subtitle file.
    """
    return _request("POST", "episodes/blacklist", data={
        "seriesid": series_id,
        "episodeid": episode_id,
        "provider": provider,
        "subs_id": subs_id,
        "language": language,
        "subtitles_path": subtitles_path,
    })


# ═══════════════════════════════════════
# MOVIES
# ═══════════════════════════════════════

@mcp.tool
def list_movies(
    start: int = 0,
    length: int = -1,
    radarr_ids: list[int] | None = None,
) -> dict[str, Any]:
    """List movie metadata in Bazarr.

    Args:
        start: Pagination offset.
        length: Pagination limit (-1 = all).
        radarr_ids: Optional list of Radarr movie IDs to filter.
    """
    params = {"start": start, "length": length}
    if radarr_ids:
        params["radarrid[]"] = radarr_ids
    return _request("GET", "movies", params=params)


@mcp.tool
def update_movie_profile(radarr_ids: list[int], profile_ids: list[str]) -> dict[str, Any]:
    """Update language profiles for one or more movies.

    Args:
        radarr_ids: List of Radarr movie IDs.
        profile_ids: List of language profile IDs (or "none" to clear), one per movie.
    """
    return _request("POST", "movies", data={
        "radarrid": radarr_ids,
        "profileid": profile_ids,
    })


@mcp.tool
def movie_action(radarr_id: int, action: str) -> dict[str, Any]:
    """Run an action on a specific movie.

    Args:
        radarr_id: Radarr movie ID.
        action: Action to run (scan-disk, search-missing, search-wanted, sync).
    """
    return _request("PATCH", "movies", params={
        "radarrid": radarr_id,
        "action": action,
    })


@mcp.tool
def wanted_movies(
    start: int = 0,
    length: int = 50,
    radarr_ids: list[int] | None = None,
) -> dict[str, Any]:
    """List movies with missing/wanted subtitles.

    Args:
        start: Pagination offset.
        length: Pagination limit.
        radarr_ids: Optional Radarr movie IDs to filter.
    """
    params = {"start": start, "length": length}
    if radarr_ids:
        params["radarrid[]"] = radarr_ids
    return _request("GET", "movies/wanted", params=params)


@mcp.tool
def movie_history(
    start: int = 0,
    length: int = 50,
    radarr_id: int | None = None,
) -> dict[str, Any]:
    """List movie subtitle download history.

    Args:
        start: Pagination offset.
        length: Pagination limit.
        radarr_id: Optional Radarr movie ID to filter.
    """
    params = {"start": start, "length": length}
    if radarr_id is not None:
        params["radarrid"] = radarr_id
    return _request("GET", "movies/history", params=params)


@mcp.tool
def movie_blacklist(
    start: int = 0,
    length: int = 50,
) -> dict[str, Any]:
    """List blacklisted movie subtitles.

    Args:
        start: Pagination offset.
        length: Pagination limit.
    """
    return _request("GET", "movies/blacklist", params={"start": start, "length": length})


@mcp.tool
def download_movie_subtitle(
    radarr_id: int,
    language: str,
    forced: bool = False,
    hi: bool = False,
) -> dict[str, Any]:
    """Download a specific subtitle for a movie.

    Args:
        radarr_id: Radarr movie ID.
        language: Language code (e.g. 'fre', 'eng').
        forced: Forced subtitles only.
        hi: Hearing impaired subtitles.
    """
    return _request("PATCH", "movies/subtitles", data={
        "radarrid": radarr_id,
        "language": language,
        "forced": forced,
        "hi": hi,
    })


@mcp.tool
def delete_movie_subtitle(
    radarr_id: int,
    language: str,
    forced: bool = False,
    hi: bool = False,
    path: str = "",
) -> dict[str, Any]:
    """Delete a subtitle from a movie.

    Args:
        radarr_id: Radarr movie ID.
        language: Language code.
        forced: Forced subtitles.
        hi: Hearing impaired subtitles.
        path: Subtitle file path.
    """
    return _request("DELETE", "movies/subtitles", data={
        "radarrid": radarr_id,
        "language": language,
        "forced": forced,
        "hi": hi,
        "path": path,
    })


@mcp.tool
def blacklist_movie_subtitle(
    radarr_id: int,
    provider: str,
    subs_id: str,
    language: str,
    subtitles_path: str,
) -> dict[str, Any]:
    """Add movie subtitle to blacklist, delete file, trigger re-download.

    Args:
        radarr_id: Radarr movie ID.
        provider: Subtitle provider name.
        subs_id: Subtitle ID from provider.
        language: Language code.
        subtitles_path: Path to subtitle file.
    """
    return _request("POST", "movies/blacklist", data={
        "radarrid": radarr_id,
        "provider": provider,
        "subs_id": subs_id,
        "language": language,
        "subtitles_path": subtitles_path,
    })


# ═══════════════════════════════════════
# PROVIDERS
# ═══════════════════════════════════════

@mcp.tool
def providers_status() -> dict[str, Any]:
    """Get providers status (throttled providers list)."""
    return _request("GET", "providers")


@mcp.tool
def providers_reset_throttled() -> dict[str, Any]:
    """Reset all throttled providers."""
    return _request("POST", "providers", data={"action": "reset"})


@mcp.tool
def search_episode_providers(episode_id: int) -> list[dict[str, Any]]:
    """Search manually for episode subtitles from providers.

    Args:
        episode_id: Episode ID.
    """
    return _request("GET", "providers/episodes", params={"episodeid": episode_id})


@mcp.tool
def search_movie_providers(radarr_id: int) -> list[dict[str, Any]]:
    """Search manually for movie subtitles from providers.

    Args:
        radarr_id: Radarr movie ID.
    """
    return _request("GET", "providers/movies", params={"radarrid": radarr_id})


@mcp.tool
def manual_download_episode_subtitle(
    series_id: int,
    episode_id: int,
    hi: bool,
    forced: bool,
    original_format: bool,
    provider: str,
    subtitle: str,
) -> dict[str, Any]:
    """Manually download an episode subtitle from provider search results.

    Args:
        series_id: Sonarr series ID.
        episode_id: Episode ID.
        hi: Hearing impaired.
        forced: Forced subtitles.
        original_format: Keep original format.
        provider: Provider name.
        subtitle: Subtitle identifier from provider search.
    """
    return _request("POST", "providers/episodes", data={
        "seriesid": series_id,
        "episodeid": episode_id,
        "hi": hi,
        "forced": forced,
        "original_format": original_format,
        "provider": provider,
        "subtitle": subtitle,
    })


@mcp.tool
def manual_download_movie_subtitle(
    radarr_id: int,
    hi: bool,
    forced: bool,
    original_format: bool,
    provider: str,
    subtitle: str,
) -> dict[str, Any]:
    """Manually download a movie subtitle from provider search results.

    Args:
        radarr_id: Radarr movie ID.
        hi: Hearing impaired.
        forced: Forced subtitles.
        original_format: Keep original format.
        provider: Provider name.
        subtitle: Subtitle identifier.
    """
    return _request("POST", "providers/movies", data={
        "radarrid": radarr_id,
        "hi": hi,
        "forced": forced,
        "original_format": original_format,
        "provider": provider,
        "subtitle": subtitle,
    })


# ═══════════════════════════════════════
# SUBTITLES (external file actions)
# ═══════════════════════════════════════

@mcp.tool
def get_subtitles_info(
    subtitles_path: str,
    sonarr_episode_id: int | None = None,
    radarr_movie_id: int | None = None,
) -> dict[str, Any]:
    """Get available audio tracks, embedded & external subtitles for a media file.

    Args:
        subtitles_path: Path to the media file.
        sonarr_episode_id: Sonarr episode ID (optional).
        radarr_movie_id: Radarr movie ID (optional). Provide one.
    """
    params = {"subtitlesPath": subtitles_path}
    if sonarr_episode_id is not None:
        params["sonarrEpisodeId"] = sonarr_episode_id
    if radarr_movie_id is not None:
        params["radarrMovieId"] = radarr_movie_id
    return _request("GET", "subtitles", params=params)


@mcp.tool
def sync_subtitle(
    language: str,
    path: str,
    media_type: str,
    media_id: int,
    forced: bool = False,
    hi: bool = False,
    original_format: bool = True,
    reference: str | None = None,
    max_offset_seconds: int | None = None,
    no_fix_framerate: bool = False,
    gss: bool = False,
) -> dict[str, Any]:
    """Sync an external subtitle file (adjust timing).

    Args:
        language: Language code.
        path: Subtitle file path.
        media_type: 'episode' or 'movie'.
        media_id: Sonarr episode ID or Radarr movie ID.
        forced: Forced subtitles.
        hi: Hearing impaired.
        original_format: Keep original format.
        reference: Reference subtitle path for sync.
        max_offset_seconds: Max offset in seconds (-1 for no limit).
        no_fix_framerate: Don't fix framerate.
        gss: Golden section search.
    """
    params = {
        "action": "sync",
        "language": language,
        "path": path,
        "type": media_type,
        "id": media_id,
        "forced": forced,
        "hi": hi,
        "original_format": original_format,
        "no_fix_framerate": no_fix_framerate,
        "gss": gss,
    }
    if reference:
        params["reference"] = reference
    if max_offset_seconds is not None:
        params["max_offset_seconds"] = max_offset_seconds
    return _request("PATCH", "subtitles", data=params)


# ═══════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════

@mcp.tool
def history_stats(
    time_frame: str = "month",
    action: str | None = None,
    provider: str | None = None,
    language: str | None = None,
) -> list[dict[str, Any]]:
    """Get subtitle history statistics (aggregated by day).

    Args:
        time_frame: Time frame (week, month, trimester, year).
        action: Optional filter by action type.
        provider: Optional filter by provider.
        language: Optional filter by language.
    """
    params = {"timeFrame": time_frame}
    if action:
        params["action"] = action
    if provider:
        params["provider"] = provider
    if language:
        params["language"] = language
    return _request("GET", "history/stats", params=params)


# ═══════════════════════════════════════
# FILES (filesystem browser)
# ═══════════════════════════════════════

@mcp.tool
def browse_files(path: str = "") -> list[dict[str, Any]]:
    """Browse Bazarr's own filesystem.

    Args:
        path: Directory path to browse (default: root).
    """
    return _request("GET", "files", params={"path": path})


@mcp.tool
def browse_sonarr_files(path: str = "") -> list[dict[str, Any]]:
    """Browse filesystem as seen by Sonarr.

    Args:
        path: Directory path to browse.
    """
    return _request("GET", "files/sonarr", params={"path": path})


@mcp.tool
def browse_radarr_files(path: str = "") -> list[dict[str, Any]]:
    """Browse filesystem as seen by Radarr.

    Args:
        path: Directory path to browse.
    """
    return _request("GET", "files/radarr", params={"path": path})


if __name__ == "__main__":
    mcp.run()
