# Restore / Import from Data Tables Pattern

The inverse of the sync pattern: read data from n8n internal Data Tables and recreate/resync it on the external service. Use when migrating between accounts, recovering from data loss, or seeding a fresh instance.

## Architecture

```
Manual Trigger → Get User Profile (API call for user_id)
├── Phase 1: Restore Playlists
│   ├── Get List from Data Table
│   ├── Loop (batchSize=1)
│   │   ├── Create on External API (Spotify node)
│   │   ├── Get Child Items from Data Table (filtered by parent_id)
│   │   ├── Batch Items (Code node, e.g. 100 per batch)
│   │   └── Create Batch on External API (HTTP Request node)
│   └── Done
├── Phase 2: Restore Simple Data
│   ├── Get List from Data Table
│   ├── Batch Items (Code node, e.g. 50 per batch)
│   └── Loop → API Call per batch → Done
└── Phase 3: Restore More Data (same as Phase 2)
```

## SDK Patterns

### 1. Get user profile for API calls

```javascript
const getProfile = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Get User Profile',
    parameters: {
      method: 'GET',
      url: 'https://api.spotify.com/v1/me',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'spotifyOAuth2Api',
      options: { response: { response: { responseFormat: 'json' } } }
    },
    position: [540, 300]
  },
  output: [{ id: 'user_123' }]
});
```

### 2. Read Data Table with filters (get child rows by parent_id)

```javascript
const getChildItems = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Get Child Items',
    parameters: {
      resource: 'row',
      operation: 'get',
      dataTableId: { __rl: true, mode: 'name', value: 'spotify_playlist_tracks' },
      matchType: 'allConditions',
      filters: {
        conditions: [
          { keyName: 'parent_id', condition: 'eq', keyValue: expr('{{ $json.parent_id }}') }
        ]
      },
      returnAll: true
    }
  },
  output: [{ child_id: 'abc123' }]
});
```

### 3. Batch items via Code node

Reads N items and groups them into batches that respect the API's max per-call limit:

```javascript
const batchItems = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Batch Items N',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `
const items = $input.all();
if (!items.length) return [];

const batchSize = 100; // Spotify: 100 tracks per playlist call, 50 per saved/follow call
const values = items.map(item => item.json.track_id);
const batches = [];

for (let i = 0; i < values.length; i += batchSize) {
  batches.push({
    json: {
      parent_id: upstreamField, // reference from $('Upstream Node').first().json.field
      ids: values.slice(i, i + batchSize).join(',')
    }
  });
}
return batches;`
    }
  },
  output: [{ parent_id: 'xyz', ids: 'id1,id2,id3' }]
});
```

Then feed batches through a SplitInBatches (batchSize=1) to process each batch via HTTP Request or equivalent.

### 4. HTTP Request with predefined OAuth2 credential

Reuse the same OAuth2 credential from a service node (e.g. Spotify) in HTTP Request nodes:

```javascript
const apiCall = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'API Call',
    parameters: {
      method: 'POST',
      url: expr('https://api.spotify.com/v1/playlists/{{ $json.parent_id }}/tracks'),
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'spotifyOAuth2Api',
      sendBody: true,
      specifyBody: 'json',
      jsonBody: expr('{ "uris": {{ JSON.stringify($json.uris) }} }'),
      options: { response: { response: { responseFormat: 'json' } } }
    }
  },
  output: [{ snapshot_id: 'snap123' }]
});
```

**Pitfall**: The n8n SDK creates the nodes correctly but CANNOT auto-assign credentials to HTTP Request nodes with `predefinedCredentialType`. The credential dropdown in the UI stays empty — the user must manually select the credential for each such node before activating.

### 5. Reading from Data Table with `returnAll: true`

```javascript
const readTable = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Read Data',
    parameters: {
      resource: 'row',
      operation: 'get',
      dataTableId: { __rl: true, mode: 'name', value: 'spotify_playlists' },
      returnAll: true
    }
  },
  output: [{ id: 'row1', field: 'value' }]
});
```

**Pitfall**: `returnAll: true` returns ALL rows with no limit. For very large tables, consider adding filters or limiting pages.

## Multi-Phase Execution

Since each restore phase is independent, chain from the profile-fetch node:

```javascript
export default workflow('restore-id', 'Restore from Backup')
  .add(manualTrigger)
  .to(getProfile)

  // Phase 1
  .add(getProfile)
  .to(readPlaylistTable)
  .to(enrichWithUserId)
  .to(loopPlaylists
    .onEachBatch(createPlaylist.to(getChildTracks).to(batchTracks).to(addTracks).to(nextBatch(loopPlaylists)))
    .onDone(playlistsDone)
  )

  // Phase 2
  .add(getProfile)
  .to(readSavedTracks)
  .to(batchSavedTracks)
  .to(loopSavedBatches
    .onEachBatch(saveTracksAPI.to(nextBatch(loopSavedBatches)))
    .onDone(savedDone)
  )

  // Phase 3
  .add(getProfile)
  .to(readArtists)
  .to(batchArtists)
  .to(loopArtistBatches
    .onEachBatch(followArtistsAPI.to(nextBatch(loopArtistBatches)))
    .onDone(artistsDone)
  );
```

Each `.add(getProfile)` creates an independent parallel execution path from the profile data — use this pattern when all phases need the same upstream data.

## API Rate Limits

Batch sizes per Spotify endpoint:
| Endpoint | Max per call | Method |
|---|---|---|
| Add tracks to playlist | 100 | POST /v1/playlists/{id}/tracks |
| Save tracks to library | 50 | PUT /v1/me/tracks |
| Follow artists | 50 | PUT /v1/me/following |
