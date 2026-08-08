#!/usr/bin/env python3
"""Check if léoytb replied in the DM channel. Silent if nothing new."""

import json, os, sys
import urllib.request

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    token_file = os.path.join(os.path.dirname(__file__), ".discord_token")
    if os.path.exists(token_file):
        TOKEN = open(token_file).read().strip()
if not TOKEN:
    sys.exit(0)

LEOYTB_ID = "806559854851784815"
LEOYTB_DM = "1510929495295791155"

req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{LEOYTB_DM}/messages?limit=10",
    headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "DiscordBot (Hermes Cron)",
    },
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        messages = json.loads(resp.read())
except Exception:
    sys.exit(0)

replies = [m for m in messages if m.get("author", {}).get("id") == LEOYTB_ID]
if not replies:
    sys.exit(0)

for msg in reversed(replies):
    ts = msg.get("timestamp", "?")[:10]
    content = msg.get("content", "")
    print(f"💬 **léoytb a répondu** ({ts}):")
    if content:
        print(f"> {content}")
    if msg.get("embeds"):
        print("  (embed inclus)")
    for att in msg.get("attachments", []):
        print(f"  📎 {att.get('filename', 'fichier')}")

print(f"\n📩 https://discord.com/channels/@me/{LEOYTB_DM}")
