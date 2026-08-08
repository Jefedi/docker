import sqlite3, json

conn = sqlite3.connect('/tmp/n8n.db')
cur = conn.cursor()

# Get user info
cur.execute("SELECT id, email, firstName, lastName FROM user LIMIT 5")
for r in cur.fetchall():
    print(f"User: {r[1]} ({r[2]} {r[3]})")

conn.close()