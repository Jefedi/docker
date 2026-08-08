---
name: service-removal
title: Service Removal Verification
description: Verify that a service (Docker, systemd, or containerized) was completely removed across all system layers — containers, images, files, ports, firewall, reverse proxy, and agent state.
tags: [cleanup, verification, docker, pangolin, homelab, uninstall]
---

# Service Removal Verification

Systematically verify that a service is fully gone. When the user asks "did you actually delete X?" or "tu l'as pas supprimer?", this skill provides a layered verification approach.

## When to Use

- User asks to confirm/unconfirm a deletion
- User reports a URL or port is still accessible after removal
- You want to do a cleanup and need to verify all traces are gone
- User says "supprime X et tout ce qui concerne"
- User says "l'url est encore accessible"

## Verification Checklist (Layered)

Work through each layer in order. For each, report a clear ✅ or ❌.

### 1. Docker Layer
```bash
# Containers (running AND stopped)
docker ps -a --format '{{.Names}}\t{{.Status}}' | grep -i <service>

# Images
docker images | grep -i <service>

# Volumes
docker volume ls --format '{{.Name}}' | grep -i <service>

# Networks
docker network ls --format '{{.Name}}' | grep -i <service>
```

### 2. Filesystem Layer
```bash
# Config/data directories
ls -la /root/docker/<service>/ 2>/dev/null
ls -la /root/<service>/ 2>/dev/null
ls -la /opt/<service>/ 2>/dev/null

# Docker compose files
find / -name "docker-compose*" -path "*<service>*" 2>/dev/null

# Config files
find / -name "*<service>*" -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null
```

### 3. Network Layer
```bash
# Listening ports
ss -tlnp | grep -E ':<port1>|<port2>'

# Any remaining connections
ss -tnp | grep -i <service>
```

### 4. Firewall Layer
```bash
# iptables rules (by port)
iptables -L -n --line-numbers | grep -i <port>

# UFW rules
ufw status numbered | grep -i <port>

# Persistent iptables
cat /etc/iptables/rules.v4 2>/dev/null | grep -i <port>
cat /etc/iptables/rules.v6 2>/dev/null | grep -i <port>
```

### 5. Reverse Proxy Layer (Pangolin)
Check the Pangolin API for orphaned resources. The MCP `pangolin` tool may be disabled — use curl directly if possible:

```bash
curl -sk "https://api.jefe.ovh/v1/org/jefe/resources" \
  -H "x-api-key: $PANGOLIN_API_KEY" | jq '.data[] | select(.fullDomain | test("<service>"))'
```

**Pitfall:** The Pangolin API key may be stored in `/root/.hermes/config.yaml` under `mcp.pangolin.env.PANGOLIN_API_KEY`. If it appears truncated (e.g. `e0411i...upd3`), you cannot query the API directly — the MCP binary resolves it at runtime but the stored value is incomplete. In this case:
- Check if the user can see the resource in their Newt client
- Ask the user to provide the full API key
- Or temporarily enable the pangolin MCP (`enabled: true` in config) and use its tools

**Pangolin resource states:**
- `404 page not found` from public proxy = resource may be private/deleted
- User can still see it in Newt client = resource still exists in Pangolin DB
- To actually DELETE: resource must be removed via Pangolin API, not just the container/files

### 6. Cron / Agent State Layer
```bash
# Cron jobs
cronjob action=list

# Memory — check for stale references to the service
# Remove any memory entries about the deleted service
```

### 7. Systemd Layer (if applicable)
```bash
systemctl list-units --all | grep -i <service>
systemctl list-unit-files | grep -i <service>
systemctl status <service> 2>/dev/null
```

## Efficient Verification Pattern

For a fast comprehensive check, delegate the verification:

```python
from hermes_tools import terminal, mcp_dockhand_*

# Check Dockhand across all environments
for env_id in [1, 2, 3, 4]:
    containers = mcp_dockhand_dockhand_list_containers(environment_id=env_id)
    # Filter for service name
    images = mcp_dockhand_dockhand_list_images(environment_id=env_id)
    # Filter for service image

# Local terminal checks
result = terminal("docker ps -a | grep -i <service>")
# ... etc
```

Or use `delegate_task` with a comprehensive goal:
- Pass service name, ports, known paths, and host info
- Subagent checks Docker, filesystem, ports, firewall, proxy
- Returns summary of what's left

## Reference Files

- `references/pangolin-cleanup.md` — Detailed Pangolin API setup, key status, resource-vs-container mapping, temporary MCP enable pattern

## Common Pitfalls

- 🚩 **Docker image persists** after container/compose removal. The image stays on disk until pruned. Ask the user if they want `docker rmi <image>` to free space.
- 🚩 **Pangolin resource outlives the container.** Deleting a Docker container does not delete its Pangolin reverse proxy resource. Must delete via Pangolin API separately.
- 🚩 **Pangolin API key may be truncated** in hermes config. MCP tool may resolve at runtime but curl doesn't work without the real key. Always check `enabled: true/false` for the pangolin MCP first.
- 🚩 **iptables rules persist** after container stops. If you used iptables to restrict a service to localhost, the rules stay even after the container is gone. Remove them explicitly.
- 🚩 **UFW not installed** — common on fresh Debian VPS. The system relies on raw iptables or Docker's built-in rules.
- 🚩 **"URL encore accessible"** from Newt client can mean EITHER:\n  - **Resource still exists** in Pangolin (not actually deleted) → check via Pangolin API\n  - **Client-side caching** (DNS cache, Newt stale entry) — the resource IS deleted but the client hasn't refreshed yet\n  \n  How to tell the difference:\n  - Check the **public proxy** first: `https://<domain>` → if `404 page not found` via browser/proxy, the resource is gone; the Newt accessibility is just a stale cache\n  - If the public proxy also resolves/loads content, the resource was NOT deleted\n  - The #1 false-positive scenario: user says "l'url marche encore" but public proxy returns 404 → reassure them it's deleted, the client just needs a refresh/restart
