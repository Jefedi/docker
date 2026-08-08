import urllib.request, json, time, urllib.error

import os
BOT_TOKEN = open("/opt/data/scripts/.discord_token_cleanup").read().strip()
HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (https://trakii.tv, 1.0)",
}
BASE = "https://discord.com/api/v10"
GUILD_ID = "1415049639476072530"

def api(method, endpoint, data=None):
    url = f"{BASE}{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            c = resp.read().decode()
            return json.loads(c) if c else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "body": e.read().decode()[:200]}
    except Exception as e:
        return {"_error": str(e)}

# Empty channels to delete
empty = [
    ("1493461377451294820", "pangolin-logs"),
    ("1497664915903742063", "pocketid"),
    ("1497664916860174376", "vaultwarden"),
    ("1497664917925531798", "headscale"),
    ("1497664918944616459", "anonaddy"),
    ("1497664948904394817", "librespeed"),
    ("1497664951307993253", "freshrss"),
    ("1497664980307280033", "qbittorrent"),
    ("1497665005192220823", "immich"),
    ("1497665055058034852", "script"),
]

print("=== Deleting empty channels ===")
for cid, name in empty:
    r = api("DELETE", f"/channels/{cid}")
    ok = not (isinstance(r, dict) and r.get("_error"))
    print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    time.sleep(0.5)

# Delete Security category (all channels gone)
print("\n=== Deleting Security category ===")
r = api("DELETE", "/channels/1497664914410704968")
ok = not (isinstance(r, dict) and r.get("_error"))
print(f"  [{'OK' if ok else 'FAIL'}] Security category")

time.sleep(0.5)

# Create notif-ia channel in Bot & Sync category
print("\n=== Creating notif-ia channel ===")
r = api("POST", f"/guilds/{GUILD_ID}/channels", {
    "name": "notif-ia",
    "type": 0,
    "parent_id": "1471581568244908123",
    "topic": "Notifications Hermes Agent",
})
nid = r.get("id", "?")
print(f"  Created (ID: {nid})")

time.sleep(0.5)

# Post first message
print("\n=== Posting first message ===")
r = api("POST", f"/channels/{nid}/messages", {
    "embeds": [{
        "title": "Hermes Agent connecte",
        "description": "Channel de notifications operationnel. Je posterai ici mes alertes et rapports.",
        "color": 65280,
        "footer": {"text": "Hermes Agent - Jefe ALL"}
    }]
})
mid = r.get("id", "?")
print(f"  Message sent (ID: {mid})")

print("\n=== Done ===")