---
name: discord-server-builder
description: "Build and configure a Discord server from A to Z via the Discord REST API (Python stdlib only — no discord.js or discord.py needed). Covers role hierarchy, channel structure, permission overwrites, security settings, welcome messages, and invites. Use when the user asks to create, set up, or restructure a Discord server."
version: 1.0.0
---

# Discord Server Builder

Build and configure a Discord server end-to-end via the Discord REST API.
Uses only Python stdlib (urllib) — no external dependencies.

## When to use

- User asks to create/set up a Discord server
- User wants to restructure an existing server (roles, channels, permissions)
- User wants to automate Discord server configuration
- User shares a bot token and asks you to "make a Discord"

## When NOT to use

- One-off message sending (use `xurl` or the `discord` skill)
- Bot development / hosting (use coding workflow)
- Discord gateway events / real-time bot (requires discord.js/discord.py)

## Prerequisites

1. **A Discord bot token** — from https://discord.com/developers/applications
2. **The bot must be invited to the target server** with appropriate permissions
3. **Privileged Gateway Intents** enabled if member listing is needed

## Bot Invite URL Format

When the user needs to invite a bot to a new server, generate the OAuth2 URL:

```
https://discord.com/api/oauth2/authorize?client_id={BOT_CLIENT_ID}&permissions=8&scope=bot
```

- `permissions=8` = Administrator (required for full server setup)
- `scope=bot` = bot scope (add `applications.commands` if slash commands needed)
- The `client_id` is the bot's **application ID**, NOT the bot token

**IMPORTANT**: Always verify the bot identity with `GET /users/@me` using the token BEFORE generating the invite URL. This confirms:
- You're working with the correct bot (the user may have multiple bots)
- The token is still valid (not reset/revoked)
- You extract the correct `client_id` from the response (`id` field)

## Verifying Bot Identity & Token Validity

**Use `curl` (not Python urllib) for quick token checks** — curl sends a proper User-Agent by default, while Python's `urllib` gets Cloudflare-blocked (error 1010) unless you explicitly set a Discord-format User-Agent header.

```bash
# Quick token check via curl (works out of the box)
curl -s -H "Authorization: Bot $TOKEN" \
  -H "User-Agent: DiscordBot (https://example.com, 1.0)" \
  "https://discord.com/api/v10/users/@me"
```

```python
# Python equivalent (MUST set User-Agent or get Cloudflare 403)
import urllib.request, json
headers = {
    "Authorization": f"Bot {token}",
    "User-Agent": "DiscordBot (https://example.com, 1.0)",
}
req = urllib.request.Request("https://discord.com/api/v10/users/@me", headers=headers)
bot = json.loads(urllib.request.urlopen(req).read())
print(f"Bot: {bot['username']} (ID: {bot['id']})")
```

After a user invites the bot to a new server, verify it joined by re-listing guilds:
```
GET /users/@me/guilds  →  check the new guild appears in the list
```

## Managing Multiple Discord Bots

Users with multiple Discord bots may confuse which bot is which. Before acting:
1. Ask the user which bot (by name or client ID) if ambiguous
2. Always call `GET /users/@me` first to confirm the bot identity matches
3. The bot's `id` field from `@me` is the same as the `client_id` in the invite URL
4. If the user gives you an invite URL, extract the `client_id` parameter to identify the bot

## Key API Quirks (read before starting)

See `references/discord-api-quirks.md` for full details. Quick summary:

1. **Bots CANNOT create guilds** — `POST /guilds` returns 403 "Bots cannot use this endpoint". The user must create the server manually and invite the bot.
2. **User-Agent header REQUIRED** — Cloudflare returns 403 (error 1010) without a proper `User-Agent` string. Use: `"DiscordBot (https://example.com, 1.0)"`
3. **@everyone role ID = guild ID** — the @everyone role shares the guild's ID.
4. **Channel type 5 (announcement) requires Community features** — use type 0 (text) as fallback.
5. **Role positions must be set in a single batch PATCH** — individual position changes don't stick.
6. **Rate limiting** — Discord returns HTTP 429 with `retry_after` (seconds). Always handle retries.

## Server Build Workflow

### Step 1: Discover the guild
```
GET /users/@me/guilds  →  list of guilds the bot is in
GET /guilds/{guild_id}  →  guild metadata
GET /guilds/{guild_id}/roles  →  existing roles
GET /guilds/{guild_id}/channels  →  existing channels
```

### Step 2: Create roles (bottom-up, then fix positions)
Create roles one by one via `POST /guilds/{guild_id}/roles`, then fix all positions in a single `PATCH /guilds/{guild_id}/roles` with a list of `{id, position}`.

### Step 3: Create categories
`POST /guilds/{guild_id}/channels` with `type: 4` (category). Save IDs for parenting channels.

### Step 4: Create channels
`POST /guilds/{guild_id}/channels` with `parent_id` set to category ID. Use `permission_overwrites` for private channels.

### Step 5: Configure guild security
`PATCH /guilds/{guild_id}` — set `verification_level`, `explicit_content_filter`, `default_message_notifications`.

### Step 6: Lock @everyone permissions
`PATCH /guilds/{guild_id}/roles/{guild_id}` — remove dangerous permissions (mass mention, admin, manage channels/roles).

### Step 7: Post welcome messages
`POST /channels/{channel_id}/messages` with embeds for start-here, rules, announcements.

### Step 8: Polish visuals (channel names + topics + slowmode)
After channels are created, rename them with emoji prefixes and improved topics:
- Use the `・` (katakana middle dot) separator: `🚀・start-here`, `💬・général`, `🎬・films`
- Categories: Title Case (`💬 Communauté`) not ALL CAPS (`💬 COMMUNAUTÉ`)
- Set slowmode on high-traffic channels: `rate_limit_per_user: 5` for off-topic, `3` for event chat
- Each channel gets a descriptive `topic` (shows in channel header)
- See `references/channel-polish-guide.md` for the full naming convention and topic templates

### Step 9: Post embed messages
Post rich embeds (not plain text) for:
- `start-here` — welcome message with numbered steps and channel mentions (`<#channel_id>`)
- `règles` — rules with `━━━` separators, sanctions section
- `annonces` — intro embed
- `roles` — role list with category separators

Embed best practices:
- Use `color` (hex int), `footer`, `timestamp` (ISO 8601)
- Channel mentions: `<#channel_id>` in embed descriptions
- Use `━━━━━━━━━━━━━━━━━━━━━━━━━━` as visual separators between sections
- Keep embeds under 6000 chars total

### Step 10: Create invite
`POST /channels/{channel_id}/invites` with `max_age: 0, max_uses: 0` for permanent unlimited invite.

## Permission Bit Reference

| Permission | Bit | Value |
|-----------|-----|-------|
| ViewChannel | 1<<10 | 1024 |
| SendMessages | 1<<11 | 2048 |
| ReadMessageHistory | 1<<16 | 65536 |
| ManageChannels | 1<<4 | 16 |
| ManageRoles | 1<<28 | 268435456 |
| Administrator | 1<<3 | 8 |
| MentionEveryone | 1<<17 | 131072 |
| KickMembers | 1<<1 | 2 |
| BanMembers | 1<<2 | 4 |
| ModerateMembers | 1<<40 | 1099511627776 |

## Channel Types

| Type | Name |
|------|------|
| 0 | Text |
| 2 | Voice |
| 4 | Category |
| 5 | Announcement (requires Community) |
| 15 | Forum |

## Security Baseline

- `verification_level: 2` — must be registered 5+ min
- `explicit_content_filter: 2` — scan all members
- `default_message_notifications: 1` — mentions only
- Lock @everyone: remove mass mention, admin, manage channels/roles
- Create private staff channels with permission overwrites (deny ViewChannel to @everyone)

## Pitfalls

- **Token in chat**: If the user shares a bot token in the chat, warn them to regenerate it after setup. Never store tokens in memory or skills.
- **Cloudflare 403**: Missing User-Agent → HTTP 403 "error code: 1010". This is NOT a token issue — add the header. Note: `curl` works by default (sends its own UA), but Python `urllib` does NOT — you must set it explicitly.
- **Wrong bot identity**: Users with multiple bots may give you the wrong client ID. Always verify with `GET /users/@me` before acting. In this session, I initially gave the wrong client ID (1437886424622282969 vs the correct 1437886424622829699 — transposed digits) and the user caught it.
- **Announcement channels**: `type: 5` fails with 400 if Community features aren't enabled. Fall back to `type: 0`.
- **Role position conflicts**: New roles all get position 1 by default. Must batch-update positions after creation.
- **Channel ordering**: Discord assigns positions automatically. Parent channels to categories via `parent_id`, not position.
- **Old default channel**: Discord creates a default `général`/`general` text channel. If you create your own with the same name, you'll have duplicates. Delete the old one by ID (the one with `parent_id: null`).

## Reference Files

- `references/discord-api-quirks.md` — detailed API gotchas, Cloudflare behavior, rate limiting patterns
- `references/channel-polish-guide.md` — emoji naming convention, topic templates, embed patterns
- `templates/server-setup.py` — reusable Python script for full server setup via REST API