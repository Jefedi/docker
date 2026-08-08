---
name: paperclip-setup
description: "Install, configure, and run Paperclip AI — the open-source orchestration platform for zero-human AI agent companies (paperclipai/paperclip)"
version: 1.0.0
author: Hermes Agent
tags: [paperclip, ai-agents, orchestration, setup, deployment, postgres, self-hosted, ceo-agent]
---

# Paperclip Setup

**Paperclip** (github.com/paperclipai/paperclip) is an open-source Node.js server + React UI that orchestrates a team of AI agents to run a business. It provides org charts, budgets, governance, heartbeats, and agent coordination.

> *"If OpenClaw is an employee, Paperclip is the company."*

## Prerequisites

- Node.js >= 18 (tested with v22)
- npm (comes with Node.js)
- PostgreSQL (recommended) or embedded PostgreSQL

## Installation

### Quick start (embedded PostgreSQL — NOT as root)

```bash
npx paperclipai onboard --yes
```

**⚠️ Root user problem:** embedded-postgres does NOT support running as root. If running as root, use system PostgreSQL instead (see below).

### Quick start via npm global install (recommended)

**Why global install over npx:** Each `npx paperclipai run` invocation recompiles the `node_sqlite3` native module from C source (~5 minutes), because npx uses ephemeral cache directories. A global `npm install -g paperclipai` compiles once and reuses the binary on every run.

```bash
# Install globally (compiles sqlite3 once)
npm install -g paperclipai

# Verify
paperclipai --version

# Then onboard
paperclipai onboard --yes
```

**⚠️ Non-root user permissions:** If installing as a non-root user, ensure `~/.local/` is fully owned by your user:

```bash
chown -R $(whoami):$(whoami) ~/.local/
```

And verify `~/.local/bin` is in your `PATH`. If `paperclipai` is not found after global install, the CLI binary lives at `~/.local/lib/node_modules/paperclipai/dist/index.js` — symlink it:

```bash
ln -sf ~/.local/lib/node_modules/paperclipai/dist/index.js ~/.local/bin/paperclipai
```

**⚠️ Broken npm binary for non-root users:** The `~/.local/bin/npm` installed by tools like `n` or `nvm` can be a tiny stub pointing to a nonexistent `../lib/cli.js`. Fix by symlinking to the system npm:

```bash
ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js ~/.local/bin/npm
```

### Quick start (system PostgreSQL — works as root/sudo)

```bash
# 1. Install PostgreSQL if not present
apt-get install -y postgresql postgresql-client

# 2. Create database and user
sudo -u postgres psql -c "CREATE USER paperclip WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE paperclip OWNER paperclip;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE paperclip TO paperclip;"

# 3. Run Paperclip onboard
npx paperclipai onboard --yes

# 4. Edit the config file
# File: ~/.paperclip/instances/default/config.json
```

### Config file changes

Replace the `database` section:

```json
"database": {
    "mode": "postgres",
    "connectionString": "postgresql://paperclip:your_password@127.0.0.1:5432/paperclip",
    "backup": { "enabled": true, "intervalMinutes": 60, "retentionDays": 30 }
}
```

Also add `DATABASE_URL` to the instance `.env` file at `~/.paperclip/instances/default/.env`:

```
DATABASE_URL=postgresql://paperclip:your_password@127.0.0.1:5432/paperclip
```

## Running

```bash
# Start Paperclip server
cd ~/.paperclip && npx paperclipai run

# The server starts on http://127.0.0.1:3100
```

### Exposing to LAN/public

Change the `server` section in config.json:

```json
"server": {
    "deploymentMode": "authenticated",     # Required for non-loopback bind
    "exposure": "private",
    "bind": "lan",
    "host": "0.0.0.0",
    "port": 3100,
    "allowedHostnames": ["YOUR_SERVER_IP"],
    "serveUi": true
}
```

And update auth base URLs:

```json
"auth": {
    "baseUrlMode": "explicit",
    "publicBaseUrl": "http://YOUR_SERVER_IP:3100",
    "baseUrl": "http://YOUR_SERVER_IP:3100",
    "disableSignUp": false
}
```

## Hermes Agent as a Paperclip Worker

Paperclip can use **Hermes Agent** as a worker/employee inside your AI company. The user chooses "Hermes Agent" during Paperclip onboarding, and Paperclip spawns `hermes chat` as a subprocess.

### How Paperclip invokes Hermes

Paperclip uses the `hermes-paperclip-adapter` npm package. It spawns:

```bash
hermes chat -q "<prompt>" -Q --yolo --source tool
```

Flags:
- `-q / --query` — single query (non-interactive)
- `-Q` — quiet mode (no banner/spinner, clean output)
- `--yolo` — bypass dangerous-command prompts (no TTY in subprocess)
- `--source tool` — tags sessions for filtering
- `-m <model>` — optional model override
- `--provider <provider>` — optional provider override
- `-t <toolsets>` — optional toolset filter

### Critical: environment variable propagation

**Problem:** Hermes Agent loads API keys from `~/.hermes/.env` into Python's `os.environ`, but does NOT export them to the shell environment. Paperclip's Node.js process inherits only shell env vars, so `process.env.OPENROUTER_API_KEY` is `undefined`.

Additionally, **npx/npm sanitizes the environment** — arbitrary bash env vars are NOT passed through to the Node.js child process.

**Fix — export before starting Paperclip:**

```bash
export OPENROUTER_API_KEY="sk-or-v1-..." && cd /root/.paperclip && npx --yes paperclipai run
```

Or add it to Paperclip's `.env` file (Paperclip reads it via dotenv on startup, adding entries to `process.env`):

```
OPENROUTER_API_KEY=sk-or-v1-...
```

### Adapter behavior

The Hermes adapter in Paperclip (`hermes-paperclip-adapter`) runs two phases:

1. **`testEnvironment`** — checks CLI installed, version, Python, model, API keys, provider consistency. Returns status `"pass"`, `"warn"`, or `"fail"`.
2. **`execute`** — builds the prompt from templates (task, heartbeat, comment), spawns `hermes chat`, parses output for session ID, token usage, cost, and error patterns.

The adapter resolves the provider from three sources (priority order):
1. Explicit provider in adapter config (user override)
2. Provider from `~/.hermes/config.yaml` (auto-detected at runtime)
3. Inferred from model name prefix

## Running Behind a Reverse Proxy (Pangolin / Caddy / Nginx)

When Paperclip runs on a server with a reverse proxy that terminates SSL and forwards traffic to `127.0.0.1:3100`:

### Config changes

```json
"server": {
    "bind": "loopback",                          // NOT "0.0.0.0" — proxy handles external traffic
    "host": "127.0.0.1",                         // Listen only locally
    "port": 3100,
    "allowedHostnames": [
        "paperclip.yourdomain.com"              // Add the proxy URL hostname
    ],
    "public_url": "https://paperclip.yourdomain.com"
},
"auth": {
    "baseUrlMode": "explicit",
    "publicBaseUrl": "https://paperclip.yourdomain.com"  // Must match browser URL
}
```

### Critical fields

| Field | Value | Why |
|-------|-------|-----|
| `server.bind` | `loopback` / `lan` / `tailnet` / `custom` | Enum — `0.0.0.0` is INVALID. Behind proxy = `loopback`. |
| `server.allowedHostnames` | Array of strings | Paperspipe rejects requests with Host headers not in this list. Add **every** hostname that will reach it (IP, proxy domain, localhost). |
| `server.public_url` / `auth.publicBaseUrl` | `https://proxy.domain` | Must match what the user types in the browser. Auth redirects break if this mismatches. |

### Pitfalls

- **hostname not allowed error**: If you see `Hostname 'X' is not allowed for this Paperclip instance`, add that hostname to `server.allowedHostnames` and restart Paperclip. The CLI command `paperclipai allowed-hostname X` works for adding hostnames at runtime, or edit config.json directly. Do NOT prepend `pnpm` unless the user is inside a Paperclip workspace — the global install provides `paperclipai` directly.
- **Old processes still serve stale config after restart**: If there are OLD Paperclip processes still running when you start a NEW one, the old process(es) continue serving requests with stale config. **Kill ALL Paperclip processes before restarting:**
  ```bash
  pkill -f "paperclipai/server" 2>/dev/null
  sleep 2  # allow port release
  ```
  Then verify nothing is on port 3100 before starting fresh:
  ```bash
  ss -tlnp | grep 3100  # should return nothing
  ```
- **Bad Gateway (502)**: Usually means Paperclip is not running (crashed or not started). Check with `curl http://127.0.0.1:3100/api/health`. The Paperclip process must be running BEFORE the proxy routes traffic.
- **Pangolin auth redirect loop**: Pangolin intercepts requests before forwarding to Paperclip. The user sees Pangolin's auth page, not Paperclip's. After logging into Pangolin, they're redirected to Paperclip. This is expected behavior — no SSO/header config needed if the Pangolin route already terminates.
- **Restart required**: Any config.json or allowed-hostname change requires restarting the Paperclip process. Kill ALL old instances first (see above), then restart with `paperclipai run` (global install) or `node .../dist/index.js`. Starting in background via `terminal(background=true, watch_patterns=["listening on"])` is the recommended pattern for server launches — verify with `curl` before telling the user it's up.

## Pitfalls

### -1. "Process adapter missing command" — missing `command` field in adapter_config

A Paperclip agent with `adapter_type = "process"` fails immediately on execution with:

```
Process adapter missing command
(adapter_failed)
```

The `process` adapter requires a `command` field in its `adapter_config` JSONB column. Without it, the adapter throws before spawning any subprocess.

**Fix — add the command via PostgreSQL:**

```sql
UPDATE agents
SET adapter_config = adapter_config || '{"command": "/usr/local/lib/hermes-agent/venv/bin/hermes", "args": ["chat"]}'::jsonb
WHERE name = 'Hermes Agent'
  AND adapter_type = 'process';
```

Then reset the agent status from `error` to `idle`:

```sql
UPDATE agents
SET status = 'idle'
WHERE name = 'Hermes Agent'
  AND status = 'error';
```

**Prevention:** When creating a new `process`-type agent in Paperclip (either via UI or API), ensure `adapter_config` always includes:

```json
{
  "command": "/path/to/executable",
  "args": ["arg1", "arg2"],
  "role": "operator",
  "waitTimeoutMs": 120000,
  "paperclipApiUrl": "http://localhost:3100",
  "sessionKeyStrategy": "issue"
}
```

The `command` must be an absolute path. The Hermes CLI lives at `/usr/local/lib/hermes-agent/venv/bin/hermes` in this deployment.

**Why this happens:** The on-demand adapter selection during Paperclip onboarding can default to `"process"` type without populating the `command` field if the user chose "Hermes Agent" during board claim. The `hermes_local` builtin adapter type exists in Paperclip's adapter registry but its implementation ships via the `hermes-paperclip-adapter` npm package — if that package is not installed, the fallback to `process` type leaves the `command` field empty.

### 0. `paperclipai` CLI is a separate package from `@paperclipai/server`

There are **two npm packages:**
- `@paperclipai/server` — the server library (no CLI binary, used as dependency)
- `paperclipai` — the CLI wrapper (provides `paperclipai` binary)

Installing `@paperclipai/server` globally does NOT give you the `paperclipai` command. Always install `paperclipai`.

```bash
npm install -g paperclipai      # ✅ Has the CLI
npm install -g @paperclipai/server  # ❌ No paperclipai binary
```

### 0b. JWT secret is auto-generated — don't overwrite with truncated value

Paperclip's `onboard --yes` auto-generates `PAPERCLIP_AGENT_JWT_SECRET` in the instance `.env`. If you overwrite this file (e.g., with a truncated value from redacted terminal output), the server will reject the JWT and auth operations will fail.

Always preserve the auto-generated JWT secret, or generate a proper 64-char hex secret:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"  # 64 hex chars
```

### 0c. npx cache corruption — missing `lib/` directory

The npx cache (`~/.npm/_npx/<hash>/node_modules/`) can have incomplete package installations where the `lib/` subdirectory is missing (e.g., `ipaddr.js` has `package.json` and `ipaddr.min.js` but no `lib/ipaddr.js`). This causes:

```
Cannot find module '.../ipaddr.js/lib/ipaddr.js'
```

**Fix:** install the missing package properly and copy the `lib/` dir:

```bash
mkdir -p /tmp/fix_pkg && cd /tmp/fix_pkg
npm init -y
npm install ipaddr.js@1.9.1   # or whatever version is needed
# Copy lib/ to the npx cache
cp -r node_modules/ipaddr.js/lib ~/.npm/_npx/<hash>/node_modules/ipaddr.js/
chown -R $(whoami) ~/.npm/_npx/<hash>/node_modules/ipaddr.js/
```

Alternatively, skip npx entirely by installing globally (pitfall #0).

### 1. PostgreSQL config field names
|---------------|---------------|-------|
| `"mode": "postgres-url"` | `"mode": "postgres"` | Enum: `embedded-postgres` or `postgres` |
| `"url": "..."` | `"connectionString": "..."` | Must use `connectionString` (PR #1500 added aliases in later versions) |
| `auth.publicUrl` | `auth.publicBaseUrl` | Must use `publicBaseUrl` |

### 2. DATABASE_URL in .env must have real password

When writing credentials to `.env`, ensure the actual password is written — not `***`. The Hermes terminal tool masks passwords in display output, but the file must contain the real value. If the file has `***` literally, the `postgres` npm package will fail to parse the URL.

Check with: `grep "^DATABASE_URL" ~/.paperclip/instances/default/.env | wc -c`

Expected length for `DATABASE_URL=postgresql://paperclip:your_password_here@127.0.0.1:5432/paperclip`: depends on password length.

### 3. local_trusted mode requires loopback bind

Paperclip enforces: `local_trusted` deployment mode requires `server.bind: loopback` and `server.host: 127.0.0.1`. To bind to `0.0.0.0` (LAN), change to `authenticated` mode.

### 4. First-time setup needs board claim — in the right order

**Correct order:**
1. Visit the web UI at your **public IP** (not localhost)
2. **Create an account** first (Sign Up / Sign In button)
3. **Then** use the one-time board claim URL to claim admin ownership

> ⚠️ If you visit the board claim URL **before** signing up, the API calls return 401/403 because no session exists. You must create a user account first.

The server output shows the claim URL with `localhost`. Replace `localhost` with your actual public IP:

```
http://localhost:3100/board-claim/<token>?code=<code>
→ http://YOUR_PUBLIC_IP:3100/board-claim/<token>?code=<code>
```

**Important:** The `auth.publicBaseUrl` in config MUST match the URL users access in their browser. If `publicBaseUrl` is `http://127.0.0.1:3100` but users visit via `http://YOUR_IP:3100`, the auth flow will fail silently (401/403 on all API calls after sign-in). Always set:

```json
"publicBaseUrl": "http://YOUR_PUBLIC_IP:3100"
```

**Sending claim URLs over messaging platforms:** Platform credential-masking may auto-redact `code=xxxxx` parameters with `***`. To work around this, split the URL into two parts or send the code as separate text.

### 5. Restart after config changes

Kill the running server and restart with `paperclipai run` (not `npx paperclipai run`). The global install command avoids recompilation.

### 5b. Non-root user: config.json paths may still point to another user's home

When Paperclip is set up as user A, then copied/migrated to user B, the `config.json` paths (backup.dir, logging.logDir, storage.localDisk.baseDir, secrets.localEncrypted.keyFilePath) still point to user A's home. Paperclip runs doctor checks on startup and fails with:

```
✗ Secrets adapter: Could not read secrets key file: EACCES: permission denied
✗ Storage: Local storage directory is not writable
✗ Log directory: Log directory is not writable
```

**Fix — update all paths in config.json** to use the current user's home directory (`/home/<user>/.paperclip/instances/...`), then recreate directories with correct ownership:

```bash
mkdir -p ~/.paperclip/instances/default/{secrets,data/{storage,backups},logs}
chown -R $(whoami) ~/.paperclip/instances/
```

**Key paths to update in config.json:**
| Key path | Example fix |
|----------|------------|
| `database.backup.dir` | `/home/paperclip/.paperclip/instances/default/data/backups` |
| `logging.logDir` | `/home/paperclip/.paperclip/instances/default/logs` |
| `storage.localDisk.baseDir` | `/home/paperclip/.paperclip/instances/default/data/storage` |
| `secrets.localEncrypted.keyFilePath` | `/home/paperclip/.paperclip/instances/default/secrets/master.key` |

### 6. Board claim URL regenerates on server restart

Every time Paperclip restarts, it generates a **new** board claim token and code. If you noted down a claim URL from a previous run, it will return **404** after a restart.

Always check the server logs for the latest claim URL after starting Paperclip. The token and code are printed to stdout/stderr during startup.

### 7. Hermes API keys not found by Paperclip adapter

When Paperclip tests the Hermes Agent environment, it runs `checkApiKeys()` which looks at:
1. `config.env` (adapter-configured secrets in Paperclip's secret store)
2. `process.env` (the Node.js server environment)

Hermes loads API keys from `~/.hermes/.env` into Python memory, not shell env vars. Start Paperclip with explicit exports:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..." && npx paperclipai run
```

### 8. npx strips custom environment variables

`npx` and `npm exec` sanitize the shell environment for security. Even with `export VAR=val` in the parent shell, the Node.js process launched by npx may not inherit it. Export must happen in the **same shell invocation** that runs npx:

```bash
# This works — export + run in one command
export KEY=val && npx paperclipai run

# This may NOT work — env lost between commands
export KEY=val
npx paperclipai run        # separate shell call may lose env
```

### 9. `public_url` mismatch breaks auth redirects

Paperclip uses `auth.publicBaseUrl` for all API URLs, form actions, and auth redirects. If `publicBaseUrl` points to `127.0.0.1` but users access via the public IP, the browser gets redirected to `http://127.0.0.1:3100/...` which doesn't resolve on their device.

After sign-in, API calls return 401/403 not because auth failed, but because the session cookie was set from a public-IP URL but subsequent API requests use the loopback publicBaseUrl.

**Fix:** Always set `publicBaseUrl` to the address users actually type in their browser.

### 10. Special characters in PostgreSQL password break shell `export $(grep ... xargs)`

When restarting Paperclip with env vars using `export $(grep -v '^#' .env | xargs)`, special characters in the `DATABASE_URL` password (`!`, `@`, `#`, `$`, `%`, `^`, `&`, `*`, `(`, `)`, etc.) cause shell parsing failures. `xargs` does not handle URL-encoded or shell-special characters in the password component.

**Error:**
```
TypeError: Invalid URL
    at new URL (node:internal/url:818:25)
    at parseUrl (postgres/src/index.js:545:18)
```

**Fix:** Export env vars individually with explicit values, not by sourcing the whole .env file:
```bash
export "OPENROUTER_API_KEY=*** "OTHER_VAR=value" && npx paperclipai run
```

Or let Paperclip read its own `.env` automatically (dotenv) by starting without explicit exports:
```bash
cd ~/.paperclip && npx paperclipai run
```

## Claude Code as a Paperclip Worker

Paperclip can use **Claude Code** (`@anthropic-ai/claude-code`) as a worker/adapter. The `claude_local` adapter is built into Paperclip.

### Installation

```bash
npm install -g @anthropic-ai/claude-code
```

The package ships a native Linux binary (`bin/claude.exe`). Symlink it into PATH:

```bash
ln -sf $(npm root -g)/@anthropic-ai/claude-code/bin/claude.exe /usr/local/bin/claude
```

Verify:
```bash
claude --version
# → 2.1.152 (Claude Code)
```

### Authentication

Claude Code supports two authentication methods:

1. **Subscription (OAuth)** — uses your Claude Pro/Max subscription. Run:
   ```bash
   claude auth login
   ```
   This prints an OAuth URL. Open it in a browser on any device, log in to your Anthropic account, and if prompted paste the verification code back.

2. **API key** — set `ANTHROPIC_API_KEY` in the environment. See `claude auth login --console` for console/API billing.

### How Paperclip's Claude adapter works

The adapter (`@paperclipai/adapter-claude-local`) runs the official `claude` CLI with flags:
```bash
claude --print - --output-format stream-json --verbose <prompt>
```

It detects billing type from the environment:
```javascript
billingType = has("ANTHROPIC_API_KEY") ? "api" : "subscription"
```

The adapter resolves model/provider, builds prompt bundles from Paperclip skills, and supports session persistence via `--resume`.

### ⚠️ Important: Anthropic ban policy awareness (2026)

As of 2026, Anthropic actively enforces restrictions on Claude Code usage:

**What triggers bans:**
- Using OAuth tokens from consumer plans (Pro/Max) in **third-party harnesses** that spoof the official Claude Code client identity (e.g., OpenCode, RooCode — these send fake HTTP headers)
- Running Claude from **multiple accounts on the same machine** (device fingerprinting)
- **High-frequency autonomous agent loops** (e.g., 419 cycles in 48 hours → flagged)
- Browser automation integrations wrapping Claude

**What is OK:**
- Using the official `claude` CLI directly (as Paperclip does — it runs the real binary, not a spoofed harness)
- Using `ANTHROPIC_API_KEY` (API key / metered billing) — no restrictions
- Normal interactive Claude Code usage

**Practical guidance for Paperclip:**
- Paperclip's adapter runs the ACTUAL `claude` binary, not a spoofed harness — this is the safe path
- If using subscription/OAuth auth, avoid high-frequency loops (>400 runs in 48h) that look like automation farming
- For production/commercial use, use `ANTHROPIC_API_KEY` (API billing) — this completely avoids consumer-plan restrictions
- See `references/claude-code-setup.md` for the full authentication flow and policy details

## Self-Hosted: CEO Agent (Claude Code) Configuration

When the CEO agent uses the `claude_local` adapter (Claude Code CLI), these steps are required for a self-hosted Paperclip instance where Paperclip runs as a dedicated user (e.g., `paperclip`) rather than root.

### 1. Authentication Check

```bash
# Paperclip runs as 'paperclip' user — Claude must be authed for that user
sudo -u paperclip claude whoami
# If 401, copy credentials from root:
sudo cp /root/.claude/.credentials.json /home/paperclip/.claude/.credentials.json
sudo chown paperclip:paperclip /home/paperclip/.claude/.credentials.json
sudo chmod 600 /home/paperclip/.claude/.credentials.json
```

### 2. Instructions File (AGENTS.md)

The CEO agent has **two** absolute paths in `adapter_config`: `instructionsFilePath` and `instructionsRootPath`. If Paperclip was installed as root then switched to the `paperclip` user, both may point to `/root/` instead of `/home/paperclip/`.

**Fix both paths via PostgreSQL:**

```sql
UPDATE agents 
SET adapter_config = jsonb_set(adapter_config::jsonb, '{instructionsFilePath}',
  '"/home/paperclip/.paperclip/instances/default/companies/COMPANY_UUID/agents/AGENT_UUID/instructions/AGENTS.md"')
WHERE id = 'AGENT_UUID';

UPDATE agents 
SET adapter_config = jsonb_set(adapter_config::jsonb, '{instructionsRootPath}',
  '"/home/paperclip/.paperclip/instances/default/companies/COMPANY_UUID/agents/AGENT_UUID/instructions"')
WHERE id = 'AGENT_UUID';
```

Create the `instructions/` directory (it may not exist):

```bash
sudo -u paperclip mkdir -p /home/paperclip/.paperclip/instances/default/companies/COMPANY_UUID/agents/AGENT_UUID/instructions
```

Use the template at `skill_view(name='paperclip-setup', file_path='templates/CEO-AGENTS.md')` as a starting point for the AGENTS.md file — customize the company name and mission.

### 3. Resume CEO After Fix

```sql
UPDATE agents SET status = 'idle' WHERE id = 'CEO_AGENT_UUID';
UPDATE agents SET runtime_config = jsonb_set(runtime_config::jsonb, '{heartbeat,enabled}', 'true') WHERE id = 'CEO_AGENT_UUID';
```

### CEO Agent Troubleshooting Queries

See `references/ceo-agent-queries.md` for detailed SQL queries to inspect and fix CEO agent state, including:
- Agent status and adapter config inspection
- Instructions path update
- Issue and activity log queries
- CEO heartbeat configuration

## Daily Ops Status Check

For daily or on-demand status reports on Paperclip AI companies, load `references/daily-ops.md`.

### Quick Diagnostics

```bash
# Companies
sudo -u paperclip psql -d paperclip -c "SELECT name, status, issue_prefix FROM companies;"

# Agents and their status
sudo -u paperclip psql -d paperclip -c "SELECT a.name, a.role, a.status, a.adapter_type FROM agents a JOIN companies c ON a.company_id = c.id ORDER BY a.created_at;"

# Recent activity (CEO failures show up here)
sudo -u paperclip psql -d paperclip -c "SELECT created_at, action, details FROM activity_log ORDER BY created_at DESC LIMIT 10;"
```

### Report Format
```
📋 Paperclip Daily Ops
🏢 **<Company>** — Phase X
  Board: X% complete | Sprint: "<goal>"
  Agents: X actifs / X total
  ⏳ Blockers: X
  ✅ Last 24h: X tasks done
```

### Cron Usage
```python
cronjob(action='create', skills=['paperclip-setup'],
  schedule='0 9 * * *', prompt='Run Paperclip daily ops status check')
```

## Diagnostics — Inspecting Paperclip State

When users ask "check what the CEO did" or "what's the status", **query the PostgreSQL database directly** rather than navigating the UI through Pangolin auth. This is faster and gives the full picture (agents, issues, membership, error details).

### Key diagnostic queries (quick)

```bash
# Companies
sudo -u paperclip psql -d paperclip -c "SELECT name, status, issue_prefix FROM companies;"

# Agents and their status  
sudo -u paperclip psql -d paperclip -c "SELECT a.name, a.role, a.status, a.adapter_type FROM agents a JOIN companies c ON a.company_id = c.id ORDER BY a.created_at;"

# Recent activity (CEO failures show up here)
sudo -u paperclip psql -d paperclip -c "SELECT created_at, action, details FROM activity_log ORDER BY created_at DESC LIMIT 10;"

# Issues for active company
sudo -u paperclip psql -d paperclip -c "SELECT i.id, c.issue_prefix || '-' || i.issue_number AS ref, i.title, i.status FROM issues i JOIN companies c ON i.company_id = c.id ORDER BY i.created_at;"
```

### Common CEO failure patterns

| `details` snippet | Meaning | Fix |
|---|---|---|
| `'Claude run failed: ... 401 Invalid authentication credentials'` | CEO with `claude_local` adapter — Claude Code not authenticated | Run `claude auth login` (OAuth) or set `ANTHROPIC_API_KEY` in Paperclip's env |
| `'Adapter failed'` | Generic adapter crash (`hermes_local`) | Check Hermes config, ensure API keys are exported |
| `'Process adapter missing command'` | `adapter_type = 'process'` but `adapter_config` lacks `command` | Add command field via SQL: `UPDATE agents SET adapter_config = adapter_config || '{"command": "/path/to/hermes", "args": ["chat"]}'::jsonb WHERE name = 'Hermes Agent' AND adapter_type = 'process';` then reset status |
| `'No such file AGENTS.md'` | Instructions path wrong or directory missing | Update `adapter_config` path + create the instructions directory |
| `'--dangerously-skip-permissions cannot be used with root/sudo'` | `adapter_config` has `dangerouslySkipPermissions: true` but Paperclip launched via sudo ancestry | Remove the flag: `UPDATE agents SET adapter_config = adapter_config::jsonb - 'dangerouslySkipPermissions' WHERE name = 'CEO';` then reset status |

### CEO agent lifecycle
1. User creates a company → CEO agent is spawned (role=ceo, adapter chosen)
2. CEO runs heartbeat ticks → creates issues, hires sub-agents, builds org chart
3. If CEO crashes → status=error, issues get `blocked` with `stranded_assigned_issue`
4. User recovers by resolving the recovery action in UI → CEO restarts
5. **Critical:** CEO keeps retrying after failure. If auth is broken, it will fail repeatedly and fill activity_log with `environment.lease_released` + `adapter_failed` events

Full query reference with schema details: `skill_view(name='paperclip-setup', file_path='references/database-inspection.md')`

## Verification

```bash
# Health check
curl http://127.0.0.1:3100/api/health

# Expected response:
# {"status":"ok","version":"2026.525.0","deploymentMode":"...","authReady":true}
```

## Updating Paperclip

```bash
npx paperclipai update
# Or: npm update -g paperclipai
```

## Removing

```bash
rm -rf ~/.paperclip
```