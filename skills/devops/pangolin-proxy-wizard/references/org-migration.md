# Resource Migration Between Pangolin Organizations

Transfer a Pangolin resource (public resource + target) from one org to another.

## Prerequisites

- API key with write access to **both** the source and target organizations
- The domain must already exist in the target organization

## The Pattern

Pangolin has no org-transfer API. The `orgId` field is not accepted in resource POST/PUT updates. The solution is: **delete from source, recreate in target**.

```python
# Step 1 — Get full resource details (note: mode="http", domainId, target config)
r = api("GET", f"resource/{RESOURCE_ID}")
# Record: name, domainId, mode, target siteId/ip/port/method

# Step 2 — Delete from source org (cascades to targets)
r = api("DELETE", f"resource/{RESOURCE_ID}")

# Step 3 — Recreate in target org
r = api("PUT", f"org/{TARGET_ORG}/resource", {
    "name": "service-name",
    "domainId": "domain-id",         # use same domain
    "mode": "http",                  # required
})

# Step 4 — Add target
r = api("PUT", f"resource/{NEW_ID}/target", {
    "siteId": SITE_ID,
    "ip": "127.0.0.1",
    "port": PORT,
    "method": "http",                # required for HTTP services
    "enabled": True,
})
```

## API Field Constraints

When **creating** a resource via `PUT org/{orgId}/resource`, these fields are **rejected**:
- `fullDomain` — set automatically from domainId
- `ssl` — defaults to `true`
- `sso` — defaults to `null` (no auth)
- `subdomain` — only if the domain supports it

Minimal working creation body:
```python
{
    "name": "service-name",          # display name
    "domainId": "domain-id",         # required
    "mode": "http",                  # required
}
```

## Key Permission Levels

Pangolin API keys can have different access scopes:
- **Read-only**: Can GET resources, targets, sites, org details
- **Org-scoped**: Only access resources within specific org(s)
- **Write**: Can create, update, delete resources
- **Root**: Full access to all orgs and settings

When the user provides multiple keys, test each against the source and target orgs:
```python
# Test key scope
api("GET", f"org/{ORG_ID}/resources")  # 200 = write access, 403 = no access
api("PUT", f"org/{ORG_ID}/resource", name="test", domainId="x", mode="http")  # 200 = write
```

## Pitfalls

- **No org-transfer endpoint exists** — must delete + recreate
- **`fullDomain`, `ssl`, `sso` rejected** on resource creation body
- **Target method must be "http"** for HTTP services — omitting it defaults to TCP tunnel
- **Delete cascades to targets** — no need to delete targets separately
- **Outage window**: the service is briefly down between delete and recreate (10-15s)
