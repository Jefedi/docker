# Discord REST API Quirks & Gotchas

Learned from building a Discord server via REST API (Python stdlib only).

## Cloudflare 403 "error code: 1010"

**Symptom**: All API calls return HTTP 403 with body "error code: 1010", even with a valid bot token.

**Root cause**: Cloudflare (Discord's CDN) blocks requests without a proper `User-Agent` header. Python's `urllib` sends `Python-urllib/3.x` which gets blocked.

**Fix**: Add a Discord-compliant User-Agent header:
```python
headers = {
    "Authorization": f"Bot {token}",
    "User-Agent": "DiscordBot (https://yourdomain.com, 1.0)",
    "Content-Type": "application/json",
}
```

The format Discord expects: `DiscordBot (url, version)`. Without it, Cloudflare returns 1010 for ALL endpoints — including `GET /users/@me`. This is NOT a token validity issue.

**The first `curl` call works** because curl sends its own User-Agent. But `urllib.request` in Python does NOT unless you set it explicitly. This makes the token appear valid when tested via curl but broken when used in Python.

## Bots Cannot Create Guilds

`POST /guilds` returns HTTP 400 with `{"message": "Bots cannot use this endpoint", "code": 20001}`.

This is a Discord API limitation — only user accounts (not bots) can create guilds. The user must:
1. Create the server manually in Discord
2. Generate a bot invite URL with `applications.commands` + required permissions
3. Invite the bot to the server
4. Share the server invite link (or the guild ID) with you

## Announcement Channels (type 5)

`POST /guilds/{guild_id}/channels` with `type: 5` returns HTTP 400 "Invalid Form Body" if the server doesn't have Community features enabled.

Community features require: `GET /guilds/{guild_id}/preview` to work (needs rules channel + announcements channel set up first). Chicken-and-egg situation.

**Workaround**: Create as `type: 0` (text) first. The server owner can convert it to an announcement channel later in Discord settings after enabling Community.

## Role Position Batch Update

When you create multiple roles via `POST /guilds/{guild_id}/roles`, they ALL get position 1 by default. Individual `PATCH /guilds/{guild_id}/roles/{role_id}` with a `position` field does NOT reliably set the position.

**Fix**: Use `PATCH /guilds/{guild_id}/roles` with a JSON array of `{"id": "role_id", "position": N}` for ALL roles at once. Discord resolves the full hierarchy from the batch.

```python
positions = [
    {"id": bot_role_id, "position": 10},
    {"id": fondateur_id, "position": 9},
    {"id": admin_id, "position": 8},
    # ... all roles
]
requests.patch(f"{BASE}/guilds/{guild_id}/roles", json=positions)
```

## Rate Limiting

Discord API rate limits return HTTP 429 with:
```json
{
  "retry_after": 0.5,
  "global": false,
  "message": "You are being rate limited."
}
```

- `retry_after` is in **seconds** (float), not milliseconds
- `global: true` means the global rate limit (all endpoints) is hit
- Always implement retry logic with exponential backoff
- Channel creation hits rate limits after ~5 rapid calls — add 0.5s delay between calls

## Permission Overwrites

Permission overwrites are per-channel, NOT per-category. Setting an overwrite on a category does NOT propagate to child channels automatically.

Format:
```json
{
  "id": "role_id_or_user_id",
  "type": 0,  // 0 = role, 1 = member
  "allow": "1024",  // ViewChannel — as STRING not int
  "deny": "2048"    // SendMessages — as STRING not int
}
```

**Critical**: Permission values must be **strings** in the JSON payload, not integers.

## @everyone Role ID

The @everyone role's ID is the same as the guild ID. To modify @everyone permissions:
```
PATCH /guilds/{guild_id}/roles/{guild_id}
```

## Deleting the Default Channel

When a guild is created, Discord auto-creates a text channel (usually "general" or "général"). If you create your own channel with the same name, you'll have duplicates.

To identify and delete the old one:
1. `GET /guilds/{guild_id}/channels`
2. Find channels with `parent_id: null` and the same name
3. `DELETE /guilds/{guild_id}/channels/{channel_id}`

## Bot Role Position

The bot's role (auto-created when the bot joins) must be positioned ABOVE the roles it needs to manage. If the bot role is at position 1 and you try to create roles at position 2+, the API may silently fail or the bot may lack permissions to manage those roles.

**Fix**: After creating all roles, batch-update positions with the bot's role at the top.