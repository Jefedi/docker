# Register Telegram Slash Commands for MCP Tools

How to wire a Telegram bot command (like `/dl`) to an MCP tool so the command appears in Telegram's autocomplete and triggers the right action.

## Architecture (Two Approaches)

### ❌ Skill-only approach (DOES NOT WORK)

A skill telling Hermes "when you see `/dl`, use the MCP tool" fails because the **gateway intercepts unknown commands before the LLM is invoked**. The code at `gateway/run.py:7801` checks `GATEWAY_KNOWN_COMMANDS` and returns "Unknown command" if the command isn't registered. The skill never fires.

### ✅ Plugin approach (WORKS)

```
Telegram: /dl <url>
    │
    ▼
Hermes Gateway → checks quick_commands → NO
                → checks plugin commands → YES → _dl_handler(url)
                    │
                    ▼
              Calls service API directly
              (via docker exec or HTTP)
                    │
                    ▼
              Returns result string
```

A plugin registers a command handler at the gateway level, bypassing the LLM entirely. Fast and reliable.

---

## Step 1: Create the Plugin

Structure:
```
~/.hermes/plugins/dl-video/
  └── __init__.py
```

`~/.hermes/plugins/dl-video/__init__.py`:
```python
from __future__ import annotations
import json, logging, os, subprocess

logger = logging.getLogger(__name__)

MANIFEST = {
    "name": "dl-video",
    "version": "1.0.0",
    "description": "Commande /dl pour télécharger des vidéos via MeTube",
}

async def _dl_handler(raw_args: str) -> str:
    url = raw_args.strip()
    if not url:
        return "Usage: `/dl <url>`"
    if not url.startswith(("http://", "https://")):
        return f"❌ URL invalide: {url}"
    try:
        cmd = ["docker", "exec", "pangolin-cli", "curl", "-sk", "-X", "POST",
               "https://metube.jefe.al/add",
               "-H", "Content-Type: application/json",
               "-d", json.dumps({"url": url, "quality": "best"}), "--max-time", "60"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=65)
        response = json.loads(result.stdout)
        if response.get("status") == "ok":
            return f"✅ Vidéo ajoutée !"
        return f"⚠️ Réponse: {response}"
    except Exception as e:
        return f"❌ Erreur: {e}"

def register(ctx) -> None:
    ctx.register_command(
        name="dl",
        handler=_dl_handler,
        description="Télécharger une vidéo (ex: /dl https://youtu.be/xxx)",
        args_hint="<url>",
    )
```

Full working example: see `references/plugins/dl-video-plugin.py`.

## Step 2: Enable the Plugin

Add to `~/.hermes/config.yaml`:
```yaml
plugins:
  enabled:
    - dl-video
```

## Step 3: Register with Telegram API

Use `setMyCommands`:
```python
import requests
token = "YOUR_BOT_TOKEN"

# Always get existing commands first (setMyCommands overwrites!)
existing = requests.get(f"https://api.telegram.org/bot{token}/getMyCommands").json()
commands = existing.get("result", [])
commands.append({"command": "dl", "description": "Télécharger une vidéo (ex: /dl https://youtu.be/xxx)"})

for scope in ["all_private_chats", "all_group_chats", "default"]:
    requests.post(f"https://api.telegram.org/bot{token}/setMyCommands",
                  json={"commands": commands, "scope": {"type": scope}})
```

## Step 4: Restart Gateway

```bash
hermes gateway restart
```

## Gateway Command Dispatch Order

The gateway checks commands in this order (see `gateway/run.py`):

1. **Built-in commands** — `/new`, `/help`, `/stop`, `/restart`
2. **Quick commands** — `config.yaml:quick_commands`
3. ⭐ **Plugin commands** — `ctx.register_command()` ⭐ This is where `/dl` is caught
4. Bundle/skill commands
5. ❌ **Unknown command error** — if none of the above matched

Plugin commands (#3) run BEFORE the unknown-command check. Skills live at #4, which is AFTER the gate — that's why skills alone can't handle unrecognized commands.

## Pitfalls

- **`setMyCommands` overwrites, doesn't merge.** Always get existing commands first.
- **No gateway restart after adding a plugin?** It won't load.
- **Handler signature**: `fn(raw_args: str) -> str | None`. Return `None` to fall through silently.
- **`register()` function** is the entry point. Must accept a single `ctx` argument.
- **Command names** can't contain hyphens in Telegram's API. Hermes normalizes internally.
- **Handler can be sync or async** — gateway dispatch handles both.
