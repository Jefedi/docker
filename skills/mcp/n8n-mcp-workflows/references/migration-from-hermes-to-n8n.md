# Migration: Hermes-Native MCPs → n8n Central MCP Hub

## Status: COMPLETED (2026-07-25)

All 22 Hermes-local MCP servers have been migrated to n8n. Hermes now has
a single MCP entry (`n8n-mcp`) that connects to the n8n MCP server, which
exposes 24 MCP workflows + 33 management tools.

## Inventory (final state)

### 24 MCP workflows in n8n (all active, all `availableInMCP: true`)

| MCP | n8n SSE Path | Auth | Workflow ID |
|-----|-------------|------|-------------|
| bazarr | `/mcp/bazarr/sse` | none | PAKX65tGYBtsAZGh |
| crosswatch | `/mcp/crosswatch/sse` | none | DIaSPqpmLTTuG4RD |
| dockhand | `/mcp/dockhand/sse` | none | 1e5xYNsxxfBS4IyE |
| ha-mcp | `/mcp/ha-mcp/sse` | none | MIvbiq8FcRDTcfWV |
| libretranslate | `/mcp/libretranslate/sse` | none | dHbZWnhWR7AtdVBv |
| metube | `/mcp/metube/sse` | none | TaAemgb62qRjG1aH |
| myanimelist | `/mcp/myanimelist/sse` | none | yTqEvTpamb9IL4Dl |
| portainer | `/mcp/portainer/sse` | none | dokgKkdPpQONJfST |
| profilarr | `/mcp/profilarr/sse` | none | jtp0JO4f2SwQj8HM |
| prowlarr | `/mcp/prowlarr/sse` | none | cPyb5X41Oe5FW5EA |
| searxng | `/mcp/searxng/sse` | none | ZLLJLImTkQ8dC6mc |
| cineverse | `/mcp/cineverse/sse` | bearerAuth | UsEeOOm5oBSDS3bI |
| discord | `/mcp/discord/sse` | none | zbmRHgwpDoLXnNzp |
| github | `/mcp/github/sse` | none | k9d7hUyyElZKxz12 |
| jellyfin | `/mcp/jellyfin/sse` | bearerAuth | 23YoSYBH7ayPKMMV |
| pangolin | `/mcp/pangolin/sse` | bearerAuth | 6HGntC63ycMMcAQo |
| paperless | `/mcp/paperless/sse` | none | D66eN3COcL2XQHL6 |
| paymenter | `/mcp/paymenter/sse` | bearerAuth | 1NHfpf86Vl8Yxg9q |
| pterodactyl | `/mcp/pterodactyl/sse` | bearerAuth | 1d85yXx8waAHe1gD |
| radarr | `/mcp/radarr/sse` | bearerAuth | XYvDGZoVLucDwHMp |
| seerr | `/mcp/seerr/sse` | bearerAuth | Lb9wwYA4C7YAYYAM |
| sonarr | `/mcp/sonarr/sse` | bearerAuth | ZioimVQbTbBD891Y |
| uptimekuma | `/mcp/uptimekuma/sse` | bearerAuth | y8DywTpX2WrGMZZk |
| qbittorrent | `/mcp/qbittorrent/sse` | bearerAuth | UMCiYYHUuLOxWwVU |

### Hermes config (final state)

Only one MCP server entry remains:

```yaml
mcp_servers:
  n8n-mcp:
    connect_timeout: 30
    enabled: true
    headers:
      Authorization: Bearer <token>  # stored in /opt/data/.env as MCP_N8N_MCP_API_KEY
    timeout: 180
    url: https://n8n.jefe.ovh/mcp-server/http
```

Original Python MCP scripts are preserved in `/opt/data/mcp/` but no longer used.

## Migration Procedure (what was actually done)

### Step 1: Audit existing n8n MCP workflows

Before creating anything, list all existing MCP workflows in n8n:

```bash
N8N_KEY=$(cat /opt/data/.n8n_api_key)
curl -s "http://localhost:5678/api/v1/workflows?limit=100" \
  -H "X-N8N-API-KEY: $N8N_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for wf in data.get('data', []):
    name = wf.get('name','')
    nodes = wf.get('nodes', [])
    has_mcp = any('mcpTrigger' in n.get('type','') for n in nodes)
    if has_mcp or name.startswith('MCP'):
        print(f'{wf[\"id\"]:25s} | {\"ON\" if wf.get(\"active\") else \"OFF\"} | {name}')
"
```

**Key learning:** Most MCPs already existed in n8n. Only 3 were missing
(Discord, MyAnimeList, UptimeKuma) and they turned out to already exist too
under slightly different names. Always audit first.

### Step 2: Clean up duplicates

If duplicate MCP workflows exist (same SSE path, one active + one inactive),
delete the inactive ones via the REST API:

```bash
curl -s -X DELETE "http://localhost:5678/api/v1/workflows/<id>" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

### Step 3: Remove all Hermes-local MCP servers

Use `hermes mcp remove` for each one. The command asks for confirmation
interactively — pipe `Y` if scripting:

```bash
/opt/hermes/bin/hermes mcp remove <name>   # interactive Y/n
```

Or in a loop:

```bash
for srv in bazarr cineverse crosswatch discord dockhand ... ; do
  /opt/hermes/bin/hermes mcp remove "$srv"
done
```

### Step 4: Re-add n8n-mcp with correct token

The MCP token gets truncated by Hermes secret redaction (`eyJhbG...6Jgs`).
Use `hermes mcp add --auth header` which saves the token to `/opt/data/.env`
as `MCP_N8N_MCP_API_KEY`, bypassing the redaction:

```bash
# Interactive: pipe Y, token, and y to the three prompts
printf "Y\n<full_mcp_token>\ny\n" | /opt/hermes/bin/hermes mcp add n8n-mcp \
  --url "https://n8n.jefe.ovh/mcp-server/http" \
  --auth header \
  --connect-timeout 30
```

The three prompts are:
1. "Does this server require authentication? [Y/n]" → Y
2. "API key / Bearer token:" → <full token>
3. "Save config anyway? [y/N]" → y (only if connection test fails, which it
   may due to streaming protocol quirks — the config still works)

### Step 5: Fix bearerAuth on SSE endpoints

10 MCP workflows had `authentication: "bearerAuth"` on their MCP trigger nodes,
causing 403 on their SSE endpoints. Since n8n is behind Pangolin (proxy auth),
bearerAuth is unnecessary. Fix by setting `authentication: "none"` via PUT:

```bash
# For each workflow with bearerAuth:
curl -s "http://localhost:5678/api/v1/workflows/$ID" \
  -H "X-N8N-API-KEY: $N8N_KEY" > /tmp/wf.json

python3 -c "
import json
with open('/tmp/wf.json') as f:
    wf = json.load(f)
for n in wf['nodes']:
    if 'mcpTrigger' in n.get('type',''):
        n['parameters']['authentication'] = 'none'
        if 'credentials' in n:
            del n['credentials']
    n.pop('webhookId', None)
wf['settings'] = {'executionOrder': 'v1', 'availableInMCP': True}
for field in ['id','versionId','createdAt','updatedAt','active','activeVersionId',
              'triggerCount','shared','tags','sourceWorkflowId','parentFolder',
              'activeVersion','versionCounter','isArchived','pinData','staticData',
              'meta','nodeGroups']:
    wf.pop(field, None)
with open('/tmp/wf_update.json', 'w') as f:
    json.dump(wf, f)
"

curl -s -X PUT "http://localhost:5678/api/v1/workflows/$ID" \
  -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" \
  -d @/tmp/wf_update.json

# MUST toggle to refresh webhook
curl -s -X POST "http://localhost:5678/api/v1/workflows/$ID/deactivate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
curl -s -X POST "http://localhost:5678/api/v1/workflows/$ID/activate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

### Step 6: Test all SSE endpoints

```bash
for name in bazarr crosswatch dockhand ... qbittorrent; do
  echo -n "$name: "
  timeout 5 curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:5678/mcp/$name/sse" --max-time 3
  echo
done
```

All should return 200. If 500, check execution errors via
`GET /api/v1/executions?workflowId=<id>&limit=3` — common cause is
`$fromAI` description strings with nested quotes causing parse errors.

### Step 7: Verify Hermes config

```bash
/opt/hermes/bin/hermes mcp list
# Should show: n8n-mcp | https://n8n.jefe.ovh/mcp-... | all | ✓ enabled
```

New session required for tools to load.

## Checking MCP workflow auth types

To see which auth type each MCP workflow uses:

```bash
N8N_KEY=$(cat /opt/data/.n8n_api_key)
for ID in <workflow_id1> <workflow_id2> ...; do
  curl -s "http://localhost:5678/api/v1/workflows/$ID" \
    -H "X-N8N-API-KEY: $N8N_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for n in data.get('nodes', []):
    if 'mcpTrigger' in n.get('type',''):
        p = n['parameters']
        print(f'{p.get(\"path\",\"\"):20s} | auth={p.get(\"authentication\",\"none\"):12s} | {data[\"name\"]}')
"
done
```

All 24 workflows now use `authentication: "none"` (bearerAuth removed 2026-07-25
since n8n is behind Pangolin proxy).

## Key files

- `/opt/data/.n8n_api_key` — n8n REST API key (`X-N8N-API-KEY`)
- `/opt/data/.env` — MCP token (`MCP_N8N_MCP_API_KEY`), set by `hermes mcp add`
- `/opt/data/mcp/` — original Python MCP scripts (preserved but unused)