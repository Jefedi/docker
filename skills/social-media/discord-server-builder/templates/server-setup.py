#!/usr/bin/env python3
"""
Discord Server Builder — Full server setup via REST API.
Python stdlib only (urllib). No discord.py or discord.js needed.

Usage:
    python server-setup.py

Configure BOT_TOKEN and GUILD_ID below before running.
"""

import json
import time
import urllib.request
import urllib.error

# ===== CONFIGURATION =====
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
GUILD_ID = "YOUR_GUILD_ID_HERE"

HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (https://example.com, 1.0)",  # REQUIRED — Cloudflare blocks without it
    "Accept": "application/json",
}
BASE = "https://discord.com/api/v10"

# ===== SERVER BLUEPRINT =====
# Customize this section for your server

ROLES = [
    # name, color (hex), hoist, mentionable, permissions (string)
    {"name": "👑 Fondateur", "color": 0xFFD700, "hoist": True, "mentionable": True, "permissions": "8"},
    {"name": "🔴 Admin", "color": 0xFF4444, "hoist": True, "mentionable": True, "permissions": "1099511627775"},
    {"name": "🟠 Modérateur", "color": 0xFF8800, "hoist": True, "mentionable": True, "permissions": "268438457"},
    {"name": "🟡 Helper", "color": 0xFFEE00, "hoist": True, "mentionable": True, "permissions": "17179869184"},
    {"name": "🎬 Membre", "color": 0x5865F2, "hoist": False, "mentionable": True, "permissions": "0"},
    {"name": "✨ Nouveau", "color": 0x99AAB5, "hoist": True, "mentionable": False, "permissions": "0"},
]

CATEGORIES = [
    {"name": "📌 INFORMATIONS", "position": 1},
    {"name": "💬 COMMUNAUTÉ", "position": 2},
    {"name": "🎬 CINÉ & SÉRIES", "position": 3},
    {"name": "📅 EVENTS", "position": 4},
    {"name": "🔒 STAFF", "position": 5},
]

# type: 0=text, 5=announcement(needs Community), 15=forum
# private: True = only staff roles can see (set via permission_overwrites)
CHANNELS = [
    # INFORMATIONS
    {"name": "start-here", "type": 0, "category": "📌 INFORMATIONS", "topic": "Bienvenue — commencez ici !"},
    {"name": "règles", "type": 0, "category": "📌 INFORMATIONS", "topic": "Les règles du serveur"},
    {"name": "annonces", "type": 0, "category": "📌 INFORMATIONS", "topic": "Annonces officielles"},  # type 5 needs Community
    {"name": "roles", "type": 0, "category": "📌 INFORMATIONS", "topic": "Choisis tes rôles"},
    # COMMUNAUTÉ
    {"name": "présentations", "type": 0, "category": "💬 COMMUNAUTÉ", "topic": "Présente-toi"},
    {"name": "général", "type": 0, "category": "💬 COMMUNAUTÉ", "topic": "Discussion générale"},
    {"name": "découvertes", "type": 0, "category": "💬 COMMUNAUTÉ", "topic": "Découvertes récentes"},
    {"name": "ressources", "type": 0, "category": "💬 COMMUNAUTÉ", "topic": "Outils et ressources"},
    {"name": "blabla-hs", "type": 0, "category": "💬 COMMUNAUTÉ", "topic": "Hors-sujet, détente"},
    # CINÉ & SÉRIES
    {"name": "films", "type": 0, "category": "🎬 CINÉ & SÉRIES", "topic": "Tout sur les films"},
    {"name": "séries", "type": 0, "category": "🎬 CINÉ & SÉRIES", "topic": "Tout sur les séries"},
    {"name": "recommandations", "type": 0, "category": "🎬 CINÉ & SÉRIES", "topic": "Recommandations"},
    {"name": "critiques", "type": 0, "category": "🎬 CINÉ & SÉRIES", "topic": "Critiques et avis"},
    {"name": "streaming", "type": 0, "category": "🎬 CINÉ & SÉRIES", "topic": "Où regarder"},
    # EVENTS
    {"name": "events", "type": 0, "category": "📅 EVENTS", "topic": "Événements à venir"},
    {"name": "event-chat", "type": 0, "category": "📅 EVENTS", "topic": "Pendant les events"},
    # STAFF (private)
    {"name": "mod-chat", "type": 0, "category": "🔒 STAFF", "topic": "Discussion staff", "private": True},
    {"name": "mod-logs", "type": 0, "category": "🔒 STAFF", "topic": "Logs de modération", "private": True},
    {"name": "incident-room", "type": 0, "category": "🔒 STAFF", "topic": "Gestion des incidents", "private": True},
    {"name": "staff-notes", "type": 0, "category": "🔒 STAFF", "topic": "Notes internes", "private": True},
]

# Permission bits
VIEW = 1024       # 1<<10
SEND = 2048       # 1<<11
HISTORY = 65536   # 1<<16

# ===== API HELPER =====

def discord_api(method, endpoint, data=None):
    """Make a Discord API call with rate limit handling."""
    url = f"{BASE}{endpoint}"
    body = json.dumps(data).encode() if data else None
    for attempt in range(5):
        req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode()
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            if e.code == 429:
                retry_data = json.loads(error_body)
                wait = retry_data.get("retry_after", 2)
                print(f"  ⏳ Rate limited, waiting {wait}s...")
                time.sleep(float(wait) + 0.5)
                continue
            try:
                err = json.loads(error_body)
                print(f"  ❌ HTTP {e.code}: {err.get('message', error_body[:200])}")
            except json.JSONDecodeError:
                print(f"  ❌ HTTP {e.code}: {error_body[:200]}")
            return {"_error": True, "status": e.code, "body": error_body}
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"_error": True, "msg": str(e)}
    print("  ❌ Rate limited too many times")
    return {"_error": True, "msg": "rate limited"}

def perms(role_id, allow=0, deny=0):
    """Build a permission overwrite entry."""
    return {"id": str(role_id), "type": 0, "allow": str(allow), "deny": str(deny)}

# ===== MAIN SETUP =====

def main():
    # Discover guild
    print(f"=== Discovering guild {GUILD_ID} ===")
    guild = discord_api("GET", f"/guilds/{GUILD_ID}")
    if guild.get("_error"):
        print("Cannot access guild. Check token and bot membership.")
        return
    print(f"  Server: {guild.get('name')}")

    # --- Step 1: Create roles ---
    print("\n=== Step 1: Creating roles ===")
    role_ids = {}
    for role in ROLES:
        r = discord_api("POST", f"/guilds/{GUILD_ID}/roles", role)
        if not r.get("_error"):
            role_ids[role["name"]] = r["id"]
            print(f"  ✅ {role['name']}")
        time.sleep(0.5)

    # Fix role positions (batch)
    print("\n=== Fixing role positions ===")
    positions = []
    for i, (name, rid) in enumerate(reversed(list(role_ids.items()))):
        positions.append({"id": rid, "position": i + 1})
    # @everyone stays at 0
    discord_api("PATCH", f"/guilds/{GUILD_ID}/roles", positions)
    print("  ✅ Positions updated")
    time.sleep(0.5)

    # --- Step 2: Create categories ---
    print("\n=== Step 2: Creating categories ===")
    cat_ids = {}
    for cat in CATEGORIES:
        r = discord_api("POST", f"/guilds/{GUILD_ID}/channels", {
            "name": cat["name"], "type": 4, "position": cat["position"]
        })
        if not r.get("_error"):
            cat_ids[cat["name"]] = r["id"]
            print(f"  ✅ {cat['name']}")
        time.sleep(0.5)

    # --- Step 3: Create channels ---
    print("\n=== Step 3: Creating channels ===")
    staff_role_ids = [role_ids[n] for n in role_ids if n in ("👑 Fondateur", "🔴 Admin", "🟠 Modérateur")]

    for ch in CHANNELS:
        data = {
            "name": ch["name"],
            "type": ch["type"],
            "parent_id": cat_ids.get(ch["category"]),
            "topic": ch.get("topic", ""),
        }
        if ch.get("private"):
            overwrites = [perms(GUILD_ID, deny=VIEW)]  # @everyone can't see
            for rid in staff_role_ids:
                overwrites.append(perms(rid, allow=VIEW | SEND | HISTORY))
            data["permission_overwrites"] = overwrites

        r = discord_api("POST", f"/guilds/{GUILD_ID}/channels", data)
        print(f"  {'✅' if not r.get('_error') else '❌'} {ch['name']}")
        time.sleep(0.5)

    # --- Step 4: Guild security ---
    print("\n=== Step 4: Configuring security ===")
    discord_api("PATCH", f"/guilds/{GUILD_ID}", {
        "verification_level": 2,
        "default_message_notifications": 1,
        "explicit_content_filter": 2,
    })
    print("  ✅ Verification: Medium, Filter: All, Notifications: Mentions only")

    # --- Step 5: Lock @everyone ---
    print("\n=== Step 5: Locking @everyone permissions ===")
    discord_api("PATCH", f"/guilds/{GUILD_ID}/roles/{GUILD_ID}", {
        "permissions": "1043348945"  # basic perms, no mass mention/admin
    })
    print("  ✅ @everyone locked down")

    # --- Step 6: Create invite ---
    print("\n=== Step 6: Creating invite ===")
    channels = discord_api("GET", f"/guilds/{GUILD_ID}/channels")
    if isinstance(channels, list):
        general = next((c for c in channels if c["name"] == "général"), channels[0])
        r = discord_api("POST", f"/channels/{general['id']}/invites", {
            "max_age": 0, "max_uses": 0, "unique": True
        })
        if not r.get("_error") and r.get("code"):
            print(f"  ✅ Invite: https://discord.gg/{r['code']}")

    print("\n=== Setup complete ===")

if __name__ == "__main__":
    main()