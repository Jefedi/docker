# Remote API Server Setup Instructions

The file contains the exact steps used in the session to expose the Hermès API server on port **9119** (the port used by Pangolin).  It serves purely as a quick‑reference and can be‑copied in future
operations.

1. Edit the profile `.env` and add:
   ```bash
   API_SERVER_ENABLED=true
   API_SERVER_HOST=0.0.0.0
   API_SERVER_PORT=9119
   API_SERVER_KEY=hermes-ios-shortcut-a80ac18a29ed5d62
   ```
2. Restart the Hermès gateway.
3. Verify with:
   ```bash
   curl -H "Authorization: Bearer hermes-ios-shortcut-a80ac18a29ed5d62" https://hermes.jefe.al/v1/models
   ```

The API is now reachable via `https://hermes.jefe.al/v1/`.
