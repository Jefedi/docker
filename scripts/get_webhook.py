import sqlite3
conn = sqlite3.connect('/opt/data/scripts/n8n_db.sqlite')
c = conn.cursor()
c.execute("PRAGMA table_info(webhook_entity)")
cols = [col[1] for col in c.fetchall()]
print(f"Columns: {cols}")
c.execute("SELECT * FROM webhook_entity LIMIT 5")
for r in c.fetchall():
    print(r)
conn.close()