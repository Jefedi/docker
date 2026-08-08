# RAG Workflows in n8n

Pattern for building Retrieval-Augmented Generation (RAG) systems in n8n,
adapted to this homelab's infrastructure.

## Infrastructure Requirements

Before building RAG workflows, these services must be running (on AX42
or whichever Docker host):

### Qdrant (vector store)
```bash
docker run -d --name qdrant --restart unless-stopped \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```
Dashboard: `http://<host>:6333/dashboard`

### Ollama (local embeddings — souverain)
```bash
docker run -d --name ollama --restart unless-stopped \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest
```
Pull embedding model:
```bash
docker exec -it ollama ollama pull nomic-embed-text
```
Alternative models: `mxbai-embed-large` (1024 dims), `nomic-embed-text` (768 dims).

**⚠️ LiteLLM (port 4000) does NOT expose embedding models** — only chat
models. The Ollama API key (`OLLAMA_API_KEY`) is restricted to chat models
(glm-5.2, minimax-m3, gpt-oss-20b, deepseek-v4-flash, gemma4-vision,
local-aux). Embeddings must go through a local Ollama instance or a
dedicated embeddings provider (OpenAI, Cohere, Jina).

## Architecture: 3-Workflow Pattern

Inspired by Thomas Janssen's community templates (workflow #5148 local RAG
with Ollama+Qdrant, #5403 RAG as MCP Server, #5398 RAG MCP + Search MCP).

### Workflow 1 — Ingestion (scheduled)

```
Schedule Trigger (weekly/daily)
  → Execute Command: git clone --depth 1 <docs repo>
  → Read Files (glob: source/_docs/**/*.md, source/_integrations/**/*.md)
  → Recursive Character Text Splitter (1000 chars, 200 overlap)
  → Embeddings Ollama (nomic-embed-text, http://<host>:11434)
  → Qdrant Vector Store (insert mode, collection: <name>)
```

Key nodes:
- `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` — recommended for most use cases
- `@n8n/n8n-nodes-langchain.embeddingsOllama` — subnode of Qdrant Vector Store
- `@n8n/n8n-nodes-langchain.vectorStoreQdrant` (mode: `insert`)

### Workflow 2 — Chat with RAG

```
Chat Trigger
  → AI Agent
    ├── OpenAI Chat Model (LiteLLM 127.0.0.1:4000, glm-5.2)
    ├── Qdrant Vector Store (retrieve-as-tool mode)
    │     └── Embeddings Ollama (same model as ingestion)
    └── Window Buffer Memory
```

The `retrieve-as-tool` mode is the canonical RAG pattern — the vector
store becomes a tool the agent calls automatically. The agent decides
when to search the docs vs answer from its own knowledge.

Alternative: `retrieve` mode exposes the store as a subnode for
`subnodes.vectorStore` (non-tool, always-on retrieval).

### Workflow 3 — MCP Server (optional, for Hermes integration)

```
MCP Trigger (path: <name>-rag)
  → Qdrant Vector Store (load mode)
  → Return chunks as tool response
```

This lets Hermes Agent call `search_<name>_docs` as a tool, integrating
RAG into any conversation without a separate chat interface.

## LLM Backend Selection

| Backend | URL | Use case |
|---------|-----|----------|
| Hermes API server | `http://127.0.0.1:9119/v1` | Chat-only (no tools). Full Hermes system prompt. |
| LiteLLM direct | `http://127.0.0.1:4000/v1` | Tool-calling workflows. Tools work correctly. |

For RAG chat workflows: **LiteLLM direct is preferred** because the
`retrieve-as-tool` mode requires tool calling, which the Hermes API
server silently strips (see hermes-api-as-llm-backend.md pitfall).

Set `responsesApiEnabled: false` on the OpenAI Chat Model node to use
`/v1/chat/completions` instead of `/v1/responses`.

## n8n Node Reference

### Qdrant Vector Store modes
- `insert` — upsert documents into the store (ingestion workflow)
- `load` — one-shot similarity search on the main flow
- `retrieve-as-tool` — canonical RAG mode, plug into AI Agent's `subnodes.tools`
- `retrieve` — exposes store as subnode for another node's `subnodes.vectorStore`
- `update` — update a single document by ID

### Embeddings nodes available in n8n
- `@n8n/n8n-nodes-langchain.embeddingsOllama` — local, free, souverain
- `@n8n/n8n-nodes-langchain.embeddingsOpenAi` — OpenAI (US, paid)
- `@n8n/n8n-nodes-langchain.embeddingsCohere` — Cohere (paid)
- `@n8n/n8n-nodes-langchain.embeddingsAwsBedrock` — AWS (paid)
- `@n8n/n8n-nodes-langchain.embeddingsLemonade` — AMD ROCm local

### Text Splitters
- `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` — recommended for most use cases
- `@n8n/n8n-nodes-langchain.textSplitterCharacterTextSplitter` — simpler, less smart splitting
- `@n8n/n8n-nodes-langchain.textSplitterTokenSplitter` — split by token count

## Document Sources for RAG

### Home Assistant documentation
- Repo: `home-assistant/home-assistant.io` (branch: `current`)
- Doc files: `source/_docs/**/*.md`
- Integration docs: `source/_integrations/**/*.md`
- ~3000+ markdown files, ~50K chunks after splitting
- Ingestion time: 30-60 min depending on embeddings speed
- Storage: ~500MB-1GB in Qdrant

### Other potential sources
- `home-assistant/core` — developer docs in `docs/`
- Local HA config (automations.yaml, scripts.yaml) — user's own setup
- Paperless documents (via API or filesystem)

## Pitfalls

- **Embeddings model mismatch**: The ingestion and query workflows MUST
  use the same embeddings model. If you ingest with `nomic-embed-text`
  (768 dims) and query with `mxbai-embed-large` (1024 dims), similarity
  search returns garbage. Create separate Qdrant collections per model.

- **Qdrant collection dimensions**: The collection must be created with
  the correct vector size matching the embeddings model. Qdrant auto-creates
  collections on first insert, but the dimension must match.

- **`localhost` in n8n → IPv6**: Use `127.0.0.1` or the Docker host IP
  (e.g. `http://192.168.x.x:11434`) for Ollama/Qdrant URLs inside n8n
  nodes. `localhost` resolves to `::1` in Node.js and fails if the
  service listens on IPv4 only.

- **n8n Docker network**: If n8n runs in Docker, it can't reach
  `127.0.0.1` on the host. Use `host.docker.internal` (Docker Desktop)
  or the host's LAN IP, or put n8n and Qdrant/Ollama on the same Docker
  network.

- **LiteLLM has no embeddings**: The `OLLAMA_API_KEY` only allows chat
  models. Don't try to use LiteLLM for embeddings — it will return
  `key_model_access_denied`. Use a local Ollama instance instead.

- **Hermes API server strips tools**: For `retrieve-as-tool` mode (which
  requires tool calling), use LiteLLM direct (`:4000`), not Hermes API
  server (`:9119`). See `references/hermes-api-as-llm-backend.md`.

- **Large repo ingestion**: `git clone --depth 1` is essential for large
  repos like home-assistant.io (40K+ commits). Full clone would take
  forever and waste disk. The `--depth 1` flag gets only the latest state.

## Community Template References

- **#5148** — Local RAG with Ollama + Qdrant (Thomas Janssen) — 100% local, PDF upload
- **#5403** — RAG as MCP Server (Thomas Janssen) — exposes RAG as MCP tool
- **#5398** — RAG MCP + Search MCP (Thomas Janssen) — dual MCP agent
- **#5010** — RAG Starter Template (n8n Team) — simple, Simple Vector Store
- **#4827** — WhatsApp RAG Bot (NovaNode) — multi-channel RAG
- **#2753** — Google Drive RAG with Gemini (Mihai Farcas) — Drive-based ingestion