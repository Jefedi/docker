# Remote Deployment Guidance

When the user deploys on a remote server (e.g. Hetzner VPS) but Hermes runs on a different host, the agent **cannot** run docker/terminal commands on the target server.

## Core Rules

### 1. Guide, don't execute
- `execute_code` and `terminal` run locally on the Hermes host, NOT on the user's server.
- Don't try `ls /srv/docker/radicale` expecting to see the user's files — you'll get "No such file or directory" from your own host.
- Send commands for the user to paste in their terminal.

### 2. Telegram command format (CRITICAL)
See `assistant-plugin/references/user-preferences.md` for the full rules. Summary:
- One message = one command, nothing else. No backticks, no code blocks.
- Explanations in a separate message.
- User long-press → copy → paste in their terminal.

### 3. sudo vs root access on fresh VPS
On fresh VPS images (e.g. Debian Trixie base `jefe@Debian-trixie-latest-amd64-base`):
- `sudo` may be available even when `su -` fails (root password unknown).
- Always try `sudo <cmd>` before suggesting `su - -c`.
- If `sudo` works, the user can `sudo passwd root` to set a root password if needed.

### 4. passwd complexity enforcement
Debian's cracklib rejects passwords with:
- 4+ consecutive same-class characters (e.g. `aaaa`, `1234`, `AAAA`)
- Missing cracklib dict: `/var/cache/cracklib/cracklib_dict.pwd: No such file or directory` — the check still fails, just pick a complex password.

Suggest mixed passwords like `MonMdp2026!` (uppercase + lowercase + digits + symbol, no 4-consecutive-same-class).

### 5. Pre-existing root-owned directories
If `mkdir -p /path/to/dir` succeeds but `chown` fails with "Operation not permitted":
- The directory already exists and is owned by root.
- The current user can't `chown` files they don't own.
- Fix: `sudo chown -R <user>:<user> <dir>`

### 6. Resuming an interrupted deployment
When returning to a service setup after session expiry:
- Use `session_search` to find the previous session and recover context.
- Ask the user for current state: `ls` the directory, `docker ps -a | grep <service>`.
- Don't assume the deployment is at the same step as when you left off.