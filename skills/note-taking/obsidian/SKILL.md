---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault. Also covers headless LiveSync setup via CouchDB for multi-device sync.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, adding wikilinks, AND setting up headless LiveSync sync via CouchDB.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

---

# LiveSync Headless CLI Setup

Use this when the user asks to connect an Obsidian vault to an existing CouchDB LiveSync instance for multi-device sync, or when you need to sync a vault without the Obsidian desktop GUI.

## How LiveSync works (headless)

Obsidian LiveSync uses CouchDB as the sync backend. All vault content is **End-to-End Encrypted** by default (AES-256-GCM). The headless CLI syncs between a local PouchDB database (which mirrors the CouchDB) and the filesystem. The flow:

```
CouchDB (remote)  <-->  Local PouchDB (node)  <-->  Filesystem (.md files)
                     sync via CLI                   mirror by CLI
```

## Prerequisites

```bash
# Node.js v22+
node --version

# git for cloning the repo
git --version
```

## Installation

The headless CLI is part of the `vrtmrz/obsidian-livesync` source repo — NOT published as an npm package. Build from source:

```bash
git clone --recurse-submodules https://github.com/vrtmrz/obsidian-livesync.git /tmp/obsidian-livesync
cd /tmp/obsidian-livesync
npm install
cd src/apps/cli
npm install
npm run build
```

The CLI binary is at `src/apps/cli/dist/index.cjs`.

⚠️ **CRITICAL: Do NOT install Docker or a separate CouchDB just because the skill mentions a database.** The user's LiveSync instance is already running — you're connecting to it, not creating a new one. When the user says "CouchDB is already on my server", stop. Do not `docker run couchdb`. Do not `apt install couchdb`. Configure the CLI to use their existing CouchDB URL.

## Configuration

### Settings file

The vault directory stores LiveSync config at `.livesync/settings.json`. Initialize it:

```bash
CLI="node /tmp/obsidian-livesync/src/apps/cli/dist/index.cjs"
$CLI init-settings "/path/to/vault/.livesync/settings.json"
```

### Key settings fields

| Field | Description | Example |
|-------|-------------|---------|
| `couchDB_URI` | CouchDB server URL | `https://localsync.example.com` |
| `couchDB_USER` | CouchDB username | `jefe` |
| `couchDB_PASSWORD` | CouchDB password | (long token string) |
| `couchDB_DBNAME` | Database name | `obsidianvault` |
| `encrypt` | Enable E2E encryption | `true` (must match remote) |
| `passphrase` | E2E encryption passphrase | (user must provide this) |
| `liveSync` | Enable LiveSync | `true` |
| `syncOnStart` | Sync on start | `true` |
| `syncOnSave` | Sync on file change | `true` |
| `periodicReplication` | Continuous polling | `true` |
| `periodicReplicationInterval` | Poll seconds | `30` |

Edit settings via `patch` on the settings.json file.

### Remote connection string

The CLI also supports a `sls+` connection string format via `remote-add`:

```bash
$CLI "/path/to/vault" remote-add my-remote \
  "sls+https://user:password@host:port/dbname"
```

But the primary workflow uses the settings.json fields directly (couchDB_URI, couchDB_USER, couchDB_PASSWORD, couchDB_DBNAME).

## Sync commands

### One-shot sync (pull from CouchDB)

```bash
$CLI "/path/to/vault" sync
```

This runs one replication cycle. On first run, if the local encryption/passphrase doesn't match the remote, the CLI will prompt interactively. See pitfalls below.

### Mirror to filesystem

```bash
# Mirror from local PouchDB to .md files on disk
$CLI "/path/to/vault" mirror
```

### Continuous daemon

```bash
# Runs mirror scan then continuously syncs CouchDB <-> filesystem
$CLI "/path/to/vault"

# With polling instead of _changes feed
$CLI "/path/to/vault" --interval 30
```

The daemon is the default command (no subcommand needed).

**Running the daemon persistently**:
- When using Hermes terminal tool, always launch with `pty=true` and `background=true` — the CLI uses an Ink terminal UI on stdout that requires a pseudo-terminal.
- The daemon will: mirror scan, start _changes feed, watch filesystem, push local edits back to CouchDB.
- Verify it's alive: `ps aux | grep livesync | grep -v grep`.
- For script/CI contexts where PTY is not available, prefer `--interval N` polling mode instead of the default _changes feed.

**Writing notes while daemon runs**: every file write to the vault directory is auto-detected by the daemon's filesystem watcher, pushed to local PouchDB, and replicated to CouchDB within seconds. No manual sync/mirror needed.

### Other useful commands

| Command | Purpose |
|---------|---------|
| `ls [prefix]` | List DB files as `path\tsize\tmtime\trevision` |
| `cat <src>` | Read a file from local DB to stdout (decrypted) |
| `cat-rev <src> <rev>` | Read a file at a specific revision |
| `info <path>` | Show detailed file metadata (ID, revision, conflicts, chunks) |
| `push <src> <dst>` | Push a local file into the local DB |
| `pull <src> <dst>` | Extract a file from the local DB to disk |
| `remote-ls` | List stored remote configurations |
| `remote-activate <id>` | Activate a registered remote |

## Pitfalls

### Encryption mismatch on first sync

The first `sync` will fail with a configuration mismatch error like:

```
| Value name | This device | On Remote |
| End-to-End Encryption | false | true |
| Property Encryption | false | true |
```

**Fix — two settings to match**:

1. Set `"encrypt": true` in `.livesync/settings.json` for E2E encryption.
2. Set `"usePathObfuscation": true` for Property Encryption (file path obfuscation). The remote PREFERRED settings typically have this enabled.

Also ask the user for their encryption passphrase. Without the passphrase you cannot decrypt the vault content.

```json
{
  "encrypt": true,
  "usePathObfuscation": true,
  "passphrase": "user-provided-passphrase"
}
```

After all three fields match the remote, delete any existing LevelDB files (`headless-vault-*` directories in the vault root) so the CLI creates fresh PouchDB databases with the correct encryption settings. Then run `sync` again.

If the mismatch still persists (e.g. due to stale PouchDB state), set `"disableCheckingConfigMismatch": true` as a temporary bypass — the CLI will skip the interactive dialog and proceed with replication.

### CLI blocks on interactive prompts

The CLI uses an Ink/React terminal UI for interactive prompts (configuration mismatch, locked DB, etc.). Standard stdin piping (`echo y | ...` or `printf '1\n' | ...`) does NOT work — the UI reads raw keyboard events (Tab, Enter). Workarounds:

- **Config mismatch**: set `"disableCheckingConfigMismatch": true` in settings.json to skip the check entirely.
- **Locked DB**: see the separate pitfall below — modify the remote CouchDB milestone directly.

### Remote database locked

If `sync` fails with:
```
[Error] The remote database is locked and this device is not yet accepted.
[Error] Please unlock the database from the Obsidian plugin and retry.
```

The remote CouchDB has a **milestone document** (`_local/obsydian_livesync_milestone`) with `"locked": true`. The CLI has no way to unlock it interactively — it defaults to Cancel. Fix by modifying the milestone directly via curl:

```bash
# 1. Get the current milestone
MILESTONE=$(curl -s -u "user:password" \
  "https://couchdb.example.com/dbname/_local/obsydian_livesync_milestone")

# 2. Set locked: false
MODIFIED=$(echo "$MILESTONE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
d['locked'] = False
print(json.dumps(d))
")

# 3. PUT it back
curl -s -X PUT -u "user:password" \
  -H "Content-Type: application/json" \
  -d "$MODIFIED" \
  "https://couchdb.example.com/dbname/_local/obsydian_livesync_milestone"
```

After unlocking, delete any existing LevelDB directories from the vault root and retry `sync`.

### Passphrase is mandatory

Obsidian LiveSync encrypts file **paths AND content** by default. You cannot read meaningful data from CouchDB directly (the documents are opaque encrypted blobs). Only the headless CLI (with the correct passphrase) can decrypt.

### Data is stored in a local PouchDB

The vault directory contains `.livesync/` with the PouchDB data files. The `.md` files on disk are a mirror of the PouchDB — they are NOT the source of truth. Write changes will be synced back through the PouchDB → CouchDB path.

### CouchDB 401 despite correct credentials

If `curl -u "user:pass" https://couchdb-url/` returns `401 "Name or password is incorrect"`, this does NOT necessarily mean wrong credentials. Possible causes:

1. **The CouchDB user does not exist** in the database — the user was never created on this CouchDB instance. Connect to CouchDB as admin to create it.
2. **The CouchDB is not running at all** — the Pangolin resource may point to `127.0.0.1:5984` on a site, but the container may have been removed. See `references/sync-daemon-troubleshooting.md` → "CouchDB not running on the VPS" section.
3. **Wrong credentials** — verify by checking the item in Vaultwarden via `bw get item "Livesync"`.

Always check the CouchDB container presence first before assuming bad credentials.

### Do NOT install a separate CouchDB or Docker

Critical: if the user says CouchDB is already running (even if you can ping it from the VPS), do NOT install a new one. Just connect the headless CLI to their existing instance. The user's LiveSync instance is the source of truth — creating a separate CouchDB creates a complete fork that diverges.

### Passphrase via Vaultwarden / Bitwarden

The user prefers issuing a dedicated, restricted Vaultwarden account for the agent instead of sharing their master credentials. See `references/vaultwarden-credentials.md` for the full workflow:

```
npm install -g @bitwarden/cli
bw config server https://vault.example.com
export BW_PASS='master-password'
bw login user@example.com --passwordenv BW_PASS
export BW_SESSION=$(bw unlock --passwordenv BW_PASS --raw)
bw list items --session "$BW_SESSION"
```

The `bw` binary lands in the global npm prefix. On this system: `/root/.hermes/node/bin/bw` — symlink to `/usr/local/bin/bw`.

---

# Agent-to-vault sync pattern

Use this when the user asks you to expose your internal state (memory, skills, config) in the Obsidian vault, or when you want to use the vault as a shared "second brain" that both you and the user can read/write.

## Goal

- The user can browse what you know (memory, skills) from Obsidian on their devices.
- You document fixes, solutions, and discoveries directly in the vault.
- Edits the user makes propagate back to you.

## Setup

### 1. Create a folder in the vault

```
Mémoire AI/Hermes Agent/
├── 00 - Index.md           # Overview, connections, capabilities
├── 01 - Configuration technique.md
├── memories/
│   ├── MEMORY.md            # Copy of agent's persistent memory
│   └── USER.md              # Copy of user profile
├── skills/
│   └── _inventory.md        # Auto-generated skills list
└── config_snippet.txt
```

### 2. Cronjob for periodic sync

Create a script in `~/.hermes/scripts/` that copies or generates the files above, then schedule it with `cronjob(action='create')`:

```bash
# ~/.hermes/scripts/sync-to-vault.sh — example structure
VAULT="/path/to/vault"
HERMES="/root/.hermes"
OUTDIR="$VAULT/Memoire AI/Hermes Agent"

mkdir -p "$OUTDIR/memories" "$OUTDIR/skills"

# Copy memory files
[ -f "$HERMES/memories/MEMORY.md" ] && cp "$HERMES/memories/MEMORY.md" "$OUTDIR/memories/MEMORY.md"
[ -f "$HERMES/memories/USER.md" ] && cp "$HERMES/memories/USER.md" "$OUTDIR/memories/USER.md"

# Generate skills inventory
find "$HERMES/skills" -name "SKILL.md" -maxdepth 3 | sort | while read f; do
  # generate markdown list with name, category, description
done > "$OUTDIR/skills/_inventory.md"
```

Schedule every 15–30 minutes:
```bash
cronjob(action='create', name='sync-hermes-to-vault', script='sync-to-vault.sh', schedule='every 15m')
```

For cronjob setup, prefer `no_agent=True` so the script runs directly without LLM overhead, and make the script exit 0 with empty stdout on success — this keeps the sync **silent** when nothing is wrong. See the `watchdog` skill for the full silent-on-success pattern.

### Silent cron pattern

The sync script should exit silently on success. Users typically do NOT want confirmation messages for routine syncs:

```bash
# End of script — silent exit on success
exit 0
# Only output + exit non-zero on failure
```

Configure the cronjob with `no_agent=True` so empty stdout means no delivery, and non-zero exit triggers an automatic alert to the user. See `devops/watchdog` skill for the full pattern.

### 3. Log solved problems

Whenever you fix something non-trivial, create a note in the vault documenting:
- What the problem was
- What the root cause was
- How you fixed it (commands, config changes)
- Any pitfalls to avoid next time

This turns the vault into a shared operations log that both you and the user can reference.

---

---

# obsidian-sync-mcp (npm MCP Server)

Use this when the user has the `obsidian-sync-mcp` npm package installed globally instead of the CLI built from source. This package is an MCP server that also acts as a bidirectional sync daemon between the vault and CouchDB.

## When to use this vs the CLI approach

The `obsidian-sync-mcp` package (v0.5.3+) is lighter-weight than the full CLI approach:
- Installed via `npm i -g obsidian-sync-mcp` (no source build needed)
- Binary at `<npm-prefix>/bin/obsidian-sync-mcp`
- Can run in **local/filesystem mode** (direct vault access, no CouchDB) OR **remote/CouchDB mode**
- Provides both read AND write MCP tools (write tools are enabled by default)
- Watches the vault AND CouchDB bidirectionally

## Environment variables

| Variable | Required for | Description | Default |
|----------|-------------|-------------|---------|
| `VAULT_PATH` | Local mode | Path to vault directory | - |
| `VAULT_NAME` | Optional | Vault display name | - |
| `COUCHDB_URL` | Remote mode | CouchDB server URL | - |
| `COUCHDB_USER` | Remote mode | CouchDB username | - |
| `COUCHDB_PASSWORD` | Remote mode | CouchDB password (from Vaultwarden) | - |
| `COUCHDB_DATABASE` | Remote mode | Database name (e.g. `obsidianvault`) | - |
| `COUCHDB_PASSPHRASE` | Remote mode | E2E encryption passphrase (from Vaultwarden) | - |
| `PORT` | Optional | HTTP listen port | `8787` |
| `READ_ONLY` | Optional | Disable write tools | empty (writes enabled) |
| `MCP_AUTH_TOKEN` | Optional | Password-gated auth | empty (no auth) |
| `BASE_URL` | Optional | Public URL for OAuth callbacks | - |
| `DATA_DIR` | Optional | Persistence directory | - |
| `HOST` | Optional | Bind address | - |
| `LOG_LEVEL` | Optional | Debug logging | - |

## Running as sync daemon

### Local/Filesystem mode (no CouchDB)

Reads `.md` files directly from disk. Simpler but no multi-device sync:

```bash
VAULT_PATH="/path/to/vault" obsidian-sync-mcp
```

### Remote/CouchDB mode (with LiveSync)

Requires CouchDB credentials + E2E passphrase — typically retrieved from Vaultwarden:

```bash
export COUCHDB_URL="https://localsync.example.com"
export COUCHDB_USER="username"
export COUCHDB_PASSWORD="<from-vaultwarden>"
export COUCHDB_DATABASE="obsidianvault"
export COUCHDB_PASSPHRASE="<from-vaultwarden>"
export VAULT_PATH="/path/to/vault"
export VAULT_NAME="MyVault"

obsidian-sync-mcp
```

The daemon will:
1. Pull decrypted notes from CouchDB and mirror them to `.md` files on disk
2. Watch for file changes in the vault and push them to CouchDB
3. Watch the CouchDB `_changes` feed for updates from other devices

If the daemon won't start or sync stops working, see `references/sync-daemon-troubleshooting.md` for common failure modes (VPS restart killed process, Vaultwarden locked, CouchDB unreachable/CouchDB container missing, stale LevelDB, missing env vars, plugin mismatch).

### As background process in Hermes

```bash
terminal(
  background=true,
  pty=true,
  command="VAULT_PATH=/path/to/vault COUCHDB_URL=... COUCHDB_USER=... COUCHDB_PASSWORD=*** COUCHDB_DATABASE=... COUCHDB_PASSPHRASE=... obsidian-sync-mcp"
)
```

Verify it's running:
```bash
curl http://localhost:8787/health
```

## Integrating as Hermes MCP server

Register it so Hermes can use its tools directly:

```bash
hermes mcp add obsidian-vault \
  --command obsidian-sync-mcp \
  --env "VAULT_PATH=/path/to/vault" \
  --env "COUCHDB_URL=https://..." \
  --env "COUCHDB_USER=..." \
  --env "COUCHDB_PASSWORD=***" \
  --env "COUCHDB_DATABASE=..." \
  --env "COUCHDB_PASSPHRASE=..."
```

## Getting credentials from Vaultwarden

The CouchDB password and E2E passphrase are typically stored in Vaultwarden (item "Livesync"). See `references/vaultwarden-credentials.md` for the full `bw` CLI workflow.

The `.livesync/settings.json` has the CouchDB URI encrypted under `remoteConfigurations.legacy-couchdb.uri` (starts with `%$VK...`, `isEncrypted: true`). The plain-text credentials must be retrieved from Vaultwarden.

## Filesystem mode vs CouchDB mode

| Feature | Filesystem | CouchDB |
|---------|-----------|---------|
| Works without CouchDB | ✅ | ❌ |
| Multi-device sync | ❌ | ✅ |
| MCP read tools | ✅ | ✅ |
| MCP write tools | ✅ | ✅ |
| Vault watching | ✅ | ✅ |
| E2E decryption | N/A | ✅ (via passphrase) |

---

# Remotely Save Obsidian Plugin (Alternative to LiveSync)

Use this when the user asks to switch from LiveSync to Remotely Save, or to install Obsidian plugins on a headless vault.

## When to choose Remotely Save over LiveSync

| Aspect | LiveSync | Remotely Save |
|--------|----------|---------------|
| Backend | CouchDB (self-hosted) | WebDAV, S3, Dropbox, OneDrive, Google Drive, pCloud |
| Stability | Prone to sync bugs, DB lock issues | Very stable, simple sync model |
| Real-time | Near real-time (CouchDB changes feed) | Periodic sync (configurable interval) |
| Setup complexity | High (CouchDB server + CLI daemon) | Low (plugin + remote storage URL) |
| Mobile support | Excellent | Excellent |
| Encryption | Built-in E2EE (AES-256-GCM) | Optional (plugin-level) |

## Installing plugins on a headless vault

When Obsidian has never been opened on the machine, there's no `.obsidian/` directory. Create it manually:

```bash
mkdir -p "/path/to/vault/.obsidian/plugins/<plugin-id>"
```

**Files required per plugin:**

| File | Source | Description |
|------|--------|-------------|
| `main.js` | GitHub release asset | The plugin's compiled code (largest file, ~1-5 MB) |
| `manifest.json` | GitHub repo root | Plugin metadata (id, name, version, minAppVersion) |
| `styles.css` | GitHub release asset (optional) | Custom CSS styling |

**Download from GitHub releases:**
```bash
curl -sL -o "/path/to/vault/.obsidian/plugins/<plugin-id>/main.js" \
  "https://github.com/<owner>/<repo>/releases/download/<version>/main.js"

# Manifest from repo root (or release)
curl -sL -o "/path/to/vault/.obsidian/plugins/<plugin-id>/manifest.json" \
  "https://raw.githubusercontent.com/<owner>/<repo>/master/manifest.json"
```

**Enable community plugins:**
```json
// .obsidian/community-plugins.json
["remotely-save"]
```

## Remotely Save with WebDAV

### Via Pangolin private resource

If the WebDAV server is behind a Pangolin VPN (private site resource), the URL format is:
```
https://webdav.yourdomain.com
```

The corresponding Pangolin site resource:
```
mode: "http"
destination: "127.0.0.1"
destinationPort: <webdav-port>
scheme: "https"       # ← backend speaks HTTPS
ssl: true              # ← Pangolin terminates TLS
subdomain: "webdav"
```

### Plugin config (`data.json`)

Created automatically when you configure the plugin in Obsidian, stored at `.obsidian/plugins/remotely-save/data.json`:

```json
{
  "uri": "https://webdav.jefe.al",
  "auth": {
    "authMethod": "password",
    "username": "<user>",
    "password": "<password>"
  },
  "syncInterval": 5
}
```

⚠️ **Credentials are required** — WebDAV username/password must be provided by the user.

### Transitioning from LiveSync

**LiveSync and Remotely Save CAN coexist** in the same vault — they're independent plugins writing to different backends. Steps:

1. Install Remotely Save plugin (manual steps above)
2. Configure WebDAV endpoint + credentials in Remotely Save
3. Do a full sync (pull from WebDAV) to populate the vault
4. Keep LiveSync running until user confirms Remotely Save works
5. Only then disable LiveSync (remove `.livesync/` directory, disable in settings)

## Manual plugin directory structure

Final layout for a working vault with Remotely Save:
```
/path/to/vault/
├── .obsidian/
│   ├── community-plugins.json     # ["remotely-save"]
│   ├── plugins/
│   │   └── remotely-save/
│   │       ├── main.js             # 4.1 MB (compiled plugin)
│   │       ├── manifest.json       # Plugin metadata
│   │       └── styles.css          # (optional)
│   └── ... (app.json, etc.)
├── Notes.md
└── ...
```