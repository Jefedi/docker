# Container Self-Check Procedure

Quick health audit of the Hermes container itself (not the full homelab — for that use `infrastructure-doctor`).

## Checklist

### 1. Locales
```bash
locale
echo "LANG=$LANG"
echo "LC_ALL=$LC_ALL"
```
**Healthy:** `LANG=fr_FR.UTF-8` or `en_US.UTF-8`, `LC_ALL` set.
**Problem:** `LANG=` (empty), everything `POSIX` — can cause encoding issues.
**Fix:** Add `LANG=fr_FR.UTF-8` to docker-compose.yml environment (survives reboots), or `export LANG=fr_FR.UTF-8` in shell init (ephemeral).

### 2. Tailscale interface
```bash
ls /sys/class/net/tailscale0 2>/dev/null && echo "tailscale0 present" || echo "NO tailscale0"
cat /proc/net/fib_trie | grep -oP '100\.\d+\.\d+\.\d+' | sort -u
```
**Note:** The `tailscale` CLI binary may NOT be in PATH inside the container. The interface can still be present at kernel level. Check `/sys/class/net/tailscale0` and IPs in the 100.64.0.x range rather than relying on `tailscale status`.

### 3. Gateway processes
```bash
ps aux | grep "hermes.*gateway run" | grep -v grep
```
Should show only the profiles you want active. Each profile has a service dir at `/run/service/gateway-<profile>`.

### 4. Key services reachable
```bash
# NAS
ping -c1 -W2 100.64.0.1
# Home Assistant
ping -c1 -W2 100.64.0.8
# Hermes local
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000
# API server
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
```

### 5. s6 services status
```bash
ls /run/service/ | grep gateway
```
Each gateway-<profile> dir should exist. Check for `down` files (means disabled):
```bash
for d in /run/service/gateway-*/down; do echo "disabled: $(dirname $d | xargs basename)"; done
```

### 6. Disk and memory
```bash
df -h /
free -h
uptime
```

### 7. Pangolin tunnel (Newt)
```bash
docker logs newt --tail 5 2>&1
```
Look for "connection refused" errors — means local services aren't listening on the ports Newt expects.