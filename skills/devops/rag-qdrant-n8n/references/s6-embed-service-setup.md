# s6 Embedding Service Setup — Full Walkthrough

## Context

The FastEmbed embedding service (port 9200) needs to be persistent — it should survive Hermes container restarts and auto-restart on crash. This is achieved by registering it as a runtime s6 service under `/run/service/`.

## Key learning: `#!/bin/sh` vs `#!/command/with-contenv sh`

**This is the #1 gotcha.** Static s6 services in the Hermes Docker image (like `dashboard`, `main-hermes`) use `#!/command/with-contenv sh` as their shebang. This works because the Dockerfile copies them into `/etc/s6-overlay/s6-rc.d/` and s6-overlay's init process sets up the PATH for them.

**Runtime services** created under `/run/service/` at runtime do NOT have `with-contenv` on their PATH. If you use `#!/command/with-contenv sh`, the service will fail with **exit code 127** (command not found) and s6-svstat will show `down (exitcode 127)`.

**Fix**: Use plain `#!/bin/sh` for all three scripts (`run`, `log/run`, `finish`). The container environment variables are still inherited — you just don't get the explicit `with-contenv` re-export.

## Step-by-step setup

### 1. Create the service directory

```bash
mkdir -p /run/service/embed-service/log
mkdir -p /run/service/embed-service/event
echo "longrun" > /run/service/embed-service/type
```

### 2. Write the run script

```bash
cat > /run/service/embed-service/run << 'EOF'
#!/bin/sh
set -e
export HOME=/opt/data
cd /opt/data/rag
exec /opt/data/rag-venv/bin/python3 embedding_service.py
EOF
chmod +x /run/service/embed-service/run
```

Note: Use `/opt/data/rag-venv/bin/python3` (absolute path), NOT `source venv/bin/activate && python3`. The venv activation script can fail in restricted s6 environments.

### 3. Write the log/run script

```bash
cat > /run/service/embed-service/log/run << 'EOF'
#!/bin/sh
: "${HERMES_HOME:=/opt/data}"
log_dir="$HERMES_HOME/logs/embed-service"
mkdir -p "$log_dir"
rm -f "$log_dir/lock"
exec s6-log 1 n10 s1000000 T "$log_dir"
EOF
chmod +x /run/service/embed-service/log/run
```

### 4. Write the finish script

```bash
cat > /run/service/embed-service/finish << 'EOF'
#!/bin/sh
if [ "$1" = "78" ]; then exit 125; fi
exit 0
EOF
chmod +x /run/service/embed-service/finish
```

Exit 125 = s6 "permanent failure, do not restart". We use it for exit code 78 (EX_CONFIG, fatal config error).

### 5. Set ownership

```bash
chown -R hermes:hermes /run/service/embed-service/
```

### 6. Start s6 supervision

```bash
/command/s6-supervise /run/service/embed-service &
```

### 7. Verify

```bash
sleep 5
/command/s6-svstat /run/service/embed-service
# Should show: up (pid XXXX) N seconds

curl -s http://localhost:9200/health
# {"status": "ok", "model": "sentence-transformers/all-MiniLM-L6-v2", "dim": 384}
```

## Troubleshooting

### `down (exitcode 127)`

The shebang is `#!/command/with-contenv sh`. Change to `#!/bin/sh`.

### `down (exitcode 1)`

The python script itself is crashing. Check the log:
```bash
cat /opt/data/logs/embed-service/current | tail -20
```

### Service not picked up by s6

After creating the directory, you need to either:
- Start `s6-supervise` manually: `/command/s6-supervise /run/service/embed-service &`
- Or trigger a scan: `/command/s6-svscanctl -a /run/service`

### Restarting the service after code changes

```bash
/command/s6-svc -t /run/service/embed-service
```

### Checking status

```bash
/command/s6-svstat /run/service/embed-service
# up (pid XXXX) N seconds  → running
# down (exitcode N) ...     → crashed, check logs
```

## Note on container restarts

The `/run/service/` directory is on tmpfs and is wiped on container restart. The s6 reconciler (`02-reconcile-profiles`) only restores profile gateway services, not custom runtime services. For full persistence across container restarts, either:

1. Add a cont-init.d script that recreates the service directory on boot (requires modifying the Docker image)
2. Use a watchdog cron that checks the service and recreates it if missing
3. Accept manual restart after container restart (simplest for now)