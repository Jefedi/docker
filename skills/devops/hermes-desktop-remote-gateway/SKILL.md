---
name: hermes-desktop-remote-gateway
description: "Handling Remote Gateway failures when using Hermes Desktop: WebSocket /api/status, /api/ws, firewall, SSH tunnel workarounds, known bugs, checklist."
version: 1.0.0
---

# Hermes Desktop Remote Gateway Connection Issues

Remote mode in Hermes Desktop relies on two APIs that the regular gateway does not expose:

1. **`/api/status`** – health check, must return 200 JSON.
2. **`/api/ws`** – WebSocket endpoint for the embedded chat. This endpoint is gated behind the `--tui` flag (embedded chat enabled) and an origin check. The Electron renderer sends `Origin: null` (via `file://`) and on non‑loopback binds the server rejects it.

## Workarounds

* **Use the Dashboard** – start the server with `hermes dashboard --host 0.0.0.0 --port 9119 --no-open --insecure` and set `HERMES_DASHBOARD_TUI=1`. This enables both required endpoints.
* **SSH Tunnel** – forward a local port to the remote gateway and point the Desktop to `http://127.0.0.1:<local_port>`. Loopback satisfies the origin guard.
* **Web UI** – open `https://<gateway-host>/` in a browser instead of Desktop.

## Known Bugs

* Hermes Desktop remote mode hangs until `192.168.0.0`? Bug tracked in Hermes Agent Issues #520, #41566, upstream PR #37405. Fix for the WebSocket origin guard is in commit `37405`.
* The WebSocket endpoint returns 404 if `--tui` is not enabled.

## Checklist for Remote Configuration

1. Launch gateway with `hermes dashboard …` **or** ensure `hermes.gateway` is compiled with the websocket route.
2. If using Docker, expose the port and set `HERMES_DASHBOARD_TUI=1`.
3. On the Desktop, enable *Remote Gateway* and enter the hostname/port.
4. If still failing, try an SSH tunnel or Web UI.

---

## References

- `references/remote_gateway.md` – session‑specific detail.
