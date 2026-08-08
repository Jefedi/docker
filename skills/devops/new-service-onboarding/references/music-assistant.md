# Music Assistant (MA) — Docker Deploy & Spotify Troubleshooting

## Docker Install

Music Assistant **requires** `--network host` for mDNS/UPnP discovery (mandatory).

### docker run (quick)
```bash
docker run -d \
  --name music-assistant-server \
  --restart unless-stopped \
  --network host \
  -v /root/docker/music-assistant-server/data:/data \
  -e LOG_LEVEL=info \
  --cap-add=SYS_ADMIN \
  --cap-add=DAC_READ_SEARCH \
  --security-opt apparmor:unconfined \
  ghcr.io/music-assistant/server:latest
```

### docker-compose (preferred — Jefe uses this)
```bash
cd /root/docker/music-assistant-server && docker compose up -d
```

```yaml
services:
  music-assistant-server:
    image: ghcr.io/music-assistant/server:latest
    container_name: music-assistant-server
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/data
    cap_add:
      - SYS_ADMIN
      - DAC_READ_SEARCH
    security_opt:
      - apparmor:unconfined
    environment:
      - LOG_LEVEL=info
```

Template available at `templates/music-assistant-compose.yml`.

- `cap-add` and `security-opt` are only required for SMB/NFS remote mounts. Omit if not needed.
- Web UI: `http://localhost:8095` **or** `http://127.0.0.1:8095` **or** `http://<tailscale-ip>:8095` (both loopback addresses work identically)
- Streaming: TCP 8097 (auto-selected if occupied)
- First-run: open `/setup` path on first visit
- **Network host mode** means there's NO port mapping — the service binds directly to the host's ports. You can't restrict to `127.0.0.1` via Docker, but the service is only accessible via Tailscale / localhost.

## Spotify 403 Forbidden — Diagnosis

Error from MA logs:
```
403, message='Forbidden', url='https://api.spotify.com/v1/artists/.../top-tracks?market=from_token&country=from_token'
```

**Cause:** The Spotify OAuth token stored by Music Assistant has expired or been revoked (password change, app permission revoked on Spotify's website).

**Fix:** Re-authenticate in MA's UI:
1. Open MA Web UI → Settings → Providers
2. Find the Spotify provider entry
3. Click re-authenticate / re-link your Spotify account
4. A new token pair (access + refresh) is generated

This is NOT the same as the Hermes Spotify tool 403 (which is "no active device" or "Premium required"). The MA-level 403 means the upstream API token itself is dead.

## Data Persistence

- `/data` — all config, database, metadata cache
- Default data dir: `/root/docker/music-assistant-server/data/`
- No additional volumes needed unless streaming local music files (mount `/media`)
