# Scheduled Data Sync Patterns

Building scheduled workflows that fetch data from external services and store it in n8n Data Tables for backup, migration, or audit.

Absorbed from the `n8n-scheduled-data-sync` skill (archived). This covers the **data sync domain** of n8n MCP workflows — as opposed to the **tool-building domain** (catch-all MCP patterns) covered in the main skill.

## The Core Pattern

```
Schedule Trigger (daily at 8:00)
├── Branch A: Fetch Source A → Transform → Upsert Table A
├── Branch B: Fetch Source B → Transform → Upsert Table B
└── Branch C: (...) → Loop over items → per-item fetch → Transform → Upsert Table C
```

All branches run in **parallel** from the same schedule trigger.

See `references/parallel-schedule-branches.md` for SDK wiring details.

## Data Table Upsert

Use `operation: 'upsert'` (not `insert`) for daily sync to avoid duplicates.

### Required parameters
```javascript
matchType: 'allConditions',
filters: {
  conditions: [
    { keyName: 'playlist_id', condition: 'eq', keyValue: expr('{{ $json.playlist_id }}') }
  ]
}
```

### Compound keys (unique row = 2+ columns)
```javascript
conditions: [
  { keyName: 'playlist_id', condition: 'eq', keyValue: expr('{{ $json.playlist_id }}') },
  { keyName: 'track_id', condition: 'eq', keyValue: expr('{{ $json.track_id }}') }
]
```

### Resource mapper schema
Each column needs a schema entry. Mark matching columns with `canBeUsedToMatch: true`:
```javascript
columns: {
  mappingMode: 'defineBelow',
  value: {
    field1: expr('{{ $json.field1 }}')
  },
  schema: [
    { id: 'field1', displayName: 'field1', required: false, defaultMatch: true, display: true, type: 'string', canBeUsedToMatch: true },
    { id: 'field2', displayName: 'field2', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false }
  ]
}
```

**Pitfall:** `filters` is REQUIRED for upsert. Omitting it causes validation warnings.

## Data Table GET with Filters

```javascript
const getFiltered = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Get Filtered Rows',
    parameters: {
      resource: 'row',
      operation: 'get',
      dataTableId: { __rl: true, mode: 'name', value: 'table_name' },
      matchType: 'allConditions',
      filters: {
        conditions: [
          { keyName: 'column_name', condition: 'eq', keyValue: expr('{{ $json.value }}') }
        ]
      },
      returnAll: true
    }
  },
  output: [{ id: 'result1' }]
});
```

## HTTP Request with Predefined OAuth2 Credential

Reuse a service node's OAuth2 credential (e.g. Spotify) in HTTP Request nodes:

```javascript
const httpCall = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Custom API Call',
    parameters: {
      method: 'PUT',
      url: expr('https://api.spotify.com/v1/me/tracks?ids={{ $json.ids }}'),
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'spotifyOAuth2Api',
      options: { response: { response: { responseFormat: 'json' } } }
    }
  },
  output: [{}]
});
```

**Pitfall:** The n8n SDK cannot auto-assign credentials to HTTP Request nodes using `predefinedCredentialType`. The credential dropdown stays empty — the user must manually select it in the UI.

## Code Node Transform Patterns

### API list → table rows (Run Once For All Items)
```javascript
const items = $input.all();
return items.map(item => ({
  json: {
    id: item.json.id,
    name: item.json.name || '',
    nestedField: item.json.parent?.child || ''
  }
}));
```

### Nested API data → flat rows
```javascript
return items.map(item => ({
  json: {
    track_id: item.json.track?.id || '',
    track_name: item.json.track?.name || '',
    artists: (item.json.track?.artists || []).map(a => a.name).join(', '),
  }
}));
```

### Referencing upstream node in a loop
```javascript
const upstreamData = $('Set Playlist ID').first();
const playlistId = upstreamData.json.playlist_id || '';
```

## Service Node Setup (OAuth2)

Service nodes like Spotify require OAuth2 credentials that **must** be created interactively via the n8n UI:
- `newCredential('Spotify Account')` in the SDK declares the placeholder
- The user must create the credential in n8n before the workflow can be activated
- A single credential can be shared across multiple nodes of the same type

**Pitfall:** Workflow creation and validation succeeds. Activation fails with "Missing required credential". Tell the user upfront.

## Restore / Import Pattern (Data Tables → External API)

The inverse of sync: read from Data Tables and recreate data on the external service.

```
Manual Trigger → Get User Profile (API call for user_id)
├── Phase 1: Restore Parents + Children
│   ├── Get List from Data Table
│   ├── Loop (batchSize=1)
│   │   ├── Create on External API
│   │   ├── Get Children from Data Table (filtered by parent_id)
│   │   ├── Batch Children (Code node, N per API limit)
│   │   └── Create Batch via HTTP Request
│   └── Done
```

See `references/restore-import-pattern.md` for full SDK code and batch sizing.

## Bidirectional Sync: Deleting Orphaned Rows

A pure upsert sync only adds/updates. Over time the backup accumulates rows
for items the user has removed from the source (e.g. unliked tracks). To keep
the backup in sync, add a **delete-orphans** branch after the upsert step.

### Pattern

```
Store Liked Tracks (upsert)
  → Get All Backup Tracks (dataTable GET, returnAll: true)
  → Find Orphaned Tracks (Code node)
  → Delete Orphaned Tracks (dataTable DELETE)
```

### Code Node: Find Orphaned Tracks

```javascript
// Get all backup tracks from this node's input (from the GET node)
const backupItems = $input.all();

// Get all Spotify liked track IDs from the original fetch node
// Reference it by name — the output still has the raw API data
const likedItems = $('Get Liked Tracks').all();
const likedIds = new Set(likedItems.map(item => item.json?.track?.id || '').filter(id => id));

// Find backup tracks that are no longer liked
const orphaned = backupItems.filter(item => {
    const trackId = item.json?.track_id || '';
    return trackId && !likedIds.has(trackId);
});

if (orphaned.length === 0) return [];

return orphaned.map(item => ({
    json: {
        track_id: item.json.track_id,
        track_name: item.json.track_name || '',
        artists: item.json.artists || ''
    }
}));
```

### Data Table Delete Node

```json
{
  "operation": "deleteRows",
  "dataTableId": { "__rl": true, "mode": "name", "value": "spotify_saved_tracks" },
  "matchType": "allConditions",
  "filters": {
    "conditions": [
      { "keyName": "track_id", "keyValue": "={{ $json.track_id }}" }
    ]
  },
  "options": {}
}
```

⚠️ **The operation is `deleteRows`, NOT `delete`** — the SDK validator rejects
`"delete"` with `INVALID_PARAMETER: expected one of: "deleteRows"`. This was
confirmed in a 2026-07-28 session. Older versions of this doc used `"delete"`
which is wrong.

The delete node processes each item from the Code node output, deleting the
matching row. If the Code node returns 0 items (no orphans), the delete node
does nothing — no error.

### Key Points

- **The n8n REST API does NOT support DELETE on data table rows** — it returns
  HTTP 405 "DELETE method not allowed". Deletion can only be done via the Data
  Table node within a workflow, NOT via `curl -X DELETE` to the API.
- **The Data Table node's `deleteRows` operation** (NOT `delete` — the validator rejects `"delete"`, use `"deleteRows"`) uses the same `filters.conditions`
  pattern as upsert — match rows by column value and delete all matches.
- **Reference the original fetch node by name** (`$('Get Liked Tracks').all()`)
  to get the live source data for comparison — don't rely on data flowing through
  the upsert node (it transforms the data shape).
- **Return empty array when no orphans** — the Code node returning `[]` is safe;
  downstream nodes simply receive no items.

## Updating a Workflow via the n8n REST API

When modifying workflows programmatically (not via MCP tools):

### PUT /api/v1/workflows/{id} Payload

The PUT endpoint accepts ONLY these top-level fields:
```json
{
  "name": "workflow name",
  "nodes": [...],
  "connections": {...},
  "settings": {"executionOrder": "v1"}
}
```

**Rejected fields:**
- `active` — read-only (returns 400 "active is read-only")
- `id`, `createdAt`, `updatedAt`, `versionId` — "must NOT have additional properties"
- `settings` with extra keys like `availableInMCP`, `binaryMode` — only
  `executionOrder` and a few others are accepted. Strip unknown keys.

### Adding Nodes Programmatically

When adding nodes to an existing workflow:

1. GET the current workflow JSON
2. Append new nodes to the `nodes` array (include `position` offsets from
   existing nodes)
3. Add entries to the `connections` dict — each connection is:
   ```json
   "Source Node Name": {
     "main": [[{"node": "Target Node Name", "type": "main", "index": 0}]]
   }
   ```
4. PUT the updated workflow back with only the allowed fields

**Connection direction**: `main` connections flow source → target. The source
key is the node name, the target is inside the array.

## File Reference

Absorbed from the `n8n-scheduled-data-sync` skill (archived). For scheduled sync/backup workflow patterns with Data Tables, see:
- `references/spotify-backup-pattern.md`
- `references/data-table-upsert.md`
- `references/restore-import-pattern.md`
