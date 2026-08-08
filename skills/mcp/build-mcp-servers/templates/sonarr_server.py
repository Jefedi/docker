"""
Sonarr MCP Server — 100% API coverage via FastMCP
Connects directly to Sonarr v4 via Tailscale/Headscale (100.64.0.2:8989)

Template for the build-mcp-servers skill.
Full implementation at /root/.hermes/mcp/sonarr_server.py
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Sonarr")

SONARR_URL = os.getenv("SONARR_URL", "http://100.64.0.2:8989")
SONARR_API_KEY=os.get...
if not SONARR_API_KEY:
    key_file = os.path.expanduser("~/.hermes/sonarr_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file) as f:
            SONARR_API_KEY=f.read...\nif not SONARR_API_KEY:\n    raise RuntimeError("SONARR_API_KEY env var or ~/.hermes/sonarr_api_key.txt is required")
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


@mcp.tool
def system_status() -> dict[str, Any]:
    """Get Sonarr system status (version, OS, DB, auth, etc.)."""
    return _request("GET", "system/status")


# Full 47-tool implementation at /root/.hermes/mcp/sonarr_server.py
# This template shows the pattern: one _request helper + typed @mcp.tool functions


if __name__ == "__main__":
    mcp.run()
