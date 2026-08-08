import sqlite3, json, base64, hashlib, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# n8n encryption key
key = "jM3O6Po9Oo8BS5yk1wvdmSEH8Unps1Ug"

# n8n uses AES-256-CBC with the key as the encryption key
# The encrypted format is: "Salted__" + 8 bytes salt + ciphertext
# Actually n8n uses a simpler approach - let's decrypt

conn = sqlite3.connect('/opt/data/scripts/n8n_db.sqlite')
c = conn.cursor()
c.execute("SELECT id, name, type, data FROM credentials_entity WHERE type = 'telegramApi'")
rows = c.fetchall()

for r in rows:
    cred_id, name, cred_type, encrypted_data = r
    print(f"ID: {cred_id}, Name: {name}")
    
    # n8n stores encrypted data as base64
    raw = base64.b64decode(encrypted_data)
    
    # n8n uses AES-256-CBC
    # The key derivation: SHA-256 of the encryption key
    key_bytes = hashlib.sha256(key.encode()).digest()
    
    # First 8 bytes are "Salted__", next 8 are salt
    if raw[:8] == b'Salted__':
        salt = raw[8:16]
        ciphertext = raw[16:]
        
        # Derive key and IV using OpenSSL EVP_BytesToKey
        # MD5 based key derivation
        d = b''
        d_i = b''
        while len(d) < 48:
            d_i = hashlib.md5(d_i + key_bytes + salt).digest()
            d += d_i
        
        derived_key = d[:32]
        iv = d[32:48]
        
        cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(plaintext) + unpadder.finalize()
        
        data = json.loads(plaintext)
        print(f"Decrypted: {json.dumps(data, indent=2)}")
    else:
        print(f"Unknown format: {raw[:20]}")

conn.close()