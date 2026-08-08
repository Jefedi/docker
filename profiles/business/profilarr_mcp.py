"""
Profilarr MCP Server — covers 100% of the Profilarr API v1.

Env vars:
  PROFILARR_URL     Base URL (default: http://100.64.0.2:6868)
  PROFILARR_API_KEY API key for X-Api-Key auth
"""

import os
import base64
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Profilarr")

BASE_URL = os.getenv("PROFILARR_URL", "http://100.64.0.2:6868").rstrip("/")
API_KEY = os.getenv("PROFILARR_API_KEY", "")

HEADERS = {"X-Api-Key": API_KEY} if API_KEY else {}


def _get(path: str):
    url = f"{BASE_URL}/api/v1{path}"
    resp = httpx.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, json_body: dict | None = None):
    url = f"{BASE_URL}/api/v1{path}"
    resp = httpx.post(url, headers=HEADERS, json=json_body, timeout=60)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"status": resp.status_code}


def _patch(path: str, json_body: dict):
    url = f"{BASE_URL}/api/v1{path}"
    resp = httpx.patch(url, headers=HEADERS, json=json_body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _delete(path: str):
    url = f"{BASE_URL}/api/v1{path}"
    resp = httpx.delete(url, headers=HEADERS, timeout=30)
    if resp.status_code == 204:
        return {"success": True}
    try:
        return resp.json()
    except Exception:
        return {"status": resp.status_code}


# ─── System ────────────────────────────────────────────────────────────────


@mcp.tool
def profilarr_get_health() -> dict:
    """Health check. Returns system health status (healthy/degraded/unhealthy) and timestamp. No auth required."""
    return _get("/health")


@mcp.tool
def profilarr_get_status() -> dict:
    """System status dashboard. Returns version, uptime, timezone, linked databases with entity counts, arr instances with sync status, job queue state, backup status, and unread announcement count."""
    return _get("/status")


@mcp.tool
def profilarr_get_openapi_spec() -> dict:
    """Get the resolved OpenAPI 3.1 specification as JSON."""
    return _get("/openapi.json")


# ─── Arr ───────────────────────────────────────────────────────────────────


@mcp.tool
def profilarr_list_arr_instances() -> list:
    """List all Arr instances (Radarr/Sonarr) with secrets stripped. Returns id, name, type, url, enabled, tags, timestamps."""
    return _get("/arr")


# ─── Databases ─────────────────────────────────────────────────────────────


@mcp.tool
def profilarr_list_databases() -> list:
    """List all linked configuration databases. Secrets are stripped: personal_access_token is replaced by hasPat boolean, local_path is excluded."""
    return _get("/databases")


@mcp.tool
def profilarr_create_database(
    name: str,
    repository_url: str,
    branch: str = None,
    personal_access_token: str = None,
    git_user_name: str = None,
    git_user_email: str = None,
    sync_strategy: int = None,
    auto_pull: bool = None,
    local_ops_enabled: bool = None,
    conflict_strategy: str = None,
) -> dict:
    """Link a new configuration database. Clones the repository, validates its PCD manifest, and processes dependencies.
    Required: name (display name, must be unique), repository_url (GitHub URL).
    Optional: branch, personal_access_token, git_user_name, git_user_email, sync_strategy, auto_pull, local_ops_enabled, conflict_strategy (override/align/ask)."""
    body = {"name": name, "repository_url": repository_url}
    for k, v in [
        ("branch", branch), ("personal_access_token", personal_access_token),
        ("git_user_name", git_user_name), ("git_user_email", git_user_email),
        ("sync_strategy", sync_strategy), ("auto_pull", auto_pull),
        ("local_ops_enabled", local_ops_enabled), ("conflict_strategy", conflict_strategy),
    ]:
        if v is not None:
            body[k] = v
    return _post("/databases", body)


@mcp.tool
def profilarr_get_database(id: int) -> dict:
    """Get a specific database instance by ID. Secrets are stripped (hasPat boolean instead of token)."""
    return _get(f"/databases/{id}")


@mcp.tool
def profilarr_update_database(
    id: int,
    name: str = None,
    personal_access_token: str = None,
    git_user_name: str = None,
    git_user_email: str = None,
    sync_strategy: int = None,
    auto_pull: bool = None,
    local_ops_enabled: bool = None,
    conflict_strategy: str = None,
) -> dict:
    """Update a database instance. Partial update — only provided fields are changed. All fields are optional."""
    body = {}
    for k, v in [
        ("name", name), ("personal_access_token", personal_access_token),
        ("git_user_name", git_user_name), ("git_user_email", git_user_email),
        ("sync_strategy", sync_strategy), ("auto_pull", auto_pull),
        ("local_ops_enabled", local_ops_enabled), ("conflict_strategy", conflict_strategy),
    ]:
        if v is not None:
            body[k] = v
    return _patch(f"/databases/{id}", body)


@mcp.tool
def profilarr_delete_database(id: int) -> dict:
    """Unlink (delete) a database instance. Removes the database row, deletes the cloned repo from disk, cancels scheduled sync jobs."""
    return _delete(f"/databases/{id}")


@mcp.tool
def profilarr_sync_database(id: int) -> dict:
    """Trigger a sync for a database. Async — enqueues a pcd.sync job and returns the job ID. Poll with profilarr_get_job()."""
    return _post(f"/databases/{id}/sync")


# ─── Jobs ──────────────────────────────────────────────────────────────────


@mcp.tool
def profilarr_get_job(id: int) -> dict:
    """Get the current status of a job queue entry. Returns id, jobType, status (queued/running/success/failed/cancelled), source, timestamps, and result (output/error/durationMs)."""
    return _get(f"/jobs/{id}")


# ─── Backups ───────────────────────────────────────────────────────────────


@mcp.tool
def profilarr_list_backups() -> list:
    """List all backup files, sorted newest first. Returns filename, created timestamp, size in bytes and formatted."""
    return _get("/backups")


@mcp.tool
def profilarr_create_backup() -> dict:
    """Create a new backup. Async — enqueues a backup.create job and returns the job ID. Poll with profilarr_get_job() for completion."""
    return _post("/backups")


@mcp.tool
def profilarr_download_backup(filename: str) -> dict:
    """Download a backup archive. Sanitized on the fly (Arr instances, tokens, API keys removed). Returns base64 content."""
    url = f"{BASE_URL}/api/v1/backups/{filename}"
    resp = httpx.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return {
        "filename": filename,
        "content_base64": base64.b64encode(resp.content).decode(),
        "content_type": resp.headers.get("content-type", ""),
    }


@mcp.tool
def profilarr_delete_backup(filename: str) -> dict:
    """Delete a backup file by filename."""
    return _delete(f"/backups/{filename}")


@mcp.tool
def profilarr_get_backup_settings() -> dict:
    """Get current backup settings: schedule, retentionDays, enabled, includeDatabase, compressionEnabled."""
    return _get("/backups/settings")


@mcp.tool
def profilarr_update_backup_settings(
    schedule: str = None,
    retention_days: int = None,
    enabled: bool = None,
) -> dict:
    """Update backup settings. Partial update — only provided fields are changed. schedule: hourly/daily/weekly/monthly, retention_days: 1-365."""
    body = {}
    if schedule is not None:
        body["schedule"] = schedule
    if retention_days is not None:
        body["retentionDays"] = retention_days
    if enabled is not None:
        body["enabled"] = enabled
    return _patch("/backups/settings", body)


# ─── Announcements ─────────────────────────────────────────────────────────


@mcp.tool
def profilarr_list_announcements() -> list:
    """List all announcements. Returns array of announcement summaries (id, severity, title, createdAt, read)."""
    return _get("/announcements")


@mcp.tool
def profilarr_get_announcement(id: int) -> dict:
    """Get a specific announcement by ID. Returns full detail including body content."""
    return _get(f"/announcements/{id}")


if __name__ == "__main__":
    mcp.run()
