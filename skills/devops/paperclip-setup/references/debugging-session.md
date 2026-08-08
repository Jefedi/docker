# Paperclip Setup — Full Debugging Session

This references the complete debugging path from a Paperclip installation session on 2026-05-27.

## Environment

- Host: Linux (cloud VM, root user)
- Node.js v22.22.3, npm 10.9.8
- PostgreSQL 17 (system install)
- Paperclip version: 2026.525.0
- Running as root (no dedicated user)

## Error Timeline

### Error 1: embedded-postgres root failure

```
You are running this script as root. Postgres does not support running as root.
If you wish to continue, configure embedded-postgres to create a Postgres user
by setting the `createPostgresUser` option to true.
```

**Fix:** Switch to system PostgreSQL instead of embedded.

### Error 2: embedded-postgres initdb EACCES

Even with `createPostgresUser: true` in config, the embedded postgres initdb binary fails with EACCES when spawned as root. The binary at `~/.npm/_npx/*/node_modules/@embedded-postgres/linux-x64/native/bin/initdb` has correct permissions (755) but the embedded-postgres library tries to spawn it as the `postgres` system user, who can't access root's npm cache.

**Fix:** Avoid embedded-postgres entirely when running as root. Use system PostgreSQL.

GitHub issue: [#5345](https://github.com/paperclipai/paperclip/issues/5345) — still open.

### Error 3: Invalid config — database.mode enum

```
database.mode: Invalid enum value. Expected 'embedded-postgres' | 'postgres',
received 'postgres-url'
```

**Fix:** Use `"mode": "postgres"` not `"postgres-url"`.

GitHub issue: [#1271](https://github.com/paperclipai/paperclip/issues/1271) — fixed in PR #1500 (Mar 2026).

### Error 4: Invalid config — auth.publicBaseUrl required

```
auth.publicBaseUrl: auth.publicBaseUrl is required when auth.baseUrlMode is explicit
```

**Fix:** Add both `publicBaseUrl` and `baseUrl` when using `"baseUrlMode": "explicit"`.

### Error 5: PostgreSQL connection string not detected

Using `"url"` field instead of `"connectionString"` in the config. The server's `loadConfig()` reads `fileConfig?.database.connectionString`.

**Fix:** Use `"connectionString"` (not `"url"`).

### Error 6: "Invalid URL" from postgres npm package

```
TypeError: Invalid URL
    at new URL (node:internal/url:818:25)
    at parseUrl (postgres/src/index.js:545:18)
    at createUtilitySql (@paperclipai/db/dist/client.js:12:12)
    at ensureMigrations (@paperclipai/server/dist/index.js:62:27)
```

**Root cause:** The `.env` file had `***` written literally instead of the real password. The `echo` command used `***` as a placeholder, and the actual file contained the literal string `***`. The `postgres` npm package's `parseUrl()` function calls `new URL()` which fails because `***` is not a valid host component (the function first extracts the host from the URL and then reconstructs it).

**Fix:** Write the actual password (not `***`) to the `.env` file.

### Error 7: local_trusted requires loopback bind

```
server.bind: local_trusted requires server.bind=loopback
```

**Fix:** Either keep `bind: loopback` + `host: 127.0.0.1`, or switch to `"deploymentMode": "authenticated"` for LAN/public bind.

## Config File Final State

Location: `~/.paperclip/instances/default/config.json`

Key sections:
- `database.mode`: `"postgres"`
- `database.connectionString`: valid PostgreSQL URL
- `server.deploymentMode`: `"authenticated"` (for LAN access)
- `server.bind`: `"lan"`, `host`: `"0.0.0.0"`, `port`: 3100
- `server.allowedHostnames`: public IP as string
- `auth.baseUrlMode`: `"explicit"`
- `auth.publicBaseUrl` + `auth.baseUrl`: `http://IP:3100`

## Server Output (Healthy)

```
Mode             external-postgres  |  static-ui
Deploy           authenticated (private)
Bind             lan (0.0.0.0)
Auth             ready
Server           3100
API              http://localhost:3100/api
UI               http://localhost:3100
Migrations       already applied
Agent JWT        set
Heartbeat        enabled (30000ms)
DB Backup        enabled (every 60m, keep 30d)
```

Health endpoint: `{"status":"ok","version":"2026.525.0","deploymentMode":"authenticated","authReady":true}`