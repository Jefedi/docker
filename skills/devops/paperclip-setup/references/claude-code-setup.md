# Claude Code — Paperclip Adapter Setup

This covers installing, authenticating, and configuring Claude Code as a Paperclip worker, plus 2026 Anthropic ban policy context.

## Installation

```bash
# Install globally
npm install -g @anthropic-ai/claude-code

# Symlink binary to PATH
ln -sf $(npm root -g)/@anthropic-ai/claude-code/bin/claude.exe /usr/local/bin/claude

# Verify
claude --version
# → 2.1.152 (Claude Code)

# Test print mode (will say "Not logged in" — expected)
claude --print "hello" 2>&1
# → Not logged in · Please run /login
```

### Binary notes

The `bin/claude.exe` file is actually a **native Linux ELF 64-bit binary** (not a Windows `.exe` despite the name), dynamically linked, x86-64. The npm package's `package.json` maps `"bin": {"claude": "bin/claude.exe"}` but npm doesn't always create the symlink properly depending on the npm prefix configuration.

## Authentication

### Option A: Subscription/OAuth (no API key)

Use this when you have a Claude Pro ($20/mo) or Max ($200/mo) subscription and don't want to set up API billing.

```bash
claude auth login
```

This outputs:
```
Opening browser to sign in…
If the browser didn't open, visit: https://claude.com/cai/oauth/authorize?code=...
Paste code here if prompted > 
```

**Flow:**
1. Copy the OAuth URL
2. Open it in any browser (works on phone, tablet, desktop)
3. Log in with your Anthropic account
4. If a verification code is shown, paste it back in the terminal
5. Claude Code stores credentials in `~/.claude/` (projects, cache, sessions, backups)

**First-run theme prompt:** On first launch in PTY mode, Claude Code shows an interactive theme/starter selection (Monokai, Light, Dark, etc.). You can pass through this by submitting Enter/return a few times.

**Verification after login:**
```bash
claude --print "hello" 2>&1
# Should respond with actual content, not "Not logged in"
```

### Option B: API key

```bash
claude auth login --console
```

Or set `ANTHROPIC_API_KEY` in the environment. Paperclip auto-detects this:
```
billingType = has("ANTHROPIC_API_KEY") ? "api" : "subscription"
```

The `--bare` flag enforces API-key-only mode:
```
--bare  OAuth and keychain are never read. Strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings.
```

## Paperclip Adapter Integration

Paperclip's `claude_local` adapter uses the official `claude` CLI with these flags:

```
claude --print - --output-format stream-json --verbose
```

Additional flags used by the adapter:
- `--resume <sessionId>` — session persistence across heartbeats
- `--dangerously-skip-permissions` — bypass approval prompts (no TTY in subprocess)
- `--model <model>` — optional model override (e.g., `claude-sonnet-4-20250514`)
- `--effort <level>` — effort level (low/medium/high/xhigh/max)
- `--add-dir <dir>` — additional directories for tool access
- `--append-system-prompt-file <file>` — Paperclip skill prompts
- `--agent <name>` — custom agent profile

## Anthropic Ban Policy (2026)

### Key timeline

| Date | Event |
|------|-------|
| Jan 2026 | Major sweep against third-party harnesses (OpenCode, RooCode). Partial rollback after pushback. |
| Feb 18, 2026 | Official policy: OAuth tokens from consumer plans banned in third-party tools. Documented in Claude Code legal docs. |
| Feb-Mar 2026 | Bans widen: new computers, VPN changes, browser automation, high-frequency loops. Device fingerprinting confirmed. |
| Mar 2026 | Suspension reports spike. Multiple behavioral classifiers deployed. |

### What triggers bans (confirmed cases)

1. **Multiple accounts on same machine** — Device-level fingerprinting ties usage to machine ID. Using 2+ accounts on one laptop = flagged.
2. **OAuth token reuse in third-party harnesses** — Tools like OpenCode/RooCode that spoof the Claude Code HTTP client identity (fake headers). Anthropic calls this "spoofing."
3. **Browser automation integration** — Playwright/Camoufox wrapping Claude with autonomous drivers.
4. **High-frequency autonomous agent loops** — >400 cycles in 48 hours triggers behavioral classifiers.
5. **IP/device anomalies** — New computer + intensive use, rapid VPN changes, Starlink connections.

### What is NOT banned

- Using the official `claude` CLI directly
- Using `ANTHROPIC_API_KEY` (API billing) — exempt from consumer-plan restrictions
- Normal development workflows

### Economic context

Claude Max ($200/mo flat rate) vs API pricing: a power user doing 419 autonomous cycles in 48h would have spent **>$1,000/month** on API. Anthropic's enforcement is widely seen as protecting the business model — blocking the "unlimited buffet" arbitrage where harnesses remove Claude Code's built-in rate limits.

### Sources

- VentureBeat, Jan 9 2026: "Anthropic cracks down on unauthorized Claude usage by third-party harnesses"
- Medium (jia li), Mar 19 2026: "Why Anthropic Is Banning Claude Code Users"
- Claude's Corner (Substack), Feb 19 2026: "Are You Breaking Anthropic's Rules?"
- OpenCode docs: "Using your Claude Pro/Max subscription in OpenCode is not officially supported by Anthropic."
- Hacker News discussion: "In a month of Claude Code, it's easy to use tokens worth >$1,000 on the API."