# Retrieving Obsidian LiveSync secrets via Vaultwarden

## Workflow

The user prefers issuing a dedicated, restricted Vaultwarden account for the agent instead of sharing their master credentials or pasting secrets directly.

1. **User creates an account** on their Vaultwarden instance (e.g. `vault.jefe.al`) and shares a login/email + master password.
2. **User adds the secret** (e.g. LiveSync passphrase) as an item in their own vault, then shares/assigns it to the agent's account. Or they add it directly to the agent's vault after creation.
3. **Agent installs `bw` CLI** if not present:
   ```bash
   npm install -g @bitwarden/cli
   # Binary lands at /root/.hermes/node/bin/bw
   ln -sf /root/.hermes/node/bin/bw /usr/local/bin/bw
   ```
4. **Agent configures server** (self-hosted only):
   ```bash
   bw config server https://vault.jefe.al
   ```
5. **Agent logs in** (use `--passwordenv` or pipe to avoid exposing the master password in shell history or terminal output):
   ```bash
   export BW_PASS="master-password-here"
   bw login user@example.com --passwordenv BW_PASS
   ```
6. **Agent unlocks vault**:
   ```bash
   export BW_SESSION=$(bw unlock --passwordenv BW_PASS --raw)
   ```
7. **Agent syncs vault** (important: the vault may show empty at first — the user is creating items on their own device. Run sync first before listing):
   ```bash
   bw sync --session "$BW_SESSION"
   ```
8. **Agent lists items** to find the target secret:
   ```bash
   bw list items --session "$BW_SESSION"
   ```
   Or if you already know the item ID (e.g. from a prior list), use `get` for the full item including field values:
   ```bash
   bw get item <item-id> --session "$BW_SESSION"
   ```
   Parse the JSON with Python (available everywhere) since `jq` may not be installed:
   ```bash
   python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Login:', data['login']['username'])
print('Password:', data['login']['password'])
for f in data['fields']:
    print(f['name'] + ':', f['value'])
" <<< "$(bw get item <item-id> --session "$BW_SESSION")"
   ```
9. **Agent retrieves the secret value** (passphrase, API key, etc.) and applies it to the target tool/configuration.

## Pitfalls

### Empty vault on first login

A freshly created account will return `[]` from `bw list items`. The user must populate the vault with at least one item before the agent can retrieve anything. Tell the user the account is connected but empty.

### Master password with special characters

Some characters confuse shell quoting. Use `--passwordenv BW_PASS` with `export BW_PASS='...'` (single quotes) to avoid shell interpretation of `$`, `!`, `*`, etc.

### Server URL must be configured before login

`bw config server` is required before `bw login` for self-hosted instances. If you skip this, `bw login` will try the Bitwarden cloud and fail.
