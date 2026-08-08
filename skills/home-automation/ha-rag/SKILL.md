---
name: ha-rag
description: "Query the Home Assistant RAG knowledge base via n8n webhook."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [home-assistant, rag, documentation, knowledge-base]
---

# HA RAG — Home Assistant Knowledge Base

## When to use

Use this skill when the user asks about Home Assistant topics:
- Configuration (YAML, packages, secrets, groups)
- Automations (triggers, conditions, actions, examples)
- Scripts (service calls, variables, conditions)
- Templates (Jinja2, states, sensors)
- Integrations (MQTT, ZHA, Zigbee2MQTT, Hue, Spotify, Freebox, etc.)
- Dashboards (Lovelace cards, views, layout)
- Getting started / installation
- Energy management
- Voice / Assist

This queries a RAG knowledge base (Qdrant + FastEmbed + Hermes API) populated with
the official Home Assistant documentation. It returns context-aware answers with
source URLs.

## How it works

The RAG pipeline is:
1. **Embedding service**: FastEmbed (all-MiniLM-L6-v2, 384-dim) on port 9200
2. **Vector store**: Qdrant on port 6333, collection `ha-docs`
3. **LLM**: Hermes Agent API on port 9119 (model: hermes-agent)
4. **Orchestration**: n8n workflows

## Querying the RAG

Send a POST request to the n8n webhook:

```bash
curl -s -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query": "QUESTION HERE"}'
```

The response is JSON:
```json
{
  "query": "the question",
  "answer": "context-aware answer in French",
  "sources": [
    {"title": "page title", "score": 0.75, "source": "https://..."}
  ],
  "context_count": 5
}
```

## Ingesting new documents

### Single document
```bash
curl -s -X POST http://localhost:5678/webhook/rag-ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Document title",
    "content": "Document content text...",
    "source": "manual",
    "category": "configuration"
  }'
```

### Auto-ingest from a URL (fetches + chunks + embeds)
```bash
curl -s -X POST http://localhost:5678/webhook/rag-ha-ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.home-assistant.io/docs/...", "category": "automation"}'
```

## Architecture details

| Component | Location | Port |
|-----------|----------|------|
| FastEmbed service | Hermes container (s6 supervised, /run/service/embed-service) | 9200 |
| Qdrant | Docker container on AX42 host | 6333 |
| Hermes API | Hermes container (s6, API_SERVER) | 9119 |
| n8n workflows | n8n Docker container | 5678 |

**Network note**: n8n runs in a separate Docker container and accesses Hermes services
via the Docker bridge gateway IP `172.17.0.1` (not localhost).

### n8n workflows

- `RAG - HA Docs Ingestion` (ID: JLbUk8sEKU7rKJ1p) — webhook `/webhook/rag-ingest`
- `RAG - HA Docs Query` (ID: ps4vDz4zRHWHBVGm) — webhook `/webhook/rag-query`
- `RAG - HA Docs Auto Ingest` (ID: a4MBBPRpVnwDRUd4) — webhook `/webhook/rag-ha-ingest-url`

### Qdrant collection

- Name: `ha-docs`
- Vector size: 384
- Distance: Cosine
- ~190 docs ingested (official HA docs + manual entries)

## Workflow for the agent

1. When a user asks about Home Assistant, use the terminal tool to call the RAG query webhook
2. Parse the JSON response
3. Present the answer to the user, with sources if relevant
4. If the user wants to add documentation, use the ingest webhooks

## Pitfalls

- The embedding service on port 9200 is s6-supervised and auto-restarts on crash
- If Qdrant is unreachable, check that the Docker container is running on the host
- n8n webhooks must be activated (workflow active=true) for production URLs to work
- The Hermes API key for n8n is `hermes-ios-shortcut-a80ac18a29ed5d62` (stored in .env)
- Score threshold in query is 0.3 — lower for more results, higher for precision