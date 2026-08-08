# Discord MCP Server Reference

FastMCP server wrapping Discord REST API v10 with Bot token auth.

## Auth

```
Authorization: Bot <token>
Base URL: https://discord.com/api/v10
User-Agent: DiscordBot (Hermes MCP, 1.0)
```

Store the token in Vaultwarden. Retrieve via:
```bash
bw login <email> --passwordfile /tmp/bw_pass.txt   # avoid shell escaping
bw get item "Bot mcp" | python3 -c "import sys,json; print(json.load(sys.stdin)['login']['password'])"
```

## Tool Surface (21 tools)

| Category | Tools |
|---|---|
| Bot Info | `bot_info`, `list_guilds`, `get_guild` |
| Members | `list_members`, `get_member`, `search_members`, `modify_member_nick` |
| Channels | `list_channels`, `get_channel`, `get_messages`, `send_message` |
| Roles | `list_roles`, `add_member_role`, `remove_member_role` |
| Moderation | `kick_member`, `ban_member`, `unban_member`, `list_bans` |
| Invites | `get_channel_invites`, `create_channel_invite` |
| DM | `create_dm` |

## Implementation Pattern

```python
from fastmcp import FastMCP
mcp = FastMCP("Discord")
API_BASE = "https://discord.com/api/v10"
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

def _headers():
    return {"Authorization": f"Bot {TOKEN}", "Accept": "application/json",
            "User-Agent": "DiscordBot (Hermes MCP, 1.0)"}

def _request(method, path, params=None, json_body=None):
    url = f"{API_BASE}/{path.lstrip('/')}"
    with httpx.Client(timeout=20, headers=_headers()) as client:
        resp = client.request(method, url, params=params, json=json_body)
        if resp.status_code == 429:
            time.sleep(resp.json().get("retry_after", 1) + 0.5)
            resp = client.request(method, url, params=params, json=json_body)
        resp.raise_for_status()
        return resp.json() if resp.content else {}
```

## Key Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/users/@me` | GET | Bot info |
| `/users/@me/guilds` | GET | List servers |
| `/guilds/{id}` | GET | Guild details |
| `/guilds/{id}/members` | GET | List members (paginate with `after`) |
| `/guilds/{id}/members/{uid}` | GET/DELETE/PATCH | Get/kick/modify member |
| `/guilds/{id}/members/search` | GET | Search by name |
| `/guilds/{id}/channels` | GET | List channels |
| `/channels/{id}` | GET | Channel info |
| `/channels/{id}/messages` | GET/POST | Get/send messages |
| `/guilds/{id}/roles` | GET | List roles |
| `/guilds/{id}/members/{uid}/roles/{rid}` | PUT/DELETE | Manage roles |
| `/guilds/{id}/bans/{uid}` | PUT/DELETE | Ban/unban |
| `/users/@me/channels` | POST | Create DM with `recipient_id` |

## Discord Cron Monitoring

For monitoring DM replies (e.g. payment reminder responses):
```python
# ~/.hermes/scripts/check-replies.py — no_agent=True cron
LEOYTB_ID = "user_id"
LEOYTB_DM = "dm_channel_id"
messages = _request("GET", f"/channels/{LEOYTB_DM}/messages?limit=10")
replies = [m for m in messages if m["author"]["id"] == LEOYTB_ID]
if replies:  # Only output if there's a reply (silent otherwise)
    for m in replies:
        print(f"💬 User replied: {m['content']}")
```

## Notes
- Discord API rate limits: 50 req/s per endpoint. 429 = retry after `retry_after` seconds.
- Bot user-agent required: Discord blocks requests without `User-Agent` header.
- Bot must have `GUILD_MEMBERS` intent to list members on larger servers.
- DM channels are persistent — create once, reuse the channel ID.
- The bot token starts with `MT...` format (3 base64 segments separated by dots).
- Register the server with: `hermes mcp add discord --command "python3" --args "discord_server.py" --env "DISCORD_BOT_TOKEN=<token>"`
- **Re-registration double prompt**: If the server already exists, `hermes mcp add` prompts twice: "Overwrite?" then "Enable all N tools?". Use `printf 'Y\nY\n'` instead of a single `echo "Y"` to auto-confirm both.
