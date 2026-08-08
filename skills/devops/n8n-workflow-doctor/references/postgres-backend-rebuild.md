# Rebuilding a Postgres Backend for n8n

When an n8n workflow pipeline depends on Postgres and the database has been recreated/reset, you need to rebuild the full backend: user, database, tables, functions, network config, and n8n credential.

## Step-by-step (Ubuntu/Debian, Postgres 17)

### 1. Create Database User and Database

```bash
# Create the user role with a password
runuser -u postgres -- psql -c "CREATE USER nextdns WITH PASSWORD 'your_password_here';"

# Create the database owned by that user
runuser -u postgres -- psql -c "CREATE DATABASE nextdns OWNER nextdns;"
```

Verify:
```bash
runuser -u postgres -- psql -c "\du"    # list roles
runuser -u postgres -- psql -c "\l"     # list databases
```

### 2. Create Tables and Indexes

```sql
CREATE TABLE IF NOT EXISTS nextdns_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    domain TEXT NOT NULL,
    type TEXT,
    action TEXT,
    device_name TEXT,
    device_model TEXT,
    device_id TEXT,
    client_ip INET,
    protocol TEXT,
    reason TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    root_domain TEXT,
    gafam TEXT,
    tracker TEXT,
    query_type TEXT,
    status TEXT
);

CREATE INDEX IF NOT EXISTS idx_nextdns_logs_timestamp ON nextdns_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_nextdns_logs_domain ON nextdns_logs(domain);

CREATE TABLE IF NOT EXISTS dashboard_cache (
    cache_key TEXT PRIMARY KEY,
    cache_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3. Create Stored Functions

```sql
CREATE OR REPLACE FUNCTION compute_dashboard_stats()
RETURNS JSONB LANGUAGE plpgsql AS $$
DECLARE
    result JSONB;
    all_count BIGINT;
    blocked_count BIGINT;
    encrypted_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO all_count FROM nextdns_logs;
    SELECT COUNT(*) INTO blocked_count FROM nextdns_logs WHERE action = 'blocked';
    SELECT COUNT(*) INTO encrypted_count FROM nextdns_logs WHERE encrypted = TRUE;
    
    result := jsonb_build_object(
        'generated_at', NOW()::TEXT,
        'stats', jsonb_build_object(
            'all', jsonb_build_object(
                'total', all_count,
                'blocked', blocked_count,
                'blockedPercent', CASE WHEN all_count > 0 THEN ROUND(blocked_count::NUMERIC / all_count * 100, 2) ELSE 0 END,
                'encrypted', encrypted_count,
                'encryptedPercent', CASE WHEN all_count > 0 THEN ROUND(encrypted_count::NUMERIC / all_count * 100, 2) ELSE 0 END
            )
        )
    );
    
    RETURN result;
END;
$$;
```

### 4. Configure Network Access

For n8n running on another machine (e.g. AX42 at 100.64.0.2 via Tailscale):

```bash
# Add host-based auth to pg_hba.conf
echo "host    nextdns         nextdns         100.64.0.2/32     scram-sha-256" >> /etc/postgresql/17/main/pg_hba.conf

# Set listen_addresses to include the Tailscale IP
sed -i "s/^#listen_addresses = 'localhost'/listen_addresses = 'localhost,100.64.0.9'/" /etc/postgresql/17/main/postgresql.conf

# Restart Postgres
systemctl restart postgresql

# Verify listening
ss -tlnp | grep 5432
```

Expected output:
```
LISTEN 0 200 100.64.0.9:5432  0.0.0.0:*  users:(("postgres",...))
LISTEN 0 200 127.0.0.1:5432  0.0.0.0:*  users:(("postgres",...))
```

### 5. Update n8n Credential

The n8n credential must be updated to point to the new Postgres host:
- **Host**: `100.64.0.9` (or the Tailscale IP of the Postgres server)
- **Port**: `5432`
- **Database**: `nextdns`
- **User**: `nextdns`
- **Password**: the one set in step 1

NOTE: The n8n MCP tools currently do NOT include a credential update function. You must update the credential via:
- The n8n web UI at n8n.jefe.ovh
- The n8n REST API directly
- Or create a new credential and update the workflow nodes

### 6. Activate Pipeline Workflows

After the credential is updated, activate workflows in order:
1. **Ingestion/Logs workflow** (e.g. NextDNS Logs → Postgres, 30s polling) — starts collecting raw data
2. **Cache/Stats workflow** (e.g. every 15 min) — pre-computes aggregated stats
3. **Dashboard webhook** — serves the HTML/API frontend

Verify each step:
```python
mcp_n8n_mcp_search_executions(workflowId="<id>", limit=3)
# Check for "success" status
```
