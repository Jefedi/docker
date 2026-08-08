# Site Resource → Public Resource Conversion

When a service is configured as a **Site Resource** (private, requires Pangolin client) and needs to become a **Public Resource** (accessible via browser without the client), follow this workflow.

## Overview

| Before | After |
|--------|-------|
| Site Resource (siteResourceId) | Public Resource (resourceId) |
| Requires Newt client connection | Accessible via any browser |
| `mode: "http"`, `destination: "127.0.0.1:PORT"` | Same target, different routing layer |
| Found via `org/{org}/site-resources` | Found via `org/{org}/resources` |

## Workflow

### Step 1 — Delete the Site Resource

```python
mcp_pangolin_delete_site_resource_by_siteResourceId(siteResourceId=OLD_ID)
```

The site resource contains the domain/subdomain config AND the backend destination. Deleting it removes the private routing rule from the Newt client.

⚠️ **This immediately breaks access for anyone using the client** — the subdomain stops resolving. Do this during a maintenance window.

### Step 2 — Create the Public Resource

```python
mcp_pangolin_create_org_by_orgId_resource(
    orgId="jorganisation",
    name="Service Name",
    http=True,
    protocol="tcp",           # ← "tcp", NOT "http" (the MCP tool rejects "http" here)
    domainId="domain1",       # jefe.ovh
    subdomain="myservice"
)
```

**Key param details:**
- `http: true` tells Pangolin this is an HTTP resource (as opposed to raw TCP/UDP)
- `protocol: "tcp"` is the transport layer (the MCP tool's enum is "tcp"|"udp")
- The combination `http: true, protocol: "tcp"` produces `mode: "http"` on the created resource

**⚠️ SSO defaults to `true` on new public resources.** If the service has its own auth (or you want open access), disable it immediately:

```python
mcp_pangolin_update_resource_by_resourceId(resourceId=NEW_ID, sso=False)
```

Without this step, visitors see the Pangolin auth page first.

### Step 3 — Add a Target

```python
mcp_pangolin_create_resource_by_resourceId_target(
    resourceId=NEW_ID,
    siteId=SITE_ID,           # same site where the service container runs
    ip="127.0.0.1",
    port=SERVICE_PORT,
    enabled=True
)
```

The target tells Pangolin's load balancer where to forward traffic. The `siteId` must match the site where the Newt client runs that can reach the service.

### Step 4 — (Optional) Enable Health Check

If the resource shows `health: "unknown"`, enable health checks on the target:

```python
mcp_pangolin_update_target_by_targetId(
    targetId=TARGET_ID,
    siteId=SITE_ID,
    ip="127.0.0.1",
    hcEnabled=True,
    hcMode="http",
    hcHostname="127.0.0.1",
    hcMethod="GET",
    hcPath="/",
    hcPort=SERVICE_PORT,
    hcScheme="http",
    hcStatus=200,
    hcInterval=15,
    hcTimeout=5,
    hcHealthyThreshold=2,
    hcUnhealthyThreshold=3,
    hcUnhealthyInterval=15,
)
```

⚠️ `update_target_by_targetId` has **full-replace semantics** — always pass ALL params.

### Step 5 — Test

```python
# Confirm it's accessible (no auth if SSO disabled)
curl -sI https://myservice.jefe.ovh
# Should return 200 or the service's own page, not the Pangolin placeholder
```

## When NOT to Convert

Keep a service as a Site Resource when:
- The service is sensitive and should only be accessible via VPN/Newt client
- The service expects a local agent (Electron desktop app pattern)
- You want an additional security layer beyond what the service provides

## "no available server" After Conversion

If the browser shows the Termix-style "no available server" (not the Pangolin one), this means the **frontend loaded but the backend API is unreachable**. Common causes:

1. **The frontend expects a local agent** (Termix pattern) — the SPA is designed for Electron + local API on `localhost:PORT`. It can't work remotely.
2. **The service port is wrong** — double-check `destinationPort` on the target
3. **The Newt tunnel is down** — verify the target site is online

The Pangolin "no available server" (503) is different — it means Pangolin can't reach ANY target (site offline, wrong IP/port, or target not created successfully).
