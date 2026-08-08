# Guard Chunk Injection & RAG Testing Methodology

## The hallucination problem

When a user asks a question where the correct answer involves safety-critical
knowledge that scores below the main search threshold, the LLM will "complete"
with generic knowledge from its training data — producing plausible but wrong
answers.

### Concrete example (HA RAG)

**Question:** "Quelle est la syntaxe Jinja2 pour `states.sensor.xxx.last_changed` ?"

**Retrieved context:** 5 chunks about `last_changed`, `time_since`, templating basics (all correct, scores 0.5-0.69).

**Missing from context:** The guard pattern (`has_value()` vs `is defined`).

**LLM output:** Suggested `{% if states.sensor.xxx is defined %}` as a guard — **technically wrong** because `states.sensor.xxx` raises `UndefinedError` at evaluation time, before `is defined` runs.

**Root cause:** The guard-rail page (`/docs/templating/errors/`, score 0.508) was indexed in Qdrant but didn't surface in the top-5 results for this specific query. The LLM filled the gap with Jinja2 generic knowledge.

## Solution: Guard chunk injection

### Step 1: Ingest guard-rail chunks with a dedicated category

```bash
curl -X POST http://localhost:5678/webhook/rag-ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Template Jinja2 - Bonnes pratiques",
    "content": "PROBLEME: states.sensor.xxx leve UndefinedError avant is defined.\nSOLUTION: has_value() retourne false si absent/unavailable/unknown.\nstates() retourne \"unknown\" sans erreur.\nis_state() compare sans erreur.",
    "source": "manual-guard-rail",
    "category": "templates-guard"
  }'
```

### Step 2: Sequential guard search in n8n workflow

**NOT** an async `fetch()` in a Code node (silently fails). A dedicated
HTTP Request node in the sequential pipeline:

```
Embed Query → Search Qdrant (threshold 0.3) → Search Guard (threshold 0.0, filter category=templates-guard) → Merge Context → LLM → Respond
```

Qdrant filter for guard search:
```json
{
  "vector": "<embedding>",
  "limit": 2,
  "with_payload": true,
  "score_threshold": 0.0,
  "filter": {
    "must": [
      {"key": "category", "match": {"value": "templates-guard"}}
    ]
  }
}
```

### Step 3: Merge Context tags guard chunks

The Code node prepends `[BONNES PRATIQUES]` to guard chunk content, distinguishing
it from regular search results.

### Step 4: System prompt enforces inclusion

```
5. Si le contexte mentionne des bonnes pratiques (sections [BONNES PRATIQUES]),
   inclus-les OBLIGATOIREMENT dans ta reponse.
```

Temperature: 0.1 (not 0.3).

## Testing methodology

### Rule 1: Verify execution data, not just the answer

After a RAG query, check the n8n execution to confirm:
- How many chunks were retrieved (`context_count`)
- Whether guard chunks were injected (`guard_count > 0`)
- Whether the tag `BONNES PRATIQUES` is in the actual context sent to the LLM
- What the LLM received (not what it output)

```python
# Check execution data
run_data = exec_data["data"]["resultData"]["runData"]
search_results = run_data["Search Qdrant"][0]["data"]["main"][0][0]["json"]["result"]
guard_results = run_data["Search Guard"][0]["data"]["main"][0][0]["json"]["result"]
merge_output = run_data["Merge Context"][0]["data"]["main"][0][0]["json"]

assert merge_output["guard_count"] > 0, "Guard chunk not injected!"
assert "BONNES PRATIQUES" in merge_output["context"], "Guard tag missing!"
```

### Rule 2: Don't lower the global threshold

If a chunk scores below 0.3, do NOT lower the main search threshold to make it
pass. This injects noise into ALL queries. Use category-filtered guard injection
instead (threshold 0.0 + `filter.must`).

### Rule 3: Test for carry-over false positives

The LLM can reproduce correct-sounding text from conversation context, not from
the RAG. To verify the answer comes from retrieval:
- Check the execution data (does the context contain the information?)
- If context_count is 0 but the answer is correct → it's carry-over, not RAG

### Rule 4: Test with semantically distant questions

A question like "comment vérifier qu'un capteur a une valeur valide" scores 0.28
for the guard chunk — below 0.3. This is the exact scenario guard injection is
designed for. Test it explicitly.