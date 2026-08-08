# Docker + rp_filter Compatibility

## The Problem
Setting `net.ipv4.conf.all.rp_filter = 1` (strict mode) breaks Docker networking.
Docker containers use bridge networks where the container's source IP is reachable
through a different interface than the one packets arrive on.

When `rp_filter=1`, the kernel performs strict reverse path filtering:
- Checks that the source IP of each incoming packet is reachable via the interface it arrived on
- Docker's bridge (docker0) and container veth interfaces fail this check
- Result: **packets from containers are silently dropped**

## Safe settings for Docker hosts

### Option A: Loose mode (recommended)
```ini
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.default.rp_filter = 2
```
- Validates that the source IP is reachable via **any** interface (not just the one it arrived on)
- Catches spoofed packets from completely unknown sources
- Full Docker compatibility

### Option B: Per-interface (advanced)
Set strict mode on physical interfaces only, leave Docker's interfaces at 0:
```ini
# Apply to eth0 only (adjust for your interface name)
net.ipv4.conf.eth0.rp_filter = 1
# Docker interfaces (lo, docker0, veth*) stay at default (0)
```

## Verification
```bash
# Check the active value
sysctl net.ipv4.conf.all.rp_filter

# Check Docker containers are reachable
docker ps
docker run --rm alpine ping -c 1 8.8.8.8
```

## Note for server-hardening
The imthenachoman guide recommends `rp_filter=1` (strict). This is correct for
systems without Docker. On a Docker host, override to `=2` in the skill's
`99-hardening.conf` template.
