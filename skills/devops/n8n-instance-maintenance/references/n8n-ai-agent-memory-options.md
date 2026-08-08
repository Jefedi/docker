# n8n AI Agent Memory Options

Comparison of memory backends for n8n AI Agent nodes, as of August 2026.

## Native Memory Nodes (appear in the "Memory" slot of AI Agent)

These nodes connect via `ai_memory` and automatically inject conversation history:

| Node | Persistence | Setup | Best for |
|---|---|---|---|
| **Simple Memory** (Window Buffer) | ❌ RAM only, lost on restart | Zero config | Quick prototyping |
| **Postgres Chat Memory** | ✅ Survives restarts | Postgres credential + table | Production, persistence |
| **Redis Chat Memory** | ✅ Survives restarts | Redis instance | High-throughput, low-latency |
| **MongoDB Chat Memory** | ✅ Survives restarts | MongoDB instance | Mongo-based stacks |
| **Xata** | ✅ External service | Xata account + API key | Xata users |

All native memory nodes work the same way: a sliding window of N recent messages. No semantic recall, no fact extraction, no summarization.

## Community Memory Nodes

### Mem0 (`@mem0/n8n-nodes-mem0`)

⚠️ **CRITICAL PITFALL**: The Mem0 community node is NOT a memory backend for the AI Agent's Memory slot. It is an **action/tool node** (`group: ['transform']`, `usableAsTool: true`, connects via `ai_tool` not `ai_memory`). It will NOT appear in the Memory dropdown — it appears in the Tools dropdown.

- Install: Settings → Community Nodes → `@mem0/n8n-nodes-mem0`
- Operations: Add, Search, Get, Get Many, Update, Delete memories
- Uses Mem0 Cloud API (not self-hosted) — requires API key from mem0.ai
- The AI agent calls it as a tool when it decides to save/retrieve memories
- Can be combined WITH a native memory node (Postgres for context window + Mem0 for long-term facts)

### Hindsight (`@vectorize-io/n8n-nodes-hindsight`)

- Self-hosted (1 Docker container, embedded Postgres, MIT license)
- 91.4% on LongMemEval benchmark
- Not yet tested on this instance

### Zep — DEPRECATED

- n8n removed the native Zep memory node
- Zep CE (Community Edition) is deprecated
- SDK incompatible with self-hosted version
- Even HTTP Request workaround fails (connection errors)
- **Do not recommend Zep** — abandoned for n8n

## Recommendation for Jefe's setup

- **Postgres Chat Memory** for conversation context (litellm-db already available, DB `n8n_memory` created, connected via shared-db Docker network)
- **Mem0 as tool** for long-term fact extraction (optional, requires Mem0 Cloud API key)
- Session key should be based on user identity (`firstName-chatId` for Telegram), NOT on message content (each message = new session = no memory)

## Docker network connectivity

n8n container networks: `n8n_n8n-net`, `shared-db`, `shared-translate`
litellm-db container network: `litellm_default`

To connect n8n → litellm-db Postgres:
```bash
docker network connect shared-db litellm-db
# Verify from n8n container:
docker exec n8n-n8n-1 sh -c 'echo | nc -z litellm-db 5432 && echo OPEN'
```

litellm-db credentials: user `litellm`, db `litellm`, password in container env `POSTGRES_PASSWORD`.
Dedicated DB for n8n memory: `n8n_memory` (created via `CREATE DATABASE n8n_memory`).
pgvector extension NOT available on litellm-db (postgres:16-alpine without vector package).