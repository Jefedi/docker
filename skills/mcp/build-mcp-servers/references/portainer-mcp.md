# Portainer MCP Server (Official)

**Repo:** [portainer/portainer-mcp](https://github.com/portainer/portainer-mcp)  
**PyPI:** `mcp-portainer`  
**License:** MIT | **Latest:** 2.42.6 (Jun 2026)

## Overview

Official MCP server generated from Portainer's OpenAPI spec via FastMCP. Exposes ~193 tools covering environments, stacks, Docker/K8s, and GitOps. Also proxies through to underlying Docker and K8s APIs.

## Version Matching

Match MCP server minor version to Portainer instance minor version:

| MCP Server | Portainer |
|------------|-----------|
| `2.42.x` | CE/EE `2.42.x` |
| `2.41.x` | CE/EE `2.41.x` |

If no exact match exists, use the closest available — may still work with minor spec differences.

## Jefe's Setup

- **Portainer version:** 2.39.3 CE
- **MCP server installed:** 2.42.6 (no 2.39 available — works despite version mismatch)
- **URL:** `https://portainer.jefe.ovh` (behind Pangolin Private Resource)
- **API Key:** `ptr_sMwE9ch/FRHkKOCBquFpmHy0Is7mE/yuxrhRBYMa4nk=`
- **Hermes server name:** `portainer`
- **Command:** `/usr/local/lib/hermes-agent/venv/bin/mcp-portainer` (stdio)
- **Portainer bind:** `127.0.0.1:9443` on AX42 (local-only, no network access)

## Connectivity via Pangolin Newt Tunnel

Portainer is on AX42, behind a Pangolin **Private Resource**. The solution was to route through the Newt WireGuard tunnel using a hosts entry:

```
100.96.128.22 portainer.jefe.ovh
```

**Network topology:**
- `pangolin` WG interface on this VPS: `100.90.128.14/24`
- Newt client subnet (private resources): `100.96.128.0/24`
- Portainer internal IP: `100.96.128.22` (resolved from inside pangolin-cli container via Newt DNS override)
- Route exists automatically: `100.96.128.0/24 dev pangolin`

**To add the entry:**
```bash
echo "100.96.128.22 portainer.jefe.ovh" >> /etc/hosts
```

Verify:
```bash
curl -sk -H "X-API-Key: ptr_..." https://portainer.jefe.ovh/api/system/version
# → {"UpdateAvailable":false,...,"ServerVersion":"2.39.3",...}
```

## Critical Fix: Header Case Sensitivity (CE vs EE)

Portainer **2.39.3 CE** is case-sensitive with the auth header. The official MCP server sends `X-API-KEY` (uppercase) which Portainer CE rejects with "Invalid JWT token". Patch:

```python
# In passthrough.py:
-UPSTREAM_KEY_HEADER = "X-API-KEY"
+UPSTREAM_KEY_HEADER = "X-API-Key"
```

## ⚠️ Double `/api` Prefix

The OpenAPI spec uses paths without `/api` prefix (e.g. `/endpoints`). FastMCP's OpenAPI provider **automatically prepends `/api`**. So `PORTAINER_URL` must NOT include `/api`:

- ✅ `PORTAINER_URL=https://portainer.jefe.ovh` → calls `https://portainer.jefe.ovh/api/endpoints` ✓
- ❌ `PORTAINER_URL=https://portainer.jefe.ovh/api` → calls `https://portainer.jefe.ovh/api/api/endpoints` ✗ 404

## Guidance Gate

The server enforces a `get_guidance` call once per session before any other tool. This gate also interferes with `hermes mcp add` initial connection test (sends `tools/list` → gate refuses → save as `enabled: false`).

**Fix:** After `hermes mcp add portainer`, edit `~/.hermes/config.yaml`:
1. Add `PORTAINER_URL` to `env:` section
2. Set `enabled: true`

## Registration Command

```bash
printf "Y\nY\n" | hermes mcp add portainer \
  --command "/usr/local/lib/hermes-agent/venv/bin/mcp-portainer" \
  --env "PORTAINER_URL=https://portainer.jefe.ovh" \
  --env "PORTAINER_API_KEY=ptr_..."
```

**Bash quoting gotcha:** API keys with `/` chars break inline `--env`. Save key to file and use `$(cat file)` or Python subprocess.

## Tailscale + Pangolin

Tailscale and Pangolin both use WireGuard — running them together causes instability:
- `docker exec pangolin-cli curl` → exit 28 (timeout) or 6 (DNS)
- **Fix:** `tailscale down` before Pangolin operations
- **Restore:** `tailscale up --accept-dns=false --accept-routes --login-server=https://heand.jefe.ovh`
