# MCP Jellyfin Natif — Example FastMCP Server

This is a concrete example of a FastMCP server built using the methodology in the parent `build-mcp-servers` skill. It wraps the Jellyfin API with 46 tools, connecting via HTTPS through Pangolin.

## Connection

- **URL**: `https://jflix.jefe.al`
- **Auth**: Header `X-Emby-Token`
- **Token**: `~/.hermes/jellyfin_token.txt` or `JELLYFIN_TOKEN` env var

## Source File

`/root/.hermes/mcp/jellyfin_server.py`

## Tool Categories

| Category | Count | Examples |
|----------|-------|---------|
| System | 4 | `get_system_info`, `get_activity_log` |
| Users | 3 | `list_users`, `get_user`, `get_user_views` |
| Libraries | 2 | `list_libraries`, `get_virtual_folders` |
| Navigation & Search | 6 | `get_items`, `get_item`, `search_items` |
| History | 1 | `get_play_history` |
| Metadata | 3 | `list_genres`, `list_studios`, `list_persons` |
| Sessions & Remote | 4 | `get_now_playing`, `get_sessions`, `send_playback_command` |
| Watch Status | 4 | `mark_played`, `mark_unplayed`, `mark_favorite` |
| Library | 5 | `refresh_library`, `refresh_item`, `get_item_ancestors` |
| Series | 2 | `get_seasons`, `get_episodes` |
| Music | 2 | `list_artists`, `list_album_artists` |
| Live TV | 2 | `get_live_tv_channels`, `get_live_tv_guide` |
| Administration | 4 | `list_plugins`, `list_scheduled_tasks`, `list_devices` |
| Catch-all | 2 | `read_api` (GET anything), `write_api` (POST/PUT/DELETE) |

## Registration Command

```bash
printf 'Y\\nY\\n' | hermes mcp add jellyfin \\
  --command "/usr/local/lib/hermes-agent/venv/bin/python3" \\
  --args "/root/.hermes/mcp/jellyfin_server.py" \\
  --env "JELLYFIN_URL=https://jflix.jefe.al" \\
  --connect-timeout 30
```

## Key Design Patterns

- **Header-based auth**: Uses `X-Emby-Token` custom header (common pattern for self-hosted APIs)
- **Catch-all tools**: `read_api` and `write_api` for anything not covered by the 44 specific tools
- **Direct HTTPS**: No Docker tunnel needed — API is publicly accessible behind Pangolin
