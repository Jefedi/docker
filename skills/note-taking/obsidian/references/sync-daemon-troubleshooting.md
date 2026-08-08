# Sync Daemon Troubleshooting

## Common failure modes for headless LiveSync

### No sync daemon running

Symptom: files modified in the vault do not appear on other devices (or vice versa).

Check:
```bash
ps aux | grep -E 'livesync|obsidian-sync-mcp' | grep -v grep
```

If nothing found, the daemon is down. Possible causes:
- VPS restart killed the background process
- Node.js process crashed
- The daemon was never set up to auto-start (no systemd, no cron, no Docker restart policy)

Fix: restart the daemon (see SKILL.md `obsidian-sync-mcp (npm MCP Server)` section or `LiveSync Headless CLI Setup` section depending on which approach is installed).

### Vaultwarden locked

Symptom: `bw status` shows `"status":"locked"` or `"status":"unauthenticated"`.

The `BW_SESSION` environment variable is empty/stale after a VPS restart or session expiry.

Fix: re-login and unlock:
```bash
bw login user@example.com --passwordfile /tmp/bw_pwd.txt
export BW_SESSION=$(bw unlock --passwordenv BW_PASS --raw)
```

### CouchDB unreachable

Symptom: sync daemon logs connection errors.

Check reachability:
```bash
curl -s -o /dev/null -w "%{http_code}" https://localsync.yourdomain.com/
```

- **HTTP 401** = CouchDB is up but needs auth. Retry with credentials from Vaultwarden.
- **HTTP 000 / connection refused / timeout** = CouchDB server may be down entirely.
- **401 "Name or password is incorrect"** despite correct credentials = could mean the CouchDB user does not exist in the database yet, or the server is behind a reverse proxy with additional auth.

### CouchDB not running on the VPS (Pangolin target mismatch)

Symptom: the Pangolin resource `localsync.jefe.al` points to `127.0.0.1:5984` on a site (e.g. "Hetzner"), but there is no CouchDB container or process on that machine.

Diagnostic workflow (when running on the VPS / target host):

1. **Check the Pangolin resource target** via Pangolin MCP:
   ```
   mcp_pangolin_org_by_orgId_resources(orgId="jorganisation", query="localsync")
   ```
   Look for the site name and target IP:port.

2. **Check Docker containers on the host:**
   ```bash
   docker ps | grep couch
   ```
   If no CouchDB container is listed, it's not running locally.

3. **Check all listening ports for CouchDB (5984):**
   ```bash
   ss -tlnp | grep 5984
   ```

4. **Check if the CouchDB Docker compose stack exists but is stopped:**
   ```bash
   docker ps -a | grep couch
   docker-compose ps  # look for couchdb in compose projects
   ```

5. **If the container is completely absent**, the CouchDB may be on a different host (AX42, jNas, jTower). Try:
   - Checking Dockhand MCP: `mcp_dockhand_dockhand_list_containers(environment_id=N)` for each host
   - Checking the docker-compose files on this host for references to CouchDB
   - Ask the user which host the CouchDB container runs on

**Common scenario**: The Pangolin resource `localsync.jefe.al → 127.0.0.1:5984` was created when CouchDB was running on this VPS, but the container was removed/stopped during a Docker migration or cleanup. The resource still exists but the backend is missing.

### Encrypted credentials in settings.json

The `.livesync/settings.json` stores the CouchDB URI as an encrypted blob:

```json
"remoteConfigurations": {
  "legacy-couchdb": {
    "uri": "%$VK7dOWdKsc...",
    "isEncrypted": true
  }
}
```

This blob cannot be decrypted outside of the Self-hosted LiveSync plugin/CLI — the passphrase and CouchDB credentials must be retrieved from Vaultwarden directly, not decoded from settings.json.

### LevelDB database stale

The local PouchDB data lives under `/path/to/vault/headless-vault-livesync-v2/`. Check the last log timestamp:

```bash
cat /path/to/vault/headless-vault-livesync-v2/LOG | tail -5
```

The last compaction time tells you when sync last ran. If it's days old, the daemon has been down since then.

Also check the `.livesync/` LevelDB log file timestamps:
```bash
ls -la /path/to/vault/.livesync/runtime/
```

### `obsidian-sync-mcp` — COUCHDB_PASSWORD is required

If running `obsidian-sync-mcp` without setting `COUCHDB_URL`, it expects `VAULT_PATH` for local mode. If you run it with no args, it requires either `VAULT_PATH` (local) or `COUCHDB_URL` + `COUCHDB_PASSWORD` (remote). The error `COUCHDB_PASSWORD is required in remote mode` means it detected a missing required env var.

Fix: set the correct env vars as documented in the SKILL.md `obsidian-sync-mcp` section.

### Plugin mismatch: remotely-save vs obsidian-livesync

Symptom: The `.obsidian/plugins/` directory contains `remotely-save` but NOT `obsidian-livesync`, even though the vault root has `.livesync/` settings and `headless-vault-livesync-v2/` data.

This is expected when the LiveSync sync was handled by a **headless CLI** or **obsidian-sync-mcp daemon**, not by the Obsidian plugin itself. The Obsidian desktop app on the user's other devices runs the `obsidian-livesync` plugin to sync to CouchDB, but the server-side vault relies on the headless daemon. The `remotely-save` plugin may be present but unconfigured — it's not actively used for sync in this setup.

Fix: Do NOT replace the plugin. The headless daemon (`obsidian-sync-mcp`) handles the server-side sync. If the daemon is not running, restart it.
