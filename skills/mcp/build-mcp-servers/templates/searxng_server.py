#!/usr/bin/env python3
"""
SearXNG MCP Server — Search via personal SearXNG instance
Routes requests through the Pangolin Newt tunnel (pangolin-cli container)
to access the private resource at search.jefe.al
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("SearXNG")

SEARXNG_URL = os.getenv("SEARXNG_URL", "https://search.jefe.al")
DOCKER_EXEC = os.getenv("SEARXNG_DOCKER_CMD", "docker exec pangolin-cli")
SEARXNG_INTERNAL = os.getenv("SEARXNG_INTERNAL", "false").lower() == "true"


def _search(query: str, categories: str | None = None,
            language: str | None = None, pageno: int = 1) -> dict[str, Any]:
    """Execute a SearXNG search query.

    If SEARXNG_INTERNAL=true, uses direct HTTP request (for when SearXNG
    is directly accessible). Otherwise routes through the Newt tunnel
    via docker exec pangolin-cli.
    """
    params = {
        "q": query,
        "format": "json",
        "pageno": pageno,
    }
    if categories:
        params["categories"] = categories
    if language:
        params["language"] = language

    url = f"{SEARXNG_URL.rstrip('/')}/search"

    if SEARXNG_INTERNAL:
        import httpx
        resp = httpx.get(url, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        return resp.json()
    else:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        cmd_parts = DOCKER_EXEC.split()
        cmd_parts.extend(["curl", "-sk", full_url, "--max-time", "30"])
        result = subprocess.run(
            cmd_parts, capture_output=True, text=True, timeout=35
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"SearXNG search failed (exit={result.returncode}): "
                f"{result.stderr[:500]}"
            )

        return json.loads(result.stdout)


@mcp.tool
def search(
    query: str,
    categories: str | None = None,
    language: str | None = None,
    pageno: int = 1,
) -> dict[str, Any]:
    """Search the web using SearXNG.

    Args:
        query: Search query.
        categories: Optional category filter (e.g. 'general', 'news', 'images',
                   'videos', 'music', 'files', 'it', 'science', 'social media').
                   Comma-separate multiple categories.
        language: Optional language filter (e.g. 'fr', 'en', 'de').
        pageno: Page number (default: 1).
    """
    try:
        data = _search(query, categories, language, pageno)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }

    results = []
    for r in data.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "engine": r.get("engine", ""),
            "score": r.get("score", 0),
            "category": r.get("category", "general"),
            "publishedDate": r.get("publishedDate"),
            "engines": r.get("engines", []),
        })

    return {
        "success": True,
        "query": data.get("query", query),
        "total_results": len(results),
        "results": results,
        "answers": data.get("answers", []),
        "suggestions": data.get("suggestions", []),
        "infoboxes": data.get("infoboxes", []),
        "unresponsive_engines": data.get("unresponsive_engines", []),
    }


@mcp.tool
def search_simple(query: str, limit: int = 10) -> list[dict[str, str]]:
    """Quick search — returns just title, URL, and snippet.

    Args:
        query: Search query.
        limit: Max results to return (default: 10).
    """
    data = _search(query)
    results = data.get("results", [])
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:300],
            "engine": r.get("engine", ""),
        }
        for r in results[:limit]
    ]


if __name__ == "__main__":
    mcp.run()
