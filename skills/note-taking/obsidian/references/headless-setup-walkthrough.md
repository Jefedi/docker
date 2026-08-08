# Headless LiveSync setup — complete walkthrough

Covers the full flow: from Vaultwarden credentials to a running daemon with real-time sync.

## Prerequisites

- Obsidian vault directory exists (empty is fine)
- CouchDB LiveSync instance running (URL, database name, user, password)
- Vaultwarden/Bitwarden account with the E2E passphrase stored
- `bw` CLI installed and logged in
- `obsidian-livesync` CLI built from source at `/tmp/obsidian-livesync/src/apps/cli/dist/index.cjs`

## Step-by-step

### 1. Get the passphrase from Vaultwarden

```bash
bw sync
bw list items | python3 -c "
import json, sys
items = json.load(sys.stdin)
for item in items:
    print(item['name'], '->', item['id'])
"
bw get item <item-id> | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Username:', data['login']['username'])
print('Password:', data['login']['password'])
for f in data['fields']:
    print(f['name'] + ':', f['value'])
"
```

The Vaultwarden item typically has:
- **Login** → CouchDB credentials (username + password)
- **Fields** → database name, E2E passphrase

### 2. Configure `.livesync/settings.json`

If it doesn't exist, init it:
```bash
CLI="node /tmp/obsidian-livesync/src/apps/cli/dist/index.cjs"
$CLI init-settings "/path/to/vault/.livesync/settings.json"
```

Then patch the critical fields:
```json
{
  "couchDB_URI": "https://yourserver.example.com",
  "couchDB_USER": "username",
  "couchDB_PASSWORD": "password",
  "couchDB_DBNAME": "obsidianvault",
  "encrypt": true,
  "passphrase": "e2e-passphrase",
  "usePathObfuscation": true,
  "liveSync": true,
  "syncOnStart": true,
  "periodicReplication": true,
  "periodicReplicationInterval": 30
}
```

### 3. Delete stale LevelDB directories

Before first sync, remove any LevelDB files that may have been created without encryption:

```bash
rm -rf "/path/to/vault/headless-vault-livesync-v2" \
       "/path/to/vault/headless-vault-headless-app-livesync-v2"
```

### 4. (If needed) Unlock remote database

Try sync first. If it says "remote database is locked":
→ Follow `references/unlock-remote-db.md` to unlock via direct CouchDB API.

### 5. (If needed) Disable config mismatch check

If sync still fails with a configuration mismatch after setting encrypt + pathObfuscation, temporarily set:
```json
"disableCheckingConfigMismatch": true
```
This skips the interactive prompt. After successful sync, you can set it back to `false`.

### 6. Sync (pull from CouchDB to local PouchDB)

```bash
CLI="node /tmp/obsidian-livesync/src/apps/cli/dist/index.cjs"
VAULT="/path/to/vault"
node "$CLI" "$VAULT" sync
```

Expected output: "Replication result received" messages followed by "[Done] Command 'sync' completed".
Exit code 0 = success.

### 7. Mirror (PouchDB to .md files on disk)

```bash
node "$CLI" "$VAULT" mirror
```

This creates all `.md` files from the decrypted PouchDB data.

### 8. Verify

```bash
find "$VAULT" -name "*.md" | wc -l
cat "$VAULT/some-expected-note.md"
```

### 9. Start daemon (continuous sync)

```bash
node "$CLI" "$VAULT" &
```

Or via process tool in Hermes:
```
terminal(background=true, pty=true, command="node $CLI $VAULT")
```

The daemon:
- Runs initial mirror scan
- Starts continuous `_changes` feed replication (CouchDB → PouchDB)
- Watches filesystem and pushes changes back (PouchDB → CouchDB)
- Everything is bidirectional and real-time

Verify daemon is running:
```bash
ps aux | grep livesync | grep -v grep
```

## Troubleshooting notes

### Sync succeeds but mirror finds 0 files
- Check that `encrypt: true` and `passphrase` are set correctly
- Check that stale LevelDB dirs were deleted before first sync

### Daemon exits immediately
- The interactive Ink UI doesn't work in non-PTY mode. Always use `pty=true` with background.
- If running via cron or script, use `--interval N` polling mode instead of _changes feed.

### "Replication result received, but not processed automatically" spam
This is normal for CLI sync mode — it means the replication completed but the auto-processing (mirror) is a separate step. The daemon mode handles both automatically.
