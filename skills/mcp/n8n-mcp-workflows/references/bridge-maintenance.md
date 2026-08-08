# n8n MCP Bridge Maintenance

When a self-hosted backend service moves hosts, ALL HTTP Request tool nodes in the n8n MCP bridge workflow need their URLs updated.

## Diagnosis

1. `get_workflow_details({workflowId})` on the MCP bridge workflow
2. Scan each node's `url` parameter — likely still the old IP
3. Check BOTH draft + active versions (`activeVersion` key) — they can diverge
4. Double-check: probe the backend directly (curl/browser) to confirm it's alive

## Fix

```javascript
// Step 1: Update every HTTP Request node's URL
const operations = [
  {type: "setNodeParameter", nodeName: "node_name", path: "/url", 
   value: "http://NEW_IP:PORT/api/v3/..."},
  // ... one per node
];
mcp_n8n_mcp_update_workflow({workflowId, operations});

// Step 2: Publish for changes to take effect
mcp_n8n_mcp_publish_workflow({workflowId});
```

## Pitfalls

- **Partial migration**: draft may have some nodes fixed, others not. Check both versions
- **Publish required**: draft changes don't affect MCP until published
- **Credentials**: MCP bridge auth is separate from backend auth — verify the credential still works
- **Pangolin SSO**: if the backend is behind Pangolin, SSO may have auto-flipped to false on resource update — set `sso=True` after updating the resource target
- **setNodeParameter path**: use `/url` for URL updates. The old `updates: {url: "..."}` pattern doesn't work with the new `mcp_n8n_mcp_update_workflow` API. Use `{type: "setNodeParameter", nodeName: "...", path: "/url", value: "..."}` instead.

## Example: Sonarr moved from jNas to AX42

- Old IP: `100.64.0.4` (jNas) → New IP: `100.64.0.2` (AX42)
- "MCP Sonarr" workflow had 11 nodes with hardcoded URLs
- MCP returned "connection refused" for all tools
- Fix: updated all 11 `/url` values, published → immediate recovery

## Creating a New MCP Bridge Workflow

Use the n8n Workflow SDK via `mcp_n8n_mcp_validate_workflow` + `mcp_n8n_mcp_create_workflow_from_code` to create new MCP bridges.

### Step 1: Gather info

- Service host:port (same IP as Sonarr/Radarr if co-located, e.g. `100.64.0.2:8080`)
- Auth method (API key in header, cookie-based login, or none for local services)
- API version prefix (`/api/v2/`, `/api/v3/`, etc.)
- Read-only endpoints for diagnostic tools

### Step 2: Choose auth pattern

**Pattern A — API Key in Header** (Sonarr, Radarr, Prowlarr, etc.)
Use a single `httpRequestTool` with `genericAuthType: "httpHeaderAuth"` and a credential for the API key.

```javascript
const api = node({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'ServiceName API',
    parameters: {
      method: fromAi('method', 'GET or POST'),
      url: '=http://HOST:PORT/api/v3/{{ $fromAI("path", "...") }}',
      authentication: 'none',
      sendQuery: true, specifyQuery: 'json',
      jsonQuery: fromAi('query', '{}'),
      options: { timeout: 30000 }
    }
  }
});
```

**Pattern B — Cookie-Based Login** (qBittorrent)
Chain a login HTTP Request before the httpRequestTool. n8n's cookie jar shares cookies across chained nodes.

```javascript
const login = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Login',
    executeOnce: true,
    alwaysOutputData: true,
    parameters: {
      method: 'POST',
      url: 'http://HOST:PORT/api/v2/auth/login',
      authentication: 'none',
      sendBody: true, contentType: 'form-urlencoded', specifyBody: 'keypair',
      bodyParameters: {
        parameters: [
          { name: 'username', value: 'user' },
          { name: 'password', value: 'pass' }
        ]
      },
      options: { response: { response: { fullResponse: true } } }
    }
  }
});

const api = node({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'API Call',
    parameters: {
      method: fromAi('method', 'GET or POST'),
      url: '=http://HOST:PORT/api/v2/{{ $fromAI("path", "...") }}',
      authentication: 'none',
      sendQuery: true, specifyQuery: 'json',
      jsonQuery: fromAi('query', '{}'),
      options: { timeout: 15000, response: { response: { neverError: true } } }
    }
  }
});

// Chain: trigger → login → api
export default workflow('mcp-servicename', 'MCP ServiceName')
  .add(mcpTrigger).to(login).to(api);
```

### Step 3: Publish and handle conflicts

```javascript
// If an old version exists with the same MCP path
mcp_n8n_mcp_unpublish_workflow({workflowId: "OLD_ID"});
mcp_n8n_mcp_archive_workflow({workflowId: "OLD_ID"});

// Then publish the new one
mcp_n8n_mcp_publish_workflow({workflowId: "NEW_ID"});
```

### Pitfalls for new bridges

- **Webhook conflict**: "conflict with one of the webhooks" = old active workflow with same MCP path. Unpublish+archive it first.
- **Credentials**: The `mcp_n8n_mcp_create_workflow_from_code` auto-assigns random credentials to the MCP trigger. If wrong, update via `setNodeCredential` with empty strings: `{type: "setNodeCredential", nodeName: "...", credentialKey: "httpBearerAuth", credentialId: "", credentialName: ""}`.
- **Login node must be before API node**: Cookie propagation only works in the same execution chain. If they're disconnected the cookie won't flow.
- **ExecuteOnce + alwaysOutputData**: Both MUST be true on the login node for the chain to work reliably.
- **Read-only documentation**: When creating tools for private tracker environments, explicitly document "NE RIEN SUPPRIMER" / "READ ONLY" in the tool description — tools shouldn't have delete/remove/modify operations.
