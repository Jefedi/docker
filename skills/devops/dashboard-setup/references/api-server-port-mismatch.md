# API Server Port Mismatch — `.env` vs `config.yaml`

## Problem

After migrating the API server port from 9119 to 9120 in `config.yaml`
(`api_server.port: 9120`), the iOS app or remote client shows:

> "Could not reach this gateway yet. Check the URL — the auth method will
> appear once it responds."

And `curl https://hermes.jefe.al/` returns **502 Bad Gateway**.

## Root Cause

The API server port is determined by **two** sources, and `.env` wins:

1. `/opt/data/.env` → `API_SERVER_PORT=9119` (old value, never updated)
2. `/opt/data/config.yaml` → `api_server.port: 9120` (new value)

At gateway startup, the `.env` value takes precedence. The API server starts
on 9119, but Pangolin routes `hermes.jefe.al` → `127.0.0.1:9120` (per the
config.yaml migration). Port 9120 has nothing listening → 502.

## Diagnostic Steps

1. **Check which port the API server actually listens on:**
   ```bash
   python3 -c "
   import socket
   for port in [9119, 9120]:
       s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       s.settimeout(2)
       print(f'Port {port}: {\"OPEN\" if s.connect_ex((\"127.0.0.1\", port))==0 else \"CLOSED\"}')
       s.close()
   "
   ```
   If 9119 is OPEN and 9120 is CLOSED → port mismatch confirmed.

2. **Check .env for stale port:**
   ```bash
   grep API_SERVER_PORT /opt/data/.env
   ```
   If it says 9119 but config.yaml says 9120 → found the cause.

3. **Check config.yaml:**
   ```bash
   grep -A3 'api_server' /opt/data/config.yaml
   ```

4. **Verify through Pangolin (remote):**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://hermes.jefe.al/
   # 502 = proxy target port has nothing listening
   ```

5. **Verify API still works on the old port:**
   ```bash
   curl -s -X POST http://127.0.0.1:9119/api/v1/responses \
     -H "Authorization: Bearer $API_SERVER_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4o-mini","input":"test","max_output_tokens":10}'
   ```
   If this works but 9120 doesn't → confirmed: API server on wrong port.

## Fix

1. Update `/opt/data/.env`:
   ```bash
   # Change from:
   API_SERVER_PORT=9119
   # To:
   API_SERVER_PORT=9120
   ```
   Or remove the line entirely so `config.yaml` is the sole source of truth.

2. Restart the gateway (requires user confirmation per ntfy rule):
   ```bash
   hermes gateway restart
   ```

3. Verify:
   ```bash
   curl http://127.0.0.1:9120/health
   # Should return {"status":"ok",...}

   curl -X POST https://hermes.jefe.al/api/v1/responses \
     -H "Authorization: Bearer $API_SERVER_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4o-mini","input":"test","max_output_tokens":10}'
   # Should return a valid response object
   ```

## Prevention

When changing the API server port, **always update both**:
- `config.yaml` → `api_server.port`
- `.env` → `API_SERVER_PORT`

Or remove `API_SERVER_PORT` from `.env` entirely and rely solely on
`config.yaml` to avoid this class of drift.

## Related

- `api-server-setup` skill → "Hermes Port Map" section (also patched with this pitfall)
- `dashboard-setup` skill → post-migration notice (updated Aug 1, 2026)