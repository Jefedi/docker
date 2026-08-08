# Spotify Backup / Sync Pattern

Scheduled workflow that fetches a user's Spotify data and stores it in n8n Data Tables.

## Available Spotify Operations

| Resource | Operation | Returns (key fields) |
|---|---|---|
| `playlist` | `getUserPlaylists` | `id`, `name`, `description`, `owner.display_name`, `tracks.total`, `snapshot_id` |
| `playlist` | `getTracks` | `track.id`, `track.name`, `track.artists[].name`, `track.album.name`, `added_at` |
| `library` | `getLikedTracks` | Same shape as `getTracks` |
| `myData` | `getFollowingArtists` | `id`, `name`, `genres[]`, `popularity`, `followers.total` |

All support `returnAll: true` for unpaginated fetch.

## Credential

Requires **Spotify OAuth2 API** credential. Must be created interactively in the n8n UI — OAuth redirect flow cannot be automated. Workflow activation fails without it.

## Loop Gotcha: Playlist ID Propagation

When looping over playlists to fetch tracks:
1. SplitInBatches outputs each playlist (has `id`, `name`, etc.)
2. A **Set node** adds `playlist_id = {{ $json.id }}` to the item
3. The **Spotify** `getTracks` node uses `{{ $json.playlist_id }}` as its `id` param
4. After the Spotify node, the response **overwrites** the input — `playlist_id` is lost
5. **Fix**: In the downstream Code node, reference the upstream Set node:
   ```javascript
   const playlistId = $('Set Playlist ID').first().json.playlist_id || '';
   // Now use playlistId when building output items
   ```

## Code Transforms

### Playlist row
```javascript
{ playlist_id: item.json.id, name: item.json.name,
  owner: item.json.owner?.display_name || '',
  tracks_count: item.json.tracks?.total || 0 }
```

### Track row (with playlist_id from upstream)
```javascript
const playlistId = $('Set Playlist ID').first().json.playlist_id || '';
return items.map(item => ({
  json: {
    playlist_id: playlistId,
    track_id: item.json.track?.id || '',
    track_name: item.json.track?.name || '',
    artists: (item.json.track?.artists || []).map(a => a.name).join(', '),
    album: item.json.track?.album?.name || '',
    duration_ms: item.json.track?.duration_ms || 0 }
}));
```

### Artist row
```javascript
{ artist_id: item.json.id, name: item.json.name,
  genres: (item.json.genres || []).join(', '),
  popularity: item.json.popularity || 0,
  followers: item.json.followers?.total || 0 }
```
