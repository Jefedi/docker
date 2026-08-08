# Signal Setup Architecture for Hermes Agent

## The core incompatibility

Hermes's Signal adapter (`gateway/platforms/signal.py`) expects:
- `GET /api/v1/check` → health probe (200 = healthy)
- `GET /api/v1/events?account=+NUMBER` → SSE stream for inbound messages
- `POST /api/v1/rpc` → JSON-RPC for outbound send

These are the endpoints of **signal-cli native HTTP daemon mode**, NOT bbernhard/signal-cli-rest-api.

## What bbernhard/signal-cli-rest-api exposes (INCOMPATIBLE)

- `GET /v1/about` → health info
- `GET /v1/health` → health check
- `GET /v1/receive/{number}` → WebSocket (NOT SSE) for inbound messages
- `POST /v2/send` → REST for outbound

Completely different protocol (WebSocket vs SSE) and different paths.

## Correct architecture: signal-cli + signal-bridge

### Components

1. **signal-cli** (`ghcr.io/asamk/signal-cli:latest`) — official signal-cli in JSON-RPC TCP daemon mode
2. **signal-bridge** (`ghcr.io/gjcourt/signal-bridge:latest`) — Go service that translates signal-cli TCP JSON-RPC into the SSE + JSON-RPC HTTP shape Hermes expects

### Docker setup

```bash
# Create dedicated network (Docker DNS requires custom networks)
docker network create signal-net

# signal-cli daemon (TCP JSON-RPC on port 7583)
docker run -d --name signal-cli --restart unless-stopped \
  --network signal-net \
  --user 1000:1000 \
  -v /srv/docker/signal-cli/config:/var/lib/signal-cli \
  ghcr.io/asamk/signal-cli:latest \
  daemon --tcp=0.0.0.0:7583 --receive-mode=on-connection --ignore-stories

# signal-bridge (HTTP SSE+JSON-RPC on port 8080)
docker run -d --name signal-bridge --restart unless-stopped \
  --network signal-net \
  -e SIGNAL_CLI_HOST=signal-cli \
  -e SIGNAL_CLI_PORT=7583 \
  -e LISTEN_ADDR=0.0.0.0 \
  -e LISTEN_PORT=8080 \
  ghcr.io/gjcourt/signal-bridge:latest
```

### Hermes .env configuration

```env
SIGNAL_HTTP_URL=http://<signal-bridge-IP>:8080
SIGNAL_ACCOUNT=+33612345678
SIGNAL_ALLOWED_USERS=+33612345678
```

**Important:** In Docker-in-Docker Hermes, `127.0.0.1` refers to the Hermes container itself, NOT the host. Use the signal-bridge container's IP on the shared Docker network, or a custom network name.

### Linking Signal account

The link QR code must be generated from the **signal-cli** container (not bbernhard):

```bash
# Generate QR code
docker exec signal-cli signal-cli link -n "HermesAgent"
```

This outputs a `sgnl://link?...` URI. Convert to QR and scan with Signal app → Settings → Linked Devices → Link New Device.

### Key pitfalls

1. **Docker DNS requires custom networks** — `docker run --network bridge` does NOT resolve container names. Create a dedicated network (`docker network create signal-net`) and put both containers on it.

2. **UID/GID for signal-cli data** — bbernhard uses UID 1000, official signal-cli image also expects 1000. Use `--user 1000:1000` to avoid permission issues with existing data.

3. **Data directory differs** — bbernhard mounts to `/home/.local/share/signal-cli`, official image expects `/var/lib/signal-cli`. If migrating, the data subfolder structure is the same but the mount path differs.

4. **Secret redactor blocks phone numbers** — Hermes secret redactor masks E.164 numbers in ALL agent outputs (terminal, docker exec, read_file, execute_code). The agent CANNOT programmatically extract a phone number from signal-cli and write it to `.env`. The user must do this manually in their terminal.

5. **Gateway restart from inside** — `hermes gateway restart` is blocked from inside the gateway process. The user must run it from a separate terminal, or restart the Docker container.

6. **`signal-cli link` command** — in the official Docker image, the command is `signal-cli link -n "name"` (not `signal-cli -u NUMBER link`). The daemon runs in multi-account mode and auto-detects the linked account.

### Verification

```bash
# Health check through bridge
curl -s http://<bridge-ip>:8080/api/v1/check
# Should return 200

# SSE stream (should connect and stay open)
curl -s -N -H "Accept: text/event-stream" \
  "http://<bridge-ip>:8080/api/v1/events?account=+YOUR_NUMBER"

# Check Hermes gateway logs
grep -i "signal" /opt/data/logs/gateway.log | tail -10
# Look for: "Signal SSE: connected" (success) or "health check failed" (problem)
```

### Sending a test message via signal-cli directly

```bash
# Send via signal-cli JSON-RPC (bypasses Hermes)
ACCOUNT="+33612345678"
curl -s -X POST http://<signal-cli-ip>:7583 \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"send\",\"params\":{\"account\":\"$ACCOUNT\",\"message\":\"Test\"},\"id\":1}'
```

Or via signal-cli container:
```bash
docker exec signal-cli signal-cli -u $ACCOUNT send -m "Test" $ACCOUNT
```