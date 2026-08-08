# Multi-Trigger + Merge Crash Loop

Case study: RSS Curation par Hermes (JAWwQaCUx1mN0IA7) — 68 consecutive errors, 0% success.

## Architecture Bug

The workflow had 3 independent RSS Feed Read **Trigger** nodes:
- `Trigger LoKan` (rssFeedReadTrigger) → Tag LoKan → Merge input 0
- `Trigger Korben` (rssFeedReadTrigger) → Tag Korben → Merge input 1
- `Trigger HN` (rssFeedReadTrigger) → Tag HN → Translate HN → Rebuild HN → Merge input 2

The Merge node (`n8n-nodes-base.merge`, version 3.2) had `numberInputs: 3`.

**Problem**: Each RSS trigger fires independently when its feed updates. When one fires, the Merge receives data on only 1 of 3 inputs. With `executionOrder: v1`, n8n cannot wait for the other triggers — the Merge either hangs or crashes. Result: every execution fails in <100ms.

## Fix Applied

Replaced 3 trigger nodes with 1 Schedule Trigger + 3 non-trigger RSS Feed Read nodes:

```
Schedule Trigger (every 30min)
├── RSS Read LoKan (n8n-nodes-base.rssFeedRead) → Tag LoKan → Merge[0]
├── RSS Read Korben (n8n-nodes-base.rssFeedRead) → Tag Korben → Merge[1]
└── RSS Read HN (n8n-nodes-base.rssFeedRead) → Tag HN → Rebuild HN → Merge[2]
```

All 3 feeds are fetched in the same execution → Merge receives all 3 inputs simultaneously.

### update_workflow operations (16 total)

```json
[
  // Remove old connections from triggers
  {"type":"removeConnection","source":"Trigger LoKan","target":"Tag LoKan"},
  {"type":"removeConnection","source":"Trigger Korben","target":"Tag Korben"},
  {"type":"removeConnection","source":"Trigger HN","target":"Tag HN"},
  // Remove old trigger nodes
  {"type":"removeNode","nodeName":"Trigger LoKan"},
  {"type":"removeNode","nodeName":"Trigger Korben"},
  {"type":"removeNode","nodeName":"Trigger HN"},
  // Add Schedule Trigger
  {"type":"addNode","node":{"name":"Schedule Trigger","type":"n8n-nodes-base.scheduleTrigger","typeVersion":1,"parameters":{"rule":{"interval":[{"field":"minutes","minutesInterval":30}]}},"position":[0,272]}},
  // Add 3 RSS Feed Read (non-trigger)
  {"type":"addNode","node":{"name":"RSS Read LoKan","type":"n8n-nodes-base.rssFeedRead","typeVersion":1,"parameters":{"url":"https://lokan.fr/feed/"},"position":[384,272]}},
  {"type":"addNode","node":{"name":"RSS Read Korben","type":"n8n-nodes-base.rssFeedRead","typeVersion":1,"parameters":{"url":"https://korben.info/feed"},"position":[384,464]}},
  {"type":"addNode","node":{"name":"RSS Read HN","type":"n8n-nodes-base.rssFeedRead","typeVersion":1,"parameters":{"url":"https://news.ycombinator.com/rss"},"position":[160,80]}},
  // Connect Schedule → RSS Reads
  {"type":"addConnection","source":"Schedule Trigger","target":"RSS Read LoKan"},
  {"type":"addConnection","source":"Schedule Trigger","target":"RSS Read Korben"},
  {"type":"addConnection","source":"Schedule Trigger","target":"RSS Read HN"},
  // Connect RSS Reads → existing pipeline
  {"type":"addConnection","source":"RSS Read LoKan","target":"Tag LoKan"},
  {"type":"addConnection","source":"RSS Read Korben","target":"Tag Korben"},
  {"type":"addConnection","source":"RSS Read HN","target":"Tag HN"}
]
```

## Secondary Issue: LibreTranslate API Key

After fixing the Merge, the workflow crashed at `Translate HN` with:
```
400 — "Please contact the server operator to get an API key"
```

LibreTranslate (translate.jefe.ovh) now requires an API key. The n8n credential `LibreTranslate API` (httpQueryAuth, ID `7M024UDixjBFYYsA`) was missing the key.

**Fix**: Disabled Translate HN, reconnected Tag HN → Rebuild HN directly, updated Rebuild HN to use original `$json.title` instead of `$json.translatedText`. Hermes handles translation in its curation prompt.

```json
[
  {"type":"setNodeDisabled","nodeName":"Translate HN","disabled":true},
  {"type":"removeConnection","source":"Tag HN","target":"Translate HN"},
  {"type":"addConnection","source":"Tag HN","target":"Rebuild HN"},
  {"type":"updateNodeParameters","nodeName":"Rebuild HN","replace":true,"parameters":{"assignments":{"assignments":[
    {"id":"title-t","name":"title","type":"string","value":"={{ $json.title }}"},
    {"id":"link-hn","name":"link","type":"string","value":"={{ $json.link }}"},
    {"id":"content-hn","name":"content","type":"string","value":"={{ $json.contentSnippet || $json.content || \"\" }}"},
    {"id":"date-hn","name":"pubDate","type":"string","value":"={{ $json.pubDate || $json.isoDate || \"\" }}"},
    {"id":"src-hn","name":"source","type":"string","value":"hackernews"}
  ]}}}
]
```

## Testing Procedure

1. Temporarily set schedule to 1 min: `updateNodeParameters` with `replace: true`
2. `publish_workflow` — schedule only fires on published version
3. Wait 60-90s
4. `search_executions(workflowId)` — check for new `mode: "trigger"` executions
5. If success: restore 30 min schedule and re-publish
6. If error: `get_execution(includeData=true)` to find failing node

## Result

- 58 articles in RSS output (10 LoKan + 18 Korben + 30 HN)
- Execution time: 35-80s (includes Hermes API call)
- 100% success rate after fixes