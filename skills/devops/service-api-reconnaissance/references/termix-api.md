# Termix API — Capability Reference

**Date researched**: June 13-14, 2026
**Version**: v2.3.2 (latest)
**Source**: GitHub source code + docs.termix.site

## Overview

Termix is a self-hosted, open-source SSH & remote desktop management platform (Termius alternative). Apache 2.0 license. 13.5k stars.

- **GitHub**: https://github.com/Termix-SSH/Termix
- **Docs**: https://docs.termix.site/
- **API keys docs**: https://docs.termix.site/api-keys/
- **Tech**: Node.js/Express backend, React/Tailwind frontend, SQLite (encrypted)

## Jefe's Deployment Architecture (vs Default)

| Aspect | Default Docker (docs) | Jefe's deployment |
|--------|----------------------|-------------------|
| Frontend port | 8080 (standalone) | 443 (via Pangolin at `termix.jefe.ovh`) |
| Backend API port | 8080 (same process) | **8748** and/or **30001** on localhost only |
| Guacd | Separate container | Unknown if used |
| Access method | Browser directly | SPA frontend proxied via Pangolin, API **not proxied** |
| Auth | Internal login/register | Internal + OIDC via UI, API key for programmatic |

**Key discovery**: Jefe's Termix runs as an **Electron/desktop-mode** app. The frontend JS bundle reveals:
- `fetch(\`http://localhost:30001/health\`)` — API health check on localhost only
- `window.electronAPI` — Electron desktop integration
- `window.ReactNativeWebView` — mobile app variant
- The backend listens on `127.0.0.1:8748` (from Pangolin site resource config) and/or `30001`

**Impact**: The Termix API key (`tmx_xxx`) is valid but **cannot be used remotely** — the API is only accessible from localhost on the VPS. No Pangolin path-based routing exists for `/api/*`.

## Authentication

- **API Key format**: `tmx_xxx`
- **Header**: `Authorization: Bearer tmx_your_token_here`
- **Scope**: User-scoped — the key acts as the user it was created for
- **Access**: Any endpoint that requires a logged-in user

## Backend API Routes (from source)

The Express router mounts routes across these files in `src/backend/database/routes/`:

### Host Management (`host.ts` — 71KB, largest route file)
| Method | Path | Description | R/W |
|--------|------|-------------|:--:|
| GET | `/db/host` | List all hosts (own + shared) | R |
| GET | `/db/host/:id` | Single host details | R |
| POST | `/db/host` | Create a new SSH/ RDP/ VNC/ Telnet host | W |
| PUT | `/db/host/:id` | Update host config | W |
| POST | `/quick-connect` | Temporary connection (no storage) | W |
| GET | `/db/host/:id/password` | Get password for clipboard | R |
| GET | `/db/host/:id/export` | Export single host config | R |
| GET | `/db/hosts/export` | Export ALL hosts | R |

### Sub-routers under host management
| File | Purpose |
|------|---------|
| `host-internal-routes.ts` | Internal host operations |
| `host-file-manager-bookmark-routes.ts` | File manager bookmarks |
| `host-command-history-routes.ts` | SSH command history |
| `host-autostart-routes.ts` | Auto-start host connections |
| `host-folder-routes.ts` | Host folder organization |
| `host-bulk-routes.ts` | Bulk host operations |
| `host-opkssh-routes.ts` | OPKSSH key deployment |
| `host-network-routes.ts` | Network configuration |

### Credentials & Keys
| File | Description |
|------|-------------|
| `credentials.ts` | SSH passwords, keys, sudo passwords CRUD |
| `credential-key-routes.ts` | SSH key-specific operations |
| `credential-deploy-routes.ts` | Deploy SSH keys to remote hosts |

### User Management
| File | Description |
|------|-------------|
| `user-admin-routes.ts` | Admin operations on users |
| `user-api-key-routes.ts` | API key CRUD |
| `user-data-access-routes.ts` | Data access permissions |
| `user-oidc-account-routes.ts` | OIDC account linking |
| `user-password-reset-routes.ts` | Password reset flow |
| `rbac.ts` | Role-based access control (44KB) |

### Other Modules
| File | Description |
|------|-------------|
| `snippets.ts` / `snippets-reorder.ts` | Reusable command snippets |
| `alerts.ts` | System alerts |
| `terminal.ts` | Terminal session data |
| `open-tabs.ts` | Persistent SSH tabs |
| `network-topology.ts` | Network graph data |
| `c2s-tunnel-presets.ts` | Client-to-server tunnel presets |
| `delete-user-data.ts` | GDPR-style data deletion |

### SSH/Infrastructure Backend Modules
| Path | Description |
|------|-------------|
| `src/backend/ssh/terminal.js` | WebSocket SSH terminal |
| `src/backend/ssh/tunnel.js` | SSH tunnel management |
| `src/backend/ssh/file-manager.js` | File manager (SFTP) operations |
| `src/backend/ssh/server-stats.js` | CPU, RAM, disk, network metrics |
| `src/backend/ssh/docker.js` | Docker container management |
| `src/backend/ssh/docker-console.js` | Docker exec terminal |
| `src/backend/dashboard.js` | Dashboard data |
| `src/backend/guacamole/` | RDP/VNC via Guacamole |

## Security Model (v2.3.2)

- **Sensitive fields stripped**: passwords, SSH keys, sudo passwords are replaced with boolean indicators in API responses
- **MFA enforcement**: password + TOTP required for critical operations
- **Session ownership**: file manager endpoints verify session ownership
- **Tunnel kill restricted**: only exact `tunnelMarker` matching allowed
- **CORS**: configurable via `CORS_ALLOWED_ORIGINS` env var
- **SSH keepalive**: 30s/3 interval (prevent NAT/firewall drops)
- **Database**: Encrypted SQLite (per-user DEK + system key)

## What the API key can and cannot do

### ✅ Read (API key can do this)
- List all hosts, credentials metadata, users
- View host stats, Docker containers, network topology
- Export configurations
- Read file contents (via file manager)
- View active tunnels, alerts, command history
- Access snippets and bookmarks

### ⚠️ Write (would need explicit approval)
- Create/modify/delete hosts, users, credentials
- Execute SSH commands, deploy keys
- Manage tunnels, Docker containers
- Export/import data

### ❌ Blocked by design
- Read plaintext passwords or SSH keys from API (stripped since v2.3.2)
- Server restore without backup file
- Non-TOTP MFA operations

## Installation Reference

```yaml
services:
  termix:
    image: ghcr.io/lukegus/termix:latest
    container_name: termix
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - termix-data:/app/data
    environment:
      PORT: "8080"
      GUACD_HOST: "guacd"
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
```
