# Embedding Model Comparison — Multilingual RAG (FR/EN)

Comparatif réalisé en juillet 2026 pour choisir le modèle d'embedding du RAG.
Critères: multilingual FR/EN, performance MTEB, prix, dimensions, contexte.

## Via API OpenRouter (clé déjà dans .env)

| Modèle | Prix/M tokens | Dim | Contexte | MTEB Multi | MTEB English | Notes |
|--------|--------------|-----|----------|-----------|-------------|-------|
| **Qwen3-Embedding-8B** | **$0.01** | 4096 | 32K | **70.58** (🥇 #1) | **75.22** | 100+ langues, FR excellent. Choisi. |
| BGE-M3 | $0.01 | 1024 | 8K | 59.56 | ~64 | Proven, dense+sparse+colbert |
| Qwen3-Embedding-4B | $0.02 | 2048 | 32K | ~67 | ~72 | Bon compromis |
| Perplexity pplx-embed-v1-0.6b | $0.004 | ? | 32K | ? | ? | Le moins cher, multilingue incertain |
| OpenAI text-embedding-3-small | $0.02 | 1536 | 8K | ~58.93 | ~62 | FR moyen |
| OpenAI text-embedding-3-large | $0.13 | 3072 | 8K | ~58.93 | ~64 | Cher, pas meilleur en FR |
| Mistral Embed 2312 | $0.10 | 1024 | 8K | ~61.12 | ~60 | 🇪🇺 EU souverain, mais 10x plus cher |
| Cohere embed-v4 | $0.12 | ? | 128K | ~61.12 | ~63 | Bon multilingue mais cher |
| Gemini Embedding 001 | $0.15 | ? | 20K | élevé | élevé | Cher, US |
| NVIDIA Nemotron 3 Embed 1B | **GRATUIT** | ? | ? | ? | ? | Qualité multilingue inconnue |

## Auto-hébergé (FastEmbed — service local actuel)

| Modèle | Dim | Taille | MTEB Multi | Notes |
|--------|-----|--------|-----------|-------|
| all-MiniLM-L6-v2 (actuel) | 384 | 90MB | ❌ anglais seulement | Service s6 port 9200 |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 220MB | ~56 | ~50 langues, faible |
| paraphrase-multilingual-mpnet-base-v2 | 768 | 1.0GB | ~60 | ~50 langues, correct |
| intfloat/multilingual-e5-large | 1024 | 2.24GB | **63.22** | Meilleur dispo en FastEmbed |

## Auto-hébergé via Ollama (non installé localement sur AX42)

| Modèle | Taille | Dim | MTEB Multi | Notes |
|--------|--------|-----|-----------|-------|
| qwen3-embedding:0.6b | 639MB | 1024 | **64.33** | Excellent, petit |
| bge-m3:567m | 567MB | 1024 | 59.56 | Dense+sparse+colbert |

## Décision: Qwen3-Embedding-8B via OpenRouter/LiteLLM

**Raisons**:
- #1 mondial MTEB multilingual (70.58) — 11 points au-dessus de BGE-M3
- $0.01/M tokens — même prix que BGE-M3, 10x moins cher que Mistral
- 32K tokens de contexte (4x plus que BGE-M3)
- 100+ langues, Français natif
- Clé OpenRouter déjà disponible

**Coût réel d'ingestion**: 2324 docs × ~1000 chars ≈ ~500K tokens ≈ **$0.005** pour toute la migration.
Les requêtes ensuite = quelques tokens chacune = négligeable.

**Note privacy**: les docs ingérés sont publics (HA docs, etc.). Pour des docs sensibles
(Paperless, emails), prévoir un tier auto-hébergé (e5-large ou Ollama local).

**Dimension**: 4096 par défaut. Qwen3 supporte le MRL (troncature à dimension réduite si besoin).
Qdrant gère très bien 4096-dim — plus de stockage mais négligeable.

## Benchmark MTEB Multilingual (source: Qwen3-Embedding HuggingFace)

| Model | Size | Mean (Task) | Retrieval | STS |
|-------|------|-------------|-----------|-----|
| Qwen3-Embedding-8B | 8B | **70.58** | **70.88** | **81.08** |
| Qwen3-Embedding-0.6B | 0.6B | 64.33 | 64.64 | 76.17 |
| multilingual-e5-large-instruct | 0.6B | 63.22 | 57.12 | 76.81 |
| BGE-M3 | 0.6B | 59.56 | 54.60 | 74.12 |
| Cohere-embed-multilingual-v3.0 | - | 61.12 | 59.16 | 74.80 |
| text-embedding-3-large | - | 58.93 | 59.27 | 71.68 |