# Direct Python MCP Server (Fallback Pattern)

When n8n MCP workflow doesn't expose tools (credential issues, caching, etc.), a direct Python MCP server can act as the bridge instead.

## Architecture

```
Hermes Agent ──stdio──► Python MCP Server ──HTTP──► Target API
```

The Python script reads JSON-RPC from stdin, exposes tools via MCP protocol, and makes HTTP calls to the target API.

## Minimal Template

```python
#!/usr/bin/env python3
"""Direct MCP server for any REST API"""
import os, json, sys, urllib.request, urllib.parse, urllib.error

API_TOKEN = os.environ.get("API_TOKEN", "")
API_BASE = os.environ.get("API_BASE", "https://api.example.com/v1")

def handle_request(request):
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "my-mcp", "version": "1.0.0"}
        }}

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "tools": [{
                "name": "my_api",
                "description": "API catch-all tool. Full description of resources here.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "method": {"type": "string", "enum": ["GET","POST","PUT","PATCH","DELETE"]},
                        "path": {"type": "string", "description": "API path"},
                        "query": {"type": "object", "description": "Query params"},
                        "body": {"type": "object", "description": "Request body"}
                    },
                    "required": ["method", "path"]
                }
            }]
        }}

    elif method == "tools/call":
        params = request.get("params", {})
        args = params.get("arguments", {})
        http_method = args.get("method", "GET")
        path = args.get("path", "")
        query = args.get("query", {})
        body = args.get("body", {})

        url = f"{API_BASE}/{path}"
        if query:
            url += f"?{urllib.parse.urlencode(query)}"

        headers = {"Content-Type": "application/json"}
        if API_TOKEN:
            headers["Authorization"] = f"Bearer {API_TOKEN}"

        data = json.dumps(body).encode() if body and http_method in ("POST","PUT","PATCH") else None
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=http_method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read()) if resp.read() else {}
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            }}
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"HTTP {e.code}: {err}"}], "isError": True
            }}

    elif method == "notifications/initialized":
        return None

    return {"jsonrpc": "2.0", "id": req_id, "result": None}

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        resp = handle_request(json.loads(line))
        if resp:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
    except json.JSONDecodeError:
        continue
```

## Register in Hermes

```bash
hermes mcp add my-service --command python3 --args "/path/to/script.py" --env "API_TOKEN=xxx" --env "API_BASE=https://..."
```

## When to Use This

- n8n MCP workflow won't expose tools (0 tools discovered)
- Credential API assignment fails (`setNodeCredential` unsupported)
- Need a simpler, direct integration without n8n overhead
- Testing/development before building the full n8n workflow

## Limitations

- Single-threaded (handles one request at a time)
- No SSE streaming support (stdio transport only)
- Token/credentials hard to rotate (require restart)