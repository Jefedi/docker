# Pangolin Private (Site) Resources

Private resources in Pangolin have a public domain but require the Newt client to access. Without the client, the URL returns a "Private Placeholder Screen" page.

> **Key insight**: Private resources are NOT standard resources with a flag. They are a completely different data model — **site resources** — stored under `org/{org}/site/{siteId}/resources`.

## API Endpoints

| What | Endpoint | Method |
|------|----------|--------|
| List private resources on a site | `org/{org}/site/{siteId}/resources` | GET |
| Create/update a site resource | `org/{org}/site/{siteId}/resource` | PUT (⚠️ BROKEN) |
| List public resources (paginated) | `org/{org}/resources?limit=20&page=N` | GET |
| Resource detail | `resource/{id}` | GET |

> The PUT endpoint for creating site resources returns "Validation error: Unrecognized key: siteId" regardless of body. Creation requires the Pangolin UI.

## Site Resource Data Structure

Each site resource is nested three levels deep in the response:

```
siteResources[]
├── siteNetworks  { siteId, networkId }
├── networks      { networkId, niceId, name, scope, orgId }
└── siteResources {
      siteResourceId, orgId, networkId,
      name, ssl, mode, scheme,
      proxyPort, destinationPort, destination,
      enabled, alias, aliasAddress,
      tcpPortRangeString, udpPortRangeString,
      disableIcmp, authDaemonPort, authDaemonMode,
      domainId, subdomain, fullDomain
    }
```

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `mode` | Protocol mode: `http` or `tcp` | `http` |
| `destination` | Internal IP (localhost = 127.0.0.1 on the site host) | `127.0.0.1` |
| `destinationPort` | Internal port | `6767` |
| `aliasAddress` | Auto-assigned mesh IP (100.96.128.x range) | `100.96.128.12` |
| `fullDomain` | Public URL | `bazarr.jefe.ovh` |
| `domainId` | Domain config ID | `domain1` (jefe.ovh) |
| `subdomain` | Subdomain part | `bazarr` |
| `tcpPortRangeString` | Proxy TCP ports (usually `443,80`) | `443,80` |
| `authDaemonPort` | Auth daemon port for the site | `22123` |
| `authDaemonMode` | Auth mode (`site`) | `site` |

## Listing Private Resources

### Get all resources from a site:

```python
import urllib.request, json

# Use Authorization: Bearer (NOT X-API-Key)
api_key = "your-key-here"
headers = {"Authorization": f"Bearer {api_key}"}

req = urllib.request.Request(
    "https://api.jefe.ovh/v1/org/jorganisation/site/6/resources",
    headers=headers
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

for sr in data["data"]["siteResources"]:
    r = sr["siteResources"]
    print(f"  {r['name']:25s} -> {r['fullDomain']:30s} -> {r['destination']}:{r['destinationPort']}")
```

### Known Private Resources (Site 6 - Hetzner)

| Nom | Domaine | Destination | Port | Mode |
|-----|---------|-------------|------|------|
| bazarr | `bazarr.jefe.ovh` | 127.0.0.1 | 6767 | http |
| dockhand | `dockhand.jefe.ovh` | 127.0.0.1 | 3000 | http |
| lidarr | `lidarr.jefe.ovh` | 127.0.0.1 | 8686 | http |
| prowlarr | `prowlar.jefe.ovh` | 127.0.0.1 | 9696 | http |
| qbit | `qbit.jefe.ovh` | 127.0.0.1 | 8090 | http |
| radarr | `radarr.jefe.ovh` | 127.0.0.1 | 7878 | http |
| searchxng | `search.jefe.al` | 127.0.0.1 | 8088 | http |
| sonarr | `sonarr.jefe.ovh` | 127.0.0.1 | 8989 | http |

## Known Private Resources (Site 18 - Jnas)

| Nom | Domaine | Destination | Port | Mode | Alias |
|-----|---------|-------------|------|------|-------|
| NAS SMB | (aucun — alias only) | 192.168.1.92 | 445 | host | `nas.jefe.internal` → `100.96.128.17` |
| nas interface | `nas-interface.jefe.al` | localhost | 9443 | http | — |
| NAS WebDAV | `webdav.jefe.al` | 127.0.0.1 | 4234 | http | `100.96.128.20` |
| MeTube | `metube.jefe.al` | 127.0.0.1 | 8081 | http | `100.96.128.21` |

> **NAS WebDAV**: HTTPS backend (scheme=https, ssl=true) sur le NAS. Port 4234. Créée pour Remotely Save Obsidian sync.

### SMB via Private Resource (mode: host)

SMB (port 445, TCP) is NOT HTTP. When creating a private resource for SMB:
1. In the UI, select **mode: Hôte** (not CIDR, not HTTP)
2. Destination: IP of the NAS (e.g. `192.168.1.92`)
3. Alias: optional friendly name (e.g. `nas.jefe.internal`) — resolves to a mesh IP like `100.96.128.x` via the Newt client DNS
4. TCP port restriction: **445** (Personne = restrict to this port only)
5. No domain/subdomain needed for pure TCP access — the alias is sufficient
6. SMB connections use the alias: `smb://nas.jefe.internal/partage` or `\\nas.jefe.internal\partage`

**Important**: The Newt client must be installed and connected on the device trying to access the resource. Without it, neither the alias nor the domain resolves.

## Public vs Private — Complete Breakdown

### 🌐 Public Resources (standard `org/{org}/resources` endpoint)
- Have a `fullDomain` assigned
- Proxy enabled: accessible via any browser (with Pangolin auth)
- 36 total (paginated 20/page)
- Examples: `home.jefe.al`, `jflix.jefe.al`, `paperclip.jefe.al`

### 🔒 Mesh-Private Resources (also in `org/{org}/resources`)
- `fullDomain: null` — no public URL
- Only accessible via Newt VPN mesh (like Tailscale)
- Non-web protocols (SSH, databases, relays)
- Examples: Piper (TTS), RustDesk*, SFTP, MySQL

### 🔏 Auth-Gated Private Resources (site resources — `org/{org}/site/{siteId}/resources`)
- **Have a `fullDomain`** but proxy access is blocked without Newt client
- Accessing URL without Newt → "Private Placeholder Screen" page
- Served by Pangolin's built-in Next.js UI (version 1.18.4)
- NOT visible in the standard `org/{org}/resources` endpoint
- Only reachable via `org/{org}/site/{siteId}/resources`

## Jefe's Preferred Output Format

When Jefe asks to list or create private resources, respond with this format:

```
🔒 **<name>** → `<domaine>` → `<IP>:<port>`
```

For multiple resources, use a table-like list:

```
🔒 **bazarr** → `bazarr.jefe.ovh` → `127.0.0.1:6767`
🔒 **radarr** → `radarr.jefe.ovh` → `127.0.0.1:7878`
```

## Site IDs for Jefe's Infrastructure

| ID | Name | Type | Notes |
|----|------|------|-------|
| 28 | Hermes VPN | Newt | This server, 100.64.0.9, 3 site resources |
| 6 | Hetzner | Newt | Hetzner server, 39 resources, 8 private (site) resources |
| 18 | Jnas | Newt | NAS, 4 site resources (NAS SMB, nas interface, NAS WebDAV, MeTube) |
| 1 | homeassistant | Newt | HA, 2 resources |

## Auth Notes

- **`Authorization: Bearer <key>`** — works (tested and confirmed)
- **`X-API-Key: <key>`** — returns 401 `"API key required"` (old format, no longer works)
- **Pagination**: `org/{org}/resources` returns 20 per page (`total: 36`). Use `?limit=20&page=2` for next page.
