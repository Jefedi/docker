# Pangolin Resource Management via MCP Tools

MCP-based workflow for managing Pangolin HTTP resources — creating, updating, re-targeting, and disabling auth. Faster than raw Python API calls since Hermes has the tools built-in.

## Prerequisites

The `mcp-pangolin` tools must be loaded. Verify:
```
tool_search("pangolin resource update create")
```
Should return 10+ tools.

## Common Lookups

### Find orgId
```
mcp_pangolin_orgs()
# → orgId: "jorganisation" (for Jefe)
```

### Find domain ID by name
```
mcp_pangolin_org_by_orgId_domains(orgId="jorganisation")
```
Domain IDs for Jefe:
| Domain | domainId |
|--------|----------|
| `jefe.ovh` | `domain1` |
| `jefe.al` | `ykx3vzina5zahuf` |
| `losgalactique.fr` | `51vbysoaydeg6cr` |
| `trakii.tv` | `domain4` |

### Find resource by fullDomain
```
mcp_pangolin_org_by_orgId_resources(orgId="jorganisation", pageSize=100)
# → Search the response for the matching fullDomain
# → Note the resourceId, targetId, siteId, current port
```

### List targets for a resource
```
mcp_pangolin_resource_by_resourceId_targets(resourceId=<id>)
# → Returns target(s) with targetId, ip, port, siteId, hcHealth
```

## 1. Update Existing Resource Target (Change Port/IP)

```python
# Step 1 — Find the existing target
mcp_pangolin_resource_by_resourceId_targets(resourceId=<id>)
# → Get targetId and siteId

# Step 2 — Update the target
mcp_pangolin_update_target_by_targetId(
    targetId=<targetId>,
    siteId=<siteId>,
    ip="127.0.0.1",       # new IP (required)
    port=<newPort>,        # new port
    enabled=True
)
```

**⚠️ Full-replace semantics:** `update_target_by_targetId` replaces ALL fields, not just what you pass. Omitting `method`, `hcEnabled`, etc. resets them. For a simple port/IP change, only `targetId`, `siteId`, `ip` are required — `port=NEW` sets the new port.

**⚠️ SSO reset bug:** Updating a target CAN silently reset the parent resource's `sso` to `false`. After any target update, verify SSO:
```
mcp_pangolin_resource_by_resourceId(resourceId=<id>)
# Check the resource's sso field
```

## 2. Create a New Resource + Target

**Two-step process — create resource first, then add target.**

### Step A — Create the HTTP resource
```
mcp_pangolin_create_org_by_orgId_resource(
    orgId="jorganisation",
    name="Human-readable name",
    http=True,                       # HTTP mode
    protocol="tcp",                  # always "tcp" for HTTP
    domainId="<domainId>",           # from domain lookup above
    subdomain="mysubdomain"          # API subdomain (e.g. "api" → api.trakii.tv)
)
# → Returns resourceId (e.g. 114), fullDomain (e.g. "api.trakii.tv")
```

For apex domains (e.g. `trakii.tv` without subdomain), omit `subdomain`.

### Step B — Add a target
```
mcp_pangolin_create_resource_by_resourceId_target(
    resourceId=<newId>,
    siteId=<siteId>,               # site where the service runs
    ip="127.0.0.1",
    port=<port>,
    enabled=True
)
# → Returns targetId
```

### Step C (optional) — Disable SSO / auth
If the service has its own login, disable Pangolin auth:
```
mcp_pangolin_update_resource_by_resourceId(
    resourceId=<id>,
    sso=False
)
```

## 3. Disable Auth on Existing Resource(s)

```
mcp_pangolin_update_resource_by_resourceId(
    resourceId=<id>,
    sso=False
)
# sso=False = Pangolin doesn't require SSO login
```

**When to disable auth:** The service handles its own authentication (Trakii, Jellyfin, etc.). Leaving `sso=True` would require Pocket-ID login ON TOP of the service's own login.

**Check before disabling:** `mcp_pangolin_resource_by_resourceId(resourceId=<id>)` — if `sso: null` or `sso: 0`, it's already disabled.

## Batch Workflow (Multi-Resource Setup)

When setting up related resources (e.g., main, api, sync for the same app):

```
# 1. Find the existing resource → get resourceId + targetId
# 2. Update its target port
mcp_pangolin_update_target_by_targetId(targetId=old, siteId=N, ip="127.0.0.1", port=NEW_PORT)

# 3. Create new resources (parallel — they're independent)
mcp_pangolin_create_org_by_orgId_resource(orgId="jorganisation", name="api", http=True, protocol="tcp", domainId="X", subdomain="api")
mcp_pangolin_create_org_by_orgId_resource(orgId="jorganisation", name="sync", http=True, protocol="tcp", domainId="X", subdomain="sync")

# 4. Add targets for the new resources
mcp_pangolin_create_resource_by_resourceId_target(resourceId=new1, siteId=N, ip="127.0.0.1", port=PORT1)
mcp_pangolin_create_resource_by_resourceId_target(resourceId=new2, siteId=N, ip="127.0.0.1", port=PORT2)

# 5. Disable auth on all (parallel)
mcp_pangolin_update_resource_by_resourceId(resourceId=oldId, sso=False)
mcp_pangolin_update_resource_by_resourceId(resourceId=new1, sso=False)
mcp_pangolin_update_resource_by_resourceId(resourceId=new2, sso=False)
```

All steps are independent and can run concurrently when no step depends on a previous result.

## Pitfalls

- **SSO reset on target update:** Always verify `sso` after any `update_target_by_targetId` call
- **Create then target:** Cannot create resource + target in one call — always two steps
- **domainId is required** on resource creation — look it up from `mcp_pangolin_org_by_orgId_domains`
- **siteId must match where the service runs** — wrong site = "no available server"
- **Health check defaults to disabled** — new targets have `hcEnabled: false`, `hcHealth: "unknown"`. Enable via a separate `update_target_by_targetId` call with ALL health check params if needed
