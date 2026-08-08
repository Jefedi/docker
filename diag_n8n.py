import sqlite3, json

conn = sqlite3.connect('/tmp/n8n.db')
cur = conn.cursor()

cur.execute("SELECT id, name, active, nodes, connections, settings FROM workflow_entity WHERE name='My workflow 4'")
row = cur.fetchone()
if row:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Active: {row[2]}")
    
    nodes = json.loads(row[3]) if row[3] else []
    print(f"\n=== Nodes ({len(nodes)}) ===")
    for n in nodes:
        node_type = n.get("type", "?")
        node_name = n.get("name", "?")
        disabled = n.get("disabled", False)
        print(f"  [{'OFF' if disabled else 'ON '}] {node_name} ({node_type})")
        params = n.get("parameters", {})
        if params:
            for k, v in params.items():
                v_str = str(v)[:150]
                print(f"        {k}: {v_str}")
    
    print(f"\n=== Connections ===")
    connections = json.loads(row[4]) if row[4] else {}
    print(json.dumps(connections, indent=2)[:2000])
    
    settings = json.loads(row[5]) if row[5] else {}
    print(f"\n=== Settings ===")
    print(json.dumps(settings, indent=2)[:500])
else:
    print("Workflow not found")

print("\n=== Recent Executions ===")
cur.execute("""
    SELECT id, status, startedAt, stoppedAt
    FROM execution_entity 
    WHERE "workflowId" = 'yecPzh6xd0j34DEy' 
    ORDER BY startedAt DESC 
    LIMIT 10
""")
for ex in cur.fetchall():
    print(f"  {ex[1]:10} | {ex[2]} | exec={ex[0]}")

conn.close()