# RAM Diagnosis — Duplicate MCP Servers from Multiple Gateways

## Background

Discovered during routine performance check: VPS with 3.7 GB RAM showing 73% usage
despite minimal user workload. Root cause: **2 Hermes gateways** (default + dev profiles)
each spawning their own set of MCP STDIO server processes, causing every MCP server
to run in duplicate.

## Symptoms

- `free -h` shows 2.7 GB / 3.7 GB used (73%)
- `ps aux --sort=-%mem | head -30` shows **24+ MCP server processes** each at ~60-75 MB
- `ps aux | grep "gateway run" | wc -l` shows **2 gateways** (default + dev)
- `docker stats` shows normal container usage (<70 MB total for 2 containers)

## Reproduction Recipe

1. Two Hermes gateways running simultaneously (e.g. default + `--profile dev`)
2. Default gateway config has `mcp_servers:` with 21+ servers using STDIO transport (default type)
3. Each gateway spawns its own independent MCP server processes
4. Result: `21 MCP servers × 2 gateways = 42 processes` → ~1.5 GB RAM just for MCP

## Diagnosis Commands

```bash
# Quick triage
free -h
ps aux --sort=-%mem | head -30
docker stats --no-stream

# Count duplicates per MCP server type
ps aux | grep "_server.py" | grep -v grep | \
  awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}' | \
  sort | uniq -c | sort -rn

# Total MCP RAM
ps aux | grep "_server.py" | grep -v grep | \
  awk '{sum+=$6} END {printf "MCP servers total: %.0f MB\n", sum/1024}'

# Check MCP config
python3 -c "
import yaml
with open('/root/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
mcp = cfg.get('mcp_servers', {})
for name, srv in mcp.items():
    print(f'{name}: enabled={srv.get(\"enabled\",True)} type={srv.get(\"type\",\"stdio\")}')" 2>/dev/null
```

## Fix Steps

1. **Kill the extra gateway** from a safe shell (not inside gateway's process group):
   ```bash
   cd /tmp && kill -9 $(cat ~/.hermes/profiles/<profile>/gateway.pid)
   ```
2. **Clean up lock/state files** to prevent stale PID detection:
   ```bash
   rm -f ~/.hermes/profiles/<profile>/gateway.pid
   rm -f ~/.hermes/profiles/<profile>/gateway.lock
   rm -f ~/.hermes/profiles/<profile>/gateway_state.json
   ```
3. **Kill all MCP processes** (the surviving gateway respawns what it needs):
   ```bash
   pkill -f "_server\.py"
   ```
4. **Check RAM recovered**:
   ```bash
   sleep 5 && free -h
   ```

## Known Limitation — Watchdog Respawning

Hermes gateways have a built-in watchdog mechanism (`_resume_windows_gateways_after_update`
in the gateway codebase). Simply killing the dev gateway is **temporary** — the default
gateway's watchdog detects the death and respawns it within seconds. The dev profile's
**PID was identical** (3065724) before and after the kill, confirming the respawn.

For permanent disable:
- Check `~/.hermes/profiles/dev/config.yaml` for auto-start flags
- Or modify the main `~/.hermes/config.yaml` gateway section
- Or stop using the `--profile dev` gateway entirely

## Session Reference

Original investigation: Telegram conversation 2026-06-29. DeepSeek V4 Flash.
Gateways running since Jun 23 (dashboard) and Jun 28 (default + dev gateways).
