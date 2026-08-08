# Building MCP Servers via n8n Workflow SDK

An alternative to FastMCP Python: create MCP servers as n8n workflows using the Workflow SDK.

## When to Choose This Over FastMCP Python

| Scenario | Best Approach |
|---|---|
| Service has a clean REST API, no auth | FastMCP Python |
| Service needs cookie-based login before API calls | n8n MCP (chains Login + API nodes) |
| Service is already connected in n8n (credentials exist) | n8n MCP (reuse existing n8n creds) |
| You need rapid iteration / visual testing | n8n MCP (build in n8n UI) |
| Service is unreachable from the VPS but reachable from Docker | n8n MCP (n8n is on the same Docker network) |
| Need full programmatic control | FastMCP Python |

## Workflow Structure

### Minimal (Single Tool, No Auth)

```
MCP Trigger (path: "service-name")
  └─ ai_tool → httpRequestTool (with fromAI params)
```

### Auth-First (Login Cookie Before API)

```
MCP Trigger (path: "service-name")
  ├─ main → httpRequest (Login) → main → httpRequestTool (API call)
  └─ ai_tool → httpRequestTool (MCP registration)
```

Both `main` AND `ai_tool` connections from the tool to the trigger are required:
- `main` = data flow (Login output feeds the API tool)
- `ai_tool` = MCP registration (tool is discoverable)

## SDK Code Template

### Minimal Tool (No Auth)

```javascript
import { workflow, node, trigger, fromAi } from '@n8n/workflow-sdk';

const mcpTrigger = trigger({
  type: '@n8n/n8n-nodes-langchain.mcpTrigger',
  version: 1.1,
  config: {
    name: 'MCP ServiceName',
    parameters: {
      authentication: 'bearerAuth',
      path: 'service-name'
    }
  }
});

const apiTool = node({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'service_api',
    parameters: {
      method: fromAi('method', 'HTTP method: GET or POST'),
      url: '=http://service-host:port/api/v2/{{ $fromAI("path", "API path") }}',
      authentication: 'none',
      sendQuery: true,
      specifyQuery: 'json',
      jsonQuery: fromAi('query', 'Query params JSON. Use {} for none.'),
      options: { timeout: 15000 }
    }
  }
});

export default workflow('mcp-servicename', 'MCP ServiceName')
  .add(mcpTrigger)
  .to(apiTool);
```

Note: the tool will NOT be connected correctly from a `.to()` call alone. The `ai_tool` connection must be added via `update_workflow` after creation (see below).

### Auth-First with Login (Cookie-Based)

```javascript
import { workflow, node, trigger, fromAi } from '@n8n/workflow-sdk';

const mcpTrigger = trigger({
  type: '@n8n/n8n-nodes-langchain.mcpTrigger',
  version: 1.1,
  config: {
    name: 'MCP ServiceName',
    parameters: {
      authentication: 'bearerAuth',
      path: 'service-name'
    }
  }
});

const qbLogin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Login',
    executeOnce: true,
    alwaysOutputData: true,
    parameters: {
      method: 'POST',
      url: 'http://localhost:8080/api/v2/auth/login',
      authentication: 'none',
      sendBody: true,
      contentType: 'form-urlencoded',
      specifyBody: 'keypair',
      bodyParameters: {
        parameters: [
          { name: 'username', value: 'username' },
          { name: 'password', value: 'password' }
        ]
      },
      options: { response: { response: { fullResponse: true } } }
    }
  }
});

const apiTool = node({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'service_api',
    parameters: {
      method: fromAi('method', 'HTTP method: GET or POST'),
      url: '=http://localhost:8080/api/v2/{{ $fromAI("path", "API path") }}',
      authentication: 'none',
      sendQuery: true,
      specifyQuery: 'json',
      jsonQuery: fromAi('query', 'Query params JSON. Use {} for none.'),
      options: { timeout: 15000 }
    }
  }
});

export default workflow('mcp-servicename', 'MCP ServiceName')
  .add(mcpTrigger)
  .to(qbLogin)
  .to(apiTool);
```

The password can be inlined (for private n8n instances) or read from a credential.

## Post-Creation Steps

### 1. Add ai_tool Connection

The SDK `.to()` creates a `main` connection. The `ai_tool` connection must be added separately:

```javascript
// Via update_workflow:
{
  type: "addConnection",
  source: "service_api",       // the tool node name
  target: "MCP ServiceName",   // the trigger node name
  connectionType: "ai_tool",
  sourceIndex: 0,
  targetIndex: 0
}
```

### 2. Link MCP AUTH Credential

The MCP trigger needs the "MCP AUTH" bearer credential linked for SSE access:

```javascript
{
  type: "setNodeCredential",
  nodeName: "MCP ServiceName",
  credentialKey: "httpBearerAuth",
  credentialId: "ixt7qUkWl6yNMDBt",   // "MCP AUTH" credential
  credentialName: "MCP AUTH"
}
```

### 3. Unpublish + Republish

After changing credentials or connections, the workflow must be republished for changes to take effect:

```javascript
// 1. Unpublish
unpublish_workflow({ workflowId })

// 2. Publish again
publish_workflow({ workflowId })
```

### 4. Add SSE Bridge to Hermes

Add the MCP server to Hermes config under `mcp_servers`:

```yaml
mcp_servers:
  service-name:
    args:
    - /root/.hermes/scripts/sse_mcp_bridge.py
    command: python3
    connect_timeout: 60
    env:
      SSE_URL: https://n8n.jefe.ovh/mcp/service-name/sse
```

This can be done by appending to the YAML file or via `hermes mcp add` (which prompts — pipe `y` for non-interactive).

### 5. Verify

```bash
hermes mcp test service-name
# Expected: ✓ Connected, ✓ Tools discovered: N
```

**Important:** Tools only appear in **new** Hermes sessions, not the current one.

## Pitfalls
- **`setNodeParameter` path bug:** Setting a node parameter via JSON Pointer (e.g. `"/parameters/url"`) can create a NESTED `parameters.parameters.url` instead of replacing `parameters.url`. This happens because the update tool treats `url` as a key to insert into the existing `parameters` object rather than overwriting the existing key. **Fix:** Use `updateNodeParameters` with `replace=true` to replace the entire parameters object atomically — or verify the result with `get_workflow_details` after the operation.
- **Catch-all URL must use `$fromAI("path")`, not `$fromAI("method")`:** The most common bug when building a catch-all tool is using `$fromAI("method")` in the URL template (`/api/v3/{{ $fromAI("method") }}`). The URL should use `$fromAI("path")` for the API path segment, while `$fromAI("method")` remains for the HTTP method field. This was the exact bug fixed in the MCP Sonarr n8n workflow — the URL was `http://host/api/v3/{{ $fromAI("method") }}` instead of `http://host/api/v3/{{ $fromAI("path") }}`, causing all requests to hit `/api/v3/GET` instead of the intended path.
- **Dual connection requirement:** The `ai_tool` connection is mandatory for MCP tool discovery. Without it, `hermes mcp test` shows "Tools discovered: 0" even though the HTTP connection succeeds.

- **Dual connection requirement:** The `ai_tool` connection is mandatory for MCP tool discovery. Without it, `hermes mcp test` shows "Tools discovered: 0" even though the HTTP connection succeeds.
- **`main` vs `ai_tool`:** The `main` connection is for data flow (Login → API tool). The `ai_tool` connection is for MCP registration (tool → trigger). These are separate concerns and both are needed.
- **SSE URL 403:** If the SSE endpoint returns 403 "Authorization data is wrong!", the wrong credential is linked. Try "MCP AUTH" (httpBearerAuth) on the MCP trigger.
- **localhost vs Tailscale IP:** Services that listen only on Docker's internal network may reject connections via the Tailscale IP. Use `localhost` or the Docker service name instead.
- **Credential changes require republication:** Setting a credential on the MCP trigger via `setNodeCredential` does NOT take effect until the workflow is unpublished and republished.
- **fromAI in non-tool nodes:** `fromAI()` only works in `httpRequestTool` nodes, not regular `httpRequest` nodes. Regular nodes must use hardcoded or expression-based parameters.
- **The SDK `.description()` method doesn't exist.** Set the description via the `description` parameter in `create_workflow_from_code`.
- **Network isolation:** If the VPS can't reach the service (connection refused), the n8n workflow may still be able to reach it via localhost or Docker network.
