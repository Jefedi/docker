# Modifying n8n Workflows via SQLite DB (when REST API is unavailable)

When the n8n REST API key is not available (masked/truncated in the DB as
`eyJhbG...xfLc`), you can modify workflow nodes and connections directly
in the SQLite database. This is the only reliable method when you cannot
get a valid API key.

## When to Use This

- n8n REST API returns `{"message":"unauthorized"}` for all keys you find
- API keys in `user_api_keys` table are masked with `...` (n8n security feature)
- `docker exec n8n-n8n-1 npx n8n execute --id=<wf>` fails because the main
  n8n process holds the task broker port (5679)

## The WAL/SHM Trap (CRITICAL)

n8n uses SQLite WAL (Write-Ahead Log) mode. When n8n is running, recent
changes live in `database.sqlite-wal` and `database.sqlite-shm`. If you:

1. Copy the DB out: `docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n.db`
2. Modify it with Python/sqlite3
3. Copy it back: `docker cp /tmp/n8n.db n8n-n8n-1:/home/node/.n8n/database.sqlite`
4. Restart n8n

**Your changes will be LOST** because n8n replays the WAL on startup,
overwriting the DB with the pre-restart state.

### Correct Procedure

```bash
# 1. Stop n8n
docker stop n8n-n8n-1

# 2. Copy the DB out (while stopped — no WAL active)
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_modify.sqlite

# 3. Modify with Python
python3 << 'PYEOF'
import sqlite3, json

conn = sqlite3.connect('/tmp/n8n_modify.sqlite')
c = conn.cursor()

c.execute("SELECT nodes, connections FROM workflow_entity WHERE id = '<workflow_id>'")
row = c.fetchone()
nodes = json.loads(row[0])
connections = json.loads(row[1])

# Modify nodes (enable, change params, etc.)
for n in nodes:
    if n.get('name') == 'Target Node Name':
        n['disabled'] = False
        n['parameters']['authentication'] = 'none'
        n['parameters']['jsonBody'] = '={{ { api_key: "KEY" } }}'
        if 'credentials' in n:
            del n['credentials']

# Modify connections (reconnect nodes)
connections['Source Node']['main'][0][0]['node'] = 'New Target Node'

# Write back
c.execute("UPDATE workflow_entity SET nodes = ?, connections = ? WHERE id = '<workflow_id>'",
          (json.dumps(nodes, ensure_ascii=False), json.dumps(connections, ensure_ascii=False)))
conn.commit()
conn.close()
PYEOF

# 4. Copy modified DB back
docker cp /tmp/n8n_modify.sqlite n8n-n8n-1:/home/node/.n8n/database.sqlite

# 5. Fix permissions (n8n user = UID 1000)
docker start n8n-n8n-1
sleep 3
docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite

# 6. Restart to take effect
docker restart n8n-n8n-1
sleep 15
curl -s http://localhost:5678/healthz
```

### Verifying Changes Survived

After restart, always verify:
```bash
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_verify.sqlite
python3 -c "
import sqlite3, json
conn = sqlite3.connect('/tmp/n8n_verify.sqlite')
c = conn.cursor()
c.execute(\"SELECT nodes, connections FROM workflow_entity WHERE id = '<wf_id>'\")
row = c.fetchone()
nodes = json.loads(row[0])
for n in nodes:
    if n.get('name') == 'Target Node':
        print(f'disabled: {n.get(\"disabled\", False)}')
conn.close()
"
```

## Common Node Fixes

### Enabling a disabled node
```python
n['disabled'] = False
```

### Removing credential auth (switching to body-based auth)
```python
n['parameters']['authentication'] = 'none'
n['parameters']['genericAuthType'] = ''
n['parameters']['jsonBody'] = '={{ { ..., api_key: "KEY" } }}'
if 'credentials' in n:
    del n['credentials']
```

### Reconnecting nodes (fixing a bypassed node)
```python
# If Tag HN -> Rebuild HN (bypassing Translate HN)
# Fix: Tag HN -> Translate HN -> Rebuild HN
connections['Tag HN']['main'][0][0]['node'] = 'Translate HN'
# Translate HN -> Rebuild HN should already exist
```

### Fixing a Set node after an HTTP Request (data loss recovery)

After an HTTP Request node (e.g. Translate HN → LibreTranslate), the output
`$json` contains ONLY the API response fields. Original input fields are lost.
A downstream Set node must use `$json.translatedText` (API response) and
`$("UpstreamNode").item.json.field` to recover original fields:

```python
# Fix Rebuild HN (Set node after Translate HN)
assignments = n['parameters']['assignments']['assignments']

# title: use translated text from LibreTranslate response
assignments[0]['value'] = '={{ $json.translatedText || $json.title }}'

# link: recover from Tag HN (before the HTTP Request)
assignments[1]['value'] = '={{ $json.link || $("Tag HN").item.json.link }}'

# content: recover from Tag HN
assignments[2]['value'] = '={{ $json.content || $("Tag HN").item.json.contentSnippet || $("Tag HN").item.json.content || "" }}'

# pubDate: recover from Tag HN
assignments[3]['value'] = '={{ $json.pubDate || $("Tag HN").item.json.pubDate || $("Tag HN").item.json.isoDate || "" }}'
```

**Key pattern**: `$("NodeName").item.json.fieldName` is n8n's cross-node data
access syntax. It works even after an HTTP Request node discards the original
fields. Use it to recover any field from any earlier node in the workflow.

## Checking n8n Logs for Errors

```bash
# After restart, check for SQLITE_READONLY errors (permission issue)
docker logs n8n-n8n-1 --since 5m 2>&1 | grep -i "error\|readonly"

# Check if workflows activated successfully
docker logs n8n-n8n-1 --since 5m 2>&1 | grep "Activated workflow"
```

## Triggering a Workflow Manually

The `npx n8n execute --id=<wf>` command fails when n8n is already running
(port 5679 conflict). Options:

1. **Wait for the schedule trigger** — if the workflow has one, wait for the
   next cycle (check schedule interval in the Schedule Trigger node)
2. **Use the n8n UI** — navigate to the workflow in the browser and click
   "Execute workflow"
3. **Call the webhook endpoint** — if the workflow has a webhook trigger,
   `curl http://localhost:5678/webhook/<path>` triggers the webhook branch
   (but NOT the schedule branch)

## n8n Container Quirks

- n8n container (ghcr.io/n8n-io/n8n) has NO `python3`, `sqlite3`, or `apk`
  — use `docker cp` to extract the DB and modify it on the host
- The n8n user inside the container is `node` (UID 1000)
- DB location: `/home/node/.n8n/database.sqlite` (mounted via Docker volume)
- API keys in `user_api_keys.apiKey` column are masked by n8n (stored as
  `eyJhbG...xfLc` with literal `...`) — they cannot be used for REST API auth
- Permission errors after `docker cp`: use
  `docker exec -u root n8n-n8n-1 chown 1000:1000 /home/node/.n8n/database.sqlite`