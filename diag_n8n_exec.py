import sqlite3, json, base64, hashlib, subprocess
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

conn = sqlite3.connect('/tmp/n8n.db')
cur = conn.cursor()

enc_key = "jM3O6Po9Oo8BS5yk1wvdmSEH8Unps1Ug"

def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    d = b''
    d_i = b''
    while len(d) < key_len + iv_len:
        d_i = hashlib.md5(d_i + password + salt).digest()
        d += d_i
    return d[:key_len], d[key_len:key_len+iv_len]

def decrypt_cred(cred_id, cred_name):
    cur.execute("SELECT data FROM credentials_entity WHERE id = ?", (cred_id,))
    row = cur.fetchone()
    raw = base64.b64decode(row[0])
    salt = raw[8:16]
    ciphertext = raw[16:]
    key, iv = evp_bytes_to_key(enc_key.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ciphertext), 16)
    data = json.loads(pt.decode())
    print(f"\n=== {cred_name} ===")
    for k, v in data.items():
        if 'key' in k.lower() or 'token' in k.lower():
            print(f"  {k}: {str(v)[:10]}...{str(v)[-4:]}")
        else:
            print(f"  {k}: {v}")
    return data

d1 = decrypt_cred('NsGhLqRNaBIupFQo', 'Hermes llm')
d2 = decrypt_cred('7e8xyH8CsQyQcKus', 'Hermes API')
d3 = decrypt_cred('PC1vUpuahYbxpgom', 'Litel LM')

conn.close()