import sqlite3, json

conn = sqlite3.connect('/tmp/n8n_db.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Lister les tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r['name'] for r in cur.fetchall()]
print("Tables:", tables)

# Chercher les workflows avec 'pangolin' ou 'mcp' dans le nom
cur.execute("SELECT id, name, active FROM workflow_entity")
for row in cur.fetchall():
    name = row['name'].lower()
    if 'pangolin' in name or 'mcp' in name:
        print(f"  Found: ID={row['id']} | Name={row['name']} | Active={row['active']}")

# Chercher les credentials liés à Pangolin
cur.execute("SELECT id, name, type FROM credentials_entity")
for row in cur.fetchall():
    name = str(row['name']).lower()
    if 'pangolin' in name or 'jefe' in name or 'api' in name:
        print(f"  Credential: ID={row['id']} | Name={row['name']} | Type={row['type']}")

# Chercher la clé API Pangolin dans le JSON des workflows
cur.execute("SELECT id, name, nodes FROM workflow_entity")
for row in cur.fetchall():
    nodes = row['nodes']
    if 'pangolin' in nodes.lower() or 'api.jefe' in nodes.lower():
        print(f"\n  Workflow with Pangolin ref: ID={row['id']} | Name={row['name']}")
        try:
            nodes_list = json.loads(nodes)
            for node in nodes_list:
                node_str = json.dumps(node)
                if 'pangolin' in node_str.lower() or 'api.jefe' in node_str.lower():
                    print(f"    Node: {node.get('name')} | Type: {node.get('type')}")
                    creds = node.get('credentials', {})
                    if creds:
                        print(f"    Credentials: {json.dumps(creds)}")
                    params = node.get('parameters', {})
                    params_str = json.dumps(params)
                    if 'api.jefe' in params_str or 'pangolin' in params_str.lower():
                        print(f"    Params (filtered): {params_str[:500]}")
        except:
            pass