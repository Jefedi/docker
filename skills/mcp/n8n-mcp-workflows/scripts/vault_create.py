#!/usr/bin/env python3
"""Create items in Vaultwarden via the Bitwarden API.

Usage:
    python3 vault_create.py "Item Name" --password "secret" [--username user] [--notes "text"] [--uri url]

Requires: cryptography (install via: uv venv /tmp/venv && source /tmp/venv/bin/activate && uv pip install cryptography)

The master password is hardcoded for the Hermes agent account.
Items created via API do NOT have item-level keys (simpler decryption).
Client sync required after creation to see items in UI/mobile app.
"""
import json, urllib.request, urllib.parse, hashlib, base64, hmac as H, struct, os, argparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend as D

P = "wkngNxKh5s2dw*9s%1TSh%Dm@l8jQEV6Cy%*Ve&!6SbbzPYUHUAXQ2#4YNix^pulfroZ3S*ICVW8k0FW64f3l!X*mn^cbbSuhg#9TNHwTxjfbb#2k!l1!04pmdx^pfRS"
E = "hermesagent@jefe.ovh"
S = "https://vault.jefe.al"

# ── Login ──
mk = hashlib.pbkdf2_hmac("sha256", P.encode(), E.encode(), 600000, 32)
mph = hashlib.pbkdf2_hmac("sha256", mk, P.encode(), 1, 32)
ld = urllib.parse.urlencode({
    "grant_type": "password", "username": E,
    "password": base64.b64encode(mph).decode(),
    "scope": "api offline_access", "client_id": "cli",
    "deviceType": "14", "deviceIdentifier": "h", "deviceName": "h"
}).encode()
r = urllib.request.urlopen(urllib.request.Request(
    S + "/identity/connect/token", data=ld,
    headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=15)
lg = json.loads(r.read())
at = lg["access_token"]

# ── Derive keys ──
def hk(k, i, n=32):
    t = b""; o = b""; x = 1
    while len(o) < n:
        t = H.new(k, t + i + struct.pack("B", x), hashlib.sha256).digest()
        o += t; x += 1
    return o[:n]

ek = hk(mk, b"enc")
p = lg["Key"].split("|")
iv = base64.b64decode(p[0].split(".")[1])
ct = base64.b64decode(p[1])
c = Cipher(algorithms.AES(ek), modes.CBC(iv), backend=D()).decryptor()
pd = c.update(ct) + c.finalize()
dk = pd[:-pd[-1]]
se = dk[:32]  # symmetric encryption key

# ── Encryption helper ──
def enc(plaintext):
    iv = os.urandom(16)
    pt = plaintext.encode("utf-8")
    pad = 16 - (len(pt) % 16)
    pt += bytes([pad] * pad)
    cipher = Cipher(algorithms.AES(se), modes.CBC(iv), backend=D())
    e = cipher.encryptor()
    ct = e.update(pt) + e.finalize()
    return f"2.{base64.b64encode(iv).decode()}|{base64.b64encode(ct).decode()}"

# ── Create cipher ──
def create_item(name, password, username="", notes="", uris=None):
    cipher_data = {
        "type": 1,
        "name": enc(name),
        "notes": enc(notes) if notes else None,
        "login": {
            "username": enc(username) if username else None,
            "password": enc(password),
            "uris": [{"uri": enc(u)} for u in uris] if uris else []
        },
        "secureNote": None, "card": None, "identity": None,
        "favorite": False, "fields": []
    }
    req = urllib.request.Request(
        S + "/api/ciphers",
        data=json.dumps(cipher_data).encode(),
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read()).get("id", "unknown")
    except Exception as e:
        return f"ERROR: {e}"

# ── CLI ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Vaultwarden item")
    parser.add_argument("name", help="Item name")
    parser.add_argument("--password", required=True, help="Password/secret value")
    parser.add_argument("--username", default="", help="Username (optional)")
    parser.add_argument("--notes", default="", help="Notes (optional)")
    parser.add_argument("--uri", default="", help="URI (optional)")
    args = parser.parse_args()

    uris = [args.uri] if args.uri else None
    item_id = create_item(args.name, args.password, args.username, args.notes, uris)
    print(f"Created: {args.name} -> {item_id}")
    print("NOTE: Force-sync your Vaultwarden client to see the new item.")