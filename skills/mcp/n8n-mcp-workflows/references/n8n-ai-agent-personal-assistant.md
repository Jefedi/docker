# n8n AI Agent — Personal Assistant Pattern

Building a Hermes-like personal AI assistant entirely in n8n, with
persistent memory, personalized system prompt, and Telegram trigger.

## Architecture

```
Telegram Trigger → AI Agent ──┬── OpenAI Chat Model (gpt-oss:120b or LiteLLM)
                               ├── Postgres Chat Memory (persistent)
                               ├── Get News (RSS Feed Tool)
                               ├── Get Weather (HTTP Request Tool)
                               └── Telegram HITL Tool
                  ↓
            Send a Text Message (Telegram reply)
```

## System Prompt Personalization

The default n8n AI Agent template ships with a generic "n8n Demo AI Agent"
system prompt. For a real personal assistant, replace it with structured
sections using XML-style tags:

```
<role>Identity and personality</role>
<user_profile>Who the user is, activities, preferences</user_profile>
<infra_context>Available services, MCP tools, network details</infra_context>
<key_memories>Durable facts and quirks (Spotify workaround, qBittorrent rules, etc.)</key_memories>
<instructions>
  <goal>What the agent does</goal>
  <rules>Numbered behavioral rules</rules>
  <current_datetime>{{ $now }}</current_datetime>
  <output_format>Response formatting</output_format>
</instructions>
```

The system message supports `{{ $now }}` for dynamic date/time injection.

### Updating via MCP

```javascript
mcp_n8n_mcp_update_workflow({
  workflowId: "<id>",
  operations: [{
    type: "updateNodeParameters",
    nodeName: "AI Agent node name",
    replace: false,
    parameters: {
      options: {
        systemMessage: "=<role>...</role>\n<user_profile>...</user_profile>..."
      }
    }
  }]
})
```

The `=` prefix tells n8n to evaluate the string as an expression (needed
for `{{ $now }}` to work). Without it, the template literal is treated as
plain text.

## Postgres Chat Memory (Persistent)

### Why Postgres over Window Buffer

| Feature | Window Buffer | Postgres Chat Memory |
|---------|--------------|---------------------|
| Survives n8n restart | ❌ | ✅ |
| Cross-session persistence | ❌ | ✅ |
| Session ID segmentation | Limited | Full (customKey) |
| Setup complexity | None | Low (need Postgres) |

### Setup Steps

1. **Ensure Docker network connectivity**: n8n and the Postgres container
   must be on the same Docker network. Check with:
   ```bash
   docker inspect <n8n-container> | grep -A5 NetworkSettings
   docker inspect <postgres-container> | grep -A5 NetworkSettings
   ```
   If different networks, connect them:
   ```bash
   docker network connect <shared-network> <postgres-container>
   # Verify:
   docker exec <n8n-container> sh -c 'echo | nc -z <pg-host> 5432 && echo OPEN'
   ```

2. **Create a dedicated database** (don't pollute existing DBs):
   ```bash
   docker exec <pg-container> psql -U <user> -d <db> -c "CREATE DATABASE n8n_memory;"
   ```

3. **Node configuration**:
   - Type: `@n8n/n8n-nodes-langchain.memoryPostgres` (v1.3)
   - Credential: existing Postgres credential (reuse if one exists —
     check via `list_credentials` for `type: "postgres"`)
   - `tableName`: `n8n_chat_memory` (auto-created on first use)
   - `sessionIdType`: `customKey`
   - `sessionKey`: `={{ $json.message.from.first_name }}-{{ $json.message.chat.id }}`
   - `contextWindowLength`: 30

### Session Key Design — CRITICAL

The session key determines conversation continuity:

✅ **Good**: `={{ $json.message.from.first_name }}-{{ $json.message.chat.id }}`
   — Same session across all messages from the same Telegram chat

❌ **Bad**: `={{ $json.message.from.first_name }}-{{ $json.message.chat.id }}-{{ $json.message.text }}`
   — Includes message text → new session per message → NO memory between
   messages. The user's initial setup had this; it was corrected.

### Memory Node Type Replacement

`renameNode` only changes the display name — it does NOT change the node
type. A `memoryBufferWindow` renamed to "Chat Memory (Postgres)" is still
a Window Buffer in memory.

To replace the memory type:
1. `removeNode` the old memory node
2. `addNode` with `type: "@n8n/n8n-nodes-langchain.memoryPostgres"`
3. `addConnection` with `connectionType: "ai_memory"`, `source: "<memory node>"`, `target: "<agent node>"`

All three operations can be batched in a single `update_workflow` call.

## Telegram Integration

### Trigger → Agent → Reply Pattern

```
Telegram Trigger (updates: ["message"])
  → AI Agent (promptType: "define", text: "={{ $json.message.text }}")
  → Send a Text Message (chatId: "={{ $('Telegram Trigger').item.json.message.chat.id }}", text: "={{ $json.output }}")
```

The Agent outputs `{ output: "response text" }` which feeds into the
Telegram node's `text` field.

### Telegram HITL Tool

Add a `telegramHitlTool` (v1.2) connected to the Agent via `ai_tool`
to enable the agent to send proactive Telegram messages (e.g. asking
follow-up questions via tool calls rather than just the final response).

## Docker Network Bridging

When n8n needs to reach a service (Postgres, Redis, etc.) running in
another Docker container, they must share a Docker network.

**Diagnostic**: 
```bash
# Check networks
docker inspect n8n-n8n-1 --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
docker inspect litellm-db --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
```

**Fix**: Connect one container to the other's network:
```bash
docker network connect shared-db litellm-db
# Verify from n8n:
docker exec n8n-n8n-1 sh -c 'echo | nc -z litellm-db 5432 && echo "OPEN"'
```

Note: `nc` (netcat) is available in the n8n container. `apt-get` is NOT
(no package manager in the alpine-based image). Use `nc -z` for port
checks, not `psql` or other tools requiring installation.

## Editor Lock — Concurrent Modification

`update_workflow` fails with:
```
Cannot modify workflow while it is being edited by a user in the editor.
```

when the workflow is open in the n8n UI. This is per-workflow — other
workflows can still be modified.

**Workarounds**:
1. Ask the user to close the workflow tab in n8n
2. Wait and retry (the lock releases when the tab is closed or the
   session times out)
3. Use REST API `PUT /api/v1/workflows/{id}` directly (bypasses the
   editor lock, but requires stripping metadata fields — see the
   SKILL.md "PUT /api/v1/workflows/{id}" section)

**The user may be actively building in the editor** — they renamed nodes,
added Telegram trigger, added Telegram HITL tool, changed the agent node
name from "Your First AI Agent" to "Hermes", etc. Always `get_workflow_details`
before attempting updates to see the current state (node names, types,
connections may have changed).

## Model Selection

For the personal assistant workflow, `gpt-oss:120b` was chosen (available
via OpenRouter). Alternatives:

- **LiteLLM direct (`:4000`)**: Use for tool-calling workflows. Bypasses
  Hermes system prompt overhead. Tools work correctly.
- **Hermes API (`:9119`)**: Chat-only (no tools). Full Hermes personality
  but strips `tools` from payload.
- **OpenRouter**: External routing, supports `gpt-oss:120b` and many others.

See `references/hermes-api-as-llm-backend.md` for the detailed comparison.