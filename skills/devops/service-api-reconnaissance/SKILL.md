---
name: service-api-reconnaissance
title: Service API Capability Assessment
description: Research a new service's API capabilities when given an API key — discover available endpoints, understand auth model, map read vs write operations, identify security restrictions, and report findings. Read-only by default — no execution without explicit approval.
tags: [api, reconnaissance, integration, capabilities, read-only, assessment]
---

# Service API Capability Assessment

When a user provides API access to a new service (API key, token, or URL), research what the API can do **without executing anything** unless explicitly told to. The goal is a comprehensive capability report from documentation and source code alone.

## When to use this skill

- User gives you an API key/token/URL for a new or unfamiliar service
- User asks you to "see what you can do" or "check the possibilities"
- You need to understand a service's API surface before integrating it
- **Trigger phrase**: user says "je vais te filer la clé API" (or any "here's an API key" variant)

## User preference (Jefe-specific)

Jefe's explicit workflow when giving API access:
1. **First**: research and document ALL available endpoints and what they do
2. **Second**: report what's possible, what's read vs write, what's restricted
3. **Third**: wait for explicit go-ahead before executing ANYTHING
4. **NEVER execute, NEVER break, NEVER modify** without explicit confirmation

Save his preference to memory:
> "When given API access to a new service, research and report capabilities without executing anything unless explicitly told otherwise."

## Workflow

### 1. Identify the service
- Search the web for the service name
- Find the GitHub repo, official docs, and any API reference pages
- **Key question**: is it self-hosted or SaaS? Self-hosted means you can read the actual source code for routes

### 2. Find API documentation
Search sources in this order:

| Source | Example URL pattern |
|--------|-------------------|
| Official API docs | `docs.<service>.com/api` or `<service>.github.io/docs` |
| GitHub repo README | `github.com/<org>/<repo>` |
| GitHub source code | `github.com/<org>/<repo>/tree/main/src/backend/routes` |
| Raw GitHub API files | `api.github.com/repos/<org>/<repo>/contents/src/routes` |
| LLM context generators | `uithub.com/<org>/<repo>` or `github.com/<org>/<repo>/blob/main/` |
| OpenAPI spec | Look for `openapi.json`, `swagger.json`, `api.yml` |
| Package docs | npm/PyPI/packagist for client libraries |

### 3. Map the API surface
For each endpoint discovered, document:
- **Path** and HTTP method
- **What it does** (CRUD? Execute? Status?)
- **Authentication required** (some endpoints may be public)
- **Read vs write** — flag dangerous endpoints (DELETE, force, shutdown, etc.)
- **Input/output shape** — what parameters, what responses look like
- **Security restrictions** — are sensitive fields stripped from responses?

### 4. Assess the auth model
- What scope does the API key have? (user-scoped, admin, read-only?)
- What format is the key? (`tmx_xxx`, `sk-xxx`, etc.)
- Which endpoints require additional auth? (wallet signatures, 2FA, etc.)

## Report findings
Structure the report clearly:

```
## What I can do (read-only)
✅ List all X (hosts, users, configs, etc.)
✅ View status/stats/monitoring
✅ Export configurations
✅ Read file contents

## What requires write access (blocked until approved)
⚠️ Create/modify/delete endpoints
⚠️ Execute commands
⚠️ Destructive operations (force delete, shutdown, restart)

## What's explicitly restricted
❌ Password/credential exposure (stripped from API responses)
❌ Admin-only operations (if key is user-scoped)
```

## 🔍 SPA Behind Reverse Proxy: Architecture Discovery

When a service's frontend is proxied through Pangolin (or any reverse proxy) but the backend API is **not** exposed, you must discover the architecture through indirect methods. This technique applies when direct API calls fail (e.g. the domain returns an SPA HTML shell instead of JSON).

### 1. Identify the service

- Web search for the service name + "github" or "docker"
- **Compare documented vs actual deployment:** default Docker Compose may expose port X, but actual deployment may differ (different port, separate API backend, etc.)
- Check version: look for version strings in the SPA HTML or JS bundle (`var oe=\`termix_client_cache_version\`,se=\`2.3.2\``)

### 2. Download and analyze the SPA JS bundle

The SPA contains all frontend logic in one or more JS bundle files. These bundles reveal the API architecture:

| What to look for | Why it matters |
|---|---|
| `fetch(url, ...)` calls | Tells you which API endpoints exist and their base URL |
| `WebSocket(url)` or `new WebSocket` | Reveals real-time connections (SSH terminals, live updates) |
| `localhost:<port>` references | Backend API listening on a local-only port — **not exposed** through the proxy |
| `window.electronAPI` | Indicates the SPA is designed to run inside **Electron/desktop app**, not standalone web |
| `axios` / API client setup | Base URL configuration, auth header patterns (`Authorization: Bearer tmx_`) |
| Route paths (`/api/...`, `/db/...`) | API path structure — combine with source code to map the full surface |
| Version strings | Confirm which version is deployed |

**How to do it:**
```bash
# Find JS bundles in the SPA
curl -sk https://service.domain/assets/index-*.js -o bundle.js

# Extract localhost references (API base URL)
grep -o 'http://localhost:[0-9]*' bundle.js | sort -u

# Extract fetch calls
grep -c 'fetch(' bundle.js           # How many API calls
grep -c 'WebSocket' bundle.js        # Does it use WS?

# Extract embedded URLs
grep -oP '(https?|wss?)://[^\",;\`)]+' bundle.js | sort -u

# Check for Electron/desktop indicators
grep -c 'electronAPI' bundle.js
grep -c 'ReactNativeWebView' bundle.js
```

⚠️ **BusyBox grep** (inside Alpine Docker containers) lacks `-P` (Perl regex). Use `-E` with escaped patterns instead, or copy the file out and analyze with GNU grep.

### 3. Map the deployment architecture

**Cross-reference what you discover from the bundle against the documented architecture:**

| Bundle finding | What it implies |
|---|---|
| `fetch('http://localhost:30001/health')` | Backend health API on port 30001, **localhost only** — not part of the reverse proxy |
| `electronAPI.oidcSystemBrowserAuth(...)` | The app is designed as a **desktop app** (Electron) with its own auth flow |
| No `/api/...` paths in the bundle | The SPA doesn't call a REST API directly from the browser — the real API is consumed by the Electron backend |
| `caches`, `serviceWorker` | PWA — may work standalone but the API is still desktop-only |

**Common architecture patterns found this way:**
- **Desktop-app-behind-proxy**: App runs as Electron on a server, web UI proxied via Pangolin, but the JS expects to reach the API on `localhost:<port>` (only works from the server itself)
- **Proxy-frontend-only**: Reverse proxy serves the SPA but doesn't proxy API paths — browser JS can't reach the backend
- **Local-agent model**: The service runs a local agent (port X) for health checks and a separate backend (port Y) for business logic

### 4. Verify network accessibility

When you know the backend port but can't reach it:

```bash
# Step 1 — Check if you're on the same mesh/network
ip addr show | grep "inet "

# Step 2 — Use nmap on the site's mesh address
# (For Pangolin: find siteAddresses from the site resource config)
nmap -sT -p <backend_port>,<other_ports> <mesh_site_ip>

# Step 3 — Install tools inside network container if needed
docker exec <container> apk add --no-cache curl nmap

# Step 4 — Check iptables (common blocker on dual-mesh hosts)
# Tailscale's ts-input chain drops CGNAT traffic from non-tailscale interfaces
iptables -L ts-input -nv 2>/dev/null | grep "100\.64\.0\.0/10"
# If DROP rule found: iptables -I ts-input 1 -i pangolin -j ACCEPT

# Step 5 — Report which ports are reachable vs. localhost-only
```

### 5. Report the real architecture

When the backend API is **localhost-only** (not reachable from your location), say so clearly and offer remediation options:

```
## Architecture (from SPA analysis)
- **Frontend**: served via <proxy> at <url> (port 443)
- **Backend API**: port <PORT> on **127.0.0.1** (localhost-only)

## API key status
❌ **API unreachable** — backend listens on localhost only, not exposed through the reverse proxy

## Options to make the API reachable
1. Add path-based routing to proxy `/api/*` → backend:PORT through the existing proxy
2. Expose backend port as a separate resource/site resource
3. SSH access to the server for local API calls
```
