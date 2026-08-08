# Auth State & Pangolin Reason Codes

## Why VPS Tests Lie: Auth State Dependency

When debugging "no available server" errors in Pangolin, **the user's authentication state fundamentally changes what they see**. This is the single most confusing aspect of Pangolin troubleshooting.

| User state | Sees | What's happening |
|---|---|---|
| **Not authenticated** (fresh VPS browser, incognito, curl) | Pangolin auth page (login form + Pocket ID button) or 302 redirect | Pangolin intercepts at the auth layer — never tries to proxy. Target could be completely down and you'd still see this. |
| **Already authenticated** (existing Pocket ID session) | "no available server" directly (no auth page) | Pangolin skips auth and tries to proxy → but can't reach the target |

**Consequence for agent debugging:** From the agent's VPS (fresh browser, no Pocket ID cookie), `curl` or `browser_navigate` may show the auth page (302 or 200 with login form) even though authenticated users get "no available server". The auth page is a MISLEADING SUCCESS — it proves the Pangolin server is alive, but tells you nothing about whether the backend routing works.

## How to Diagnose Correctly

### 1. Check Pangolin Request Logs (the only reliable source)

Query logs for the user's real IP (not the VPS IP):

```python
mcp_pangolin_org_by_orgId_logs_request(
    orgId="jorganisation",
    resourceId=RESOURCE_ID,
    timeStart="2026-06-08T18:00:00.000Z"  # recent window
)
```

### 2. Interpret the `reason` Field

| reason | `action` | Meaning |
|--------|----------|---------|
| **101** | `true` | **Auth page served** — unauthenticated user got the login form. Routing was NOT tested. |
| **107** | `true` | **Authenticated request forwarded to backend** — Pangolin proxied the request through the tunnel to the target. The routing attempt was made. If the user sees "no available server", the failure is in the newt tunnel / target routing, not the auth layer. |
| **299** | `false` | **Blocked** — request was denied (bot, wrong IP, rate limit, etc). Not related to routing. |

### 3. Cross-reference with target health

If `reason: 107` and the user gets "no available server":

```python
mcp_pangolin_resource_by_resourceId_targets(resourceId=RESOURCE_ID)
# Check: hcHealth, hcEnabled, hcMode, hcHostname
```

- `hcHealth: "unhealthy"` → health check is failing (port blocked, service down, or hcMode/hcHostname null)
- `hcHealth: "unknown"` and `hcEnabled: false` → no health check configured, Pangolin may not route
- `hcHealth: "healthy"` but still 107 → something else (try delete + recreate the full resource)

### 4. Know the "VPS Auth Page" Trap

When you `curl -s https://dash.jefe.al/` from the VPS and get `302`:
- ✅ This means Pangolin is alive and serving the auth page
- ❌ This does NOT mean the resource works for the user
- The user might still get "no available server" because they're authenticated and Pangolin tries to proxy them

**The only reliable test from the VPS**: check the Pangolin request logs for the user's IP, not your own VPS IP.
