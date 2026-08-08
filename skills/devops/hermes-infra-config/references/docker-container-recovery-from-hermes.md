# Docker Container Recovery from Inside Hermes

When Hermes runs inside a Docker container with the host's Docker socket mounted,
container management has specific pitfalls and patterns.

## The Core Problem: Bind Mount Path Resolution

Docker bind mounts resolve on the **host** filesystem, not inside the Hermes container.
A compose file at `/opt/data/radicale/docker-compose.yml` with `./config:/config:ro`
makes Docker look for `/opt/data/radicale/config` on the **host** — which may not exist
if the host's directory structure differs from Hermes's.

### Symptoms
- Container logs: `Failed to load config file '/config/config': No such file or directory`
- The file EXISTS at the path inside Hermes but Docker can't see it
- `docker run --rm -v /opt/data/radicale/config:/check alpine ls /check/` shows an empty dir

### Diagnosis
Check what Docker actually sees on the host:
```bash
docker run --rm -v /srv/docker/<stack>:/check alpine ls -la /check/
```
The host paths may be completely different from Hermes's paths. The homelab uses
`/srv/docker/<stack-name>/` on the host for most compose stacks.

### Fix: Use host paths in compose, not Hermes paths

Option A — Edit the compose file on the host via a helper container:
```bash
docker run --rm -v /srv/docker/<stack>:/work alpine sh -c '
  sed -i "s|./config|/srv/docker/<stack>/config|g" /work/compose.yaml
'
```

Option B — Run compose from the host's working directory:
```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /srv/docker/<stack>:/srv/docker/<stack> \
  -w /srv/docker/<stack> \
  docker:latest compose -f compose.yaml up -d <service>
```

Option C — Create the container manually with `docker run` using absolute host paths.

## docker compose v2 Not Available Inside Hermes

The Hermes container may not have `docker compose` (v2 plugin). Solutions:

1. **Copy the plugin from a profile**:
```bash
cp /opt/data/profiles/business/home/.docker/cli-plugins/docker-compose \
   /opt/data/home/.docker/cli-plugins/docker-compose
chmod +x /opt/data/home/.docker/cli-plugins/docker-compose
docker compose version  # verify
```

2. **Use the `docker:latest` helper image** (has compose v2 built in):
```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /srv/docker/<stack>:/srv/docker/<stack> \
  -w /srv/docker/<stack> \
  docker:latest compose -f compose.yaml up -d <service>
```

⚠️ `docker/compose:latest` is compose v1 and does NOT support modern compose syntax
(networks at top level, etc.). Always use `docker:latest` with `compose` subcommand.

## Orphaned Kernel Sockets Blocking Container Startup

### Problem
After a container is force-stopped, a UDP socket may remain in the kernel's socket
table with no process owning it. New containers trying to bind the same port get
`address already in use` despite no visible process holding it.

### Diagnosis
```bash
# Find the socket (port 1900 = 0x076C in hex)
cat /proc/net/udp6 | grep ':076C'
# Shows: ref=23527 inode=53712 uid=0 — but no PID has this fd open
```

### Fix Options
1. **Wait** — orphaned sockets eventually time out (can take hours) or clear on reboot
2. **Remove the port mapping** — if the port isn't essential (e.g. DLNA/SSDP port 1900
   for Jellyfin), recreate the container without that port mapping
3. **Reboot the host** — guaranteed cleanup but requires downtime

### Common Case: Jellyfin Port 1900/UDP (SSDP/DLNA)
Port 1900 is SSDP discovery for DLNA clients. It's NOT needed for web access via
Pangolin/reverse proxy. Removing it from the compose's port list lets Jellyfin start
immediately. The only impact: DLNA auto-discovery on local network won't work (clients
need manual URL entry).

To remove: edit the compose file on the host:
```bash
docker run --rm -v /srv/docker/media-center:/work alpine sh -c '
  sed -i "/127.0.0.1:1900:1900\/udp/d" /work/compose.yaml
'
```
Then recreate the container via compose.

## read_only: true + chown Crash-Loop

Containers with `read_only: true` that attempt `chown` on their data volume will
crash-loop with `Permission denied`.

### Common Case: tomsquest/docker-radicale
The entrypoint runs `chown /data` on startup. With `read_only: true`, this fails.

**Fix**: Add `TAKE_FILE_OWNERSHIP=false` to the environment. The volume should already
be owned by UID 2999 (radicale) — verify:
```bash
docker run --rm -v <volume-name>:/check alpine stat -c '%u:%g %a' /check
# Should show: 2999:2999 770
```

## Container Without Network (Empty NetworkSettings)

If a container fails to bind a port on creation but the process starts anyway,
`docker ps` shows it as "running" but:
- `docker inspect <name> --format '{{json .NetworkSettings.Networks}}'` → `{}`
- `docker inspect <name> --format '{{json .NetworkSettings.Ports}}'` → `{}`
- `docker port <name>` → no output
- `curl 127.0.0.1:<port>` → connection refused

The container has no IP and no port mappings. Fix: stop + remove + recreate the
container (resolving the original port conflict first).

## Newt WireGuard Tunnel Down (502 on All Newt-Routed Services)

When all services through a Newt site return 502 simultaneously, the WireGuard
tunnel is down. Key diagnostic signs:

```bash
docker logs newt --tail 20 2>&1 | grep -iE 'tunnel|wg.*register|proxy manager|No tunnel'
# "No tunnel IP or proxy manager available" → tunnel is down
# "SendMessageInterval timed out for newt/wg/register" → server not responding
# "WireGuard device is not initialized" → WG device exists but has no config

docker exec newt ip addr show wg0
# state DOWN = tunnel not established
```

**Partial failure**: Services routing through Tailscale (e.g. `home.jefe.al`) may
work while Pangolin/WG-routed services return 502. This confirms the issue is
WG-specific, not a general network problem.

**Root cause is usually server-side**: The Pangolin server (`pangolin.jefe.ovh`)
stops responding to WG registration messages. Fix: restart the Pangolin+Gerbil
stack on the remote server (`46.62.210.41`), then restart Newt.

### Newt as Docker Container (Hetzner server, site 6)

On the Hetzner server, Newt runs as a Docker container:
```bash
docker ps | grep newt
docker inspect newt --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'PANGOLIN|NEWT'
docker restart newt
docker logs newt --tail 30
```

Key env vars: `PANGOLIN_ENDPOINT`, `NEWT_ID`, `NEWT_SECRET`, `NEWT_SYSTEM_SUBSTRATE=CONTAINER`.
The container uses `--network host` and `--privileged` with `CAP_NET_ADMIN` + `CAP_SYS_MODULE`.

### Newt as systemd service (VPS, site 28)

```bash
newt client  # start
# or
systemctl restart newt-client
```

Config at `~/.config/newt-client/config.json`.