# Camoufox Browser API Reference

Camoufox is an anti-detect browser built for AI agents, self-hosted in Docker.
Deployed alongside Hermes in `/srv/docker/hermes/docker-compose.yaml`.

## Container

```yaml
camofox:
  image: ghcr.io/jo-inc/camofox-browser:latest
  container_name: camofox-browser
  ports:
    - "127.0.0.1:9377:9377"
  environment:
    - CAMOFOX_PORT=9377
  volumes:
    - /srv/docker/hermes/camofox:/home/node/.camofox
```

## Network

Camoufox is on `hermes_default` network. To connect n8n:

```bash
# In n8n's compose.yaml, add to n8n service networks:
#   - hermes_default
# And in top-level networks:
#   hermes_default:
#     external: true

# Python yaml.safe_dump alternative to sed (sed corrupts YAML):
cd /srv/docker/n8n && python3 -c "
import yaml
with open('compose.yaml', 'r') as f:
    doc = yaml.safe_load(f)
nets = doc['services']['n8n']['networks']
if 'hermes_default' not in nets:
    nets.append('hermes_default')
if 'hermes_default' not in doc['networks']:
    doc['networks']['hermes_default'] = {'external': True}
with open('compose.yaml', 'w') as f:
    yaml.dump(doc, f, default_flow_style=False, sort_keys=False)
print('done')
"
```

Then recreate: `docker compose -f /srv/docker/n8n/compose.yaml up -d --force-recreate`

Verify: `docker exec n8n-n8n-1 sh -c "wget -qO- http://camofox-browser:9377/health"`

## API Endpoints (VERIFIED 2026-08-02)

Base URL from n8n: `http://camofox-browser:9377`
Base URL from host: `http://localhost:9377`

### Health
```
GET /health
→ {"ok":true,"engine":"camoufox","browserConnected":false,...}
```

### Tab Management (CORRECTED — verified via curl)

```
POST /tabs/open    {"userId":"jefe","url":"https://example.com"}  → opens tab, returns tabId + title
GET  /tabs                                                  → list active tabs
POST /tabs/{tabId}/navigate  {"url":"..."}                    → navigate existing tab
GET  /tabs/{tabId}/snapshot?userId=jefe                      → get page content (NOT POST /snapshot!)
POST /tabs/{tabId}/screenshot                               → screenshot
POST /tabs/{tabId}/click      {"selector":"..."}              → click element
POST /tabs/{tabId}/type       {"selector":"...","text":"..."} → type text
POST /tabs/{tabId}/extract    {"prompt":"..."}                → AI extraction
POST /tabs/{tabId}/evaluate   {"expression":"..."}            → JS evaluation
DELETE /tabs/{tabId}                                         → close tab
```

⚠️ **`/tabs/open` REQUIRES `url` in the body** — not just `userId`. Without `url`, returns `{"error":"url is required"}`.

⚠️ **`/snapshot` is a GET request on `/tabs/{tabId}/snapshot?userId=jefe`** — NOT a POST to `/snapshot`. POST `/snapshot` returns `Cannot POST /snapshot`. The snapshot endpoint is path-based on the tab, not a standalone endpoint.

⚠️ **`/navigate` (standalone) requires an existing tab** — returns `{"error":"Tab not found"}` if no tab is open. Use `/tabs/{tabId}/navigate` or `/tabs/open` with `url` instead.

### Simple endpoints (no tabId needed)
```
POST /navigate  {"url":"...","userId":"jefe"}  → requires existing tab
POST /act       {"userId":"jefe","action":"..."} → perform action
```

### Session management
```
POST /sessions/{userId}        → create session
GET  /sessions/{userId}         → get session info
POST /sessions/{userId}/cookies → save cookies
```

### Full OpenAPI discovery
```bash
curl -s http://localhost:9377/openapi.json | python3 -c "import sys,json; [print(p) for p in json.load(sys.stdin).get('paths',{}).keys()]"
```

## n8n AI Agent Integration: TWO-TOOL PATTERN (CRITICAL)

The AI Agent needs **TWO separate HTTP Request Tool nodes** for web browsing:

### Tool 1: "Browse Web" — opens a page
```
Type: n8n-nodes-base.httpRequestTool v4.4
Method: POST
URL: http://camofox-browser:9377/tabs/open
Headers: Content-Type: application/json
Body (keypair):
  - url: ={{ $fromAI('url', 'URL to browse', 'string') }}
  - userId: jefe
Connection: ai_tool → Hermes
```

Returns: `{"ok":true,"tabId":"xxx","url":"...","title":"..."}` — the agent gets `tabId` and `title`.

### Tool 2: "Read Page" — reads the page content
```
Type: n8n-nodes-base.httpRequestTool v4.4
Method: GET
URL: ={{ 'http://camofox-browser:9377/tabs/' + $fromAI('tabId', 'The tabId from Browse Web', 'string') + '/snapshot?userId=jefe' }}
Headers: Content-Type: application/json
Connection: ai_tool → Hermes
```

Returns: `{"url":"...","snapshot":"- dialog \"...\":\n  - paragraph: ...","refsCount":58,...}` — structured text of the page content.

### Why TWO tools (CRITICAL)

With only "Browse Web", the agent gets the `tabId` and `title` but **cannot read the page content**. It will loop trying to get more info, eventually hitting "Agent stopped due to max iterations". The "Read Page" tool is essential — the agent calls Browse Web first, extracts the `tabId` from the response, then calls Read Page with that `tabId` to get the actual content.

### Workflow

1. Agent calls **Browse Web** with URL → gets `tabId` + `title`
2. Agent calls **Read Page** with `tabId` → gets full page content as structured text
3. Agent summarizes the content for the user

⚠️ Use `specifyBody: "keypair"` with `bodyParameters` (NOT `jsonBody` with `specifyBody: "json"`) — `$fromAI` only resolves correctly in keypair mode for httpRequestTool v4.4.

## Camoufox snapshot format

The snapshot returns a structured text representation of the page (not HTML):
- Elements are prefixed with `- ` (like YAML)
- Links show as `- link "text" [eN]: /url: ...`
- Headings show as `- heading "text" [level=N]`
- Buttons, textboxes, and other interactive elements are listed
- `refsCount` indicates how many interactive elements were found
- `totalChars` shows the response size

This format is ideal for LLM consumption — it's already structured text, not raw HTML that the LLM has to parse.