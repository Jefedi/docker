# Telegram Typing Indicator for n8n AI Agent

## Problem

The n8n AI Agent node can take 10-60 seconds to respond (especially with tools like Camoufox or Mem0). During this time, the Telegram bot shows no activity — the user doesn't know if the bot is working or frozen.

Telegram's `sendChatAction: typing` indicator only lasts 5 seconds. For longer processing, you need to loop it.

## Limitation

n8n does NOT run branches in parallel within a single workflow. If you connect Telegram Trigger to both the AI Agent and a typing loop, the AI Agent branch runs first (blocking), then the typing loop runs after — defeating the purpose.

## Solution: Subworkflow Pattern (VERIFIED by community + implemented 2026-08-02)

Split into TWO workflows:

### Main Workflow (Typing Loop)
```
Telegram Trigger
├── Execute Sub-workflow (AI Agent workflow) [toggle OFF "wait for completion"]
└── Loop:
    ├── Telegram: sendChatAction typing
    ├── Wait 4 seconds
    ├── If: check if subworkflow completed (via static data / DB / file)
    │   ├── No → loop back
    │   └── Yes → send final response
```

### Sub Workflow (AI Agent)
```
Execute Workflow Trigger (inputSource: passthrough)
→ HTTP Request (self-memory from Mem0)
→ AI Agent (Hermes + tools + memory)
→ Save output to static data / DB / file
→ Return output
```

### Implementation details (VERIFIED 2026-08-02)

1. **Subworkflow creation**: Create a new workflow named "AI Perso - Agent". Add an "Execute Workflow Trigger" node (type `n8n-nodes-base.executeWorkflowTrigger`, typeVersion 1.2, `inputSource: "passthrough"`). Enable `availableInMCP` in workflow settings so the MCP API can manage it.

2. **Moving nodes to subworkflow**: Use `update_workflow` MCP with `addNode` operations for each node (Hermes, OpenAI Chat Model, Postgres Chat Memory, Mem0 Search, Mem0 Add, Confirm Update HITL, Browse Web, Read Page, HTTP Request). Then `addConnection` for each edge. The MCP auto-assigns credentials — verify they match (it may assign wrong credentials like "openwebui - ollama" instead of "ollama Cloud"). Fix with `setNodeCredential` operations.

3. **Subworkflow input data**: The Execute Workflow Trigger passes data through. When the main workflow calls the subworkflow, it can pass `chatId`, `message`, and `sessionId` as JSON. In the subworkflow, reference these as `{{ $json.chatId }}`, `{{ $json.message }}`, etc.

4. **Postgres Chat Memory in subworkflow**: The `sessionKey` must reference the input from the main workflow, NOT `$('Telegram Trigger')` (that node doesn't exist in the subworkflow). Use `={{ $json.chatId }}` or `={{ $json.sessionId }}`.

5. **Hermes prompt in subworkflow**: The prompt text must reference `{{ $json.message }}` (from the subworkflow trigger input), NOT `$('Telegram Trigger').item.json.message.text`.

6. **HITL chatId in subworkflow**: The `chatId` must be `={{ $json.chatId }}` (from the subworkflow input), NOT `$('Telegram Trigger').item.json.message.chat.id`.

### Key Configuration

1. **Execute Sub-workflow node**: Set `Mode: "Each"` and toggle OFF "Wait for subworkflow completion". This makes the main workflow continue immediately (to start the typing loop) while the agent runs in parallel.

2. **Typing loop**: Use `Telegram` node with `resource: "message"`, `operation: "sendChatAction"`, `actionType: "typing"`. Add a `Wait` node (4 seconds), then an `If` node checking completion.

3. **Completion check**: The subworkflow writes its result to n8n static data (`$getWorkflowStaticData('global')`) or a file or DB. The main workflow's `If` node polls this.

### sendChatAction configuration

```
Telegram node:
  resource: "message"
  operation: "sendChatAction"
  chatId: ={{ $('Telegram Trigger').item.json.message.chat.id }}
  actionType: "typing"
```

## Slash commands (conversation management)

The main workflow can also route slash commands before calling the subworkflow:

```
Telegram Trigger
├── If: message starts with "/"
│   ├── /new → generate new sessionKey (timestamp-based)
│   ├── /compact → fetch Postgres history → LLM summarize → replace history
│   ├── /search <term> → SQL ILIKE search in n8n_chat_histories
│   ├── /history → SELECT DISTINCT sessionKey from n8n_chat_histories
│   └── /reset → DELETE from n8n_chat_histories WHERE sessionKey = ...
└── Else → Execute Subworkflow (AI Agent) + typing loop
```

These commands manage the Postgres Chat Memory table (`n8n_chat_histories`) directly via SQL nodes.

### Session key design for slash commands

- Default: `chatId` (e.g., `7509874421`) — one conversation per Telegram chat
- `/new`: generates `chatId-timestamp` (e.g., `7509874421-1722612345`) — starts fresh conversation
- Store current sessionKey in n8n static data: `$getWorkflowStaticData('global').currentSession = "7509874421-1722612345"`
- All subsequent messages use this sessionKey until `/new` is called again

## Limitations

- **Token streaming** (like ChatGPT typing word-by-word) is NOT possible with the n8n AI Agent node. It processes the full response before returning.
- The typing indicator is the best visual feedback available.
- **Tool usage notifications** ("🔧 Using Browse Web...") are not natively supported. Would require custom tool wrappers that send Telegram messages before executing.

## Alternative: Simple sendChatAction before agent

For a simpler but less effective approach, add a single `sendChatAction` node between Telegram Trigger and the AI Agent:

```
Telegram Trigger → sendChatAction (typing) → HTTP Request (self-memory) → AI Agent → Send message
```

This shows typing for 5 seconds only, but it's trivial to set up and gives immediate feedback that the message was received.