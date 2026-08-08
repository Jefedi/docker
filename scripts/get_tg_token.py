import sqlite3, json
conn = sqlite3.connect('/opt/data/scripts/n8n_db.sqlite')
c = conn.cursor()
# Get Telegram credentials
c.execute("SELECT id, name, type, data FROM credentials_entity WHERE type LIKE '%telegram%'")
rows = c.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Name: {r[1]}, Type: {r[2]}')
    try:
        data = json.loads(r[3])
        for key, val in data.items():
            if val and isinstance(val, str) and len(val) > 10:
                print(f'  {key}: {val[:30]}...')
    except:
        print(f'  raw: {str(r[3])[:100]}')
conn.close()