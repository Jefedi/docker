# Signal Gateway Setup Details

## Incompatibility: bbernhard/signal-cli-rest-api vs Hermes

### GitHub Issues

- [#31674](https://github.com/NousResearch/hermes-agent/issues/31674) — "bbernhard/signal-cli-rest-api is API-incompatible with the Hermes adapter — and looks like it works"
- [#32337](https://github.com/NousResearch/hermes-agent/issues/32337) — "[Bug]: signal-cli-rest-api does not work"
- Comment from GottZ: "The reported 404 is caused by pointing Hermes' native signal-cli HTTP/SSE adapter at the incompatible bbernhard REST API"

### Endpoint Comparison

| Feature | Hermes expects | bbernhard provides | Match? |
|---------|----------------|-------------------|--------|
| Health check | `GET /api/v1/check` | `GET /v1/about` | ❌ |
| Inbound messages | `GET /api/v1/events` (SSE) | `GET /v1/receive/{number}` (WebSocket) | ❌ |
| Outbound send | `POST /api/v1/rpc` (JSON-RPC) | `POST /v2/send` (REST) | ❌ |
| Link device | N/A (uses signal-cli directly) | `GET /v1/qrcodelink` | Different flow |

### Correct Architecture

```
Phone (Signal app)
  ↓ (Signal protocol)
signal-cli daemon (ghcr.io/asamk/signal-cli)
  ↓ (JSON-RPC over TCP:7583)
signal-bridge (ghcr.io/gjcourt/signal-bridge)
  ↓ (SSE /api/v1/events + health /api/v1/check)
Hermes gateway (signal.py adapter)
```

### signal-bridge endpoints (what Hermes sees)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/events` | GET (SSE) | Inbound message stream | ✅ |
| `/api/v1/rpc` | POST (JSON-RPC) | Outbound send | ✅ |
| `/api/v1/check` | GET | Health probe | ✅ (alias for /v1/health) |

### Docker network setup

Containers must share a custom Docker network for hostname resolution:

```bash
docker network create signal-net
# Both containers must be on signal-net
```

If Hermes is also in Docker (Docker-in-Docker), it can reach signal-bridge via the bridge network IP. Check with:

```bash
docker inspect signal-bridge --format '{{range $net, $config := .NetworkSettings.Networks}}{{$net}}: {{$config.IPAddress}}{{"\n"}}{{end}}'
```

### Reusing bbernhard data with official signal-cli

The bbernhard container stores data at `/home/.local/share/signal-cli/`.
The official signal-cli image stores data at `/var/lib/signal-cli/`.

To migrate:
1. Stop the bbernhard container
2. Mount the same volume: `-v /srv/docker/signal-cli/config:/var/lib/signal-cli`
3. Run with `--user 1000:1000` (match the bbernhard UID/GID)
4. The official signal-cli will read the existing `data/accounts.json` and identity keys

### QR code linking

```bash
# GET (not POST!) to get QR PNG
curl -s "http://<signal-cli-ip>:8080/v1/qrcodelink?device_name=HermesAgent" -o /tmp/qr.png
```

QR codes expire after ~2-3 minutes. Regenerate if the user reports "invalid response".

### signal-bridge source

- Image: `ghcr.io/gjcourt/signal-bridge:latest`
- Source: https://github.com/gjcourt/homelab (images/signal-bridge/)
- The bridge is a Go service that translates signal-cli's JSON-RPC TCP protocol into the SSE + HTTP shape Hermes expects
- Supports bearer token auth via `HERMES_AUTH_TOKEN` env var
- Supports allowlist via `HERMES_ALLOWED_ACCOUNTS` env var

### Pangolin routing requirement

Signal-bridge must be reachable from the Hermes container. If using Docker-in-Docker, both must share a Docker network, or signal-bridge must be on a network Hermes can route to. The `SIGNAL_HTTP_URL` in `.env` must use the signal-bridge container's IP or hostname — NOT `127.0.0.1` (which points to the Hermes container itself, not the host).

If Pangolin is used to expose signal-bridge externally, the Pangolin route must forward to the signal-bridge container's port (default 8080). See the "Pangolin routing breaks" pitfall in the main SKILL.md for diagnosis steps.