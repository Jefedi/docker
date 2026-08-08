# CEO Agent Troubleshooting — Session Reference

## Agent Status Queries
```sql
-- All agents with key fields
SELECT id, name, role, status, reports_to, adapter_type, adapter_config FROM agents ORDER BY created_at;

-- CEO agents only
SELECT id, name, status, last_heartbeat_at, runtime_config->'heartbeat' as heartbeat
FROM agents WHERE role = 'ceo';

-- Agent instructions path
SELECT id, name, adapter_config->>'instructionsFilePath' as instructions_path
FROM agents;
```

## Update Agent Instructions Path
```sql
-- Fix path when running as different user
UPDATE agents 
SET adapter_config = jsonb_set(adapter_config::jsonb, '{instructionsFilePath}',
  '"CORRECT_PATH"')
WHERE id = 'AGENT_UUID';

UPDATE agents 
SET adapter_config = jsonb_set(adapter_config::jsonb, '{instructionsRootPath}',
  '"CORRECT_ROOT_PATH"')
WHERE id = 'AGENT_UUID';
```

## Resume Stuck CEO
```sql
UPDATE agents SET status = 'idle' WHERE id = 'AGENT_UUID';
UPDATE agents SET runtime_config = jsonb_set(runtime_config::jsonb, '{heartbeat,enabled}', 'true')
WHERE id = 'AGENT_UUID';
```

## Check Issues by Company
```sql
SELECT i.id, i.title, i.status, c.name as company, i.created_at
FROM issues i JOIN companies c ON i.company_id = c.id
ORDER BY i.created_at;

-- Issues with identifiers
SELECT id, title, status, created_at FROM issues
WHERE company_id = 'COMPANY_UUID'
ORDER BY created_at;
```

## Activity Log for CEO Debugging
```sql
-- Recent runs with errors
SELECT created_at, action, actor_type, entity_type, details
FROM activity_log
WHERE details->>'failureReason' IS NOT NULL
ORDER BY created_at DESC LIMIT 20;

-- Failed lease events (CEO run failures)
SELECT created_at, details->>'failureReason' as reason
FROM activity_log
WHERE action = 'environment.lease_released'
AND details->>'status' = 'failed'
ORDER BY created_at DESC LIMIT 10;
```

## Paperclip Config
```bash
# Config file location
cat /home/paperclip/.paperclip/instances/default/config.json

# Check allowed hostnames
cat /home/paperclip/.paperclip/instances/default/config.json | jq '.server.allowedHostnames'

# Check deployment mode
cat /home/paperclip/.paperclip/instances/default/config.json | jq '.server.deploymentMode'
```