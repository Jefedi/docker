"""
Radarr MCP Server — 100% API coverage via FastMCP
Connects directly to Radarr v5 via Tailscale/Headscale (100.64.0.2:7878)

Template for the build-mcp-servers skill.
Full implementation at /root/.hermes/mcp/radarr_server.py
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Radarr")

RADARR_URL = os.getenv("RADARR_URL", "http://100.64.0.2:7878")
RADARR_API_KEY=os.get...
if not RADARR_API_KEY:
    key_file = os.path.expanduser("~/.hermes/radarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            RADARR_API_KEY=f.read...
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


@mcp.tool
def system_status() -> dict[str, Any]:
    """Get Radarr system status (version, OS, DB, auth, etc.)."""
    return _request("GET", "system/status")


# Full 53-tool implementation at /root/.hermes/mcp/radarr_server.py


if __name__ == "__main__":
    mcp.run()
