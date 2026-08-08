# Site Identification — Picking the Right Newt Site

## The Problem

Generic or auto-generated hostnames (e.g. `Debian-trixie-latest-amd64-base`) don't tell you which Pangolin site the machine belongs to. Assuming "site 28 = Hermes VPN" is wrong when the machine is actually the **Hetzner** server.

This wastes time: you create the resource on the wrong site, the user corrects you, you delete and recreate.

## The Fix — Always Check External IP First

```bash
# From the machine where the service runs:
curl -s https://api.ipify.org
```

Then cross-reference against the site map:

| Site ID | IP | Name |
|---------|-----|------|
| 28 | 178.105.179.232 | Hermes VPN |
| 6 | 37.27.126.113 | **Hetzner (Edner)** |
| 18 | (Tailscale 100.64.0.3) | JNAS |
| 1 | (Tailscale 100.64.0.8) | Home Assistant |

## When Hostname Is Ambiguous

- **DO NOT** trust `hostname` or `/etc/hostname` — these are set at image creation and may not match the machine's real identity
- **DO** check the external IP before assuming a site
- **DO** check the user's infrastructure knowledge: "Tu es sur Edner ou sur le VPS Hermes ?"
