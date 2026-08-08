# Pangolin API — Create Resource + Target

Reference for exposing a local service through Jefe's Pangolin infrastructure. The service runs on a machine connected via the Hermes VPN Newt tunnel (site 28), so the target is `127.0.0.1:<port>` from Pangolin's perspective.

## Prerequisites

- Device is connected to Tailnet via Headscale (see homelab-mesh-connect skill)
- Device has a Newt tunnel running (site "Hermes VPN", ID 28, niceId `angelic-amphisbaena-fuliginosa`)
- Pangolin API key in `~/.hermes/tmp_pangolin_key.txt`
- Service on device is listening on `0.0.0.0:<port>` (not just 127.0.0.1, since Newt tunnels from the machine itself)

## API Base

```
API base: https://api.jefe.ovh/v1
Auth: Bearer token from tmp_pangolin_key.txt
Org: jorganisation (name: JHetzner)
Domain ID for *.jefe.al: ykx3vzina5zahuf
```

## Step 1 — Create the Resource

```python
import urllib.request, json

api_key = open("/root/.hermes/tmp_pangolin_key.txt").read().strip().split("=", 1)[1]
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

body = {
    "subdomain": "myservice",          # subdomain only (not full domain)
    "name": "My Service",              # human-friendly name
    "domainId": "ykx3vzina5zahuf",     # jefe.al
    "protocol": "tcp",
    "http": True
}

req = urllib.request.Request(
    "https://api.jefe.ovh/v1/org/jorganisation/resource",
    data=json.dumps(body).encode(),
    headers=headers,
    method="PUT"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    resource_id = result["data"]["resourceId"]
```

- `ssl` is auto-enabled on creation.  
- `sso` is auto-enabled on creation.  
- The full domain becomes `<subdomain>.jefe.al`.

## Step 2 — Add a Target (routes traffic via Newt tunnel)

Create a target pointing to the service through the Hermes VPN Newt tunnel site (ID 28):

```python
target_body = {
    "siteId": 28,                    # Hermes VPN Newt tunnel
    "ip": "127.0.0.1",               # localhost on the device running Newt
    "port": 8787                     # your service port
}

req = urllib.request.Request(
    f"https://api.jefe.ovh/v1/resource/{resource_id}/target",
    data=json.dumps(target_body).encode(),
    headers=headers,
    method="PUT"
)
with urllib.request.urlopen(req) as resp:
    target_result = json.loads(resp.read().decode())
```

## Step 3 — Verify

```bash
# Check resource health
curl -s -H "Authorization: Bearer *** \
  "https://api.jefe.ovh/v1/resource/$RESOURCE_ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('health'), d.get('fullDomain'))"

# External access (once TLS propagates)
curl -s -o /dev/null -w "HTTP %{http_code}" https://myservice.jefe.al/health
```

## Step 4 — Delete a Resource (teardown)

When a public URL is no longer needed, delete the resource. This removes both the resource and its target automatically:

```python
req = urllib.request.Request(
    f"https://api.jefe.ovh/v1/resource/{resource_id}",
    data=None,
    headers=headers,
    method="DELETE"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    # {"success": true, "message": "Resource deleted successfully"}
```

No need to delete the target separately — Pangolin cascades the deletion. The WebUI service can keep running on its local port or Tailscale IP after the public URL is removed.

```bash
# Check resource health
curl -s -H "Authorization: Bearer $KEY" \
  "https://api.jefe.ovh/v1/resource/$RESOURCE_ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('health'), d.get('fullDomain'))"

# External access (once TLS propagates)
curl -s -o /dev/null -w "HTTP %{http_code}" https://myservice.jefe.al/health
```

## Important Notes

- The service must bind to **0.0.0.0** (not 127.0.0.1) since the Newt tunnel routes from the machine. Change via env var or config.
- Health may show "unknown" briefly after creation — this is normal while the health check initialises.
- For services on the Hetzner server or JNAS, use their respective site IDs instead of 28.
- The Pangolan API does NOT accept `ssl`, `siteId`, or `target` keys in the initial resource creation body — they are set via separate calls.

## Site IDs (Jefe's infrastructure)

| Site ID | Name | Type | Used for |
|---------|------|------|----------|
| 28 | Hermes VPN | Newt | This server (Hermes Agent host) |
| 6 | Hetzner | Newt | Hetzner server services |
| 18 | Jnas | Newt | JNAS services |
| 1 | homeassistant | Newt | Home Assistant services |

## Domains

| Base Domain | Domain ID | Type |
|-------------|-----------|------|
| jefe.al | ykx3vzina5zahuf | Wildcard |
| jefe.ovh | domain1 | Wildcard |
| losgalactique.fr | 51vbysoaydeg6cr | Wildcard |