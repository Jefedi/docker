# Pangolin CLI Client — Docker Setup

Full Docker Compose setup for connecting a machine to the Pangolin mesh as a client (Newt/OLM).

## Docker Compose

```yaml
services:
  pangolin-cli:
    image: fosrl/pangolin-cli
    container_name: pangolin-cli
    restart: unless-stopped
    network_mode: host
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    environment:
      - PANGOLIN_ENDPOINT=https://pangolin.jefe.ovh
      - CLIENT_ID=<olm_id>
      - CLIENT_SECRET=<olm_{secret}>
```

## Get OLM ID + Secret

The client must be created in Pangolin first (via UI: Clients → Create Client, or via API). The secret is shown **only once** at creation — copy it immediately.

## System Install Alternative

```bash
curl -fsSL https://static.pangolin.net/get-cli.sh | sudo bash
sudo pangolin up --id <olm_id> --secret <olm_secret> --endpoint https://pangolin.jefe.ovh --attach
```

## Verify Connection

```bash
docker logs pangolin-cli --tail 5
# Look for: "WireGuard connection to site X is CONNECTED (RTT: ...ms)"
# Also: both sites should pass rapid holepunch tests
```

Check from Pangolin API:
```
mcp_pangolin_client_by_clientId(clientId=N)
# Look for: online: true
```

## ⚠️ Critical: Tailscale ts-input Conflict

When Tailscale is also running on the same host, its iptables `ts-input` chain DROPs all traffic in the CGNAT range (100.64.0.0/10) arriving on any interface except `tailscale0`. Pangolin also uses CGNAT addressing (100.90.128.0/24 for org subnet, 100.96.128.0/24 for utility subnet) — these fall INSIDE 100.64.0.0/10.

**Symptom:** Pangolin CLI reports `online: true` and WireGuard connections are established, but:
- `ping 100.96.128.1` (Pangolin DNS) times out
- `dig @100.96.128.1` times out
- `curl` to private resource alias addresses (100.96.128.x) times out
- `ip route get 100.96.128.21` correctly shows route via `pangolin` interface ✅ (yet still fails)

**Root cause in iptables:**
```
Chain ts-input (1 references)
 pkts bytes target     prot opt in     out     source         destination
    0     0 RETURN     all  --  !tailscale0 *  100.115.92.0/23   0.0.0.0/0
   77  4561 DROP       all  --  !tailscale0 *  100.64.0.0/10     0.0.0.0/0
```

Return packets from the Pangolin mesh arrive on the `pangolin` interface and match the DROP rule.

**Fix — Insert ACCEPT rule before the Tailscale DROP:**
```bash
iptables -I ts-input 1 -i pangolin -j ACCEPT
```

**Verify:**
```bash
iptables -L ts-input -n -v | head -5
# Chain ts-input (1 references)
#  pkts bytes target     prot opt in     out     source         destination
#     0     0 ACCEPT     all  --  pangolin *  0.0.0.0/0      0.0.0.0/0     ← new rule
#     0     0 ACCEPT     all  --  lo     *    100.64.0.9     0.0.0.0/0
# 59601 6371K ACCEPT     all  --  tailscale0 * 0.0.0.0/0      0.0.0.0/0
```

**Make persistent (survives reboots) — iptables-persistent:**
```bash
apt-get install -y iptables-persistent
netfilter-persistent save
```

**Or via systemd oneshot:**
```bash
cat > /etc/systemd/system/pangolin-iptables.service << 'UNIT'
[Unit]
Description=Fix Pangolin mesh routing blocked by Tailscale ts-input
After=network.target
Before=tailscaled.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/iptables -I ts-input 1 -i pangolin -j ACCEPT
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

systemctl enable --now pangolin-iptables.service
```

**After the fix:**
- `dig @100.96.128.1 subdomain.jefe.ovh A +short` returns the alias address (e.g. 100.96.128.21)
- `curl -sk https://100.96.128.21/` reaches the private resource backend (401 = real backend, not Pangolin placeholder)
- Private HTTP resources via alias address work

## Test Private Resource Access

Once connected and the iptables fix is applied:

```bash
# DNS resolution via Pangolin mesh
dig @100.96.128.1 subdomain.jefe.ovh A +short
# → Returns alias IP (e.g. 100.96.128.21)

# Direct API access to the backend (bypasses Pangolin proxy)
curl -sk https://100.96.128.21/users/api-keys
# → 401 = real backend responding (the service, not Pangolin's placeholder)
# → timeout/000 = routing still broken

# Via domain with resolved IP
curl -sk --resolve subdomain.jefe.ovh:443:100.96.128.21 \
  "https://subdomain.jefe.ovh/"
```

## Access Flow Summary

| Step | Method | What it proves |
|------|--------|----------------|
| 1 | `docker logs pangolin-cli` | WireGuard tunnel is UP |
| 2 | `mcp_pangolin_client_by_clientId(N)` shows `online: true` | Pangolin confirms client connected |
| 3 | `iptables -L ts-input` has `-i pangolin -j ACCEPT` | Tailscale isn't blocking return traffic |
| 4 | `dig @100.96.128.1 domain A +short` returns an IP | DNS proxy works → mesh routing works |
| 5 | `curl -sk https://100.96.128.21/` returns non-timeout | Private resource reachable via alias |
