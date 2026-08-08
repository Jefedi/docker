---
name: infrastructure-doctor
title: Infrastructure Doctor
description: Full infra health check — Docker containers, disk usage, Uptime Kuma monitors, SSL cert expiry, system updates. One-shot diagnostic report.
tags: [docker, health-check, monitoring, ssl, uptime-kuma, homelab]
---

# Infrastructure Doctor

Run a complete health scan of Jefe's homelab. Output a structured report via Telegram.

## Workflow

### 1. Docker Status
```bash
docker ps -a --format "{{.Names}}\t{{.Status}}\t{{.Image}}" | column -t
docker system df
```

### 2. Disk Usage
```bash
df -h / /home /var/lib/docker 2>/dev/null
```

### 3. System Updates
```bash
apt list --upgradable 2>/dev/null | grep -v "Listing..." | head -20
```

### 4. SSL Certificates (via Pangolin)
Check `api.jefe.ovh` and main domains (`jefe.al`, `jefe.ovh`, `losgalactique.fr`) for cert expiry:
```bash
echo | openssl s_client -servername <domain> -connect <domain>:443 2>/dev/null | openssl x509 -noout -dates
```

### 5. Uptime Kuma Monitors
Use `mcp_uptimekuma_uptimekuma_get_metrics()` to fetch all monitor statuses.

### 6. Memory & Load — Basic
```bash
free -h
uptime
```

### 7. RAM Deep Dive — Top Consumers & MCP Server Duplication

When RAM is high (>70%), the most likely culprit on a Hermes VPS is **duplicate MCP servers** spawned by **multiple running gateways** (default + dev profile, etc).

```bash
# 7a. Top memory consumers
ps aux --sort=-%mem | head -30

# 7b. Count MCP server processes
ps aux | grep "_server.py" | grep -v grep | wc -l

# 7c. Check for duplicates (same MCP server running multiple times)
ps aux | grep "_server.py" | grep -v grep | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}' | sort | uniq -c | sort -rn

# 7d. Total MCP RAM
ps aux | grep "_server.py" | grep -v grep | awk '{sum+=$6} END {printf "MCP servers total: %.0f MB\n", sum/1024}'

# 7e. Count running gateways
ps aux | grep "gateway run" | grep -v grep | wc -l

# 7f. Docker container RAM per container
docker stats --no-stream
```

**How to fix duplicate MCP servers:**
1. Identify which gateway is extra (`ps aux | grep "gateway run" | grep -v grep`)
2. Read its PID from its profile: `cat ~/.hermes/profiles/<profile>/gateway.pid`
3. Kill from OUTSIDE the gateway's process group — `cd /tmp && kill -9 <PID>` (running kill from inside a gateway shell is BLOCKED — SIGTERM propagates)
4. Clean up: `rm -f ~/.hermes/profiles/<profile>/gateway.pid ~/.hermes/profiles/<profile>/gateway.lock ~/.hermes/profiles/<profile>/gateway_state.json`
5. Kill all MCP server processes: `pkill -f "_server\.py"` — the remaining gateway will respawn its own set

**Pitfall — gateway watchdog auto-respawn:** Hermes gateways have a built-in watchdog that automatically respawns other profiles' gateways when they die. Simply killing the process is temporary — the dev gateway will come back within seconds. For permanent disable, the config needs modification (check `~/.hermes/profiles/<profile>/config.yaml` for auto-start settings, or modify the main config.yaml gateway section).

**Checking per-process MCP memory more granularly:**
```bash
ps aux | grep -E "_server\.py|mcp-" | grep -v grep | awk '{printf "PID=%-6s RSS=%-5s %s\n", $2, $6/1024"MB", $NF}'
```

## Output Format

Deliver as a clean Telegram message with emoji headers:
- 🐳 Docker — containers count, running/exited status
- 💾 Disks — usage per mount
- 🔄 Updates — number of pending updates
- 🔒 SSL — expiry dates for main domains
- 📊 Uptime Kuma — monitors status (up/down count)
- ⚡ System — load, memory, uptime

## Cron Usage

Can be scheduled: `hermes cron create "0 8 * * *" "Run infrastructure-doctor skill" --skills infrastructure-doctor --deliver telegram`

## Pitfalls
- Docker ps can be large if many containers — parse with python for clean formatting
- SSL check fails for non-public or Tailscale-only services — skip those
- Don't try to fix issues found; just report them and ask if user wants action
- Jefe prefers compact reports, not verbose output
