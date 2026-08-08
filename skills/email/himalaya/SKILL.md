---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.2.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)
- `references/jefe-email-workflow.md` (Jefe's Gmail folder structure, taxonomy rules 1-10, batch tri workflow, anti-injection protocol, and cron auto-sort setup)
- `references/multi-account-prendizef59.md` (second Gmail account added June 2026 — folder structure, config, read-only rules)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
# Syntax: himalaya message move <TARGET_FOLDER> <ID>...
himalaya message move "Archive" 42
himalaya message move "Promo" 2743
```

Copy to folder:

```bash
# Syntax: himalaya message copy <TARGET_FOLDER> <ID>...
himalaya message copy "Important" 42
```

> **⚠️ Pitfall — IMAP IDs change between folders.** Himalaya uses IMAP sequence numbers, not permanent UIDs. After moving an email, its ID in the destination folder is **different** from the source. You cannot reference it by the old ID. To read a moved email, either (a) list the destination folder to find the new ID, or (b) use `--folder '[Gmail]/Tous les messages'` which is the Gmail \"All Mail\" label that preserves the original ID.

### Delete an Email

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

### List accounts

```bash
himalaya account list
```

### Switch between accounts

In v1.2.0, `-a/--account` is a **subcommand-level option**. Always place it AFTER the subcommand for maximum compatibility:

```bash
himalaya envelope list -a work
himalaya folder list -a work
himalaya message read -a work 42
```

⚠️ **Flag-position pitfall:** Placing `-a` before the subcommand works for some subcommands (`himalaya -a work envelope list` succeeds) but **fails for others** (`himalaya --account work folder list` → `error: unexpected argument`). The position-safe form is always after: `himalaya <subcommand> -a <name>`.

### Add a second account (manual config)

Add a new `[accounts.<name>]` block in `~/.config/himalaya/config.toml`. For read-only monitoring of a second mailbox, only IMAP is needed (omit SMTP entirely — prevents accidental sends):

```toml
[accounts.secondary]
email = "other@gmail.com"
display-name = "Secondary"
default = false

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "other@gmail.com"
backend.auth.type = "password"
backend.auth.cmd = "echo 'app-password-here'"

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "[Gmail]/Sent Mail"
folder.aliases.drafts = "[Gmail]/Drafts"
folder.aliases.trash = "[Gmail]/Trash"
```

### Verify a new account

```bash
himalaya account doctor <account-name>
# Output: "Checking TOML configuration... OK / Checking IMAP integrity... OK"
```

### Per-account folder differences

Each Gmail account can have a **different set of custom folders/labels**. Always list folders after connecting:

```bash
himalaya folder list -a <account-name>
```

Do not assume the folders from one account exist on another.

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

### ⚠️ Pitfall: Gmail app passwords diverge between stores

When using Gmail app passwords for Hermes gateway email **and** Himalaya CLI, there are **two separate stores** that must both be updated when the app password is rotated:

1. **Himalaya config** (`~/.config/himalaya/config.toml`) — `backend.auth.cmd` / `message.send.backend.auth.cmd`
2. **Hermes .env** (`~/.hermes/.env`) — `EMAIL_PASSWORD`

A classic scenario: the app password was regenerated and updated in `.env` (gateway works fine), but the Himalaya config still has the old password. Symptom: `himalaya` CLI fails with `Invalid credentials (Failure)` while gateway email adapter works. Fix: update both `auth.cmd` entries in the config file.

Also check for hostname typos (`gamil.com` vs `gmail.com`) in both `.env` and `config.toml` — a subtle typo in the IMAP/SMTP host causes connection resets that look like credential errors. After any fix, restart the gateway: `hermes gateway restart`.

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
