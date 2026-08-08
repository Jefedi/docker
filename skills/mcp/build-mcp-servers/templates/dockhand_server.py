"""FastMCP server for Dockhand Docker management API.
Connects to http://100.64.0.2:3000 (Dockhand) and exposes Docker
management as MCP tools. 14 tools total.

Register with Hermes:
    echo Y | hermes mcp add dockhand --command "python3" --args "/path/to/dockhand_server.py"
"""
from __future__ import annotations
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Dockhand Docker Manager")
DOCKHAND_URL = os.getenv("DOCKHAND_URL", "http://100.64.0.2:3000")
TIMEOUT = float(os.getenv("DOCKHAND_TIMEOUT_SECONDS", "20"))


def _req(method: str, path: str, **kw) -> Any:
    url = f"{DOCKHAND_URL.rstrip('/')}/{path.lstrip('/')}"
    with httpx.Client(timeout=TIMEOUT) as c:
        r = c.request(method, url, params=kw.get("params"), json=kw.get("json"))
        try:
            return r.json()
        except Exception:
            return {"text": r.text, "status": r.status_code}


@mcp.tool()
def dockhand_list_environments() -> list[dict[str, Any]]:
    """List all Docker hosts managed by Dockhand (ax42, jnas, jtower, VPS Pangolin)."""
    return _req("GET", "/api/environments")


@mcp.tool()
def dockhand_list_containers(environment_id: int | None = None, status: str | None = None) -> list:
    """List containers. Optional env_id (1=ax42,2=jnas,3=Pangolin,4=jtower) and status filter."""
    p = {}
    if environment_id is not None:
        p["environmentId"] = environment_id
    if status:
        p["status"] = status
    return _req("GET", "/api/containers", params=p)


@mcp.tool()
def dockhand_list_stacks(environment_id: int | None = None) -> list:
    """List Docker Compose stacks. Optional environment_id filter."""
    p = {}
    if environment_id is not None:
        p["environmentId"] = environment_id
    return _req("GET", "/api/stacks", params=p)


@mcp.tool()
def dockhand_list_images(environment_id: int | None = None) -> list:
    """List Docker images. Optional environment_id filter."""
    p = {}
    if environment_id is not None:
        p["environmentId"] = environment_id
    return _req("GET", "/api/images", params=p)


@mcp.tool()
def dockhand_list_volumes(environment_id: int | None = None) -> list:
    """List Docker volumes. Optional environment_id filter."""
    p = {}
    if environment_id is not None:
        p["environmentId"] = environment_id
    return _req("GET", "/api/volumes", params=p)


@mcp.tool()
def dockhand_list_networks(environment_id: int | None = None) -> list:
    """List Docker networks. Optional environment_id filter."""
    p = {}
    if environment_id is not None:
        p["environmentId"] = environment_id
    return _req("GET", "/api/networks", params=p)


@mcp.tool()
def dockhand_container_logs(container_id: int, environment_id: int = 1, tail: int = 50) -> dict:
    """Fetch container logs. Args: container_id, environment_id (default 1=ax42), tail lines."""
    return _req("GET", f"/api/containers/{container_id}/logs", params={"environmentId": environment_id, "tail": tail})


@mcp.tool()
def dockhand_system_info() -> dict:
    """Get Dockhand system info: runtime, DB type, aggregate Docker stats."""
    return _req("GET", "/api/system")


@mcp.tool()
def dockhand_environment_info(environment_id: int) -> dict:
    """Get details for a specific Docker host by environment_id (1-4)."""
    for env in _req("GET", "/api/environments"):
        if env["id"] == environment_id:
            return env
    return {"error": f"Environment {environment_id} not found"}


@mcp.tool()
def dockhand_start_container(container_id: int) -> dict:
    """Start a stopped container."""
    return _req("POST", f"/api/containers/{container_id}/start")


@mcp.tool()
def dockhand_stop_container(container_id: int) -> dict:
    """Stop a running container."""
    return _req("POST", f"/api/containers/{container_id}/stop")


@mcp.tool()
def dockhand_restart_container(container_id: int) -> dict:
    """Restart a container."""
    return _req("POST", f"/api/containers/{container_id}/restart")


@mcp.tool()
def dockhand_deploy_stack(stack_id: int) -> dict:
    """Deploy or update a Docker Compose stack."""
    return _req("POST", f"/api/stacks/{stack_id}/deploy")


@mcp.tool()
def dockhand_stop_stack(stack_id: int) -> dict:
    """Stop a running Docker Compose stack."""
    return _req("POST", f"/api/stacks/{stack_id}/stop")


if __name__ == "__main__":
    mcp.run()
