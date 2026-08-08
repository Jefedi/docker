# Embedding Model Comparison — Multilingual FR/EN (July 2026)

## Context

The RAG pipeline initially used `all-MiniLM-L6-v2` (384-dim, English-only, self-hosted via FastEmbed).
For multilingual docs (HA docs in English, queries in French), an upgrade was needed.
The chosen architecture: route embeddings through LiteLLM (port 4000) → OpenRouter API,
so all providers converge to a single endpoint.

## Benchmark — MTEB Multilingual (higher = better)

| Model | Size | MTEB Multi | MTEB English | Dim | Context | Notes |
|-------|------|-----------|-------------|-----|---------|-------|
| **Qwen3-Embedding-8B** | 8B | **70.58** (🥇 #1) | **75.22** | 4096 (MRL) | 32K | 100+ langues, FR excellent |
| Qwen3-Embedding-0.6B | 0.6B | 64.33 | 70.70 | 1024 | 32K | Best small model |
| multilingual-e5-large-instruct | 0.6B | 63.22 | 65.53 | 1024 | 512 | FastEmbed-compatible |
| Cohere embed-v4 | - | ~61 | ~63 | ? | 128K | Good multilingual, expensive |
| Mistral Embed 2312 | - | ~61 | ~60 | 1024 | 8K | 🇪🇺 EU sovereign, 10x pricier |
| BGE-M3 | 0.6B | 59.56 | ~64 | 1024 | 8K | Dense+sparse+colbert, proven |
| OpenAI text-embedding-3-large | - | ~58.93 | ~64 | 3072 | 8K | Expensive, not best in FR |
| OpenAI text-embedding-3-small | - | ~58.93 | ~62 | 1536 | 8K | Cheap but FR mediocre |
| all-MiniLM-L6-v2 (current) | 90MB | ❌ EN only | ~62 | 384 | 256 | What we started with |

## API Pricing (per 1M tokens)

| Provider | Model | Price/M tokens |
|----------|-------|---------------|
| OpenRouter | Qwen3-Embedding-8B | **$0.01** |
| OpenRouter | BGE-M3 | $0.01 |
| OpenRouter | Qwen3-Embedding-4B | $0.02 |
| OpenRouter | OpenAI text-embedding-3-small | $0.02 |
| OpenRouter | Perplexity pplx-embed-v1-0.6b | $0.004 |
| OpenRouter | Mistral Embed 2312 | $0.10 |
| Cohere | embed-v4 | $0.12 |
| OpenRouter | Gemini Embedding 001 | $0.15 |
| OpenRouter | OpenAI text-embedding-3-large | $0.13 |
| OpenRouter | NVIDIA Nemotron 3 Embed 1B | **FREE** |

## Self-hosted options (FastEmbed / Ollama)

### FastEmbed (local ONNX, CPU)

| Model | Dim | Size | MTEB Multi | Notes |
|-------|-----|------|-----------|-------|
| all-MiniLM-L6-v2 | 384 | 90MB | ❌ EN only | Current default |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 220MB | ~56 | ~50 langues, weak |
| paraphrase-multilingual-mpnet-base-v2 | 768 | 1.0GB | ~60 | ~50 langues, OK |
| intfloat/multilingual-e5-large | 1024 | 2.24GB | **63.22** | Best available in FastEmbed |

### Ollama (local GGUF)

| Model | Size | Dim | MTEB Multi | Notes |
|-------|------|-----|-----------|-------|
| qwen3-embedding:0.6b | 639MB | 1024 | **64.33** | Excellent, small |
| bge-m3:567m | 567MB | 1024 | 59.56 | Dense+sparse+colbert |

## Decision

**Winner: Qwen3-Embedding-8B via OpenRouter ($0.01/M tokens)**

- #1 MTEB multilingual (70.58) — 11 points above BGE-M3
- Same price as BGE-M3, 10x cheaper than Mistral Embed
- 32K context (4x more than BGE-M3)
- 100+ languages, French native
- MRL support (can truncate to smaller dims if needed)
- Routed through LiteLLM for single-endpoint architecture

**Migration cost estimate:** ~2324 docs × ~1000 chars ≈ ~500K tokens ≈ **$0.005** total.

**Privacy note:** OpenRouter is US-based. For sensitive docs (Paperless, emails), a local tier
with `multilingual-e5-large` via FastEmbed or `qwen3-embedding:0.6b` via Ollama should be used.

## Sources

- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- Qwen3-Embedding HF: https://huggingface.co/Qwen/Qwen3-Embedding-8B
- OpenRouter embedding models: https://openrouter.ai/collections/embedding-models
- LiteLLM OpenRouter docs: https://docs.litellm.ai/docs/providers/openrouter
- FastEmbed supported models: https://qdrant.github.io/fastembed/examples/Supported_Models/