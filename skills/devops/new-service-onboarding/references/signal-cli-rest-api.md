# signal-cli-rest-api — Deployment Reference

Deployed on this VPS (Hermes VPN site 28, `127.0.0.1:8088`) with Pangolin at **signal.jefe.al**.

**Repository**: https://github.com/bbernhard/signal-cli-rest-api
**Image**: `bbernhard/signal-cli-rest-api:latest`
**Compose path**: `/root/docker/signal-cli-restapi/compose.yml`
**Config dir**: `./signal-cli-config/` (volume mount at `/home/.local/share/signal-cli`)

## Mode

`json-rpc-native` — fastest mode (native binary + single JVM daemon). Set via `MODE` env var.

| Mode | Notes |
|------|-------|
| `json-rpc-native` | ✅ Best perf. Native + daemon. |
| `json-rpc` | Single daemon, more memory |
| `native` | Precompiled GraalVM binary |
| `normal` (default) | JVM per request — slowest |

## Linking a Device (QR Code)

1. Open `http://127.0.0.1:8088/v1/qrcodelink?device_name=signal-api`
2. Scan QR with Signal mobile app → Settings → Linked devices → +
3. The registration is persisted in `./signal-cli-config/` (the `data/` subtree)

## Finding the Registered Phone Number

signal-cli stores registration data under `./signal-cli-config/data/`:

```bash
# The data directory structure:
data/
├── <numeric_account_id>     # JSON with "number", keys, identity
└── accounts.json            # Account index

# Read the number (may be partially redacted with asterisks)
grep '"number"' ./signal-cli-config/data/*/accounts 2>/dev/null || \
 cat ./signal-cli-config/data/<account_id> | python3 -c \
 "import sys,json; print(json.load(sys.stdin)['number'])"
```

**⚠️ Phone number redaction**: The stored number shows as `+337****5858` — the middle digits are literally asterisks in the JSON file. signal-cli (not the API) stores redacted numbers. The actual digits cannot be recovered from disk. You will need the user to confirm the full number before sending.

**API endpoints that expose the number**:
- `GET /v1/accounts` — returns `[]` in json-rpc-native mode (daemon + linked device; only returns registered accounts)
- `GET /v1/about` — no number, only version/mode info
- The number is needed as a `"number"` field in `POST /v2/send` requests

## API Endpoints

- `GET /v1/about` — server info, mode, version
- `GET /v1/qrcodelink?device_name=...` — QR code PNG for device linking
- `POST /v2/send` — send messages (requires `number` + `recipients` + `message`)
- `GET /v1/receive/{number}` — receive messages
- `GET /v1/accounts` — list accounts (empty for linked-device mode)
- Full Swagger: https://bbernhard.github.io/signal-cli-rest-api/

## Send a Test Message

```bash
curl -X POST -H "Content-Type: application/json" \
  'http://127.0.0.1:8088/v2/send' \
  -d '{"message": "Test !", "number": "+336XXXXXXXX", "recipients": ["+336XXXXXXXX"]}'
```

**Number field**: The `"number"` is the sender (your registered/linked number). `"recipients"` is an array of destination numbers.

## Pangolin Resource

- **Full domain**: `signal.jefe.al`
- **Resource ID**: 102
- **Site**: Hermes VPN (28) — NOT Hetzner (6)! This container runs on this VPS (Hermes VPN Newt client).
- **Target**: `127.0.0.1:8088` with `method: "http"` (required — see lesson below)
- **SSO**: disabled (this is an API, not a UI — no Pocket-ID auth)

## ⚠️ Site Correction Lesson (initial deploy)

**Symptom**: Pangolin showed "no available server" even though `curl 127.0.0.1:8088/v1/about` returned 200 locally.

**Two-part root cause**:
1. **Wrong site**: Target was created on siteId 6 (Hetzner), but the container runs on siteId 28 (Hermes VPN).
2. **Missing method**: Even after fixing the site, the target had `method: null` (TCP tunnel default) instead of `method: "http"` — the HTTP reverse proxy refused to route.

**How to identify the correct site**:
1. Read `/root/.config/newt-client/config.json` → get the `"id"` (e.g. `fjuyrsrb09ufxq3`)
2. Query Pangolin sites via `mcp_pangolin_org_by_orgId_sites` or `mcp_pangolin_site_by_siteId`
3. Find the site whose `newtId` matches — that's the correct siteId for targets on this machine

**Fix**: Delete the wrong target, recreate with `siteId: 28` AND `method: "http"`. The Newt client auto-syncs within seconds.

**Debugging technique that found the fix**: Compare the failing resource's target config against a known-working resource (e.g. Paperclip, Hermes Dashboard) on the same site. The difference (`method: null` vs `method: "http"`) was immediately visible.
