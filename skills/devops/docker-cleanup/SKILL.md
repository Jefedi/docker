---
name: docker-cleanup
title: Docker Cleanup
description: Clean up unused Docker resources — dangling images, large container logs, orphan volumes, dead containers. Reports freed space.
tags: [docker, cleanup, maintenance, disk-space, homelab]
---

# Docker Cleanup

Safe cleanup of Docker resources. Always report what was freed before/after.

## Workflow

### 0. MANDATORY: Before any cleanup

**Jefe's cleanup rules (DO NOT VIOLATE):**
- NEVER use `docker system prune -af` without showing Jefe what it will kill first AND getting explicit confirmation per category
- NEVER use `--volumes` flag without explicit yes — volumes may hold project data that looks "orphaned" but is wanted
- NEVER touch anything Hermes-related without asking: Hermes config, `.hermes/`, `.brv-cli/`, Docker images that Hermes workflows might need (signal-cli, pangolin-cli, etc.)
- NEVER delete backups, node_modules, or caches without asking first — these may be wanted even if they seem stale to you
- Ask about each category individually: "Docker images? Containers? Volumes? Build cache? Temp files? Caches?"

**When Jefe says "clean what you can" — that means:**
- ✅ Safe: docker container prune, docker image prune (dangling only), docker builder prune, /tmp/ temp files, pip cache
- ⚠️ ASK FIRST: `docker system prune -af`, any `--volumes`, npm cache, old backups, node_modules, Docker images that look like they belong to active services
- ❌ DON'T: Hermes cache/data/config, running service images, anything Jefe calls "Hermès"

### 1. Assessment Phase (MANDATORY)
Show the current state before proposing any cleanup:
```bash
echo "=== Disk Overview ==="
df -h /
echo ""
echo "=== Top Disk Users ==="
du -sh /* 2>/dev/null | sort -rh | head -15
echo ""
echo "=== Docker State ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""
docker system df
```

Then check what's running vs unused:
```bash
echo "=== Containers (all) ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | head -30
echo "=== Unused Images ==="
docker images -f dangling=true --format "{{.Repository}}:{{.Tag}} ({{.Size}})"
echo "=== Orphan Volumes ==="
docker volume ls -qf dangling=true
echo "=== Build Cache ==="
docker builder prune -a --filter until=48h --force 2>&1 | tail -1
```

### 2. Per-category ask (one by one, never bulk-nuke)

For each category, describe what will be removed and ask:
```markdown
🐳 Docker images in use: <count> (for: service1, service2)
🧹 Unused/dangling images: <count> (<size>)
🗑️ Stopped containers: <count>
📦 Orphan volumes: <count> (<size>) — WARNING if > 0, may be project data
🔧 Build cache: <size>
```

**Safer commands when approved:**

**Stopped containers:**
```bash
docker container prune -f
```

**Dangling images only (safe default):**
```bash
docker image prune -f
```

**All unused images (ask first — may include Hermes-adjacent images like signal-cli, pangolin-cli):**
```bash
docker image prune -af
```

**Orphan volumes** (NEVER use `docker system prune --volumes`):
```bash
docker volume prune -f
```

**Build cache:**
```bash
docker builder prune -f
```

**Log truncate** (only if user confirms):
```bash
truncate -s 0 $(find /var/lib/docker/containers/ -name "*.log" -size +100M 2>/dev/null)
```

**Non-Docker safe cleanups** (ask about these individually):
```bash
# Pip cache (safe — pip not primary package manager)
pip cache purge

# /tmp stale files (check first what's there)
ls -la /tmp/

# npm cache (only if user confirms — Hermes uses Node.js internally)
npm cache clean --force
```

### 3. Final Report
```bash
echo "=== After Cleanup ==="
df -h /
docker system df
```

## Multi-Host Cleanup (via Dockhand MCP)

This skill runs `docker` commands on the **local machine** only. For cleanup on **remote hosts** (jnas, jtower, VPS Pangolin), use the Dockhand MCP tools:

- `mcp_dockhand_dockhand_list_containers(environment_id=N)` — list containers on host N
- Dockhand env IDs: 1=ax42, 2=jnas, 3=VPS Pangolin, 4=jtower
- For disk cleanup on remote hosts, ask the user to run locally or SSH

## Pitfalls
- Never `docker system prune -af` without asking — too destructive
- Truncating logs is safe (logs restart fresh), but stop the container first if using overlay2
- `docker builder prune` is safe and can free GBs if builds happen frequently
- Always present before/after numbers so Jefe sees the value
- If Jefe says "oui" — just do all safe cleanups (containers, images, volumes, builder, logs)
- For remote hosts, prefer Dockhand MCP tools over local docker commands
