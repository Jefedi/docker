---
name: x-twitter-api-setup
description: "Complete X/Twitter API onboarding: Developer Portal account, PPU agreement, app creation, OAuth 2.0 config, production migration, credits, CLI auth."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites: []
metadata:
  hermes:
    tags: [twitter, x, developer-portal, oauth, api-setup]
---

# X/Twitter API Setup — Developer Portal to First Post

This skill covers the **full journey** from a fresh X/Twitter account to posting via the API. It complements the `xurl` CLI skill by covering the Developer Portal prerequisites that must happen before any CLI command works.

Use this when the user wants to post to X/Twitter via API but hasn't set up the Developer Portal yet.

---

## The Full Setup Flow (Overview)

```
① Developer Portal → ② PPU Agreement → ③ Create App
→ ④ Configure OAuth 2.0 → ⑤ Migrate to Production
→ ⑥ Buy Credits → ⑦ Install xurl → ⑧ Auth & Post
```

---

## Step-by-Step Walkthrough (user does this themselves)

> ⚠️ **Agent policy**: Never ask for credentials in chat. Never read `~/.xurl`. Guide the user to do the secret-bearing steps themselves.

### ① Developer Portal Access
User goes to **https://developer.x.com/en/portal/dashboard** and signs in with their X account.

### ② PPU Developer Agreement
The first time, X shows a "Pay Per Use Pilot Agreement" form in French/English. The user must fill:
- **Account name**: their brand/app name (e.g. "Trakii" or their handle minus the @)
- **Describe your API use cases**: a brief description of what they'll post and why. Keep it honest and specific. Sample template:

  > **Account:** @handle — Site: example.com
  > 
  > **Summary:** [App name] is a [brief description of what it does].
  > 
  > **Use cases:**
  > 1. Posting original content about the product/service
  > 2. Engaging with the community (replies, mentions)
  > 3. Sharing user-generated content with consent
  > 
  > **Data:** Only public X data. No resale. No spam. Content is original and manually moderated.

- Check the 3 checkboxes
- Click **"Soumettre" / "Submit"**
- Approval can take hours to a few days.

### ③ Create an App
In the Developer Portal:
1. Navigate to **"Projects & Apps"** → **Create App**
2. Name it (e.g. "my-brand-app")
3. App is created in **Development** environment by default
4. Note the **API Key / API Secret Key** (OAuth 1.0a) — **not** what we need for xurl but save them anyway

### ④ Configure OAuth 2.0 User Authentication
In the app's settings page, find **"User Authentication Settings"** and click **"Set up" / "Configure"**. Fill in:

| Field | Value |
|-------|-------|
| **App Type** | `Web App, Automated App or Bot` (NOT Native App) |
| **Redirect URI** | `http://localhost:8080/callback` |
| **Website URL** | Your site URL (e.g. `https://example.com`) |
| **Permissions** | Select at minimum **"Read and Write"** |

Click **"Save"**. The **OAuth 2.0 Client ID** and **Client Secret** are shown once — the user must save them immediately.

> **Pitfall**: If the app type is "Native App", OAuth 2.0 returns `unauthorized_client`. Must be "Web App, Automated App or Bot".

### ⑤ Migrate to Production
Back in the app list view:
- Find the app card under **"Development"**
- Click **"Move" / "Déplacer"** 
- Select **"Production"** environment
- Confirm

This is required for the API to accept requests outside the sandbox.

### ⑥ Buy Credits
In the Dashboard:
- Current balance shows at top right
- Click **"Buy credits"** / **"Acheter des crédits"**
- Minimum: **$5 USD** (enough for thousands of posts)
- Without credits, all API calls fail with `CreditsDepleted`

> **Pitfall**: Many setup failures are billing issues, not code issues. Always check credits before attempting to post.

### ⑦ Install xurl CLI
```bash
# Preferred: npm (works everywhere)
npm install -g @xdevplatform/xurl

# If EACCES on -g (Docker containers):
npm install -g @xdevplatform/xurl --prefix ~/.local
export PATH=$HOME/.local/bin:$PATH
# Binary at ~/.local/bin/xurl

# Find the binary if PATH is uncertain:
find / -name xurl -type f 2>/dev/null
```

> **⚠️ Credential type gotcha**: The Developer Portal shows TWO sets of credentials. xurl uses **OAuth 2.0** (`Client ID` + `Client Secret`), NOT OAuth 1.0a (`Consumer Key` + `Consumer Secret`). The OAuth 2.0 credentials only appear after you configure **User Authentication Settings** (step ④). The 1.0a keys appear immediately upon app creation — ignore them for xurl.

### ⑧ Register App & Authenticate in Terminal
> 🔴 User runs these commands in their own terminal — NOT in the agent session.

```bash
# Register the app locally
xurl auth apps add my-app \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET

# Authenticate (opens browser)
# If local callback fails (port in use, headless server), use --headless:
xurl auth oauth2 --app my-app @YourHandle
# OR headless mode:
xurl auth oauth2 --app my-app --headless @YourHandle

# Set as default
xurl auth default my-app

# Verify
xurl whoami
```

#### Headless Mode (for Docker / remote / port-conflict)
When `xurl auth oauth2` fails with `bind: address already in use` on port 8080:
```bash
xurl auth oauth2 --app my-app --headless @YourHandle
```
This prints an authorization URL. The user opens it in ANY browser (even on their phone), authorizes, and pastes the redirect URL back into the terminal.

> **⚠️ One-time-use code challenge**: Each `--headless` invocation generates a unique `code_challenge` embedded in the printed URL. The authorization callback code the user gets after approving is ONLY valid for that specific challenge. If the user opens a stale URL from a previous run, the callback code will fail. Always generate a fresh URL and have the user authorize against it.

### Agent-Managed OAuth2 Flow For Docker — Step-by-Step

In Docker/container setups where the agent and user share a machine but run under different HOME directories, the agent can do everything except the secret-visual step (the user must authorize in their own browser).

#### Agent does:
```bash
# 1. Install if needed (EACCES fallback)
npm install -g @xdevplatform/xurl --prefix ~/.local
# Binary lands at: ~/.local/lib/node_modules/@xdevplatform/xurl/binary/xurl

# 2. Register the app (config only, no secrets handled by agent)
xurl auth apps add my-app --client-id YOUR_ID --client-secret YOUR_SECRET

# 3. Start OAuth2 with pty=true (CRITICAL)
terminal(background=true, pty=true, command="xurl auth oauth2 --app my-app --headless @Handle")
```

Without `pty=true`, the process exits immediately with `"failed to read pasted code: EOF"` because stdin closes before the URL is even printed.

#### Agent polls and shows URL:
```python
process(action='log', session_id='...')
# Captures the printed authorization URL
# Shows it to the user via chat
```

#### User does:
1. Opens the **fresh** authorization URL in ANY browser (phone, laptop)
2. Logs in as @Handle
3. Authorizes the app
4. Gets redirected to `http://localhost:8080/callback?state=...&code=...`
5. Copies the full redirect URL (or just the `code=...` value) and sends it to the agent

#### Agent finishes:
```python
process(action='submit', session_id='...', data='THE_CODE_VALUE')
# Output: "Exchanging code for a token… OAuth2 authentication successful!"

xurl auth default my-app
xurl whoami  # Verify
```

The agent can now post directly without further user commands.

#### ⚠️ Pitfalls
- **One-time-use code challenge**: Each `--headless` call generates a unique `code_challenge`. The user's callback code from their browser is ONLY valid for that specific challenge. A stale URL from a prior run fails with `"code verifier did not match"`. Always start a **fresh** background process per attempt.
- **Process lifecycle**: After successful exchange, the background process exits. One process = one token. Start a new one for each account.
- **EOF error → almost always missing pty**: If the process exits immediately with EOF, the `pty=true` flag was likely omitted. Kill the stale process and restart with PTY.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `unauthorized_client` during OAuth | App type set to "Native App" | Change to "Web App, Automated App or Bot" in Settings |
| `bind: address already in use` on auth | Port 8080 occupied | Use `--headless` flag (no local server needed) |
| `NoAuthMethod` / `no authentication method available` | App not registered or wrong default | User runs: `xurl auth default my-app` |
| `CreditsDepleted` | $0.00 balance | Buy $5+ in Developer Console → Billing |
| `client-forbidden` / `client-not-enrolled` | App still in Development | Move app to Production environment |
| `xurl: not found` after install | Binary not in PATH | Use full path: `~/.local/bin/xurl` or `find / -name xurl`. If npm installed with `--prefix ~/.local`, the binary is at `~/.local/lib/node_modules/@xdevplatform/xurl/binary/xurl` |
| OAuth flow "succeeds" but commands fail with 401 | Token saved to built-in `default` profile (no client-id/secret) | `xurl auth oauth2 --app my-app @Handle` then `xurl auth default my-app` |
| Two "Client Secret" values in X dashboard | UI bug — first value is Client ID | Confirm on "Keys and tokens" page; ID ends in `MTpjaQ` |
| PPU form submitted but account shows empty/403 | New account needs initial bio setup on X before Developer Portal works | Complete the "Describe yourself" onboarding prompt on X.com first |
| 503 on search/timeline but whoami works | Credits depleted or app still in Development. whoami uses a cheap endpoint that may still respond when credits are $0. | Check billing (Developer Portal). Move app to Production. Top up $5+. |
| 403 "You are not permitted to use OAuth2" on user timeline endpoint | `/2/users/by/username/{username}/tweets` requires OAuth 1.0a user context, not OAuth 2.0 | Use `xurl timeline` (authenticated user's own timeline) or `xurl search from:handle` instead of the raw user timeline endpoint. OAuth 2.0 works for posting, search, and the authenticated user's timeline — only the specific "get a user's tweets" endpoint needs 1.0a. |
| Auth callback code rejected ("EOF" / "failed to read") | Stale URL from a prior `--headless` run **OR** background process without PTY | Generate a fresh URL (`--headless` again), user authorizes against the new one. **If using hybrid agent workflow**: ensure the background terminal uses `pty=true` — without it, stdin closes before the code can be submitted |

---

## Docker/Container HOME Pitfall

When Hermes runs inside Docker, the agent's terminal tool uses `/opt/data/home` as `HOME`, while the user's interactive shell might use `/root` or another path. xurl stores its config at `~/.xurl`, so the user and the agent see different config files.

**If the user ran setup as root (interactive shell) but the agent's `xurl auth status` returns "No apps registered":**
- The user's config lives at `/root/.xurl`
- The agent reads `/opt/data/home/.xurl`
- Solution: user must either (a) run xurl commands with `HOME=/opt/data/home` prefix, or (b) the agent tells the user the full binary path they found and asks them to run the post command themselves.

---

## Related Skills

- `xurl` — The X API CLI itself (post, search, DM, media, raw API)

## References

- `references/pricing.md` — Per-request costs, budget planning table, and key X API pricing facts for 2026 pay-per-use.
- `references/social-media-strategy.md` — Content planning for new account growth: post categories, day structure, repetition avoidance, budget optimization, and cron automation patterns.
