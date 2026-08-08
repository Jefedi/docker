---
name: pangolin-proxy-wizard
title: Pangolin Proxy Wizard
description: Quickly expose a local service through Pangolin — create resource, set domain, configure SSL/proxy, optional Uptime Kuma check.
tags: [pangolin, proxy, reverse-proxy, ssl, domain, homelab]
---

# Pangolin Proxy Wizard

One-shot wizard to expose any local service through Jefe's Pangolin instance.

## ⚠️ Load This Skill First

**Before any Pangolin debugging session, load this skill with `skill_view(name='pangolin-proxy-wizard')`.** This skill contains the critical "site resource" requirement, auth-state debugging trap, SSO reset bug, and health check pitfalls. Loading it first prevents hours of trial-and-error debugging.

## Prerequisites

### Newt Client (Pangolin CLI) Connection

Before private resources through Newt sites work, the machine must run a Pangolin CLI client. See `references/pangolin-cli-docker-setup.md` for Docker Compose setup.

**⚠️ Critical: Tailscale conflict on dual-mesh hosts.** If Tailscale also runs on this host, its `ts-input` iptables chain drops all CGNAT return traffic from the Pangolin interface. Apply this fix immediately after starting the Pangolin CLI client:

```bash
iptables -I ts-input 1 -i pangolin -j ACCEPT
```

Without this fix, the mesh shows as connected but all private resource traffic times out silently. See the reference file for persistence options.

- Pangolin API key in `/root/.hermes/.env` as `PANGOLIN_API_KEY`
- Service must be running and reachable from the Pangolin server (or via the Newt tunnel)
- **Newt tunnel must be running** (see §3) — without it, all targets through site 28 return 504
- Docker containers can bind to **127.0.0.1** (preferred for security) when using the Newt tunnel, since the Newt client runs on localhost

## Workflow

### 🚨 CRITICAL: Public Resource + Target ≠ Working Service (Missing Site Resource)

**Creating a public resource and target is NOT sufficient for an HTTP service on a Newt site.** You MUST also create a **site resource** (`mcp_pangolin_create_org_by_orgId_site_resource`) — otherwise the Newt client never gets the routing rule to forward traffic from the exit node to the local service.

**What happens without a site resource:**
- The public resource and target are created ✅
- DNS resolves, SSL terminates, Pangolin auth works ✅
- But the Newt client logs show `"Started tcp proxy to 127.0.0.1:PORT"` WITHOUT a corresponding `"Added target subnet from X to Y"` route ❌
- Authenticated users get **"no available server"** — including in incognito/private browsing
- The VPS curl shows **302** (auth page — misleading, the agent's browser isn't authenticated so it never hits the routing failure)

**How to spot a missing site resource:**
```python
# Check if the site resource exists
mcp_pangolin_org_by_orgId_site_by_siteId_resources(
    orgId="jorganisation", siteId=28
)
# Look for your subdomain in the results. If missing → that's the problem.
# Existing site resources show mode, destination, destinationPort, aliasAddress.
```

**How newt logs reveal the gap:**
- **WITHOUT site resource:** `"Started tcp proxy to 127.0.0.1:9119"` (only the local proxy, no route from exit node)
- **WITH site resource:** `"Added target subnet from 100.90.128.X/32 to 100.96.128.Y/32 rewrite to  with port ranges: [{443 443 tcp} {80 80 tcp} {0 0 udp}]"` (the route that actually carries traffic from Pangolin through the tunnel)

**The fix — create a site resource after the public resource + target:**

```python
# This is the MISSING step — do it after creating the public resource + target
mcp_pangolin_create_org_by_orgId_site_resource(
    orgId="jorganisation",
    name="Service Name",
    mode="http",                    # REQUIRED — "host", "cidr", or "http"
    destination="127.0.0.1",       # local IP of the service
    destinationPort=PORT,           # local port of the service
    subdomain="myservice",          # subdomain (must match public resource)
    domainId="ykx3vzina5zahuf",    # domain ID for jefe.al
    scheme="http",                  # backend scheme
    ssl=True,                       # terminate TLS at Pangolin
    siteId=28,                      # site where the Newt client runs
    enabled=True,
    userIds=[],                     # REQUIRED — can be empty
    roleIds=[],                     # REQUIRED — can be empty
    clientIds=[]                    # REQUIRED — can be empty
)
```

**⚠️ Dev subdomain SSO consistency:** When creating a subdomain resource (`dev.trakii.tv`, `api.trakii.tv`) on an existing domain, the SSO setting should match the parent. If `trakii.tv` has `sso: false` (app handles its own auth), `dev.trakii.tv` should also have `sso: false` — otherwise Pocket-ID auth is required on dev but not on prod. Check the parent first: `mcp_pangolin_resource_by_resourceId(resourceId=PARENT_ID)['sso']`.

After creation, verify newt picked up the route:
```bash
systemctl restart newt-client && sleep 5
journalctl -u newt-client --since "5 seconds ago" --no-pager | grep "Added target subnet.*100.96.128"
# Should show a line with the new aliasAddress (e.g. 100.96.128.20)
```

**Why both are needed:**
| Layer | What it does | Created by |
|-------|-------------|------------|
| **Public resource** (org level) | DNS, SSL cert, external domain, auth config | `create_org_by_orgId_resource` |
| **Target** (on public resource) | Tells Pangolin WHERE to forward traffic | `create_resource_by_resourceId_target` |
| **Site resource** (on site) | Tells the Newt client HOW to route from exit node | `create_org_by_orgId_site_resource` |

The public resource + target = the "control plane" config. The site resource = the "data plane" route. Both are needed.

### 1. Gather Details
Ask the user or use existing context:
- Service name (e.g. "Grafana", "WebUI")
- Internal URL (e.g. `http://100.64.0.9:3000` or `http://localhost:9000`)
- Domain to use:
  | Domain | domainId | Notes |
  |--------|----------|-------|
  | `*.jefe.al` | `ykx3vzina5zahuf` | Main domain (internal services) |
  | `*.jefe.ovh` | `domain1` | Secondary domain (n8n, arr stack) |
  | `*.losgalactique.fr` | `51vbysoaydeg6cr` | Public (Pterodactyl, Paymenter) |
  | `*.trakii.tv` | `domain4` | Trakii project domain |
- SSL (yes/no — default yes)
- Org: `jorganisation` / Site: use existing (Hetzner site=6, Hermes VPN site=28, jTower site=29, etc.)

### 1b. Identify the Correct Site (CRITICAL — avoid wrong-site targets)

**🚨 Common mistake**: Creating a target on the wrong Newt site. The target site MUST be the one whose Newt client runs ON the machine where the container is deployed.

**⚠️ FIRST STEP: Always check the machine's external IP before picking a site.**

The hostname alone is unreliable — especially in Docker containers where hostnames can be generic (e.g. `Debian-trixie-latest-amd64-base`). Run this FIRST:

```bash
curl -s https://api.ipify.org
# → e.g. 37.27.126.113 = Hetzner (site 6)
# → e.g. 178.105.179.232 = Hermes VPN (site 28)
```

**🚨 Common pitfall from a real session:** I assumed site 28 (Hermes VPN) because the site map says "This VPS" for site 28. But the user called their Hetzner server "Edner" / "main server" (IP 37.27.126.113 = site 6). Always verify by IP, never by the user's name for the machine. A user saying "main server" or a custom name doesn't tell you which site it is.

**Procedure to verify after IP check:**

```bash
# 1. Cross-reference the external IP with the Site Map below
# 2. Read the local Newt client's ID (if installed)
cat /root/.config/newt-client/config.json 2>/dev/null
# Look for: "id": "fjuyrsrb09ufxq3" (this machine's newtId)
```

```python
# 3. Cross-reference against Pangolin sites
# (Use mcp_pangolin_site_by_siteId or mcp_pangolin_org_by_orgId_sites)
# Find the site whose 'newtId' matches the local config's 'id'
```

**Site map for this infrastructure:**
| Site ID | Name | newtId | Machine |
|---------|------|--------|---------|
| 28 | Hermes VPN | `fjuyrsrb09ufxq3` | **This VPS** (178.105.179.232) |
| 6 | Hetzner | `ist4scbqlgo0yvc` | **Other Hetzner machine** (37.27.126.113) |
| 18 | Jnas | `jxwosr4te0n24bs` | NAS (100.64.0.3) |
| 1 | homeassistant | `5dz1vc8kmn5fj6y` | HA VM (100.64.0.8) |
| 29 | jTower | `Y7/khtREIx/Kygi2VbLxFQuSXyolwiPHcoeExBn2vAw=` | **Windows daily driver** (192.168.1.12) |

**Signs you have the wrong site:**
- Pangolin shows "no available server" even though `curl 127.0.0.1:<port>` works locally
- The target's siteId doesn't match the newtId from `/root/.config/newt-client/config.json`
- The site name doesn't match the machine where the container runs

**Fix**: Delete the wrong target (`mcp_pangolin_delete_target_by_targetId`), then recreate on the correct siteId.

### 0. Verify API Key First

Before anything, check if the Pangolin API key is valid. The key stored in `/root/.hermes/.env` may be stale:

```python
import json, urllib.request, subprocess

# Get key from Bitwarden
k = subprocess.run(['bw', 'get', 'password', 'd5718a33-6cd3-442b-8d00-d98ddf96bc5c'],
    capture_output=True, text=True).stdout.strip()

# Test against the API
h = "Authorization:"; h += " Bearer "; h += k
headers = {h.split(":")[0]: h.split(":")[1].strip(), "Content-Type": "application/json"}
req = urllib.request.Request("https://api.jefe.ovh/v1/org/jorganisation", headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("✅ Key OK from Bitwarden")
except urllib.error.HTTPError:
    print("❌ Key invalid — try a different Bitwarden item or create a new API key")
```

If the .env key is stale, update it:

```python
with open('/root/.hermes/.env') as f:
    lines = f.readlines()
with open('/root/.hermes/.env', 'w') as f:
    for line in lines:
        if line.startswith('PANGOLIN_API_KEY='):
            f.write(f'PANGOLIN_API_KEY={k}\n')
        else:
            f.write(line)
print("✅ .env updated")
```

### 2. Create Pangolin Resource
First, determine which site to use:
- If the service runs on this machine (100.64.0.9) → site **28** (Hermes VPN)
- If the service runs on the Hetzner server → site **6** (Hetzner)
- If the service is the NAS (192.168.1.92) → site **18** (Jnas)
- Other → ask (site 1 = Home Assistant)

Then create the resource & target in two steps:

**Step A — Create resource (org level):**
```python
import json, urllib.request

with open('/root/.hermes/tmp_pangolin_key.txt') as f:
    key = f.read().strip().split('=', 1)[1]

BASE = "https://api.jefe.ovh/v1"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# Create resource at org level
body = {
    "name": "<Service Name>",
    "subdomain": "<subdomain>",
    "domainId": "ykx3vzina5zahuf",  # jefe.al domain
    "http": True,
    "protocol": "tcp"
}
req = urllib.request.Request(
    f"{BASE}/org/jorganisation/resource",
    data=json.dumps(body).encode(), headers=headers, method="PUT"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    r = json.loads(resp.read())
    RESOURCE_ID = r['data']['resourceId']
    print(f"Resource ID: {RESOURCE_ID}")
    print(f"URL: https://{r['data']['fullDomain']}")
```

**Step B — Add target (API — verified working):**
```python
# ⚠️ IP choice matters:
#   - Site 28 (Hermes VPN, Newt client on this server): use 127.0.0.1
#     → Newt runs locally, so loopback is reachable and more secure
#   - Other sites (Hetzner 6, JNAS 18, HA 1): use their local IPs
#   - If Newt tunnel is DOWN, use public IP 178.105.179.232 as a TEMPORARY workaround
target_body = {
    "siteId": 28,             # 28=Hermes VPN, 6=Hetzner, 18=JNAS, 1=HomeAssistant
    "ip": "127.0.0.1",       # 127.0.0.1 when Newt runs locally; local IP for other sites
    "port": 4210,
    "method": "http",         # REQUIRED — without this the proxy returns 503
    "enabled": True,
}

req = urllib.request.Request(
    f"{BASE}/resource/{RESOURCE_ID}/target",
    data=json.dumps(target_body).encode(), headers=headers, method="PUT"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    t = json.loads(resp.read())
    print(f"Target ID: {t['data']['targetId']} → {t['data']['ip']}:{t['data']['port']}")
```

⚠️ **The endpoint `PUT org/{orgId}/site/{siteId}/resource` is broken** — it always returns "Validation error: Unrecognized key: 'siteId'" regardless of body. Do NOT use it.

**Step C — Restart Newt client on the target machine (new resources only):**
After creating a new resource + target, the Newt client on the target site may take several minutes to discover the new target — or may never discover it without a restart:

```bash
systemctl restart newt-client
# Wait 3s, then verify:
systemctl is-active newt-client
```

This is **not** needed when updating an existing target's port/IP — Newt picks those up within seconds. Only required for brand-new targets on sites where the client was already running.

### 3. Ensure Newt Tunnel Is Running

The Hermes VPN (site 28) requires a Newt tunnel process running on this machine:

```bash
# Start the Newt tunnel (runs as a background daemon)
newt client
```

The client loads config automatically from `~/.config/newt-client/config.json`.  
When it connects, it logs:
```
INFO: Tunnel connection to server established successfully!
INFO: Started tcp proxy to 127.0.0.1:3100
```

Verify the site is online via the API:
```python
api("GET", "org/jorganisation/sites")
# Look for siteId=28 → online=True
```

If the Newt tunnel is NOT running, targets through site 28 return **504 Gateway Timeout**.

### 3b. Post-Reboot / Recovery
The Newt tunnel does NOT auto-start. After a server reboot or if the process crashes:
1. Restart it: `newt client` in background
2. Wait ~3s for `"Tunnel connection established"`
3. Then the Pangolin resources start working again

### 4. Verify
```bash
curl -s -H "Authorization: Bearer $PANGOLIN_API_KEY" \
  "https://api.jefe.ovh/v1/resource/$RESOURCE_ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('health'), d.get('fullDomain'))"
```

Or simply:
```bash
curl -skL https://<subdomain>.jefe.al/index.html
```
Should return 200 if everything works.

### 5. ⚠️ UPDATED: Standard Resource + Target + Site Resource (Three-Layer Pattern)

**Existing docs (pre-2026-06-08) incorrectly presented public resources and site resources as alternatives. They are COMPLEMENTARY for HTTP services routed through Newt sites.**

A working HTTP proxy through a Newt site requires ALL THREE layers:

| Step | API Call | What it creates | Required? |
|------|----------|----------------|-----------|
| 1 | `create_org_by_orgId_resource` | Public resource (DNS, SSL, auth config) | ✅ Yes |
| 2 | `create_resource_by_resourceId_target` | Target (tells Pangolin which site & port) | ✅ Yes |
| 3 | `create_org_by_orgId_site_resource` | **Site resource** (tells Newt client how to route from exit node) | ✅ **YES — often missed** |

**The three-step workflow (complete):**

```python
# Step 1 — Create public resource (standard)
body = {"subdomain": "myservice", "name": "My Service",
        "domainId": "ykx3vzina5zahuf", "protocol": "tcp", "http": True}
req = urllib.request.Request(
    "https://api.jefe.ovh/v1/org/jorganisation/resource",
    data=json.dumps(body).encode(), headers=headers, method="PUT")
with urllib.request.urlopen(req) as resp:
    resource_id = json.loads(resp.read())["data"]["resourceId"]

# Step 2 — Add target on the VPN site
target_body = {"siteId": 28, "ip": "127.0.0.1", "port": PORT,
               "method": "http", "enabled": True}
req = urllib.request.Request(
    f"https://api.jefe.ovh/v1/resource/{resource_id}/target",
    data=json.dumps(target_body).encode(), headers=headers, method="PUT")
with urllib.request.urlopen(req) as resp:
    target_id = json.loads(resp.read())["data"]["targetId"]

# Step 3 — Create site resource (THE MISSING PIECE)
# Without this, Newt never creates the exit-node routing rule
req2 = urllib.request.Request(
    f"https://api.jefe.ovh/v1/org/jorganisation/site-resource",
    data=json.dumps({
        "name": "My Service",
        "mode": "http",
        "destination": "127.0.0.1",
        "destinationPort": PORT,
        "subdomain": "myservice",
        "domainId": "ykx3vzina5zahuf",
        "scheme": "http",
        "ssl": True,
        "siteId": 28,
        "enabled": True,
        "userIds": [],
        "roleIds": [],
        "clientIds": []
    }).encode(), headers=headers, method="PUT")
with urllib.request.urlopen(req2) as resp:
    sr = json.loads(resp.read())
    print(f"Site resource {sr['data']['siteResourceId']} → aliasAddress {sr['data'].get('aliasAddress')}")
```

**Verification — check newt logs for the exit-node route:**
```bash
systemctl restart newt-client && sleep 5
journalctl -u newt-client | grep "Added target subnet"
# WITHOUT site resource: only routes to 100.96.128.19 (hermes.jefe.al's network)
# WITH site resource: new routes to 100.96.128.X (new aliasAddress)
```

**Private-only (hidden behind VPN):** If the service doesn't need a public URL at all, create ONLY the site resource (step 3) without the public resource + target (steps 1-2). Use a host-mode or CIDR-mode site resource with an internal alias instead.

### 6. Optional: Uptime Kuma Monitor
If the user wants monitoring, create a monitor in Uptime Kuma (manual step or via Uptime Kuma API).

## Reference Files
- `references/pangolin-api-create-resource.md` — detailed Pangolin resource creation docs (includes Python code, site IDs, domain IDs, and delete patterns)
- `references/org-migration.md` — transfer a resource between organizations (delete from source, recreate in target, API field constraints)
- `references/pangolin-private-resources.md` — private (site) resource structure, listing, and output format for Jefe
- `references/localhost-only-iptables.md` — restrict services to loopback via iptables
- `references/sse-push-server.md` — full SSE push server implementation (DB queries, change detection, complete code)
- `references/auth-state-and-reason-codes.md` — Pangolin reason codes (101/107/299) and why authenticated vs unauthenticated users see different errors
- `references/pangolin-cli-docker-setup.md` — Pangolin CLI (Newt/OLM) Docker setup, the Tailscale ts-input iptables conflict, and fix for accessing private resources via mesh routing
- `references/site-to-public-resource-conversion.md` — convert a Site Resource (private, requires Newt client) into a Public Resource (accessible via browser); covers delete-site-resource → create-public-resource → add-target workflow, SSO default pitfall, and "no available server" troubleshooting
- `references/mcp-resource-management.md` — MCP tool workflow for creating/updating resources, managing targets, and disabling auth (SSO); covers the batch setup pattern for multi-subdomain apps
- `references/site-identification.md` — identifying the correct Newt site when hostnames are generic/ambiguous (check external IP before assuming the site)

## Hermes Desktop Remote Connection

For connecting a Hermes Desktop app (Windows/macOS/Linux) to this server's remote dashboard gateway.

### Pre-Flight Checks (do these first)

```bash
# 1. Check if dashboard is running
/opt/hermes/bin/hermes dashboard --status

# 2. If not running, start it
/opt/hermes/bin/hermes dashboard --no-open --skip-build --host 0.0.0.0 --port 9119 --insecure

# 3. Verify it responds locally
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/api/status
# → Should return 200

# 4. Find the session token
grep HERMES_DASHBOARD_SESSION_TOKEN /opt/data/.env
# → Token like: Pc51WZGHJTDR3rliEgvppHEXwjPBr+v311rkZYCA/9g=
```

### Configuration in the Desktop App

| Field | Value |
|---|---|
| **Connection Mode** | Remote gateway |
| **Remote URL** | `https://hermes.jefe.al` (NOT `.ai` — common typo!) |
| **Session token** | Paste from `HERMES_DASHBOARD_SESSION_TOKEN` in `.env`, or leave blank to keep saved token |
| **Save for next restart** | ✅ Check |
| **Then click** | **Save and reconnect** |

### Troubleshooting "Could not connect" / 502 Bad Gateway

**Symptom:** Hermes Desktop shows `Error invoking remote method 'hermes:connection': Error: Hermes backend did not become ready: 502: Bad Gateway`

**Most common cause: Pangolin resource target points to the wrong machine.**

The Pangolin resource `hermes.jefe.al` must point to the machine where the dashboard is actually running. If the dashboard is on a different machine than the Pangolin/Newt tunnel, the proxy returns 502.

**Diagnostic flow:**

```bash
# Step 1 — Is the dashboard running?
/opt/hermes/bin/hermes dashboard --status

# Step 2 — Does it respond locally?
curl -sI http://127.0.0.1:9119/api/status

# Step 3 — Can you reach it via public IP?
curl -sI http://$(curl -s ifconfig.me):9119/api/status
# If 200 → dashboard is reachable directly, Pangolin is the problem
# If timeout → firewall blocking 9119

# Step 4 — Test through Pangolin
curl -sI https://hermes.jefe.al/api/status
# 302 → SSO redirect (normal for browser, Desktop app handles this)
# 502 → Pangolin can't reach the backend → TARGET IS WRONG
```

**If 502 through Pangolin → fix the resource target:**
- Log into `https://pangolin.jefe.ovh`
- Find resource `hermes.jefe.al`
- Check the target destination — must point to the machine where the dashboard actually runs
  | If dashboard runs on... | Target should be... |
  |---|---|
  | **Edner** (37.27.126.113, site 6) | `37.27.126.113:9119` or Edner's tailscale IP |
  | **VPS** (178.105.179.232, site 28) | `127.0.0.1:9119` |
- **Wrong target = 502.** The most common case: dashboard is on Edner but target points to `127.0.0.1:9119` on the VPS where nothing listens.

**Temporary workaround (no Pangolin fix needed):**
Change Remote URL in the Desktop app to:
```
http://37.27.126.113:9119
```
⚠️ Plain HTTP, no SSL — use only temporarily. Revert to `https://hermes.jefe.al` once Pangolin target is corrected.

### Dashboard process persistence

The dashboard started via `hermes dashboard --no-open --skip-build --host 0.0.0.0 --port 9119 --insecure` runs as a foreground process. It dies if the terminal session ends, the process crashes, or the server reboots. For persistence, set up a systemd service or use supervisor (see "Server Process Management" section above).

### Reference
- Session token: stored in `.env` as `HERMES_DASHBOARD_SESSION_TOKEN`
- Dashboard config: `dashboard:` section in `config.yaml`
- API status endpoint: `/api/status` returns HTTP 200 when dashboard is healthy

### Dashboard OIDC Troubleshooting

If the browser redirects to Pocket ID login, then shows an error like:

```
Provider unreachable: OIDC token endpoint returned 401:
'{"error":"invalid_client","error_description":"client authentication failed
(e.g., unknown client, no client authentication included,
or unsupported authentication method)."}'
```

**Pocket ID requires `client_secret` at the token endpoint even when PKCE is enabled.** Despite PKCE being designed for public clients, Pocket ID rejects token exchange without client authentication. Add to `.env`:

```bash
HERMES_DASHBOARD_OIDC_CLIENT_SECRET=<the-client-secret-from-pocket-id>
```

The complete OIDC block should be:

```bash
HERMES_DASHBOARD_OIDC_ISSUER=https://id.jefe.ovh
HERMES_DASHBOARD_OIDC_CLIENT_ID=<client-id>
HERMES_DASHBOARD_OIDC_CLIENT_SECRET=<client-secret>
HERMES_DASHBOARD_PUBLIC_URL=https://hermes.jefe.al
```

Then restart the dashboard (kill the old process and re-launch with the full env from the terminal).

**To remove OIDC entirely** (fall back to self-hosted auth): delete the `HERMES_DASHBOARD_OIDC_*` lines from `.env` and restart the dashboard.
## Wildcard Certificates (DNS-01 Challenge)

### When to Use

Every Pangolin resource gets its own Let's Encrypt cert by default (HTTP-01 challenge). When you create/delete many subdomains, you hit rate limits (50 certs/week per domain). Wildcard certs (`*.jefe.al`, `*.jefe.ovh`, `*.losgalactique.fr`) cover ALL subdomains with a single cert request.

Jefe's three domains all use **Cloudflare** DNS (NS: rayden.ns.cloudflare.com + dayana.ns.cloudflare.com), which supports the DNS-01 challenge required for wildcard certificates.

### Prerequisite: Cloudflare API Token

Create a token at https://dash.cloudflare.com/profile/api-tokens with:
- Permissions: `Zone:Read` + `DNS:Edit`
- Zone resources: all domains (jefe.al, jefe.ovh, losgalactique.fr)

### Configuration

On the **Pangolin server** (Hetzner CX23, site 6), edit three files:

**1. `docker-compose.yml` — Add Cloudflare token to traefik service:**
```yaml
  traefik:
    environment:
      CLOUDFLARE_DNS_API_TOKEN: "your-token-here"     # ← ADD this
```

**2. `config/traefik/traefik_config.yml` — Change resolver from HTTP-01 to DNS-01:**
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      dnsChallenge:
        provider: "cloudflare"
      email: "admin@example.com"                        # ← your ACME email
      storage: "/letsencrypt/acme.json"
```

**3. `config/config.yml` — Set `prefer_wildcard_cert: true` for each domain:**
```yaml
domains:
  ykx3vzina5zahuf:      # jefe.al
    base_domain: "jefe.al"
    prefer_wildcard_cert: true
    cert_resolver: "letsencrypt"
  51vbysoaydeg6cr:      # losgalactique.fr
    base_domain: "losgalactique.fr"
    prefer_wildcard_cert: true
  domain1:               # jefe.ovh
    base_domain: "jefe.ovh"
    prefer_wildcard_cert: true
```

**4. Restart the stack:**
```bash
docker compose down && docker compose up -d
docker compose logs -f traefik    # Watch for DNS challenge + cert creation
```

### Domain Configuration Via Pangolin API

The domain `jefe.al` already has `type: wildcard` and `verified: true` in Pangolin, but `preferWildcardCert: false`. Toggle it via the dashboard or config.yml (step 3 above).

### DNS Records

The Pangolin self-hosted setup's DNS records show wildcard A records:
```
baseDomain: "*.jefe.al"
recordType: "A"
verified: true
```

These are managed externally (Cloudflare) and verified by Pangolin.

### After Migration

New subdomains get SSL status **"Valid"** immediately instead of **"Pending"** — no waiting for per-resource Let's Encrypt issuance.

### Pitfalls

- Wildcard certs require **DNS-01** — HTTP-01 cannot issue wildcards. Resolver must change.
- If you keep HTTP-01 for some routes and DNS-01 for wildcards, you need **two resolvers** and per-domain `cert_resolver` assignment.
- Cloudflare token needs **both** `Zone:Read` + `DNS:Edit`. Read-only causes silent ACME failures.
- After switching to DNS-01, existing certs re-issue during the next renewal cycle or on stack restart.
- `traefik_config.yml` changes require full `docker compose down && up`, not just `restart` — config is read at startup.

## SSL/TLS

SSL should be enabled by default on every Pangolin resource. Pangolin handles TLS termination at the proxy level while the backend stays HTTP on localhost.

When creating a resource:
- Set `ssl: true` + `scheme: "http"` → Pangolin serves HTTPS, proxies HTTP to backend
- This is how all existing services are configured (bazarr, radarr, sonarr, etc.)

### SSL: Standard Resource vs Site Resource

⚠️ **Critical difference in SSL default behavior**:

| Resource Type | SSL default | How to set |
|---|---|---|
| **Standard resource** (`PUT org/{org}/resource`) | `true` (auto-enabled) | Omit ssl param |
| **Site resource** (`PUT org/{org}/site-resource` or MCP tool) | `false` | Pass `ssl: true` **at creation time** |

#### Site resources require explicit `ssl: true` on creation. If you forget, the fix is harder than it seems — see §Update Pitfalls below.

**Concrete example — HTTPS backend on the NAS (site 18):**

For a service that speaks HTTPS internally (like the NAS WebDAV on port 4234), the site resource MUST have BOTH `scheme: "https"` (backend protocol) AND `ssl: true` (Pangolin terminates TLS for the public side):

```python
mcp_pangolin_create_org_by_orgId_site_resource(
    orgId="jorganisation",
    name="NAS WebDAV",
    mode="http",
    destination="127.0.0.1",
    destinationPort=4234,
    subdomain="webdav",
    domainId="ykx3vzina5zahuf",
    scheme="https",      # ← backend speaks HTTPS
    ssl=True,            # ← public side: Pangolin terminates TLS
    siteId=18,           # ← Jnas site
    enabled=True,
    userIds=[], roleIds=[], clientIds=[],
    authDaemonMode="site",
    authDaemonPort=22123
)
```

#### Server Process Management

**Level 1 — Manual background (quick & dirty):**
```bash
cd /var/www/<service> && python3 server.py &
```
⚠️ Dies on terminal exit. Fine for testing.

**Level 2 — tmux/screen (persistent across SSH disconnects):**
```bash
tmux new-session -d -s insights 'cd /var/www/insights && python3 server.py'
```

**Level 3 — supervisord (production, auto-restart):**
Add a program entry to `/etc/supervisor/supervisord.conf`:

```ini
[program:hermes-insights]
command=bash -lic 'cd /var/www/insights && python3 server.py'
directory=/var/www/insights
user=root
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/hermes-insights.err.log
stdout_logfile=/var/log/hermes-insights.out.log
```

Then: `supervisorctl reread && supervisorctl update && supervisorctl start hermes-insights`.

⚠️ The `bash -lic` wrapper is critical — without it, `~/.hermes/.env` variables won't load.

### Dashboard Gateway: Custom Menu + Native SPA Proxy

When one domain must serve BOTH custom pages (dashboard menu, insights) AND an existing SPA (native Hermes dashboard), use a Python reverse proxy pattern:

**Architecture:**
```
Browser → hermes.jefe.al → Pangolin → 127.0.0.1:8999 (custom server)
                                      └─ / → custom menu (cards)
                                      └─ /insights → custom page (SSE)
                                      └─ /dashboard → proxy → 127.0.0.1:9119 (native SPA)
                                      └─ /assets/* → proxy → 127.0.0.1:9119
                                      └─ /favicon.ico → proxy → 127.0.0.1:9119
```

**Server-side proxy function (stdlib only):**
```python
import urllib.request, urllib.error

async def proxy_to_native(writer, path=""):
    native_url = f"http://127.0.0.1:9119{path}"
    try:
        req = urllib.request.Request(native_url, headers={"Host": "127.0.0.1:9119"})
        resp = await asyncio.to_thread(urllib.request.urlopen, req)
        body = resp.read()
        ct = resp.headers.get("Content-Type", "text/html; charset=utf-8")
        writer.write(
            f"HTTP/1.1 {resp.status} OK\\r\\n".encode()
            + f"Content-Type: {ct}\\r\\n".encode()
            + f"Content-Length: {len(body)}\\r\\n".encode()
            + b"Cache-Control: no-cache\\r\\nConnection: close\\r\\n\\r\\n" + body)
        await writer.drain()
    except urllib.error.HTTPError as e:
        body = e.read()
        ct = e.headers.get("Content-Type", "text/html; charset=utf-8")
        writer.write(f"HTTP/1.1 {e.code} Error\\r\\n".encode()
            + f"Content-Type: {ct}\\r\\n".encode()
            + f"Content-Length: {len(body)}\\r\\n".encode()
            + b"Connection: close\\r\\n\\r\\n" + body)
        await writer.drain()
    except Exception:
        body = FALLBACK_HTML.encode()
        writer.write(b"HTTP/1.1 200 OK\\r\\nContent-Type: text/html; charset=utf-8\\r\\n"
            + f"Content-Length: {len(body)}\\r\\n".encode()
            + b"Connection: close\\r\\n\\r\\n" + body)
        await writer.drain()
    writer.close()
```

**Updating the Pangolin target (NOT creating a new one):**
When you change the backend port for an existing resource (e.g. 9119 → 8999), update the existing target:

```python
# mcp_pangolin_resource_by_resourceId_targets(resourceId=RESOURCE_ID) → get targetId
# mcp_pangolin_update_target_by_targetId(targetId=117, siteId=28, ip="127.0.0.1", port=8999)
```

`update_target_by_targetId` preserves SSL/method settings — only pass what changed. ⚠️ `update_resource_by_resourceId` alone does NOT change the port.

**Fallback page when native dashboard is down:**
```python
FALLBACK_HTML = '''<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🏠 Hermes Dashboard</title>
<style>
body{background:#0a0e17;color:#e2e8f0;font-family:sans-serif;
     display:flex;min-height:100vh;align-items:center;justify-content:center}
.card{background:#111827;border:1px solid #1e293b;border-radius:14px;
      padding:24px;max-width:400px;text-align:center}
a{color:#818cf8;text-decoration:none;font-weight:600}
</style></head><body>
<div class="card">
  <h2>Dashboard natif indisponible</h2>
  <p style="margin-top:12px;color:#64748b;font-size:13px">
    Essaie <a href="/insights">📊 Insights</a>
  </p>
</div></body></html>'''
```

**Pitfalls:**
- `urllib.request` is **sync** — must wrap in `asyncio.to_thread()` inside an async handler, otherwise SSE connections stall the event loop
- The native SPA embeds `__HERMES_SESSION_TOKEN__` inline — extract fresh per-proxy call, do not cache
- Pangolin SSO intercepts `/` before the backend. The proxy transparently passes 302 redirects; browser handles it correctly
- Root normalization: `path.rstrip("/") or ""` ensures `/`→`""` and `/dashboard` stays as `"/dashboard"`
- **🚨 SPA + WebSocket limitation: This proxy pattern BREAKS any SPA that uses WebSocket.** The Python stdlib proxy only handles HTTP — WebSocket upgrade requests (`Upgrade: websocket`, `Sec-WebSocket-Key`) get a 405 or hang silently. The SPA loads the HTML shell, then the JS tries to open WebSocket connections to relative paths (`/ws`, `/api/ws`), which the proxy can't forward, leaving the user on a dark page with no error message.
  **Fix: use a separate Pangolin subdomain** for WebSocket-based apps instead of path-based proxying:
  ```
  hermes.jefe.al/ → custom server (no WS needed)
  dash.jefe.al  → Pangolin → 127.0.0.1:9119 (SPA with WS, direct)
  ```
  This avoids the proxy-though-proxy entirely and keeps WebSocket intact.

## Static File Serving via Pangolin

For quick one-off HTML dashboards, reports, or tools:

```bash
# Step 1 — Create a dedicated directory (NEVER serve from /root or $HOME)
mkdir -p /var/www/<service-name>
cp my-dashboard.html /var/www/<service-name>/index.html

# Step 2 — Serve loopback only (secure behind Pangolin)
python3 -m http.server 8999 --bind 127.0.0.1
```

Then create a site resource pointing to `127.0.0.1:8999`. This is a lightweight alternative to setting up Nginx or a Docker container for single-file services.

**⚠️ CRITICAL — Wrong directory exposes everything**: Starting the HTTP server in `/root/` (the user's home dir) exposes every Hermes config file, .env secrets, state.db, and skills to anyone who can reach the port. Always create a dedicated directory like `/var/www/<service>/` or `/srv/www/<service>/`.
- Create the HTML file(s) there
- Start the server from that directory only
- Verify: `curl -s http://127.0.0.1:8999/` should list only your files
- Then create the Pangolin resource pointing to `127.0.0.1:8999`

#### Real-Time Dashboards

**Level 1 — HTTP Polling (simple)**

For data that updates (e.g. Hermes insights, system stats), use a custom Python server:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sqlite3, datetime

DB = os.path.expanduser("~/.hermes/state.db")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == "/api/insights":
            data = self.get_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

HTTPServer(("127.0.0.1", 8999), Handler).serve_forever()
```

HTML side (auto-poll every 15s):
```javascript
fetchData();
setInterval(fetchData, 15000);
```

**Level 2 — WebSocket Push (real-time)**

For truly real-time data with zero polling overhead, use a custom asyncio server handling both HTTP and WebSocket on the **same port**:

```python
import asyncio, json, hashlib, base64
from hashlib import sha1

WS_MAGIC = b"258EAFA5-E914-47DA-95CA-5AB5DC11B735"

def ws_accept(key):
    return base64.b64encode(sha1(key.encode() + WS_MAGIC).digest()).decode()

def ws_encode(data):
    d = data.encode() if isinstance(data, str) else data
    frame = bytearray([0x81])  # FIN + text
    if len(d) < 126:       frame.append(len(d))
    elif len(d) < 65536:   frame.extend([126, (len(d)>>8)&0xFF, len(d)&0xFF])
    else:                  frame.extend([127, *[(len(d)>>(56-i*8))&0xFF for i in range(8)]])
    frame.extend(d)
    return bytes(frame)

async def handle(reader, writer):
    data = await reader.read(65536)
    head = data[:data.find(b"\r\n\r\n")].decode(errors="replace")
    hdrs = {}
    for line in head.split("\r\n")[1:]:
        if ":" in line: k,v = line.split(":",1); hdrs[k.strip().lower()] = v.strip()

    if hdrs.get("upgrade","").lower() == "websocket":
        accept = ws_accept(hdrs["sec-websocket-key"])
        writer.write(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode())
        await writer.drain()
        # Push initial data, then check every 5s
        writer.write(ws_encode(json.dumps({"type":"update","data":current_data})))
        await writer.drain()
        while True:
            await asyncio.sleep(5)
            if data_changed():
                writer.write(ws_encode(json.dumps({"type":"update","data":fresh_data})))
                await writer.drain()
    else:
        # Regular HTTP: serve HTML at /, JSON at /api/insights
        ...

async def main():
    srv = await asyncio.start_server(handle, "127.0.0.1", 8999)
    async with srv: await srv.serve_forever()

asyncio.run(main())
```

HTML side (WebSocket with auto-reconnect + HTTP fallback):
```javascript
let ws = null;
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/');
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.type === 'update') render(m.data); };
  ws.onclose = () => setTimeout(connectWS, 3000);
  ws.onerror = () => ws.close();
}
connectWS();
// Fallback: HTTP polling if WS fails
setTimeout(() => {
  if (!ws || ws.readyState !== WebSocket.OPEN)
    setInterval(async () => { try { const r = await fetch('/api/insights'); if(r.ok) render(await r.json()); } catch(e){} }, 15000);
}, 5000);
```

**Key differences:**
- Server pushes on data change (5s check) instead of browser polling every 15s
- Always keep `/api/insights` HTTP endpoint as fallback
- The `ws_encode` function builds raw WebSocket frames — no library needed
- Must serve HTTP + WS on the same port (Pangolin proxy exposes only one port)
- Browser auto-reconnects within 3s if WS drops

**⚠️ Pangolin HTTP proxy CANNOT pass WebSocket:** WebSocket connections through Pangolin's `mode: "http"` proxy fail silently — the browser shows "Déconnecté" instantly. This is a Pangolin limitation. Use SSE instead (see Level 3 below).

**⚠️ Pitfall — avoid the `websockets` PyPI library for mixed HTTP+WS:**
The `websockets` v16+ library has a non-trivial `process_request` API that is easy to misconfigure, and its custom HTTP handling can fail silently (empty reply). Writing raw WebSocket frames via `asyncio.start_server` is simpler, more reliable, and has zero external dependencies.

See `references/hermes-state-db-schema.md` for the Hermes state.db table structure and timestamp format.

**Level 3 — SSE Push (proxy-safe real-time) ✅ Recommended for Pangolin**

Server-Sent Events work over plain HTTP streaming — no upgrade handshake, no WebSocket frames. Every reverse proxy (Pangolin, Nginx, Caddy) handles it natively.

Backend (`/api/live` — asyncio on a single port):
```python
import asyncio, json, hashlib

async def handle(reader, writer):
    data = await reader.read(65536)
    head = data[:data.find(b"\\r\\n\\r\\n")].decode(errors="replace")
    path = head.split("\\r\\n")[0].split()[1] if len(head.split("\\r\\n")[0].split()) > 1 else "/"

    if path == "/":
        body = HTML.encode()
        writer.write(f"HTTP/1.1 200 OK\\r\\nContent-Type: text/html\\r\\nContent-Length: {len(body)}\\r\\n\\r\\n".encode() + body)
        await writer.drain(); writer.close()
    elif path == "/api/live":
        writer.write(b"HTTP/1.1 200 OK\\r\\nContent-Type: text/event-stream\\r\\nCache-Control: no-cache\\r\\nConnection: keep-alive\\r\\n\\r\\n")
        await writer.drain()
        writer.write(f"data: {json.dumps(current_data())}\\n\\n".encode())
        await writer.drain()
        while True:
            await asyncio.sleep(5)
            if data_changed():
                writer.write(f"data: {json.dumps(current_data())}\\n\\n".encode())
                await writer.drain()

# Main
srv = await asyncio.start_server(handle, "127.0.0.1", 8999)
async with srv: await srv.serve_forever()
```

HTML side (EventSource auto-reconnect — no manual reconnection code needed):
```javascript
const evt = new EventSource('/api/live');
evt.onmessage = e => { try { render(JSON.parse(e.data)); } catch(err) {} };
evt.onerror = () => { /* Browser auto-reconnects — just show warning */ };
```

**Why SSE wins for proxied environments:**
| Aspect | WebSocket | SSE |
|--------|-----------|-----|
| Proxy support | Requires Upgrade handling | Plain HTTP — works everywhere |
| Pangolin HTTP mode | ❌ Fails silently | ✅ Works |
| Auto-reconnect | Manual (`onclose` → setTimeout) | Built-in (`EventSource`) |
| Complexity | Frames, masking, ping/pong | Just `data: {json}\\n\\n` |

Keep the `/api/insights` HTTP endpoint as a fallback for initial page load and debugging.

See `references/sse-push-server.md` for the full implementation (DB queries, change detection, complete server code).

## Updating Existing Resources

Use `POST /site-resource/{siteResourceId}` (not PUT):

```python
import json, urllib.request

with open('/root/.hermes/tmp_pangolin_key.txt') as f:
    key = f.read().strip().split('=', 1)[1]

body = {
    "ssl": True,
    "scheme": "http",
    "enabled": True,
    "subdomain": "myservice",
    "domainId": "ykx3vzina5zahuf",  # jefe.al domain
    "userIds": [],
    "roleIds": [1],
    "clientIds": [],
    "siteIds": [28]
}

req = urllib.request.Request(
    "https://api.jefe.ovh/v1/site-resource/16",  # resource ID
    data=json.dumps(body).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    method="POST"
)
```

⚠️ **Update pitfalls**:
- `userIds`, `roleIds`, `clientIds` are REQUIRED in update body (can be `[]`)
- `siteIds` or `siteId` is also REQUIRED
- If you omit `subdomain` + `domainId`, the **`fullDomain` gets set to `None`** — always include them
- **Even when you DO include subdomain + domainId**, the MCP `update_site_resource_by_siteResourceId` tool can still wipe them to `null`. The POST update endpoint is fragile.
- **SAFE FIX: Delete + Recreate** — instead of updating, call `mcp_pangolin_delete_site_resource_by_siteResourceId` then `mcp_pangolin_create_org_by_orgId_site_resource` with ALL params correct (ssl, subdomain, domainId, userIds, roleIds, clientIds, scheme, mode, destination, destinationPort)
- Use Python scripts to avoid shell escaping issues with the API key (`.`, `$` chars)

## Localhost-Only: iptables

For services using `--network host` (like Music Assistant), the process binds to `0.0.0.0` by default. Restrict to localhost:

```bash
# Allow loopback, drop everything else
iptables -A INPUT -p tcp --dport 8095 -i lo -j ACCEPT
iptables -A INPUT -p tcp --dport 8095 -j DROP

# Repeat for additional ports (e.g. 8097 for streaming)
iptables -A INPUT -p tcp --dport 8097 -i lo -j ACCEPT
iptables -A INPUT -p tcp --dport 8097 -j DROP

# Make persistent across reboots
apt-get install -y iptables-persistent
netfilter-persistent save
```

⚠️ **Rule order matters**: ACCEPT for lo MUST come BEFORE DROP. The `-i lo` flag filters by incoming interface — traffic from localhost or Newt client connecting to 127.0.0.1 goes through lo.

If access from Tailscale is also needed: `-i lo -j ACCEPT` first, then `-i tailscale0 -j ACCEPT`, then `-j DROP`.

## ⚠️ Debugging Trap: Agent Tests from INSIDE the Tunnel

This is the #1 time-waster in Pangolin debugging. The agent's VPS runs the newt client — every test from the VPS (`curl`, `browser_navigate`) goes through the tunnel or bypasses it. These tests ALWAYS look better than reality:

| Agent's VPS test (misleading) | Actual user experience (real) |
|---|---|
| `curl` returns **302** (auth redirect) | User sees **"no available server"** directly (no auth page) |
| Browser shows **Pangolin auth page** | User was already authenticated, got routing error instead |
| `curl 127.0.0.1:PORT` returns **200** | Pangolin still can't route through the tunnel |
| Newt logs show **target healthy** | User still gets 503 |

**Why this happens:** The agent's VPS browser/curl don't carry Pocket ID cookies. So Pangolin ALWAYS shows the VPS the auth page — even when the backend is completely broken. The VPS test only proves Pangolin server is alive, not that routing works.

**Real test from the VPS:** Check the **Pangolin request logs** for the **user's real IP** (`mcp_pangolin_org_by_orgId_logs_request`). Look at the `reason` field:
- `reason: 107` = request WAS forwarded past auth → routing failure confirmed
- `reason: 101` = auth page served → user isn't authenticated yet

**When the user says "toujours pas" after you said it was fixed:** Go back to the Pangolin logs. The user's requests will show `reason: 107` — confirming the fix didn't actually reach the routing layer.

## ⚠️ Remote Site Trap: Site Resource Created, Newt Can't Restart

Creating a site resource on a **remote** Newt site (site 18 JNAS, site 6 Hetzner) is different from creating one on the **local** site (site 28 Hermes VPN, accessible via SSH on this VPS).

**Problem:** The site resource is created in Pangolin's control plane (✅ DNS, ✅ SSL, ✅ config), but the Newt client on the remote machine doesn't pick up the new route until restarted. Without SSH/Docker API access to that machine, you CANNOT restart it from here.

**Diagnostic flow when user says "page blanche" on a private resource:**

```
1. User says "page blanche" / "blank page"
   ↓
2. Ask: "T'as le client Pangolin sur ton téléphone ?"
   ↓
3a. "Non" → le problème c'est le VPN, pas la config
3b. "Oui" → le Newt client sur le site cible (NAS, Hetzner) n'a pas pick up la route
   ↓
4. Vérifier que le service tourne bien :
   curl -sI http://<tailscale-ip>:<port>/  (si accès Tailscale)
   ↓
5. Si le service tourne → demander au USER de redémarrer le Newt client sur la machine distante :
   systemctl restart newt-client
   # ou redémarrer le conteneur Docker newt
```

**Ne PAS faire** : continuer à modifier la config Pangolin (supprimer/recreate, toggle SSL, etc.) — le problème n'est pas la config, c'est la propagation au Newt client distant.

**After user confirms restart**, verify:
```bash
# Si SSH disponible (site 28 local) :
systemctl restart newt-client && sleep 5
journalctl -u newt-client | grep "Added target subnet.*100.96.128"

# Si pas SSH (sites distants) : demander au user de vérifier que le site
# resource apparaît dans la liste :
mcp_pangolin_org_by_orgId_site_by_siteId_resources(orgId="jorganisation", siteId=SITE_ID)
# Puis tester l'URL dans le navigateur
```

## Troubleshooting: "no available server" / 503 / 504

When Pangolin shows "no available server" (or raw 503/504), the load balancer can't reach any target.

See `references/auth-state-and-reason-codes.md` for a deep-dive on how authentication state affects what error the user sees and how to interpret Pangolin request logs (`reason: 107` vs `101` vs `299`).

## 🔍 Reverse Lookup: Find a Resource by Subdomain

When you visit `https://<subdomain>.jefe.al` and see the **Pangolin placeholder screen** ("This domain is being used on a private resource") but can't find it in public resources, it's likely a **site resource** (private).

**Diagnostic flow:**
```python
# 1. First check public resources (found here → standard resource)
mcp_pangolin_org_by_orgId_resources(orgId="jorganisation", query="search")

# 2. Not found? Check site resources (private resources)
mcp_pangolin_org_by_orgId_site_resources(orgId="jorganisation", pageSize=100)
# → Look for fullDomain matching your subdomain
```

**Why the split matters:**
| Found in… | Type | Needs Newt? | Auth method |
|-----------|------|-------------|-------------|
| Public resources (`org/{org}/resources`) | Standard resource | Only if target on Newt site | SSO/password/pincode |
| Site resources (`org/{org}/site-resources`) | Private resource | ✅ **Always** (behind VPN) | Newt client + optional SSO |

**Real example — search.jefe.al:**
- `mcp_pangolin_org_by_orgId_resources(orgId="jorganisation", query="search")` → **empty** ❌
- `mcp_pangolin_org_by_orgId_site_resources(orgId="jorganisation")` → found under `"searchxng"` with `fullDomain: "search.jefe.al"`, `destination: "127.0.0.1:8088"`, site=Hetzner ✅

### What to check on the site resource itself
```python
# Get full details of a specific site resource
mcp_pangolin_site_resource_by_siteResourceId(
    siteResourceId=ID,
    siteId=SITE_ID,
    orgId="jorganisation"
)
# → Shows: mode, destination, destinationPort, ssl, scheme, subdomain, domainId
```

**Common site resource gotchas after finding it:**
- `ssl: false` → the subdomain serves HTTP only (Pangolin doesn't terminate TLS for site resources by default — must be set explicitly on creation)
- `scheme: "http"` or `"https"` → backend protocol the Newt client uses to connect to the service
- `mode: "http"` → proxied HTTP; `"host"`/`"cidr"` → direct IP/network access (no browser)
- If the browser shows a **Pangolin auth page** after the placeholder → the site resource has auth configured, or there's a corresponding public resource intercepting the domain
- Site resources **cannot** be found via the "org resources" search — only through the site-specific endpoint

### Triple Checks: UFW, SSO, Health Check + Auth State

The "no available server" error has **three distinct root causes** — check them in this order. **Also consider whether the user is already authenticated** — an authenticated user skips the auth page and hits the routing error directly, while an unauthenticated user sees the auth page first (see §❶ for details).

| Check | Symptom | Root Cause |
|-------|---------|------------|
| ❶ Missing Site Resource | Newt shows proxy started, no `Added target subnet` route, local curl works | Created public resource + target but **forgot site resource** |
| ❷ UFW | New targets, local curl works | Port blocked on real interface |
| ❸ SSO | sso=false + no other auth method | No valid auth path configured |
| ❹ Health Check | Target exists but Pangolin doesn't route | hcEnabled=false, or hcMode/hcHostname not set

### ❶ Missing Site Resource (most confusing cause — newt confirms proxy but no route)

**This is the #1 new-resource trap.** Creating a public resource + target works for direct-connect sites (site 6 Hetzner) but for Newt-tunnel sites (site 28 Hermes VPN), you also need a **site resource** that creates the exit-node routing rule.

**Symptom:** Everything looks correct:
- Public resource created ✅
- Target created & healthy ✅
- Newt log shows `"Started tcp proxy to 127.0.0.1:PORT"` ✅
- `curl http://127.0.0.1:PORT/` returns 200 ✅
- UFW allows the port ✅
- But users get **"no available server"** — incognito, cache-cleared, everything

**Why this is confusing:** The Newt client DOES show "Started tcp proxy" — but this is just the LOCAL listener (from the config file). Without a site resource, it never creates the **exit-node routing rule** that carries traffic from Pangolin through the tunnel.

**The telltale sign in newt logs:**
```bash
journalctl -u newt-client | grep "Added target subnet"
# If your resource's aliasAddress (e.g. 100.96.128.20) does NOT appear here → missing site resource
# Working example: "Added target subnet from ... to 100.96.128.19/32" (hermes.jefe.al's existing route)
# Missing: no line with your resource's aliasAddress
```

**Fix:** Create the site resource (see §5 — Three-Layer Pattern above), then restart newt-client.

### ❷ SSO / Auth Method Check (frequent cause on dashboard services)

When the resource has **`sso: false`** AND **no other auth method** (`passwordId: null`, `pincodeId: null`, `headerAuthId: null`), Pangolin has no valid authentication path and refuses to route — manifesting as **503 / "no available server"** despite the target being healthy.

**🚨 Auth state matters: authenticated vs. unauthenticated users see different errors.**

When troubleshooting "no available server", the user's authentication state changes what they see:

| User state | Sees | What's happening |
|---|---|---|
| **Not authenticated** (fresh browser, incognito) | Pangolin auth page (login form + Pocket ID button) | Pangolin intercepts and shows auth before proxying. Target may be fine. |
| **Already authenticated** (existing Pocket ID session) | "no available server" directly (no auth page) | Pangolin skips auth and tries to proxy → but can't reach the target |

**Consequence:** From the agent's VPS (fresh browser, no Pocket ID cookie), `curl` or `browser_navigate` may show the auth page (302 or 200 with login form) even though authenticated users get "no available server". Always check the Pangolin request logs for the user's real IP to see the `reason` code: `reason: 101` = auth page served, `reason: 107` = forwarded to backend (then failed), `reason: 299` = blocked.

**Debug flow when the VPS shows the auth page but the user sees "no available server":**
1. Check Pangolin request logs for the user's IP (`mcp_pangolin_org_by_orgId_logs_request`)
2. Look for the `reason` code on their requests
3. If `reason: 107` → the request was forwarded past auth → the failure is in the target routing (health check, hcMode, newt tunnel)
4. If `reason: 101` → the auth page was served → the user needs to authenticate
5. Be aware `update_target_by_targetId` can silently toggle `sso: true → false` (see SSO reset bug below)

**Check:**
```python
# Fetch the resource detail
# mcp_pangolin_resource_by_resourceId(resourceId=ID)
# Look for: sso, passwordId, pincodeId, headerAuthId
```

**If `sso: false` and all auth fields are null:**
```python
# Re-enable SSO via the API
# mcp_pangolin_update_resource_by_resourceId(resourceId=ID, sso=True)
```

**⚠️ Known bug — enabling health check can reset SSO:** Calling `mcp_pangolin_update_target_by_targetId` with `hcEnabled: true` (or any target update) may silently reset the parent resource's `sso` field from `true` to `false`. After updating a target, **always verify the resource's SSO setting** and re-enable it if it was turned off:
```python
# After any target update, check and restore SSO
resource = mcp_pangolin_resource_by_resourceId(resourceId=ID)
if not resource.get('sso'):
    mcp_pangolin_update_resource_by_resourceId(resourceId=ID, sso=True)
```

### ❷ Activate Health Check (forces Pangolin to recognize the target)

If the target has `hcEnabled: false`, Pangolin's load balancer may not consider it "available" even when the Newt client reports it as healthy. Enabling a health check forces Pangolin to probe the target:

⚠️ **`update_target_by_targetId` has FULL-REPLACE semantics** — passing only a subset of fields resets the rest to defaults. Always include ALL health check params. Each sparsely-filled call will reset omitted fields.

```python
# Enable health check on an existing target — PASS ALL PARAMS EVERY TIME
mcp_pangolin_update_target_by_targetId(
    targetId=ID,
    siteId=SITE_ID,
    ip="127.0.0.1",
    hcEnabled=True,            # ← was False
    hcMode="http",             # ← REQUIRED — without this, hcMode=null → health check never runs
    hcHostname="127.0.0.1",    # ← REQUIRED — without this, hostname=null → probe may fail
    hcMethod="GET",
    hcPath="/",
    hcPort=PORT,
    hcScheme="http",
    hcStatus=200,
    hcInterval=15,
    hcTimeout=5,
    hcHealthyThreshold=2,
    hcUnhealthyThreshold=3,
    hcUnhealthyInterval=15,    # ← recommended — without it, unhealthy targets never retry
)
```

**Full-replace trap — common casualties:**
- `hcMode` → resets to `null` → health check never runs
- `hcHostname` → resets to `null` → probe destination missing
- `hcEnabled` → resets to `false` → health check disabled
- `hcMethod`, `hcPath`, `hcPort`, `hcScheme` → resets to `null`
- `hcUnhealthyInterval` → resets to `null` → unhealthy targets never retry, stay unhealthy forever
- `hcFollowRedirects` → resets to `null`

**Creating a target with health checks:** When creating via `mcp_pangolin_create_resource_by_resourceId_target`, the initial `hcMode` and `hcHostname` are ALWAYS `null` even when you pass `hcEnabled: true`. The target shows `hcHealth: "unhealthy"` immediately after creation. **You must make a SECOND call** to update the newly-created target with ALL health check params set explicitly (see above). The health check runs every `hcInterval` seconds — wait up to 30s for the status to change from `"unhealthy"` → `"healthy"`.

```python
# Two-step dance: create, then fix health check
# Step 1 — create (hcMode/hcHostname will be null despite hcEnabled=true)
# mcp_pangolin_create_resource_by_resourceId_target(...hcEnabled=true...)
# Step 2 — immediately fix health check params
# mcp_pangolin_update_target_by_targetId(targetId=NEW_ID, siteId=..., ip="127.0.0.1",
#     hcEnabled=True, hcMode="http", hcHostname="127.0.0.1",
#     hcMethod="GET", hcPath="/", hcPort=PORT, hcScheme="http", hcStatus=200,
#     hcInterval=15, hcTimeout=5, hcHealthyThreshold=2, hcUnhealthyThreshold=3,
#     hcUnhealthyInterval=15)
```

Wait ~30s and verify the health is now `"healthy"`:
```python
# mcp_pangolin_resource_by_resourceId_targets(resourceId=ID)
# Check the target's `hcHealth` field
```

**Signs you need health checks:** the site is online, the Newt client confirms the proxy started, local curl works, UFW allows the port, but Pangolin still returns 503.

### ❸ UFW / nftables Check (most common cause on new targets)

A `DENY IN` rule in UFW or nftables blocks the Newt tunnel's forward even when `curl 127.0.0.1:<port>` works fine (loopback bypasses UFW by default):

```bash
# Check UFW rules
ufw status | grep <port>

# Check raw nftables
nft list ruleset 2>/dev/null | grep "dport <port>"
```

If `DENY` is present, the port was intentionally locked down — likely because it was previously exposed only through direct access. Since Pangolin + SSO now sits in front, you can safely allow it:

```bash
ufw allow <port>/tcp comment 'Service Name (via Pangolin SSO)'
```

The nftables rules update automatically after `ufw reload`.

**Why this is confusing:** `curl http://127.0.0.1:<port>` works because loopback isn't subject to UFW INPUT rules. But the Newt tunnel traffic arrives on a real interface (tun/wg), hits UFW, and gets dropped — manifesting as "no available server" in the browser even though local curl succeeds.

**Signs you might have a UFW issue (in addition to wrong-site signs above):**
- "no available server" on a **newly created** Pangolin target
- `curl 127.0.0.1:<port>` returns 200 locally
- The site is online, the Newt tunnel is running
- Other targets on the **same site** with different ports work fine
- `ufw status` shows `DENY` for the target port

### Compare Target Config Against a Working Resource

When local curl works and UFW isn't blocking, but Pangolin still shows "no available server" and the Newt tunnel confirms the proxy started:

1. Find a **known-working resource on the same site** (e.g. Hermes Agent at `hermes.jefe.al` on site 28)
2. Compare **both the resource config AND the target config** side by side:
   - Resource level: `mcp_pangolin_resource_by_resourceId(resourceId=ID)` — check `sso`, `health`
   - Target level: `mcp_pangolin_resource_by_resourceId_targets(resourceId=ID)` — check `hcEnabled`, `hcHealth`
3. Key differences to spot:
   - **`sso`**: must be `true` (or have another auth method configured). `sso: false` + no password/pincode/header auth = 503
   - **`hcEnabled`**: should be `true` if other working resources have it enabled
   - **`hcHealth`**: should be `"healthy"` — if `"unknown"`, enable health checks and wait 30s
   - **`method`**: must be `"http"` for HTTP resources (`null` = TCP tunnel = "no available server")
   - **`siteId`**: must match the site where the container actually runs (can differ if you picked the wrong site)
   - **`ip`/`port`**: must match the container's actual listening address
4. ⚠️ **Check if SSO was silently reset** — a target update may have flipped `sso: true → false`

This "compare against a sibling" technique found the bug on the first deploy of signal-cli-rest-api and again when dash.jefe.al stopped routing.

### 🚀 Nuclear Option: Delete + Recreate Full Resource

When targets get corrupted, the SSO keeps toggling, health checks stay stuck at "unhealthy" despite hcMode being set, or the resource has accumulated too many update iterations, **delete the entire resource and recreate it from scratch**. This avoids all cumulative configuration drift in the Pangolin API and Newt client.

**Workflow:**
```python
# Step 1 — Delete the resource (cascades to all targets)
mcp_pangolin_delete_resource_by_resourceId(resourceId=OLD_ID)

# Step 2 — Create a fresh resource (SSO defaults to TRUE automatically)
mcp_pangolin_create_org_by_orgId_resource(
    orgId="jorganisation",
    name="Service Name",
    subdomain="myservice",
    domainId="ykx3vzina5zahuf",
    http=True,
    protocol="tcp"
)

# Step 3 — Add a target
mcp_pangolin_create_resource_by_resourceId_target(
    resourceId=NEW_ID, siteId=28, ip="127.0.0.1", port=PORT
)

# Step 4 (optional) — If the service has its own auth, disable SSO
mcp_pangolin_update_resource_by_resourceId(resourceId=NEW_ID, sso=False)
```

**Advantages over target-level fixes:**
- Fresh `resourceGuid` — no stale routing state in the Newt tunnel
- SSO defaults to `true` on creation (avoids the SSO reset bug entirely)
- Clean target — no accumulated full-replace corruption from multiple `update_target_by_targetId` calls
- Newt picks up the new target immediately or after restart

**Disadvantages:** Temporary outage during recreation (10–15 seconds), need to reconfigure auth methods.

## Troubleshooting: 504 Gateway Timeout

When a Pangolin resource returns **504** (like `simu.jefe.al` did), follow this debug flow:

### Step 1 — Check Docker
```bash
docker ps --filter name=<service> --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
```
⚠️ The container must be **Up** and listening on the port configured in the target.

### Step 2 — Check Newt Tunnel
```bash
ps aux | grep -i "newt" | grep -v grep
```
If no Newt process is running → **this is the problem**. Restart it:
```bash
newt client &
```
Wait ~3s, then verify tunnel is up:
```bash
# Check via Pangolin API
curl -s -H "Authorization: Bearer $PANGOLIN_API_KEY" \
  "https://api.jefe.ovh/v1/org/jorganisation/sites" \
  | python3 -c "import sys,json; [print(f'{s[\"name\"]}: online={s.get(\"online\",\"?\")}') for s in json.load(sys.stdin)['data'] if s['siteId']==28]"
```

### Step 3 — Retry
```bash
curl -sI https://<service>.jefe.al
```
Should return **200**.

### Step 4 — Fallback: Public IP Workaround
If the tunnel won't start and the service is urgent, temporarily switch the target to the public IP:
- Change target IP from `127.0.0.1` → `178.105.179.232`
- Also change Docker from `127.0.0.1:PORT` → `0.0.0.0:PORT`
- ⚠️ This exposes the Docker port to the network; revert when the tunnel is fixed.
- **Host-network services need iptables**: Services on `--network host` listen on `0.0.0.0` by default. Use iptables to restrict to loopback: `iptables -A INPUT -p tcp --dport PORT -i lo -j ACCEPT; iptables -A INPUT -p tcp --dport PORT -j DROP`. See `references/localhost-only-iptables.md`.
- **`PUT /org/{orgId}/site-resource` WORKS for private resources**: This is the correct endpoint for creating private (site) resources via the API. Example body: `{"name": "Service", "mode": "http", "destination": "127.0.0.1", "destinationPort": 8095, "siteId": 28, "subdomain": "myservice", "domainId": "ykx3vzina5zahuf", "scheme": "http", "ssl": false}`. Required fields: `name`, `mode`, `destination`, `userIds`, `roleIds`, `clientIds`. Optional: `siteId`, `destinationPort`, `subdomain`, `domainId`, `scheme`, `ssl`, `enabled`.
- **Private resources ≠ public resources**: Private site resources have a different data model (`mode`, `destination`, `destinationPort`, `aliasAddress`). They get a public domain BUT require the Newt client to access — perfect for services meant to stay behind the VPN.
- **Target via `PUT resource/{id}/target` WORKS**: Use this instead of the broken site endpoint.
- **Target body MUST include `method: "http"`**: Without this (defaults to `null` / TCP tunnel mode), the Pangolin reverse proxy cannot route HTTP traffic. The API accepts `null` without validation error, but the service silently fails at runtime with **"no available server"** or **503** in the browser. Always set `"method": "http"` for HTTP resources. The Newt client auto-detects new/changed targets within seconds — no restart needed.
- **IP choice for site 28**: Use `127.0.0.1` (local). The Newt client runs on this machine, so loopback is reachable. The public IP `178.105.179.232` is a **temporary workaround** when the Newt tunnel is down — always switch back to `127.0.0.1` when the tunnel recovers.
- **Docker bind**: `127.0.0.1:PORT` is preferred (more secure). `0.0.0.0:PORT` is only needed when bypassing the tunnel with the public IP.
- **Newt crash = 504**: If the Newt client stops (crash, reboot, OOM), all resources on site 28 return 504. Fix: restart `newt client`.
- **Newt does NOT auto-start**: Must be manually relaunched after every reboot or crash.
- **`PUT resource/{id}/target` creates duplicates**: Calling it multiple times creates new targets. To fix, delete old targets with `DELETE target/{tid}` then recreate.
- **Deleting targets works**: `DELETE /v1/target/{targetId}` DOES work — unlike the old docs suggested, individual targets can be removed without deleting the whole resource.
- **Do NOT include** `targets`, `sites`, `siteId`, `ssl`, or `enableProxy` in the resource creation body — they cause validation errors.
- **API path quirk**: Always ensure a `/` between the base URL and the path. `BASE = "https://api.jefe.ovh/v1"` + `f"{BASE}/{path}"` works; `f"{BASE}{path}"` without leading slash concatenates incorrectly.
- **SSL is auto-enabled** on creation (no need to pass it).
- **The Pangolin API key has `.` chars** — use Python scripts to avoid shell escaping issues.
- **Auth header masking workaround**: The Hermes tool system replaces `" + key` at the end of a string with `$PANGO...EY`, breaking Python syntax when building `"Authorization: Bearer *** + k`. Build the header across multiple statements: `h = "Authorization:"; h += " Bearer "; h += k`. The multi-line `h +=` approach avoids the masking trigger. See `references/pangolin-api-create-resource.md` → Tool Masking Pitfall for details.
- **Auth header format: `Authorization: Bearer` (recent API)**: The Pangolin API at `api.jefe.ovh` requires `Authorization: Bearer <key>`. `X-API-Key: <key>` returns 401 with `"API key required"` — the older header format no longer works.
- **Health shows "unknown"** briefly while the health check initialises; this is normal.
- **Resources default to `sso: true`** (Pocket-ID auth enabled). If the service has its own auth (like Hermes Dashboard), create the resource then disable SSO: `POST resource/{id}` with `{"sso": false}`.
- **🚨 SSO reset bug**: Updating a target (via `update_target_by_targetId`) can silently reset the parent resource's `sso` to `false`. Always verify SSO after any target update, especially when a previously-working resource suddenly returns "no available server".
- **Full-replace trap on `update_target_by_targetId`**: This API replaces the ENTIRE target config, not just the fields you send. Omitting `hcMode`, `hcHostname`, `hcEnabled`, or any health check field resets them to `null`/`false`. Always pass ALL health-check params in a single update call.
- **`hcMode` and `hcHostname` are required for health checks**: Even when creating a target with `hcEnabled: true`, the initial `hcMode` may be `null` and `hcHostname` may be `null`. This causes the health check to report `"unhealthy"` forever. Fix: update the target with both fields explicitly set to `"http"` and `"127.0.0.1"` respectively.
- **No auth = 503**: A resource with `sso: false`, `passwordId: null`, `pincodeId: null`, and `headerAuthId: null` has NO authentication path. Pangolin refuses to route and returns 503/"no available server". Either enable SSO or configure an auth method.
- **Health checks matter**: Targets with `hcEnabled: false` and `hcHealth: "unknown"` may not be considered "available" by Pangolin's load balancer. After creating a target, enable health checks. See Troubleshooting → Activate Health Check above.  
  ```python
  # Disable SSO after creation
  req = urllib.request.Request(f"{BASE}/resource/{RESOURCE_ID}",
      data=json.dumps({"sso": False}).encode(), headers=headers, method="POST")
  with urllib.request.urlopen(req) as resp:
      print(f"sso=False → {json.loads(resp.read())['data'].get('sso')}")
  ```
- **Resources are public by default**: Standard resources created via `PUT org/{org}/resource` have the proxy enabled and are accessible via any browser (with Pangolin auth).
- **Private resources use a different data model**: NOT a boolean on standard resources. Private resources (with domain but requiring Newt) are **site resources** — accessible via `GET org/{org}/site/{siteId}/resources`. They have a completely different data structure (`mode`, `destination`, `destinationPort`, `aliasAddress`, etc.) and are NOT visible in the standard `org/{org}/resources` endpoint.
- **`api.jefe.ovh` is NOT a private resource**: Unlike the earlier assumption, all API calls work fine without the Newt tunnel as long as the API key is valid AND uses the correct auth header format. See Pitfalls below for header format.
- **`PUT org/{orgId}/site/{siteId}/resource` is STILL broken**: Returns "Unrecognized key: siteId" regardless of body — do NOT use. Creating private (site) resources requires the Pangolin UI.
- **Private resource creation via UI** (for non-HTTP services like SMB):
  - Go to: **Sites → select site → Resources tab → Add Resource**
  - For a single IP (e.g. NAS): select **mode: Hôte**, enter destination IP, configure port restrictions
  - For web services: select **mode: HTTP**, set subdomain + domain for a public-facing URL that still requires Newt
  - Alias (like `nas.jefe.internal`) creates a DNS name resolvable via Newt client — useful for non-HTTP protocols
- **Non-HTTP protocols (SMB, databases, SSH)**: Use `mode: host` or `mode: tcp`. No domain needed — access via alias or direct IP over the Newt mesh. Port restrictions let you lock to specific ports (e.g. `445` for SMB).
