"""
MeTube MCP Server — Download videos via MeTube (yt-dlp web UI)
Routes through the Pangolin Newt tunnel (pangolin-cli container)
to access the private resource at metube.jefe.al
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("MeTube")

METUBE_URL = os.getenv("METUBE_URL", "https://metube.jefe.al")
DOCKER_EXEC = os.getenv("METUBE_DOCKER_CMD", "docker exec pangolin-cli")
METUBE_INTERNAL = os.getenv("METUBE_INTERNAL", "false").lower() == "true"


def _api(method: str, path: str, json_body: dict | None = None,
         params: dict | None = None) -> dict[str, Any]:
    """Call a MeTube API endpoint.

    If METUBE_INTERNAL=true, uses direct HTTP request.
    Otherwise routes through the Newt tunnel via docker exec pangolin-cli.
    """
    url = f"{METUBE_URL.rstrip('/')}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    if METUBE_INTERNAL:
        import httpx
        if method == "GET":
            resp = httpx.get(url, timeout=30, verify=False)
        else:
            resp = httpx.post(url, json=json_body, timeout=30, verify=False)
        resp.raise_for_status()
        if not resp.content:
            return {"success": True}
        return resp.json()
    else:
        if method == "GET":
            full_url = url
            cmd_parts = DOCKER_EXEC.split() + [
                "curl", "-sk", full_url, "--max-time", "30"
            ]
        else:
            body_str = json.dumps(json_body) if json_body else "{}"
            cmd_parts = DOCKER_EXEC.split() + [
                "curl", "-sk", "-X", "POST", url,
                "-H", "Content-Type: application/json",
                "-d", body_str,
                "--max-time", "60"
            ]

        result = subprocess.run(
            cmd_parts, capture_output=True, text=True, timeout=65
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"MeTube API call failed (exit={result.returncode}): "
                f"{result.stderr[:500]}"
            )

        if not result.stdout.strip():
            return {"success": True}
        return json.loads(result.stdout)


@mcp.tool
def add_download(
    url: str,
    quality: str | None = None,
    download_format: str | None = None,
    playlist_start: int | None = None,
    playlist_end: int | None = None,
) -> dict[str, Any]:
    """Add a video URL to MeTube for downloading.

    Args:
        url: Video URL to download (YouTube, Vimeo, etc.).
        quality: Optional quality (e.g. 'best', '720p', '1080p', 'bestaudio').
        download_format: Optional format ('video', 'audio', 'video+audio').
        playlist_start: Start index for playlist downloads.
        playlist_end: End index for playlist downloads (0 = unlimited).
    """
    body: dict[str, Any] = {"url": url}
    if quality:
        body["quality"] = quality
    if download_format:
        body["format"] = download_format
    if playlist_start is not None:
        body["playlist_start"] = playlist_start
    if playlist_end is not None:
        body["playlist_end"] = playlist_end

    return _api("POST", "/add", json_body=body)


@mcp.tool
def get_history() -> list[dict[str, Any]]:
    """Get MeTube download history (completed and in-progress)."""
    return _api("GET", "/history")


@mcp.tool
def get_downloads() -> dict[str, list[dict[str, Any]]]:
    """Get current downloads (pending, downloading, completed, failed)."""
    history = _api("GET", "/history")
    result: dict[str, list[dict[str, Any]]] = {
        "pending": [],
        "downloading": [],
        "completed": [],
        "failed": [],
    }
    for item in history if isinstance(history, list) else []:
        status = item.get("status", "unknown")
        if status in result:
            result[status].append(item)
        else:
            result.setdefault("unknown", []).append(item)
    return result


@mcp.tool
def delete_download(
    id: str | int,
    delete_file: bool = False,
) -> dict[str, Any]:
    """Delete a download from MeTube history.

    Args:
        id: Download ID from history.
        delete_file: Also delete the downloaded file from disk.
    """
    return _api("POST", "/delete", json_body={
        "id": id,
        "delete_file": delete_file,
    })


if __name__ == "__main__":
    mcp.run()
