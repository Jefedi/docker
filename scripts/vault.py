import json,urllib.request,urllib.parse,hashlib,base64,hmac as H,struct
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.backends import default_backend as D

P = "wkngNxKh5s2dw*9s%1TSh%Dm@l8jQEV6Cy%*Ve&!6SbbzPYUHUAXQ2#4YNix^pulfroZ3S*ICVW8k0FW64f3l!X*mn^cbbSuhg#9TNHwTxjfbb#2k!l1!04pmdx^pfRS"
E = "hermesagent@jefe.ovh"
S = "https://vault.jefe.al"

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
se = dk[:32]; sm = dk[32:64]

def dec(s):
    if not s or "|" not in s:
        return s or ""
    try:
        ps = s.split("|")
        iv2 = base64.b64decode(ps[0].split(".")[1])
        ct2 = base64.b64decode(ps[1])
        cc = Cipher(algorithms.AES(se), modes.CBC(iv2), backend=D()).decryptor()
        pp = cc.update(ct2) + cc.finalize()
        return pp[:-pp[-1]].decode("utf-8", "replace")
    except Exception as e:
        return f"[err:{e}]"

r2 = urllib.request.urlopen(urllib.request.Request(
    S + "/api/ciphers",
    headers={"Authorization": f"Bearer {at}"}), timeout=15)
items = json.loads(r2.read()).get("data", [])

for item in items:
    n = dec(item.get("name", ""))
    t = item.get("type", "?")
    l = item.get("login", {}) or {}
    u = dec(l.get("username", ""))
    pw = dec(l.get("password", ""))
    no = dec(item.get("notes", ""))
    ur = [dec(x.get("uri", "")) for x in (l.get("uris", []) or []) if x.get("uri")]
    fs = item.get("fields", []) or []
    txt = (n + " " + u + " " + no + " " + " ".join(ur)).lower()
    print(f"[type={t}] {n}")
    if u: print(f"  user: {u}")
    if pw: print(f"  pass: {pw}")
    if ur: print(f"  uris: {ur}")
    if no: print(f"  notes: {no[:500]}")
    for f in fs:
        fn = dec(f.get("name", ""))
        fv = dec(f.get("value", ""))
        if fn or fv:
            print(f"  field {fn}: {fv}")
    if "n8n" in txt:
        print("  >>> N8N MATCH <<<")
    print()