#!/usr/bin/env python3
"""SSE MCP bridge for Pangolin - forwards Pangolin API as MCP tools"""
import os, json, sys, subprocess, urllib.request

TOKEN_FILE = os.path.expanduser("~/.hermes/scripts/sse_token.txt")

# Read the shared SSE token (used for n8n auth)
sse_token = open(TOKEN_FILE).read().strip() if os.path.exists(TOKEN_FILE) else ""

# The Pangolin API key - user needs to set this
PANGOLIN_API_KEY = os.environ.get("PANGOLIN_API_KEY", "")

# Read from stdin - receive JSON-RPC messages
def handle_request(request):
    method = request.get("method", "")
    req_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "pangolin-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "pangolin_api",
                        "description": "Pangolin API catch-all tool. Makes HTTP requests to https://api.jefe.ovh/v1/.\n\nRESOURCES:\nORGANISATIONS: orgs (GET list), org (PUT create), org/{id} (GET/POST/DELETE)\nUSERS: org/{id}/users (GET), org/{id}/invite (PUT), org/{id}/invitations (GET/DELETE), org/{id}/user/{userId} (POST/DELETE)\nROLES: org/{id}/roles (GET), org/{id}/role (PUT), role/{id} (GET/POST/DELETE), role/{id}/add/{userId} (POST), role/{id}/remove/{userId} (POST)\nSITES: org/{id}/sites (GET), org/{id}/site (PUT), site/{id} (GET/POST/DELETE)\nRESOURCES: org/{id}/resources (GET), site/{id}/resources (GET), org/{id}/site/{id}/resource (PUT), resource/{id} (GET/POST/DELETE), resource/{id}/users/roles/password/pincode/whitelist\nTARGETS, RULES, API KEYS, DOMAINS, IDPs, AUDIT, ACCESS TOKENS\n\nAuth: Bearer token via PANGOLIN_API_KEY env var",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "description": "HTTP method: GET, POST, PUT, PATCH, DELETE",
                                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]
                                },
                                "path": {
                                    "type": "string",
                                    "description": "API path AFTER /v1/. Example: orgs, org/my-org, org/my-org/sites, resource/abc123/targets"
                                },
                                "query": {
                                    "type": "object",
                                    "description": "Optional query parameters as JSON object"
                                },
                                "body": {
                                    "type": "object",
                                    "description": "Request body for POST/PUT/PATCH"
                                }
                            },
                            "required": ["method", "path"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        
        if tool_name == "pangolin_api":
            http_method = tool_args.get("method", "GET")
            path = tool_args.get("path", "")
            query = tool_args.get("query", {})
            body = tool_args.get("body", {})
            
            url = f"https://api.jefe.ovh/v1/{path}"
            
            if query:
                qs = urllib.parse.urlencode(query)
                url = f"{url}?{qs}"
            
            headers = {
                "Content-Type": "application/json"
            }
            if PANGOLIN_API_KEY:
                headers["Authorization"] = f"Bearer {PANGOLIN_API_KEY}"
            
            data = json.dumps(body).encode() if body and http_method in ("POST", "PUT", "PATCH") else None
            
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=http_method)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_body = resp.read().decode()
                    result_content = json.loads(resp_body) if resp_body else {}
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result_content, indent=2)}]
                    }
                }
            except urllib.error.HTTPError as e:
                error_body = e.read().decode() if e.fp else str(e)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"HTTP {e.code}: {error_body}"}],
                        "isError": True
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True
                    }
                }
    
    elif method == "notifications/initialized":
        return None  # No response needed for notifications
    
    return {"jsonrpc": "2.0", "id": req_id, "result": None}

# Main loop - read JSON-RPC from stdin, write responses to stdout
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        request = json.loads(line)
        response = handle_request(request)
        if response:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    except json.JSONDecodeError:
        continue
