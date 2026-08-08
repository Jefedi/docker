# Pangolin Path-Based Routing for Hermes Dashboard + API

## Problem

Hermes runs two HTTP servers on different ports:
- **Dashboard** (port 9120): web UI with session/basic auth → redirects to `/login`
- **API server** (port 9119): OpenAI-compatible API with Bearer token auth

When `hermes.jefe.al` only points to port 9120, API calls with Bearer tokens get intercepted by the dashboard's auth (302 → `/login`) and never reach the API server.

## Solution: Path-Based Routing on One Pangolin Resource

Pangolin supports per-target path routing. Add a second target to the existing `hermes.jefe.al` resource:

### Target 1 (existing): Dashboard
- No path configured (catch-all, priority 1)
- IP: `127.0.0.1`, Port: `9120`, Method: `http`

### Target 2 (new): API server
- **Path:** `/api`
- **Match:** `prefix` (matches `/api`, `/api/v1/...`, etc.)
- **Path Rewriting:** Strip Prefix (removes `/api` before forwarding)
- IP: `127.0.0.1`, Port: `9119`, Method: `http`

### Result
- `hermes.jefe.al/` → `localhost:9120/` (dashboard)
- `hermes.jefe.al/api/v1/responses` → `localhost:9119/v1/responses` (API, `/api` stripped)

### Match Type vs Path Rewriting — Two Separate Settings

**This is the #1 confusion when configuring path-based routing in Pangolin.**

These are **two independent configurations** on the target:

1. **Match type** (`prefix` / `exact` / `regex`): Determines WHICH requests this target handles
   - `prefix` with path `/api` → handles `/api`, `/api/v1/...`, `/api/health`, etc.
   - Without this, the target is a catch-all (handles everything not matched by other targets)

2. **Path Rewriting** (`stripPrefix` / `prefix` / `exact` / `regex`): Determines HOW the path is transformed before forwarding to the backend
   - `stripPrefix` with path `/api` → removes `/api` → backend receives `/v1/responses`
   - Without this, the backend receives the full path including `/api`

**You need BOTH configured** for a working API route:
- Match type = `prefix`, Path = `/api` → Pangolin routes `/api/*` to this target ✅
- Path Rewriting = `Strip Prefix` → Pangolin removes `/api` before forwarding ✅
- Without Path Rewriting: routing works (requests reach the backend) but the backend gets `/api/v1/responses` → 404

### SSO
Disable SSO on the Pangolin resource. Both backends handle their own auth:
- Dashboard: session-based auth configured in `config.yaml` under `dashboard:`
- API: `API_SERVER_KEY` Bearer token in `Authorization` header

## Configuration Steps (Pangolin UI)

1. Go to `pangolin.jefe.ovh` → Resources → `hermes.jefe.al`
2. Go to Targets tab
3. Click "Add Target"
4. Set: Site = Hermes VPN (site 28), IP = `127.0.0.1`, Port = `9119`, Method = `http`
5. Set Path = `/api`, Match = `prefix`
6. Enable Path Rewriting → Type = `Strip Prefix`
7. Save
8. Go to Resource settings → disable SSO (both backends have own auth)

## Testing

```bash
# API via Pangolin (with stripPrefix configured)
curl -X POST https://hermes.jefe.al/api/v1/responses \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":"test"}'

# API direct (bypass Pangolin)
curl -X POST http://localhost:9119/v1/responses \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":"test"}'

# Dashboard
curl -sI https://hermes.jefe.al/
# → 302 redirect to /login (expected — dashboard auth)
```

## Debugging Flow: 302 vs 404 vs 200

When testing `hermes.jefe.al/api/v1/responses`:

| HTTP response | `server` header | What it means | Fix |
|---|---|---|---|
| **302** → `/login` | `uvicorn` | Request hit the **dashboard** (port 9120), not the API | Pangolin target points to wrong port → change to 9119 |
| **302** → `/login` | (none/Pangolin) | Pangolin SSO intercepted before reaching any backend | Disable SSO on the resource |
| **404** | `Python/3.13 aiohttp` | Request hit the **API server** (port 9119) ✅ routing works, but `/api` was not stripped | Enable Path Rewriting → Strip Prefix on the target |
| **200** | `Python/3.13 aiohttp` | Everything works ✅ | — |

The `server` response header is the fastest way to identify which layer is intercepting:
- No `server` header or Pangolin-specific → Pangolin SSO layer
- `server: uvicorn` → Hermes dashboard (port 9120)
- `server: Python/3.13 aiohttp` → Hermes API server (port 9119)

## Without Strip Prefix

If stripPrefix is NOT configured, the API receives `/api/v1/responses`:
- Hermes API server (aiohttp) returns `404: Not Found`
- The `server: Python/3.13 aiohttp/3.14.1` header confirms the request reached the API server (not Pangolin or dashboard)
- This is the telltale sign: routing works, but path rewriting is missing

## Common Mistakes

1. **Assuming Pangolin only routes by hostname** — it supports path-based routing per target. Read `references/manage__resources__public__targets.md` in the `pangolin` skill.
2. **Pointing everything at port 9120** — that's the dashboard, not the API. The API is on 9119.
3. **Forgetting stripPrefix** — without it, the backend gets `/api/v1/...` instead of `/v1/...` and returns 404.
4. **Leaving SSO enabled** — the dashboard has its own auth; SSO intercepts API calls before they reach the Bearer token check.
5. **Confusing Pangolin SSO redirect with dashboard auth redirect** — both return 302 → `/login`, but the `server` header differs: Pangolin returns no `server` header (or its own), while the dashboard returns `server: uvicorn`. The API server returns `server: Python/3.13 aiohttp`. Check the header to know which layer is intercepting.
6. **Trying to create a subdomain-based path route** — Pangolin does NOT support path-based routing via subdomain (e.g. `hermes.jefe.al/api/` is NOT a separate subdomain). Path routing is configured **per target** within a single resource, not by creating new resources or subdomains.
7. **Configuring Match type but not Path Rewriting** — these are separate settings. Match type (`prefix`/`exact`/`regex`) determines WHICH requests the target handles. Path Rewriting (`stripPrefix`/`prefix`/`exact`/`regex`) determines HOW the path is transformed before forwarding. You need BOTH: match=`prefix` + rewrite=`stripPrefix`.