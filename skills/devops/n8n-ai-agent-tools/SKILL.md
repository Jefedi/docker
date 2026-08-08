---
name: n8n-ai-agent-tools
title: n8n AI Agent Custom Tools Integration
description: Add custom HTTP tools to n8n AI Agents.
tags: [n8n, ai-agent, mem0, tools, langchain, docker-network]
---

# n8n AI Agent Custom Tools Integration

Add custom HTTP-based tools to n8n AI Agent workflows. Use when integrating Mem0, internal APIs, or any HTTP service as an AI Agent tool.

## When to Use
- Adding Mem0 (long-term memory) to an AI Agent
- Adding any HTTP API as a callable tool for the AI Agent
- Debugging "tool input did not match expected schema" errors
- Configuring cross-container networking for AI Agent tools

## Node Type Selection (Critical)

### Use `n8n-nodes-base.httpRequestTool` (v4.4) — the WORKING option
- Display name: "HTTP Request Tool"
- Has `ai_tool` output → can be connected to AI Agent
- Supports `$fromAI()` in body parameters when using `specifyBody: "keypair"`
- **Works reliably** for custom HTTP API tools

### `@n8n/n8n-nodes-langchain.toolHttpRequest` (v1.1) — BROKEN on current n8n
- Shows "Install this node to use it" in the n8n editor
- Not shipped in the current n8n Docker image
- Do NOT use this type

### `@n8n/n8n-nodes-langchain.toolHttpRequest` (v1.6) — BROKEN
- Sends malformed schema to the LLM: "Received tool input did not match expected schema"
- Avoid

### `n8n-nodes-base.httpRequest` (standard) — CANNOT be used as ai_tool
- Does not produce `ai_tool` output
- n8n MCP update_workflow will reject the connection with error:
  "its node type does not produce an 'ai_tool' output"

## Body Parameter Binding with $fromAI

### Use `specifyBody: "keypair"` (WORKS)
Set body parameters as key-value pairs:
```json
{
  "specifyBody": "keypair",
  "bodyParameters": {
    "parameters": [
      {"name": "query", "value": "={{ $fromAI('query', 'Natural language search query', 'string') }}"},
      {"name": "user_id", "value": "jefe"},
      {"name": "limit", "value": "10"}
    ]
  }
}
```
**All values must be strings** — numbers cause validation errors ("Expected string, but got number").

### `specifyBody: "json"` with `jsonBody` — DOES NOT WORK
`$fromAI()` does not resolve inside `jsonBody` expressions when using `httpRequestTool` v4.4.
The tool receives empty/blank values, causing API errors like "Invalid query: cannot be empty".

## Auth Header Configuration

### X-API-Key (custom header) — use headerParameters
For services like Mem0 that expect `X-API-Key`:
```json
{
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {"name": "X-API-Key", "value": "m0sk_..."},
      {"name": "Content-Type", "value": "application/json"}
    ]
  }
}
```

### DO NOT use `authentication: "genericCredentialType"` with httpHeaderAuth for AI tools
The credential-based auth may inject `Authorization: Bearer` instead of the custom header,
causing auth rejection. Always use explicit `headerParameters` for AI tool nodes.

### Mem0 Auth Quirk: Bearer vs X-API-Key
Mem0 rejects `Authorization: Bearer <api_key>` — it treats Bearer as JWT validation.
Use `X-API-Key: <api_key>` header instead. The native n8n Mem0 node (`@mem0/n8n-nodes-mem0.mem0Tool`)
sends `Authorization: Bearer` and is INCOMPATIBLE with self-hosted Mem0.
Credential "test connection" in n8n will fail ("Couldn't connect") even with correct URL and key.

## Cross-Container Networking

### Add external networks to compose files
For n8n to reach Mem0's container, add the Mem0 network to n8n's compose.yaml:
```yaml
services:
  n8n:
    networks:
      - n8n-net
      - shared-translate
      - shared-db
      - mem0-dev_mem0_network    # ← add
networks:
  mem0-dev_mem0_network:
    external: true               # ← declare as external
```
This makes the connection persistent across restarts (vs manual `docker network connect`).

### URL uses Docker service name, not localhost
Inside n8n container, `localhost` refers to the n8n container itself.
Use the Docker service name: `http://mem0:8000` (not `http://localhost:8888`).

## Postgres Chat Memory for AI Agent

### Shared Postgres instance
The AI Agent's Postgres Chat Memory (session memory) can share the Mem0 Postgres:
1. Create dedicated DB: `docker exec <postgres> psql -U postgres -c "CREATE DATABASE n8n_chat_memory;"`
2. n8n credential: host = Docker container name (e.g. `mem0-dev-postgres-1`), port = 5432
3. n8n must be on the same Docker network as Postgres

### Session ID
Use `={{ $json.message.chat.id }}` for Telegram-based sessions (stable per chat).
Do NOT include message text in the session key (creates a new session per message = no memory).

## Workflow Structure

```
Telegram Trigger → Hermes (AI Agent) → Send a text message
                         ↑ ai_languageModel
              OpenAI Chat Model
                         ↑ ai_memory
              Postgres Chat Memory
                         ↑ ai_tool          ↑ ai_tool        ↑ ai_tool
                    Mem0 Search         Mem0 Add          Get News (RSS)
```

## HITL (Human-in-the-Loop) Telegram Tool for AI Agents

The `n8n-nodes-base.telegramHitlTool` (v1.2) can be used as an `ai_tool` to let the AI Agent ask for human confirmation before executing dangerous operations (e.g., updating self-memory, deleting data).

### Required configuration
```
resource: "message"
operation: "sendAndWait"          # camelCase, NOT "send_and_wait"
chatId: "={{ $('Telegram Trigger').item.json.message.chat.id }}"
message: "Static text here"      # MUST be static, $fromAI does NOT work here
responseType: "approval"
chatApproval: true               # ✅/❌ buttons in Telegram chat
chatApprovalOptions:
  approverIds: "7509874421"       # Hardcoded user ID, NOT an expression
  postDecisionBehavior: "removeButtons"
approvalOptions:
  values:
    approvalType: "double"        # "double" for ✅/❌, "single" for approve-only
    approveLabel: "Oui, retiens ça"
    disapproveLabel: "Non"
options:
  appendAttribution: false
```

### Sub-tool pattern
Connect the dangerous tool (e.g., Mem0 Add with `user_id: "hermes_self"`) as `ai_tool` to the HITL, NOT to the AI Agent directly:
```
AI Agent → ai_tool → HITL (Confirm Update) → ai_tool → Mem0 Add
```
The HITL intercepts, asks for approval via Telegram, and only executes the sub-tool if approved.

### Pitfalls
- **`$fromAI` in `message` field fails**: Causes "Received tool input did not match expected schema → hitlParameters.message". Use a static message string.
- **`approvalType: "single"` only shows approve button**: Use `"double"` for ✅/❌.
- **`approverIds` must be hardcoded string**: Expressions may not resolve in HITL context.
- **HITL requires Telegram credential**: Attach `telegramApi` credential or the node can't send messages.

## Pitfalls

- **"Cannot modify workflow while being edited"** — Close the n8n editor tab before calling `update_workflow` via MCP
- **Publish after update** — Always call `publish_workflow` after `update_workflow`, otherwise changes are draft-only
- **`$fromAI` in jsonBody** — Does not work with `httpRequestTool` v4.4. Use `specifyBody: "keypair"` with `bodyParameters`
- **Number values in bodyParameters** — Must be strings. `"value": 10` → validation error. Use `"value": "10"`
- **Native Mem0 node** — Sends `Authorization: Bearer` which Mem0 rejects. Use `httpRequestTool` with `X-API-Key` header instead
- **Endpoint paths** — Mem0 search endpoint is `/search`, NOT `/memories/search`. Check `/openapi.json` for the full list
- **--force-recreate for .env** — `docker compose down && up -d` does NOT reload env_file. Use `--force-recreate`
- **Date & Time node** — Adding a Date & Time node between Trigger and Agent breaks `$json.message.text` resolution (Agent receives Date & Time output instead of Telegram message)
- **Session ID with message text** — Including `$json.message.text` in Session ID creates a new session per message, defeating the purpose of chat memory

## References
- `references/mem0-selfhost.md` — Full Mem0 deployment guide: Docker compose modifications, .env variables, admin account creation, API endpoints, LiteLLM integration pitfalls