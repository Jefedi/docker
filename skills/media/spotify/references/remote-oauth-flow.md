# Remote Gateway OAuth Flow (Spotify)

When the user connects from a **Hermes Desktop app** (or any remote client) to a **remote gateway** (dashboard), the Spotify OAuth flow is non-trivial because:

- `hermes auth spotify` starts a local HTTP server on `127.0.0.1:43827` (server-side)
- The auth URL points to this localhost address
- The user's browser (on Windows) **cannot reach** the server's localhost

## The Flow

### 1. Start the auth process in a capturable background session

```bash
hermes auth spotify
```

Use **PTY background mode** so the auth URL appears in the process output:

```python
# Terminal: background=true, pty=true, timeout=300, notify_on_complete=true
```

### 2. Extract the auth URL

```python
process(action="log", session_id="...")
# Look for "Open this URL to authorize Hermes:" followed by the Spotify URL
```

### 3. Send the URL to the user

The user opens the URL in their browser, authorizes the app, then gets redirected to `http://127.0.0.1:43827/spotify/callback?code=...` — which fails in their browser (cannot reach server localhost).

### 4. Forward the callback locally

The user sends the callback URL (from their failed redirect) back in the chat. Extract the `code=` and `state=` parameters, then forward the callback **on the server** via curl:

```bash
curl -s "http://127.0.0.1:43827/spotify/callback?code=AQC...&state=abc..."
```

### 5. Confirm success

The server responds with HTML: `"Spotify authorization received. You can close this tab."`

The background process exits with code 0 and prints:
```
Spotify login successful!
  Auth state: /root/.hermes/auth.json
  Provider state saved under providers.spotify
```

## Pitfalls

- **Multiple process starts**: Each `hermes auth spotify` invocation generates a new `code_challenge` and `state` — the URL from a killed process is invalid. Always use the URL from the currently-running process.
- **Port 43827 already in use**: Kill all previous auth processes first (`process(action="kill")`).
- **State mismatch**: If the user opens an old URL (from a previous run), the state won't match and the callback fails. Always send the latest URL.
- **No process output**: Without `pty=true`, the URL may be suppressed. Always use PTY mode for `hermes auth spotify`.
- **Same flow applies to other OAuth providers**: Any `hermes auth <provider>` that uses a local redirect URI will have this same constraint on a remote gateway.
