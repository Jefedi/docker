# Cookie-Based Auth MCP Tools (e.g. qBittorrent)

Some services (qBittorrent, NZBGet, legacy APIs) use cookie-based auth instead of API keys. The n8n httpRequestTool node can't handle cookies alone, so a two-node chain is needed.

## Architecture

```
MCP Trigger → Login (httpRequest, form POST) → API Tool (httpRequestTool)
```

The cookie from the login response stays in the n8n execution context. The httpRequestTool reuses it for the same host automatically.

## SDK Implementation

### 1. Login Node (httpRequest, NOT httpRequestTool)

```javascript
const qbLogin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Login',
    executeOnce: true,          // runs once regardless of input items
    alwaysOutputData: true,     // keeps execution flowing on empty data
    parameters: {
      method: 'POST',
      url: 'http://host:port/api/v2/auth/login',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBasicAuth',  // stores user + password
      sendBody: true,
      contentType: 'form-urlencoded',
      specifyBody: 'keypair',
      bodyParameters: {
        parameters: [
          { name: 'username', value: '={{ $credentials.httpBasicAuth.user }}' },
          { name: 'password', value: '={{ $credentials.httpBasicAuth.password }}' }
        ]
      },
      options: {
        response: { response: { fullResponse: true } } // needed for Set-Cookie
      }
    },
    credentials: {
      httpBasicAuth: newCredential('credential-name')
    }
  }
});
```

### 2. API Tool Node (httpRequestTool)

```javascript
const qbApi = node({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'API Tool',
    parameters: {
      method: fromAi('method', 'GET or POST'),
      url: '=http://host:port/api/v2/{{ $fromAI("path", "API path description") }}',
      authentication: 'none',   // cookie from login handles auth
      sendQuery: true,
      specifyQuery: 'json',
      jsonQuery: fromAi('query', 'Query params JSON'),
      sendBody: false,
      options: { timeout: 15000 }
    }
  }
});
```

### 3. Chain

```javascript
export default workflow('mcp-service', 'MCP Service')
  .add(mcpTrigger)
  .to(qbLogin)
  .to(qbApi);
```

## Key Details

- **Cookie propagation**: n8n shares cookies across HTTP Request nodes within the same execution for the same host. Login sets SID cookie, Tool node picks it up.
- **`alwaysOutputData: true`**: Required on login so execution continues even if login returns empty data.
- **`executeOnce: true`**: Prevents login from running N× when trigger has N items.
- **`fullResponse: true`**: Ensures Set-Cookie headers are captured.
- **Form encoding**: Use `contentType: 'form-urlencoded'` for login.
- **Auth on tool**: Set to `none` — don't use `httpBasicAuth` on the tool node, it would override the cookie.

## Credential Requirement

The credential referenced by `newCredential('name')` must exist in n8n before the workflow can activate. Create it via n8n UI:
1. Go to Credentials → Add New
2. Pick the appropriate type (e.g. HTTP Basic Auth for username/password)
3. Set name to match the `newCredential()` reference
4. Supply correct values

## Testing

After creation and publish:
1. Call a simple read-only endpoint: `method=GET, path=app/version, query={}`
2. If "connection refused" → check URL/port/credential
3. If the service returns "Fails." → wrong username/password (qBittorrent specific)
