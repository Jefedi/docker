# n8n SQLite DB Direct Editing

When `npx n8n import:workflow` + `npx n8n publish:workflow` don't correctly
apply changes (especially connection graph modifications), edit the SQLite
database directly.

## When to Use This

- CLI import/publish silently ignores connection changes
- A node's `disabled` flag needs toggling but CLI doesn't expose it
- Need to modify node parameters that MCP tools can't reach
- Need to trace the connection graph programmatically

## Procedure

### 1. Stop n8n

```bash
docker stop n8n-n8n-1
```

### 2. Copy DB out of the container

```bash
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_db.sqlite
```

### 3. Edit with Python

```python
import sqlite3, json

conn = sqlite3.connect('/tmp/n8n_db.sqlite')
c = conn.cursor()

# Read workflow
c.execute("SELECT nodes, connections FROM workflow_entity WHERE id = '<WF_ID>'")
row = c.fetchone()
nodes = json.loads(row[0])
connections = json.loads(row[1])

# Example: fix a connection (reconnect Tag HN -> Translate HN instead of Rebuild HN)
connections['Tag HN']['main'][0][0]['node'] = 'Translate HN'

# Example: enable a disabled node
for n in nodes:
    if n.get('name') == 'Translate HN':
        n['disabled'] = False

# Write back
c.execute("UPDATE workflow_entity SET nodes=?, connections=? WHERE id='<WF_ID>'",
          (json.dumps(nodes, ensure_ascii=False),
           json.dumps(connections, ensure_ascii=False)))
conn.commit()
conn.close()
```

### 4. Copy DB back and fix permissions

```bash
docker cp /tmp/n8n_db.sqlite n8n-n8n-1:/home/node/.n8n/database.sqlite
docker start n8n-n8n-1

# CRITICAL: fix ownership or n8n crashes with SQLITE_READONLY
docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite
docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite-shm
docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite-wal
docker restart n8n-n8n-1
```

### 5. Verify

```bash
# Wait for n8n to start (large DBs can take 10-20s)
sleep 15
curl -s http://localhost:5678/healthz
# Should return {"status":"ok"}

# Check the workflow is active
docker exec n8n-n8n-1 npx n8n list:workflow | grep "<workflow name>"
```

## Common DB Tables

| Table | Contents |
|---|---|
| `workflow_entity` | All workflows (nodes, connections, settings, staticData) |
| `execution_entity` | Execution history (status, timestamps) |
| `execution_data` | Full execution data (node inputs/outputs) |
| `credentials_entity` | Credentials (encrypted data) |
| `user_api_keys` | API keys (masked — can't read full values) |

## Connection Graph Structure

n8n stores connections as a nested dict:

```json
{
  "SourceNodeName": {
    "main": [
      [
        { "node": "TargetNodeName", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

- `main[0]` = first output of the source node
- `main[0][0]` = first target connected to that output
- A node can have multiple targets: `main[0]` is an array of target objects

## Pitfalls

- **Always stop n8n before copying the DB** — SQLite WAL files may not be flushed
- **The DB can be very large** (12GB+ on this instance) — copying takes time
- **API keys in `user_api_keys` are masked** with `...` — don't try to extract them
- **Credentials data is encrypted** with the `encryptionKey` in `/home/node/.n8n/config`
- **After restart, schedule triggers reset** — first run may be delayed up to one full interval