# n8n MCP Catch-All Pattern

When designing n8n MCP workflows, prefer a **single catch-all tool** over N individual endpoint-specific tools. This keeps the MCP tool surface clean and leverages the LLM's ability to route requests dynamically via `$fromAI()`.

## When to Use

- You have 3+ HTTP Request nodes that all call the same base API with different endpoints (pattern: `https://api.example.com/v1/{resource}`)
- The existing tools list is cluttered (10+ tools from one MCP server hurts LLM tool selection)
- The API has predictable REST semantics (GET list, GET single, POST create, PUT create, PATCH update, DELETE)

## When NOT to Use

- Pre-built dedicated nodes exist (Slack, Gmail, Discord, etc.) — use those instead for proper auth handling
- Different tools need completely different parameter schemas with no overlap
- The tool needs special auth that a single HTTP Request can't handle

## Pattern

**Structure:**
1. **MCP Trigger** — standard, path set to service name (e.g. `discord`, `pangolin`, `jellyfin`)
2. **Single HTTP Request Tool** — catch-all with `$fromAI()` for method/path/query/body

**HTTP Request Tool parameters:**
```json
{
  "method": "={{ $fromAI(\"method\", \"HTTP method: GET, POST, PUT, PATCH, or DELETE\") }}",
  "url": "=https://api.example.com/v1/{{ $fromAI(\"path\", \"API path after /v1/ prefix. Full documentation of all endpoints...\") }}",
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth",
  "sendQuery": true,
  "specifyQuery": "json",
  "jsonQuery": "={{ $fromAI(\"query\", \"Query parameters as JSON object...\") }}",
  "sendBody": true,
  "contentType": "json",
  "specifyBody": "json",
  "jsonBody": "={{ $fromAI(\"body\", \"Request body as JSON for POST/PUT/PATCH. Use {} for GET/DELETE...\") }}",
  "options": {
    "response": { "response": { "neverError": true } },
    "timeout": 30000
  }
}
```

**Key design principle:** The `$fromAI("path", "...")` description field is CRITICAL. It serves as documentation for the LLM that will route requests. It must list:
- Every endpoint category (orgs, users, roles, sites, etc.)
- The HTTP method for each operation (GET list, POST create, etc.)
- Example paths so the LLM can construct the right URL
- Any special parameter formats

## Real Example: MCP Pangolin (64 tools → 1)

Before: 64 individual HTTP Request nodes (one per endpoint like `pangolin_list_orgs`, `pangolin_create_resource`, `pangolin_delete_target`).

After: Single `pangolin_api` tool with the complete API reference in the path description:

```
path description content structure:
1. RESOURCE CATEGORY lines: name (method) — short description
2. Every notable path template with {id} placeholders
3. Example paths at the end
4. Auth note line
```

The catch-all `url` pattern:
```
=https://api.jefe.ovh/v1/{{ $fromAI("path", "...all endpoints documented here...") }}
```

## Pitfalls

- **Connection direction matters**: For MCP tools, the `addConnection` must have `source` = the **tool node**, `target` = the **MCP trigger**, with `connectionType: "ai_tool"`. Getting the direction wrong produces DISCONNECTED_NODE warnings.
- **Credential auto-assignment is skipped** for tools added via `updateWorkflow`. You must manually assign the credential in the n8n UI, or set it in the `addNode` operation via the `credentials` field.
- **The path description MUST be comprehensive** — the LLM can only construct valid API calls if it knows all the endpoints. A sparse description leads to hallucinated API paths.
- **neverError: true** is essential — without it, non-2xx responses (404, 403, etc.) cause the tool to throw instead of returning a structured error the LLM can interpret and report to the user.