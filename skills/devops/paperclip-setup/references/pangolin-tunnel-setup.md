# Pangolin Tunnel + Paperclip Setup

This document captures the exact sequence for exposing Paperclip (running on `127.0.0.1:3100`) to the public internet via Pangolin tunnel.

## Architecture

```
Browser → https://paperclip.example.com → Pangolin → 127.0.0.1:3100 → Paperclip
```

Pangolin terminates SSL and proxies HTTP to Paperclip's loopback. Users authenticate against Pangolin first, then get proxied to Paperclip.

## Prerequisites

- Pangolin server running (e.g., at `https://pangolin.example.com`)
- Newt client installed on the Paperclip host
- Paperclip installed globally (`npm install -g paperclipai`)

## Steps

### 1. Install Newt tunnel client

```bash
curl -fsSL https://newt.quilibrium.com/install.sh | bash
newt connect https://pangolin.example.com
# Enter the ID and secret from Pangolin admin
```

Verify: `ps aux | grep newt`

### 2. Add the domain in Pangolin

Create a resource in Pangolin:
- **Domain:** `paperclip.example.com` (or wildcard `*.example.com`)
- **Target:** `http://127.0.0.1:3100` (HTTP, not HTTPS — Paperclip is plain HTTP)
- **SSL:** Enabled (Pangolin terminates TLS)
- **Organization:** The correct Pangolin org that owns the domain

### 3. Authorize the hostname in Paperclip

```bash
sudo -u paperclip bash -c 'cd /home/paperclip/.paperclip && source /home/paperclip/.paperclip/.env && /home/paperclip/.local/bin/paperclipai allowed-hostname paperclip.example.com'
```

Or edit `config.json` directly:
```json
"allowedHostnames": ["paperclip.example.com"]
```

### 4. Kill old processes and restart

**Critical:** Old Paperclip processes continue serving with stale config. Kill ALL:

```bash
pkill -f "paperclipai/server" 2>/dev/null
sleep 2
ss -tlnp | grep 3100  # verify nothing on port
```

Then restart:

```bash
sudo -u paperclip bash -c 'cd /home/paperclip/.paperclip && source /home/paperclip/.paperclip/.env && PAPERCLIP_MIGRATION_PROMPT=never PAPERCLIP_MIGRATION_AUTO_APPLY=true node /home/paperclip/.local/lib/node_modules/@paperclipai/server/dist/index.js'
```

Or if using the CLI:
```bash
sudo -u paperclip bash -c 'cd /home/paperclip/.paperclip && source /home/paperclip/.paperclip/.env && paperclipai run'
```

### 5. Verify

Local health check:
```bash
curl -H "Host: paperclip.example.com" http://127.0.0.1:3100/
# Should return HTML (200 OK)
```

External check:
```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}" -L --max-redirs 0 https://paperclip.example.com
# Should show 302 → Pangolin auth URL
```

The user accesses `https://paperclip.example.com` in browser, authenticates against Pangolin, and is redirected to Paperclip.

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Hostname not allowed" | Old Paperclip process with stale config | Kill ALL processes, restart fresh |
| 502 Bad Gateway | Paperclip not running | Start Paperclip, verify with `curl` or `ss` |
| Auth redirect loop | User not logged into Pangolin | Expected — log into Pangolin first |
| Connection refused | Port mismatch or Paperclip crashed | Check `ss -tlnp \| grep 3100` |