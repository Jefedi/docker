---
name: los-galactique-dashboard
title: Los Galactique Dashboard
description: One-shot status report for Los Galactique — Pterodactyl server stats, Discord XP leaderboard, pending Seerr requests, Jellyfin now playing, Paymenter recent activity.
tags: [pterodactyl, discord, seerr, jellyfin, dashboard, gaming]
---

# Los Galactique Dashboard

Generate a complete status snapshot of the Los Galactique community infrastructure. Ideal for a daily check-in or on-demand report.

## Reference Files
- `references/jellyfin-remote-control.md` — Jellyfin remote playback control via MCP tools (pause/unpause workaround)

## Workflow

### 1. Pterodactyl Servers
List all servers via the **Application API** (the Client API returns empty for user-scoped keys):
```
mcp_pterodactyl_pterodactyl_application(method='GET', path='servers', query='{"include": "egg"}')
```
Parse to show: server name, limits (memory/cpu/disk), suspended state, egg name (game type).

### 2. Discord XP Leaderboard
Top members by XP:
```
mcp_cineverse_cineverse_bot_api(method='GET', path='leaderboard', query='{"limit": 5}', body='{}')
```
⚠️ **This connection is flaky** — the Cineverse MCP (SSE bridge via n8n.jefe.ovh) may return connection errors. Always check if the result is an error. If it fails, **silently skip** the section (no "[ERROR]" markers, no asking the user to fix).

### 3. Seerr Pending Requests
Show pending media requests:
```
mcp_seerr_seerr_api(method='GET', path='request', query='{"take":10,"filter":"pending","sort":"added"}', body='{}')
```

### 4. Jellyfin Now Playing
What's currently being watched. The output is ~316KB — always parse with a Python script:
```
mcp_jellyfin_jellyfin_get_now_playing()
```

**Parse the output** (output saved to `/tmp/hermes-results/call_*.txt`):
```bash
python3 << 'PYEOF'
import json
with open('/tmp/hermes-results/call_<filename>.txt') as f:
    raw = f.read()
data = json.loads(raw)
items = json.loads(data['result'])
for item in items:
    now = item.get('NowPlayingItem', {})
    user = item.get('UserName', '?')
    device = item.get('DeviceName', '?')
    client = item.get('Client', '?')
    name = now.get('Name', '?')
    series = now.get('SeriesName', 'N/A')
    season = now.get('SeasonName', 'N/A')
    idx = now.get('IndexNumber', '?')
    pos = item.get('PlayState', {}).get('PositionTicks', 0)
    mins = pos // 600000000 if pos else 0
    paused = item.get('PlayState', {}).get('IsPaused', False)
    session_id = item.get('Id', '?')
    
    print(f"User: {user} | Device: {device} ({client})")
    if series != 'N/A':
        print(f"Playing: {series} - {season} Ep{idx} — {name}")
    else:
        print(f"Playing: {name}")
    print(f"Position: {mins}min {'⏸' if paused else '▶'} | Session: {session_id}")
PYEOF
```

### 5. Paymenter Recent Activity
Recent orders/invoices:
```
mcp_paymenter_paymenter_admin(method='GET', path='orders', query='{"per_page":5,"sort":"-created_at"}', body='{}')
```

## Output Format
Clean Telegram message with sections:
- 🎮 **Serveurs** — name, status, cpu/mem usage
- 🏆 **Top XP** — top 5 Discord members
- 🎬 **Demandes en attente** — pending Seerr requests
- 📺 **En cours** — Jellyfin now playing
- 💳 **Activité récente** — Paymenter orders

## Pitfalls
- **Pterodactyl**: use Application API (`mcp_pterodactyl_pterodactyl_application`) with `path='servers'`. The Client API (`mcp_pterodactyl_pterodactyl_client`) returns empty for user-scoped keys — never use it for server listing.
- **Discord Cineverse bot failure**: The MCP connection (`n8n.jefe.ovh/mcp/discord/sse`) is flaky — may return connection errors. Always catch and skip the section gracefully with no fanfare. Don't block the report or ask the user to fix it; just omit the section.
- **Jellyfin get_now_playing output is ~316KB** — always parse with Python/tools to extract key fields (session id, user name, paused state, position, item name/series/episode). Don't read raw output. Use `terminal()` with a Python heredoc or `execute_code()` to parse the saved file. The filename under `/tmp/hermes-results/` is unpredictable — pipe the tool output directly to parsing python to avoid filename guessing: run the tool, then immediately `terminal()` with `ls -t /tmp/hermes-results/ | head -1 | xargs -I{} cat /tmp/hermes-results/{} | python3 -c "..."`.
- **Paymenter recent activity**: The orders list returns historical data ordered by `-created_at`. If the latest order is weeks old, that's normal — just report "période calme" rather than flagging it as a problem.
- If a service is down, note it but don't block the whole report
- Keep it compact — Jefe prefers bullet lists, not novels
- Filter out empty sections (e.g. "no pending requests" = skip that section)
- **`send_command` with "Pause" fails** on Jellyfin Media Player (400 validation error). Use write_api `POST Sessions/{id}/Playing/Pause` instead. See `references/jellyfin-remote-control.md`.
