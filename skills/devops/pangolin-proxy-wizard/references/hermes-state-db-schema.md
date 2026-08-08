# Hermes state.db Schema for Analytics

The canonical session store at `~/.hermes/state.db` is a SQLite database with FTS5 full-text search on messages. This reference documents the schema for building custom analytics dashboards, reports, or monitoring tools without parsing the ASCII `hermes insights` output.

## Schema Version

```sql
SELECT version FROM schema_version;  -- currently 1
```

## Tables

### `sessions`

One row per conversation session. **Timestamp format: float seconds** (Unix timestamp as a float, e.g. `1780906169.3324025`). NOT milliseconds.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Primary key. Format: `YYYYMMDD_HHMMSS_<hash>` for CLI/telegram, `cron_<uuid>_<timestamp>` for cron jobs |
| `source` | TEXT | Platform: `telegram`, `cli`, `cron`, `tui`, `discord`, `webui` |
| `user_id` | TEXT | Platform user ID (hashed if `privacy.redact_pii: true`) |
| `model` | TEXT | Model name (e.g. `deepseek-v4-flash`, `claude-sonnet-4`) |
| `model_config` | TEXT | JSON blob of model configuration |
| `system_prompt` | TEXT | System prompt used |
| `parent_session_id` | TEXT | For branched/forks session |
| `started_at` | REAL | **Float seconds** Unix timestamp |
| `ended_at` | REAL | **Float seconds** Unix timestamp (NULL if session still active) |
| `end_reason` | TEXT | How session ended (e.g. `exit`, `error`, `timeout`, `interrupted`) |
| `message_count` | INTEGER | Total messages in session |
| `tool_call_count` | INTEGER | Total tool calls |
| `input_tokens` | INTEGER | Total input tokens |
| `output_tokens` | INTEGER | Total output tokens |
| `cache_read_tokens` | INTEGER | Cache read tokens |
| `cache_write_tokens` | INTEGER | Cache write tokens |
| `reasoning_tokens` | INTEGER | Reasoning tokens (for reasoning models) |
| `billing_provider` | TEXT | Provider name for billing |
| `billing_base_url` | TEXT | Base URL for billing |
| `billing_mode` | TEXT | Billing mode (e.g. `payg`, `subscription`) |
| `estimated_cost_usd` | REAL | Estimated cost |
| `actual_cost_usd` | REAL | Actual cost |
| `cost_status` | TEXT | Cost status (e.g. `estimated`, `final`) |
| `title` | TEXT | Session title (set via `/title`) |
| `api_call_count` | INTEGER | Count of API calls |
| `handoff_state` | TEXT | Multi-platform handoff state |
| `handoff_platform` | TEXT | Platform handed off to |
| `cwd` | TEXT | Working directory when session started |
| `rewind_count` | INTEGER | Number of `/undo` or `/rollback` |
| `archived` | INTEGER | 0=active, 1=archived |

### `messages`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment PK |
| `session_id` | TEXT | FK → sessions.id |
| `role` | TEXT | `user`, `assistant`, `tool` |
| `content` | TEXT | Message content (text) |
| `tool_call_id` | TEXT | Tool call ID |
| `tool_name` | TEXT | Tool name used (for tool role messages) |
| `timestamp` | REAL | Float seconds |
| `token_count` | INTEGER | Token count for this message |
| `finish_reason` | TEXT | LLM finish reason |

Plus FTS5 auxiliary tables: `messages_fts`, `messages_fts_data`, `messages_fts_idx`, `messages_fts_content`, `messages_fts_docsize`, `messages_fts_config`, `messages_fts_trigram*`.

### `compression_locks`

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | PK — session being compressed |
| `holder` | TEXT | Hostname/process holding lock |
| `acquired_at` | REAL | When lock was acquired |
| `expires_at` | REAL | When lock expires |

### `state_meta`

Key-value store for internal state metadata.

## Key SQL Queries for Analytics

### Overview counts (last N days)

```sql
-- Note: started_at is in SECONDS, not milliseconds
SELECT
    COUNT(*) AS sessions,
    COALESCE(SUM(message_count),0) AS messages,
    COALESCE(SUM(tool_call_count),0) AS tool_calls,
    COALESCE(SUM(input_tokens),0) AS input_tokens,
    COALESCE(SUM(output_tokens),0) AS output_tokens,
    COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens),0) AS total_tokens,
    COALESCE(SUM(ended_at - started_at),0) AS total_secs
FROM sessions
WHERE started_at >= ?;  -- pass: datetime.now() - timedelta(days=30)
```

### Models ranked by tokens

```sql
SELECT model, COUNT(*) AS sessions,
       COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens),0) AS tokens
FROM sessions WHERE started_at >= ? AND model IS NOT NULL
GROUP BY model ORDER BY tokens DESC;
```

### Platform breakdown

```sql
SELECT source, COUNT(*) AS sessions,
       COALESCE(SUM(message_count),0) AS msgs,
       COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens),0) AS tokens
FROM sessions WHERE started_at >= ?
GROUP BY source ORDER BY tokens DESC;
```

### Top tools

```sql
SELECT tool_name, COUNT(*) AS calls
FROM messages
WHERE session_id IN (SELECT id FROM sessions WHERE started_at >= ?)
  AND role = 'tool' AND tool_name IS NOT NULL
GROUP BY tool_name ORDER BY calls DESC LIMIT 20;
```

### Activity by day of week

```sql
-- Convert float-seconds timestamp to weekday
-- Python side: datetime.fromtimestamp(ts).weekday()
SELECT CAST(started_at AS INTEGER) AS ts
FROM sessions WHERE started_at >= ?;
-- Then group by weekday(ts) in application code
```

### Peak hours

```sql
SELECT CAST(started_at AS INTEGER) AS ts
FROM sessions WHERE started_at >= ?;
-- Python: datetime.fromtimestamp(ts).hour
```

### Notable sessions (records)

```sql
-- Find longest, most messages, most tokens, most tool calls
SELECT id, started_at, ended_at, message_count, tool_call_count,
       COALESCE(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens,0) AS total_tokens
FROM sessions WHERE started_at >= ?;
-- Then use Python max() with key=lambda r: ...
```

## ⚠️ Critical: Timestamp Unit

**`started_at` and `ended_at` are in float seconds**, not milliseconds. This is a common pitfall:

- ✅ Correct: `datetime.fromtimestamp(started_at)`
- ❌ Wrong: `datetime.fromtimestamp(started_at / 1000)` — off by factor 1000

The cutoff for "last N days" should also be in seconds:
- ✅ Correct: `(datetime.now() - timedelta(days=30)).timestamp()`
- ❌ Wrong: `int(...) * 1000`

## Python Server Pattern

For a live-refreshing dashboard, structure your server like this:

```python
import json, sqlite3, datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DB = Path.home() / ".hermes" / "state.db"
DAYS = 30

def cutoff():
    return (datetime.datetime.now() - datetime.timedelta(days=DAYS)).timestamp()

def fetch_data():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    c = cutoff()

    # Build your analytics dict from queries
    data = { "ts": datetime.datetime.now().isoformat() }

    # Overview
    r = conn.execute("""SELECT COUNT(*) AS sessions, ... FROM sessions WHERE started_at >= ?""", (c,)).fetchone()
    data["overview"] = { "sessions": r["sessions"], ... }

    conn.close()
    return data
```

## Serving Instructions

```bash
cd /var/www/<dashboard-dir>  # NOT ~/ or /root/
python3 server.py             # listens on 127.0.0.1:8999
```

Then create a Pangolin site resource (site 28, subdomain of your choice, ssl=true, scheme=http, destination=127.0.0.1:8999).
