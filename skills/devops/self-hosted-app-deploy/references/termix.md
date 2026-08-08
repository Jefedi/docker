# Termix (Web-based SSH/RDP Terminal)

Termix is a web-based terminal providing SSH and RDP (via Apache Guacamole/guacd) access through the browser. Deployed with Pocket ID OIDC authentication behind Pangolin.

## Architecture

- **termix** — main web app (port 8080 internally, exposed on 127.0.0.1:8748)
- **guacd** — Apache Guacamole daemon, required for RDP/VNC connections. Must be on same Docker network as termix.
- **Pocket ID** — OIDC identity provider (already deployed at id.jefe.ovh)

## docker-compose.yml

```yaml
services:
  termix:
    image: ghcr.io/lukegus/termix:release-2.3.2
    container_name: termix
    restart: unless-stopped
    ports:
      - '127.0.0.1:8748:8080'
    volumes:
      - ./termix-data:/app/data
    env_file:
      - .env
    environment:
      PORT: '8080'
      GUACD_URL: 'tcp://guacd:4822'
      OIDC_FORCE_HTTPS: 'true'
      OIDC_ALLOW_REGISTRATION: 'false'
      ALLOW_REGISTRATION: 'false'
      LOG_LEVEL: 'info'
    depends_on:
      - guacd
    networks:
      - termix-net

  guacd:
    image: guacamole/guacd:1.6.0
    container_name: guacd
    restart: unless-stopped
    networks:
      - termix-net

networks:
  termix-net:
    driver: bridge
```

## .env (OIDC — Pocket ID)

```
OIDC_CLIENT_ID=<from Pocket ID>
OIDC_CLIENT_SECRET=<from Pocket ID>
OIDC_ISSUER_URL=https://id.jefe.ovh
OIDC_AUTHORIZATION_URL=https://id.jefe.ovh/authorize
OIDC_TOKEN_URL=https://id.jefe.ovh/api/oidc/token
OIDC_USERINFO_URL=https://id.jefe.ovh/api/oidc/userinfo
```

## Pocket ID Setup

1. Create OIDC client named "Termix"
2. **Callback URL**: `https://termix.jefe.al/users/oidc/callback` — must match EXACTLY what Termix builds (protocol + domain + path, no trailing slash)
3. Copy Client ID, Client Secret, and all URLs into `.env`

## Key Environment Variables

| Variable | Required | Notes |
|---|---|---|
| `OIDC_CLIENT_ID` | Yes | From Pocket ID |
| `OIDC_CLIENT_SECRET` | Yes | From Pocket ID |
| `OIDC_ISSUER_URL` | Yes | Pocket ID base URL |
| `OIDC_AUTHORIZATION_URL` | Yes | Pocket ID /authorize |
| `OIDC_TOKEN_URL` | Yes | Pocket ID /api/oidc/token |
| `OIDC_USERINFO_URL` | No | Pocket ID /api/oidc/userinfo |
| `OIDC_FORCE_HTTPS` | No | Set `true` behind TLS-terminating proxy (Pangolin). Without this, callback URL is built as http:// and won't match Pocket ID registration |
| `OIDC_ALLOW_REGISTRATION` | No | Distinct from `ALLOW_REGISTRATION`. If `true`, new accounts created via OIDC even when general registration is off |
| `OIDC_SCOPES` | No | Defaults to `openid email profile`. Add `groups` for admin group support |
| `OIDC_ADMIN_GROUP` | No | Group name whose members become Termix admins (requires `groups` scope) |

## Critical Pitfalls

### `env_file` missing → OIDC vars never loaded
If OIDC vars are in a `.env` file but `env_file: .env` is not in the compose service definition, the vars never reach the container. Termix starts without OIDC and shows no error — it just falls back to local auth silently.

### `OIDC_ALLOW_REGISTRATION` vs `ALLOW_REGISTRATION`
Two separate flags. `ALLOW_REGISTRATION: false` blocks general registration but does NOT block OIDC-created accounts. Set `OIDC_ALLOW_REGISTRATION: false` explicitly to prevent new accounts via SSO.

### Callback URL mismatch
Pocket ID rejects auth with: `The redirect_uri 'https://termix.jefe.al/users/oidc/callback' is not registered for this client`. Fix: add the exact callback URL in Pocket ID client config. Verify:
1. Protocol is https (enforced by `OIDC_FORCE_HTTPS: true`)
2. Domain matches Pangolin resource
3. Path is `/users/oidc/callback` (Termix-specific)
4. No trailing slash, no spaces
5. Remove any stale callback URLs from Pocket ID (e.g. old domains, example.com placeholders)

### Clipboard paste not working in RDP sessions
Known bug (Termix GitHub issue #581, fixed in PR #666, merged April 2026). Clipboard sync host→RDP was broken. Workarounds:
- Right-click in RDP area → Paste
- Shift+Insert instead of Ctrl+V
- Add paste icon to toolbar (Settings → Toolbar → enable Paste)
- Check browser clipboard permissions: site settings → Clipboard → Allow
- Ensure "Enable Clipboard" is checked in the RDP connection settings within Termix
- Update to latest Termix image if running a pre-fix version

## Docs References
- Pocket ID Termix setup: https://pocket-id.org/docs/client-examples/termix
- Termix OIDC docs: https://docs.termix.site/features/authentication/oidc