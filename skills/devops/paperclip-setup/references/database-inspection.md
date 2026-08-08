# Paperclip State Inspection via PostgreSQL

When Paperclip's CEO or agents fail, or when you need to audit what was done, direct database inspection via `psql` is faster than navigating the UI through a reverse proxy (Pangolin auth layer). This reference documents the key queries.

## Prerequisites

The `paperclip` PostgreSQL user must have database access. Run queries as the Paperclip user:

```bash
sudo -u paperclip psql -d paperclip -c "QUERY"
```

## Schema Overview

Paperclip uses ~88 tables. The core business-entity tables relevant to state inspection:

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `companies` | AI companies (business entities) | `id`, `name`, `description`, `status` (active/archived), `issue_prefix`, `issue_counter` |
| `agents` | Agent employees in companies | `id`, `company_id`, `name`, `role` (ceo/general/...), `status` (idle/error), `adapter_type`, `adapter_config`, `reports_to` |
| `issues` | Tasks assigned to agents | `id`, `company_id`, `project_id`, `title`, `status`, `owner_agent_id` |
| `projects` | Project groupings of issues | `id`, `company_id`, `name`, `status` |
| `company_memberships` | Who belongs to which company | `company_id`, `principal_type` (user/agent), `principal_id`, `membership_role` (owner/member) |
| `activity_log` | Full audit trail | `actor_type`, `action`, `entity_type`, `details` (JSON), `created_at` |
| `goals` | Company goals | Currently sparse — used by sub-agent orchestration |
| `agent_task_sessions` | Agent execution runs | `agent_id`, run metadata (schema version-dependent) |
| `heartbeat_runs` | CEO heartbeat tick history | Related to scheduled CEO wake-ups |

## Key Queries

### List all companies and their status

```sql
SELECT id, name, status, issue_prefix, created_at
FROM companies
ORDER BY created_at;
```

**Expected:** One or more companies. Archived ones are old/discarded attempts. The active one is `status = 'active'`.

### List all agents and their state

```sql
SELECT a.id, c.name AS company, a.name AS agent_name, a.role, a.status,
       a.adapter_type, a.last_heartbeat_at, a.reports_to
FROM agents a
JOIN companies c ON a.company_id = c.id
ORDER BY a.created_at;
```

**Diagnostic patterns:**
- `status = 'error'` — Agent crashed or auth failed. Check `activity_log` for details.
- `status = 'idle'` — Agent alive but not currently working.
- `adapter_type = 'claude_local'` — Uses Claude Code CLI (OAuth or ANTHROPIC_API_KEY).
- `adapter_type = 'hermes_local'` — Uses Hermes Agent (needs Hermes auth configured).
- `adapter_type = 'process'` — Direct subprocess (used for workers like "Hermes Agent" as employee).
- `reports_to = NULL` for the CEO agent; workers have the CEO's agent ID here.

### List issues by company

```sql
SELECT i.id, c.issue_prefix || '-' || i.issue_number AS identifier,
       i.title, i.status, i.owner_agent_id, a.name AS owner_name
FROM issues i
JOIN companies c ON i.company_id = c.id
LEFT JOIN agents a ON i.owner_agent_id = a.id
ORDER BY i.created_at;
```

**Status values used in this version:** `todo`, `in_progress`, `done`, `blocked`.  
If a column doesn't exist (e.g. `issue_number` vs `issue_counter`), do `\d issues` to see schema.

### List activity log (most recent first)

```sql
SELECT created_at, actor_type, actor_id, action, entity_type, details
FROM activity_log
ORDER BY created_at DESC
LIMIT 20;
```

This is the most important diagnostic query. The `details` JSON column contains the full error context.

**Key action types:**
- `environment.lease_acquired` / `environment.lease_released` — Agent trying to start a run
- `issue.updated` — Issue status changes, includes `previousStatus` and recovery info in details
- `issue.comment_added` — User or agent commented, `bodySnippet` shows text
- `issue.recovery_action_resolved` — User manually recovered a stranded issue

### Common failure patterns

| details.failureReason snippet | Meaning | Fix |
|---|---|---|
| `"adapter_failed"` / `"Claude run failed: ... Failed to authenticate. API Error: 401"` | Claude Code not authenticated | Run `claude auth login` or set `ANTHROPIC_API_KEY` |
| `"adapter_failed"` / `"Adapter failed"` | Generic adapter crash | Check the adapter config (hermes_local needs hermes in PATH and API keys exported) |
| `"stranded_assigned_issue"` | Agent crashed mid-task, issue auto-blocked | User needs to recover (re-assign or resolve) |
| `"latestRunStatus: failed"` | Run completed with error | Check adapter logs or the specific error from activity |

### Check memberships (who owns what)

```sql
SELECT cm.company_id, c.name AS company, cm.principal_type, cm.principal_id,
       u.name AS user_name, cm.membership_role
FROM company_memberships cm
JOIN companies c ON cm.company_id = c.id
LEFT JOIN "user" u ON cm.principal_type = 'user' AND cm.principal_id = u.id
ORDER BY cm.created_at;
```

### Check if the CEO has a heartbeat active

```sql
SELECT * FROM heartbeat_runs ORDER BY created_at DESC LIMIT 10;
```

And the watchdog decisions:
```sql
SELECT * FROM heartbeat_run_watchdog_decisions ORDER BY created_at DESC LIMIT 10;
```

## Quick Diagnostic Flow

When a user says "check what the CEO did" or "it's not working":

1. **Health check** — `curl http://127.0.0.1:3100/api/health`
2. **Companies** — List all companies and identify the active one
3. **Agents** — Check CEO agent status (idle vs error)
4. **Activity log** — Most recent 20 entries, look for failure patterns
5. **Issues** — List issues for the active company to see what was created
6. **If CEO is error** — Check the `activity_log` `details.failureReason` to identify auth or adapter issue
7. **Memberships** — Verify the user owns the company (should see `membership_role = 'owner'`)