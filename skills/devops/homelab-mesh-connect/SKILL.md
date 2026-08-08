---
name: homelab-mesh-connect
description: "Install the Tailscale client and connect a new device to Jefe's self-hosted Headscale/Pangolin mesh VPN. Covers Debian install, Headscale auth, Pangolin config lookup, and common pitfalls."
version: 1.0.0
author: Agent
tags: [tailscale, headscale, pangolin, vpn, mesh, networking, homelab]
---

# Homelab Mesh Connect — Tailscale → Headscale (Pangolin)

Connect any Linux device to Jefe's **self-hosted Headscale** mesh network managed via Pangolin.

## ⚡ Important: "install headscale" means install Tailscale client

When Jefe says **"install headscale"** or **"installer headscale"**, he means:

1. Install the **Tailscale** client (the *client* software) on the device
2. Connect it to his existing Headscale **server** (the *server*, already running on his infrastructure)

He does **NOT** mean installing the Headscale server software itself. The Headscale server is managed through Pangolin.

## Server Info

| Item | Value |
|------|-------|
| Headscale server URL | `https://heand.jefe.ovh` |
| Pangolin dashboard | `https://pangolin.jefe.ovh` |
| Pangolin API | `https://api.jefe.ovh` |
| OS (this host) | Debian 13 (trixie) / Hetzner |

## Step 1 — Install Tailscale Client

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

This adds the Tailscale apt repo and installs `tailscaled` service (auto-enabled via systemd).

## Step 2 — Authenticate to Headscale

Two methods — Jefe's Headscale has OIDC configured, so prefer option A.

**A — OIDC (preferred — no pre-auth key needed):**
```bash
tailscale up --login-server=https://heand.jefe.ovh
```
This prints a login URL. Send it to Jefe to open in browser and auth via OIDC.

**B — Pre-Auth Key (alternative):**
From the Headscale server directly:
```bash
headscale preauthkeys create --user jefe
```
Or from Pangolin dashboard: `https://pangolin.jefe.ovh` → Headscale section → Pre-auth Keys → Create.

Then connect:
```bash
tailscale up --login-server=https://heand.jefe.ovh --authkey=YOUR_KEY
```

## Step 3 — Verify Connection

```bash
tailscale status
# Should show the new device in the mesh
tailscale ip -4
# Shows the Tailscale IP assigned by Headscale
```

Enable autostart:
```bash
systemctl enable tailscaled
```

## Step 4 — Expose a Service via Pangolin (optional follow-up)

Once connected to the mesh, you can make local services accessible via a public URL through Pangolin. The Newt tunnel agent runs on this host (site "Hermes VPN", ID 28 in Jefe's infrastructure) and routes traffic to `127.0.0.1:<port>`.

See `references/pangolin-api-create-resource.md` for the exact Pangolin REST API calls to create a resource and target.

## Reference

See `references/headscale-connection-examples.md` for troubleshooting, ACL snippets, and device-specific connection patterns.
