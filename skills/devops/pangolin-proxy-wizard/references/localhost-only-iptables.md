# Localhost-Only Binding via iptables

When a service uses `--network host` (required by Music Assistant, some streaming services), you cannot restrict it via Docker port binding. Use iptables to block external access while keeping localhost + Newt client access.

## iptables Rules

```bash
# ACCEPT from loopback
iptables -A INPUT -p tcp --dport 8095 -i lo -j ACCEPT
# DROP everything else
iptables -A INPUT -p tcp --dport 8095 -j DROP
```

The Newt client connects to `127.0.0.1:<port>` (loopback), so it passes the `-i lo -j ACCEPT` rule.

## Make Persistent

```bash
apt-get install -y iptables-persistent
netfilter-persistent save
```

This saves rules to `/etc/iptables/rules.v4` so they survive reboot.

## Verify

```bash
# Localhost works
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8095/  # → 200

# Public IP from INSIDE the same machine still works (via lo interface)
curl -s -o /dev/null -w "%{http_code}" http://PUBLIC_IP:8095/  # → 200 (from this machine)

# From another machine → connection timed out (actually blocked by DROP)
```

Note: testing the public IP from the same machine still succeeds because `curl` to the machine's own public IP goes through the loopback interface internally. The real test is from an external machine.

## When to Use

- Services that require `--network host` (Music Assistant, mDNS/UPnP/Discovery protocols)
- Services behind a Pangolin private resource accessed via Newt client at `127.0.0.1:<port>`
- Any Docker service you want accessible only through the VPN/Pangolin tunnel, not directly from the internet

## Reset

```bash
iptables -F INPUT
# Then re-add rules or restore from saved
```
