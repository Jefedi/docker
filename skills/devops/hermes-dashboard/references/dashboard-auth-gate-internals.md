# Dashboard Auth Gate Internals (June 2026 hardening)

## The gate: `should_require_auth()`

Location: `/opt/hermes/hermes_cli/web_server.py` ~line 400

```python
_LOOPBACK_HOST_VALUES: frozenset = frozenset({
    "localhost", "127.0.0.1", "::1",
})

def should_require_auth(host: str, allow_public: bool = False) -> bool:
    return host not in _LOOPBACK_HOST_VALUES
```

- `host == loopback` → `False` (no auth, token-based API access)
- `host != loopback` → `True` (gate engages — requires at least one provider)
- `allow_public` (legacy `--insecure`) is **ignored** — no escape hatch
- RFC1918 / CGNAT / link-local are treated as PUBLIC

## Gate enforcement at startup (~line 19173)

```python
app.state.auth_required = should_require_auth(host)
```

If `auth_required` is True and no providers are registered (`list_providers()` returns empty):
- Dashboard **refuses to start** (SystemExit)
- Error message lists skip reasons from each bundled provider
- Suggests configuring password (`dashboard.basic_auth`) or OAuth

## Auth providers

Bundled providers live in `/opt/hermes/plugins/dashboard_auth/`:

| Provider | Dir | Activates when | Auth method |
|----------|-----|----------------|-------------|
| `basic` | `basic/` | `dashboard.basic_auth.username` + `password_hash` or `password` in config.yaml | Username/password form |
| `nous` | `nous/` | Nous Portal OAuth configured | OAuth redirect |
| `self_hosted` | `self_hosted/` | `HERMES_DASHBOARD_OIDC_ISSUER` + `HERMES_DASHBOARD_OIDC_CLIENT_ID` env vars | OIDC redirect + PKCE |
| `drain` | `drain/` | — | Placeholder/legacy |

Providers register via plugin hook `ctx.register_dashboard_auth_provider` at startup.

## Login API

### Password login (basic provider)
```
POST /auth/password-login
Content-Type: application/json

{"provider": "basic", "username": "...", "password": "..."}
```
- `provider` field is **required** (omitting → 422)
- Success: `{"ok": true, "next": "/"}` + Set-Cookie session
- Failure: `{"detail": "wrong password"}` (HTTP 401, generic to prevent username oracle)

### OAuth login
```
GET /auth/login?provider=self-hosted&next=/
```
Redirects to OIDC issuer's `/authorize` endpoint with PKCE challenge.

## Password hash format (basic provider)

```python
from plugins.dashboard_auth.basic import hash_password
hash_password("mypassword")
# → "scrypt$16384$8$1$<salt_b64>$<dk_b64>"
```

- scrypt parameters: N=16384, r=8, p=1, dklen=32
- Salt: random 16 bytes, base64-encoded
- Stored in `dashboard.basic_auth.password_hash` in config.yaml

## Session token (loopback mode)

When `auth_required` is False (loopback bind):
- `HERMES_DASHBOARD_SESSION_TOKEN` env var (or auto-generated random)
- Sent via `X-Hermes-Session-Token` header or `Authorization: Bearer <token>`
- SPA HTML gets the token injected automatically
- WS endpoints accept `?token=<session_token>` query param

## Middleware flow

`gated_auth_middleware` (in `dashboard_auth/middleware.py`):
1. If `app.state.auth_required` is False → pass through (no-op)
2. Check for valid session cookie → pass if valid
3. Check for valid session token header → pass if valid
4. Otherwise → redirect to `/login` (password) or `/auth/login` (OAuth)

## Docker container constraint

In the Hermes Docker container:
- `/opt/hermes/` is owned by `root:root` (read-only for `hermes` user)
- Cannot `sed`, `patch`, or write to source files directly
- Workaround: PYTHONPATH override (copy files to `/opt/data/hermes_patch/`)
- Or: configure auth via `.env` / `config.yaml` (writable by `hermes` user)