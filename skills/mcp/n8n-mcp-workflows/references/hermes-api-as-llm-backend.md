# Hermes API as n8n LLM Backend

Using the Hermes Agent API server (`localhost:9119`) as an OpenAI-compatible
LLM backend for n8n AI Agent / chatbot workflows.

## Architecture

```
n8n Chat Trigger → AI Agent → OpenAI Chat Model (baseURL: localhost:9119/v1)
                                          ↓
                               Hermes API Server (port 9119)
                                          ↓
                               Hermes Agent → LiteLLM → Ollama Cloud (GLM-5.2)
```

The Hermes API server exposes `/v1/chat/completions` and `/v1/responses` —
both are OpenAI-compatible. Auth is a Bearer token via the `API_SERVER_KEY`
env var (in `/opt/data/.env`).

## Key Configuration Points

### 1. Create the OpenAI credential via REST API

The n8n MCP `create_workflow_from_code` tool cannot create credentials inline
(rejects `id: 'new'`). Create the credential first via the n8n REST API:

```bash
API_KEY=$(cat /opt/data/.n8n_api_key)
curl -s -X POST http://localhost:5678/api/v1/credentials \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hermes API","type":"openAiApi","data":{"apiKey":"<API_SERVER_KEY>"}}'
```

Returns `{"id":"<credId>", ...}` — use that ID in the workflow's
`credentials.openAiApi.id`.

### 2. OpenAI Chat Model node — critical parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `model` | `{ __rl: true, mode: 'id', value: 'glm-5.2' }` | Model ID via Ollama Cloud |
| `responsesApiEnabled` | `false` | **CRITICAL** — the Hermes API server's `/v1/responses` endpoint requires dashboard auth (cookie/basic_auth). The `/v1/chat/completions` endpoint works with Bearer token. Setting `responsesApiEnabled: false` forces the node to use `/v1/chat/completions`. |
| `options.baseURL` | `http://localhost:9119/v1` | Hermes API server, not `api.openai.com` |
| `options.timeout` | `120000` | Hermes can take a while (full system prompt + tools) |

### 3. Dashboard auth vs API server auth — the distinction

The Hermes dashboard (`:9120`) and the Hermes API server (`:9119`) are
**different services** with different auth:

- **Dashboard (`:9120`)**: `basic_auth` in `config.yaml` → requires
  `POST /auth/password-login` → session cookie. The `/v1/responses` route
  on the dashboard is behind this auth gate. A workflow hitting the
  dashboard's `/v1/responses` without a cookie gets the login HTML page
  back → `Cannot use 'in' operator to search for 'object' in <!doctype html>`

- **API server (`:9119`)**: Bearer token via `API_SERVER_KEY`. The
  `/v1/chat/completions` endpoint accepts `Authorization: Bearer <key>`.
  No cookie needed.

**Always use `:9119` with Bearer token for n8n workflows, not `:9120`.**

### 4. Workflow structure (SDK pattern)

```javascript
const hermesModel = languageModel({
  type: '@n8n/n8n-nodes-langchain.lmChatOpenAi',
  version: 1.3,
  config: {
    name: 'Hermes GLM-5.2',
    parameters: {
      model: { __rl: true, mode: 'id', value: 'glm-5.2' },
      responsesApiEnabled: false,
      options: {
        baseURL: 'http://localhost:9119/v1',
        temperature: 0.7,
        timeout: 120000,
      },
    },
    credentials: { openAiApi: { id: '<credId>', name: 'Hermes API' } },
  },
});

const chatMemory = memory({
  type: '@n8n/n8n-nodes-langchain.memoryBufferWindow',
  version: 1.4,
  config: {
    name: 'Chat Memory',
    parameters: { sessionIdType: 'fromInput', contextWindowLength: 10 },
  },
});

const chatTrigger = trigger({
  type: '@n8n/n8n-nodes-langchain.chatTrigger',
  version: 1.4,
  config: { name: 'Chat Trigger', parameters: {} },
});

const aiAgent = node({
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: 'Hermes Agent',
    parameters: {
      promptType: 'auto',
      options: {
        systemMessage: 'You are Hermes Agent...',
        maxIterations: 5,
        enableStreaming: true,
      },
    },
    subnodes: { model: hermesModel, memory: chatMemory },
  },
});

export default workflow('hermes-chat', 'Hermes Agent Chat')
  .add(chatTrigger)
  .to(aiAgent);
```

## Pitfalls

- **`responsesApiEnabled: true` (default) breaks the workflow**: The OpenAI
  Chat Model node defaults to `responsesApiEnabled: true` which uses the
  `/v1/responses` endpoint. On the Hermes API server this route is gated by
  dashboard auth. Always set `responsesApiEnabled: false` to use
  `/v1/chat/completions` instead.

- **Credential creation must happen before workflow creation**: The
  `create_workflow_from_code` MCP tool rejects `id: 'new'` credentials with
  `credential 'new' not found`. Create the credential via REST API first,
  then pass the real credential ID.

- **Streaming**: Set `enableStreaming: true` on the Agent and
  `responseMode: 'streaming'` on the Chat Trigger for real-time chat.
  The Chat Trigger defaults to `lastNode` mode which requires the last
  node to output `{ output: '<text>' }`.

- **System prompt**: The Hermes API server injects its own full system prompt
  (~29K tokens) on every call. The n8n system prompt is sent as an additional
  system message. Keep the n8n-side system prompt short and complementary.

- **Testing**: `test_workflow` with pin data may fail with "No prompt
  specified" because the Chat Trigger's `input` field format doesn't match
  what the Agent expects. Test via the n8n chat UI instead (open the workflow
  → Chat Trigger → Open Chat).

- **⚠️ CRITICAL — Hermes API server strips `tools` from the payload**:
  The Hermes API server (`localhost:9119`) does NOT forward OpenAI `tools`
  (function calling) to the underlying LLM. When an n8n AI Agent sends a
  request with `tools` definitions, the API server silently drops them.
  The LLM never sees the tool definitions → 0 tool calls → the agent
  responds as if it has no tools. Execution traces show
  `"ai.agent.tool_calls.requested": 0` even when MCP tools are wired.

  **This affects ALL models** through the Hermes API server — GLM-5.2,
  gpt-oss-20b, deepseek-v4-flash, minimax-m3 all return plain text
  responses with `"finish_reason": "stop"` instead of `"tool_calls"`.

  **Fix — use LiteLLM directly (bypass Hermes API server):**
  Point the OpenAI Chat Model's `baseURL` to `http://127.0.0.1:4000/v1`
  (LiteLLM, port 4000) instead of `http://localhost:9119/v1` (Hermes API
  server). LiteLLM correctly forwards `tools` to the LLM. Models return
  `"finish_reason": "tool_calls"` with proper function call arguments.

  Create a separate OpenAI credential with the LiteLLM API key:
  ```bash
  source /opt/data/.env
  API_KEY=$(cat /opt/data/.n8n_api_key)
  curl -s -X POST http://localhost:5678/api/v1/credentials \
    -H "X-N8N-API-KEY: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"LiteLLM Direct\",\"type\":\"openAiApi\",\"data\":{\"apiKey\":\"$OLLAMA_API_KEY\"}}"
  ```

  Then update the model node:
  ```javascript
  // baseURL: http://127.0.0.1:4000/v1 (NOT localhost:9119)
  // credentials: { openAiApi: { id: '<litellm_credId>', name: 'LiteLLM Direct' } }
  ```

  **When to use which backend:**
  - **Hermes API server (`:9119`)**: Chat-only workflows (no tools needed).
    Gives full Hermes system prompt, memory, personality.
  - **LiteLLM direct (`:4000`)**: Tool-calling workflows (MCP tools, HTTP
    Request tools, function calling). No Hermes system prompt overhead
    (~29K tokens saved), tools work correctly.

  **Trade-off**: LiteLLM direct bypasses Hermes' system prompt, memory,
  and personality. The n8n-side system prompt must compensate. But tool
  calling works, which is the whole point of an AI Agent with tools.

  **Verification**: Test tool calling before deploying:
  ```bash
  curl -s -X POST http://127.0.0.1:4000/v1/chat/completions \
    -H "Authorization: Bearer $OLLAMA_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"glm-5.2","messages":[{"role":"user","content":"What is 2+2?"}], "tools":[{"type":"function","function":{"name":"calc","description":"Calculate","parameters":{"type":"object","properties":{"expr":{"type":"string"}},"required":["expr"]}}}],"tool_choice":"auto"}'
  # Should return "finish_reason": "tool_calls" with tool_calls array
  ```

## Making the Chat Public

To expose the n8n chat to anyone with the URL (no n8n login required):

1. Set Chat Trigger `public: true`
2. Set `authentication: 'none'` (removes n8n user auth requirement)
3. Set `mode: 'webhook'` (embedded chat widget accessible via URL)
4. Publish the workflow

The public URL format is:
```
https://n8n.jefe.ovh/webhook/<webhookId>/chat
```

The `webhookId` is in the Chat Trigger node's `webhookId` field (visible
in `get_workflow_details` response). Anyone with this URL can chat with
the agent — no n8n account needed.

## Model Selection

The Hermes API server proxies to LiteLLM (`localhost:4000`) which routes
to Ollama Cloud. Available models can be listed:

```bash
source /opt/data/.env
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer $OLLAMA_API_KEY"
```

Known models (as of 2026-07-25):

| Model | Best for | Notes |
|-------|----------|-------|
| `glm-5.2` | Chat, complex reasoning, tool use | General purpose, default |
| `gpt-oss-20b` | Classification, triage, simple tasks | 20B params, lightweight |
| `deepseek-v4-flash` | Long context (1M tokens) | Fast, large context |
| `minimax-m3` | Alternative general purpose | |
| `gemma4-vision` | Vision/multimodal | Image analysis |
| `local-aux` | Auxiliary tasks | Compression, vision fallback |

**For email triage / classification workflows:** Use `gpt-oss-20b` —
sufficient intelligence for JSON classification, lower resource usage
than `glm-5.2`. Switch via:

```javascript
{ type: 'updateNodeParameters', nodeName: 'model node name',
  parameters: { model: { __rl: true, mode: 'id', value: 'gpt-oss-20b' } } }
```

**For chat workflows:** Keep `glm-5.2` — better at conversation, tool
use, and complex reasoning.

## Adding MCP Tools to the AI Agent (MCP Client Tool)

To give the n8n AI Agent access to n8n's own MCP tools (search_workflows,
create_workflow, publish_workflow, execute_workflow, etc.), add an
`mcpClientTool` subnode to the Agent.

### Architecture

```
Chat Trigger → AI Agent ──┬── OpenAI Chat Model (Hermes API)
                           ├── Simple Memory
                           └── MCP Client Tool (n8n MCP server)
```

### MCP Client Tool node

```javascript
// The MCP n8n server endpoint is in config.yaml: mcp_servers.n8n-mcp.url
// It uses HTTP Streamable transport (NOT SSE), with Bearer token auth
// Token: MCP_N8N_MCP_API_KEY in /opt/data/.env
const mcpN8nTools = tool({
  type: '@n8n/n8n-nodes-langchain.mcpClientTool',
  version: 1.4,
  config: {
    name: 'MCP n8n Tools',
    parameters: {
      endpointUrl: 'https://n8n.jefe.ovh/mcp-server/http',
      serverTransport: 'httpStreamable',  // NOT 'sse' — the server uses streamable HTTP
      authentication: 'bearerAuth',
      include: 'all',  // expose all 33 n8n MCP tools
      options: { timeout: 60000 },
    },
    credentials: { httpBearerAuth: { id: '<credId>', name: 'MCP n8n' } },
  },
});
```

**⚠️ CRITICAL — Finding the correct MCP endpoint:**

The MCP server URL is NOT guessable. Always check `config.yaml`:
```bash
grep -A2 'n8n-mcp' /opt/data/config.yaml
# mcp_servers:
#   n8n-mcp:
#     url: https://n8n.jefe.ovh/mcp-server/http
```

The endpoint uses **HTTP Streamable** transport (`httpStreamable`), not SSE.
Setting `serverTransport: 'sse'` to a streamable HTTP endpoint returns HTML
instead of SSE data — the MCP client gets `ECONNREFUSED` or HTML parse errors.

**⚠️ CRITICAL — `localhost` causes IPv6 ECONNREFUSED in n8n:**

n8n's Node.js runtime resolves `localhost` to IPv6 `::1` by default. If the
target service only listens on IPv4, the connection fails with:
```
SSE error: TypeError: fetch failed: connect ECONNREFUSED ::1:3001
```

**Always use `127.0.0.1` instead of `localhost`** for n8n node endpoints, or
use the full domain name (e.g. `https://n8n.jefe.ovh/...`) which resolves
correctly via DNS.

### Bearer credential creation

```bash
MCP_TOKEN=$(grep MCP_N8N_MCP_API_KEY /opt/data/.env | cut -d= -f2)
curl -s -X POST http://localhost:5678/api/v1/credentials \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"MCP n8n\",\"type\":\"httpBearerAuth\",\"data\":{\"token\":\"$MCP_TOKEN\"}}"
```

### Wiring via update_workflow

The MCP Client Tool connects to the Agent via `ai_tool` connection type
(same as other tool subnodes). Add the node first, then connect:

```javascript
// 1. Add the MCP Client Tool node
{ type: 'addNode', node: { name: 'MCP n8n Tools', type: '@n8n/n8n-nodes-langchain.mcpClientTool', ... } }

// 2. Connect it to the Agent as ai_tool
{ type: 'addConnection', source: 'MCP n8n Tools', target: 'Hermes Agent', connectionType: 'ai_tool' }

// 3. Update Agent: increase maxIterations (tools need iteration budget)
{ type: 'updateNodeParameters', nodeName: 'Hermes Agent',
  parameters: { options: { maxIterations: 10, ... } } }
```

### Key points

- **MCP server endpoint**: Find it in `config.yaml` under
  `mcp_servers.n8n-mcp.url`. It's `https://n8n.jefe.ovh/mcp-server/http`
  with `httpStreamable` transport — NOT `localhost:3001/sse` (that was a
  wrong guess that caused ECONNREFUSED IPv6 errors).
- **`localhost` → IPv6 `::1` ECONNREFUSED**: n8n's Node.js resolves
  `localhost` to `::1`. If the service listens on IPv4 only, use
  `127.0.0.1` or the full domain name.
- **`serverTransport` must match the server**: `httpStreamable` for
  streamable HTTP endpoints, `sse` for SSE endpoints. Mismatching causes
  HTML responses or connection failures.
- **`maxIterations`**: Increase from 5 to 10 when adding MCP tools — the
  agent needs iterations to call tools and process results
- **`include: 'all'`** exposes all 33 n8n MCP tools. Use `include:
  'selected'` with `includeTools: ['search_workflows', ...]` to restrict.
- **Credential assignment**: Unlike `httpRequestTool`, the
  `mcpClientTool` node CAN have credentials assigned via API using
  `setNodeCredential` with `credentialKey: 'httpBearerAuth'`.
- **System prompt**: Update to mention the available MCP tools so the
  agent knows it can manage workflows
- **Editor lock**: `update_workflow` fails with "Cannot modify workflow
  while it is being edited by a user in the editor" when the workflow is
  open in the n8n UI. Either ask the user to close the tab, or use the
  REST API `PUT /api/v1/workflows/{id}` directly with the corrected
  node parameters (see SKILL.md PUT field restrictions section).