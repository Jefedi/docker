#!/usr/bin/env python3
"""
SSE-to-stdio MCP bridge.
Connects to a remote SSE MCP server and exposes it as a local stdio MCP server.

Usage:
  SSE_URL="https://..." SSE_TOKEN="my-token" python3 sse_mcp_bridge.py
"""

import os
import sys
import asyncio
import logging

logging.basicConfig(level=logging.WARNING)

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool


async def main():
    url = os.environ.get("SSE_URL")
    token = os.environ.get("SSE_TOKEN")

    # Fallback: read token from well-known file
    if not token:
        token_file = os.path.expanduser("~/.hermes/scripts/sse_token.txt")
        if os.path.exists(token_file):
            with open(token_file) as f:
                token = f.read().strip()

    if not url:
        print("SSE_URL environment variable required", file=sys.stderr)
        sys.exit(1)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Shared state for the remote session
    remote_session = None
    session_ready = asyncio.Event()

    async def connect_sse():
        nonlocal remote_session
        try:
            async with sse_client(url, headers=headers) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    remote_session = session
                    session_ready.set()
                    # Keep connection alive indefinitely
                    await asyncio.Event().wait()
        except Exception as e:
            print(f"SSE connection error: {e}", file=sys.stderr)
            sys.exit(1)

    # Start SSE connection in background
    sse_task = asyncio.create_task(connect_sse())

    # Wait for session to be ready
    try:
        await asyncio.wait_for(session_ready.wait(), timeout=30)
    except asyncio.TimeoutError:
        print("Failed to connect to SSE server within 30s", file=sys.stderr)
        sys.exit(1)

    app = Server("sse-bridge")

    @app.list_tools()
    async def list_tools():
        tools_result = await remote_session.list_tools()
        return [
            Tool(
                name=t.name,
                description=t.description,
                inputSchema=t.inputSchema,
            )
            for t in tools_result.tools
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        result = await remote_session.call_tool(name, arguments or {})
        return result

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
