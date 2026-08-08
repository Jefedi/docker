# Unlocking a locked CouchDB LiveSync database

When the CLI refuses to sync with:
```
[Error] The remote database is locked and this device is not yet accepted.
```

## Root cause

The CouchDB database has a **milestone document** at `_local/obsydian_livesync_milestone` with `"locked": true`. This happens when the Obsidian LiveSync plugin locks the remote after a rebuild was triggered on another device — it's a safety mechanism to prevent database corruption.

## Fix steps

1. **Fetch the milestone document** using the same CouchDB credentials from `.livesync/settings.json`:

```bash
MILESTONE=$(curl -s -u "user:password" \
  "https://couchdb.example.com/dbname/_local/obsydian_livesync_milestone")
```

The document has this shape:
```json
{
  "_id": "_local/obsydian_livesync_milestone",
  "_rev": "0-37",
  "type": "milestoneinfo",
  "locked": true,
  "accepted_nodes": ["node1", "node2"],
  "node_info": { ... },
  "node_chunk_info": { ... },
  "tweak_values": { ... }
}
```

2. **Set locked to false** and PUT it back:

```bash
MODIFIED=$(echo "$MILESTONE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
d['locked'] = False
print(json.dumps(d))
")

curl -s -X PUT -u "user:password" \
  -H "Content-Type: application/json" \
  -d "$MODIFIED" \
  "https://couchdb.example.com/dbname/_local/obsydian_livesync_milestone"
```

Expected response: `{"ok":true,"id":"_local/obsydian_livesync_milestone","rev":"0-38"}`

3. **Clean up stale LevelDB files** in the vault directory (they may have been created with wrong encryption settings):

```bash
rm -rf "/path/to/vault/headless-vault-livesync-v2" \
       "/path/to/vault/headless-vault-headless-app-livesync-v2"
```

4. **Retry sync + mirror**:
```bash
CLI="/path/to/obsidian-livesync/src/apps/cli/dist/index.cjs"
VAULT="/path/to/vault"
node "$CLI" "$VAULT" sync
node "$CLI" "$VAULT" mirror
```

## Notes

- The `_local/` prefix means this is a CouchDB-local document — it does NOT replicate between databases.
- Setting `"locked": false` on the milestone bypasses the safety mechanism. Only do this when you're sure the remote DB is in a consistent state (e.g. the device that triggered the lock has completed its rebuild).
- After successful sync, the CLI will add the current device's node ID to `accepted_nodes`.
