#!/usr/bin/env bash
# Camofox integration + Hermes config deployment — run on AX42 host
# Idempotent, backs up with .bak-<timestamp> before editing.
set -euo pipefail

COMPOSE=/opt/hermes/docker-compose.yml
CAMOFOX_DIR=/srv/docker/hermes/camofox
TS=$(date +%Y%m%dT%H%M%SZ)

echo "=== 1. Backup compose ==="
cp -p "$COMPOSE" "$COMPOSE.bak-$TS"
echo "  -> $COMPOSE.bak-$TS"

echo "=== 2. Create camofox data dir ==="
mkdir -p "$CAMOFOX_DIR"
chown -R 10000:10000 "$CAMOFOX_DIR" 2>/dev/null || true
echo "  -> $CAMOFOX_DIR"

echo "=== 3. Patch docker-compose.yml (add camofox service, add depends_on to gateway) ==="

# Use python3 for safe YAML edit (same approach as inside the container)
python3 << 'PYEOF'
import yaml, re, sys
from pathlib import Path

path = Path('/opt/hermes/docker-compose.yml')
txt = path.read_text()

# Load YAML
cfg = yaml.safe_load(txt)
services = cfg.setdefault('services', {})

# Add camofox service if absent
if 'camofox' in services:
    print("  camofox service already present — overwriting")
else:
    print("  adding camofox service")
services['camofox'] = {
    'image': 'ghcr.io/jo-inc/camofox-browser:latest',
    'container_name': 'camofox-browser',
    'restart': 'unless-stopped',
    'ports': ['127.0.0.1:9377:9377'],
    'environment': [{'CAMOFOX_PORT': '9377'}],
    'volumes': ['/srv/docker/hermes/camofox:/home/node/.camofox'],
    'logging': {
        'driver': 'json-file',
        'options': {'max-size': '50m', 'max-file': '3'},
    },
}

# Add depends_on to gateway (the hermes service is named "gateway" in this compose)
gw = services.get('gateway', {})
depends = gw.get('depends_on')
if isinstance(depends, list):
    if 'camofox' not in depends:
        depends.append('camofox')
    gw['depends_on'] = depends
elif isinstance(depends, dict):
    if 'camofox' not in depends:
        depends['camofox'] = {'condition': 'service_started'}
else:
    gw['depends_on'] = ['camofox']
services['gateway'] = gw

# Write back (preserve comments is hard with PyYAML — but the original has very few
# comments, all at the top as a header. We re-dump and prepend the header.)
header_match = re.search(r'^#\n# docker-compose\.yml for Hermes Agent.*?#\n', txt, re.DOTALL)
header = header_match.group(0) if header_match else ''
body = yaml.dump(cfg, sort_keys=False, default_flow_style=False, allow_unicode=True, width=10000)
path.write_text(header + body)
print("  compose updated")
print("  gateway.depends_on:", services['gateway'].get('depends_on'))
PYEOF

echo "=== 4. docker compose up -d ==="
cd /opt/hermes
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d

echo "=== 5. Restart hermes container fully (reload config.yaml) ==="
docker restart hermes

echo "=== 6. Wait for boot (camofox + hermes) ==="
echo "  waiting up to 60s for camofox health..."
for i in $(seq 1 30); do
    if curl -sf --max-time 2 http://127.0.0.1:9377/health >/dev/null 2>&1; then
        echo "  camofox healthy after ${i}x2s"
        break
    fi
    # try /  as fallback
    if curl -sf --max-time 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:9377/ 2>/dev/null | grep -qE '200|404|302'; then
        echo "  camofox responding (non-/health) after ${i}x2s"
        break
    fi
    sleep 2
done

echo "  waiting up to 60s for hermes gateway..."
for i in $(seq 1 30); do
    if docker logs --tail 5 hermes 2>&1 | grep -qiE "gateway (started|ready|listening)"; then
        echo "  hermes gateway ready after ${i}x2s"
        break
    fi
    sleep 2
done

echo ""
echo "=== 7. Validations ==="
echo "--- a) Camofox health ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 http://127.0.0.1:9377/health \
  || curl -s -o /dev/null -w "HTTP %{http_code} (root)\n" --max-time 5 http://127.0.0.1:9377/

echo "--- b) glm-5.2 responds ---"
docker exec hermes hermes chat -q "réponds uniquement OK" 2>&1 | tail -20

echo "--- c) Browser tool via Camofox ---"
docker exec hermes hermes chat -q "navigue sur https://trakii.tv et décris la page en 2 phrases" 2>&1 | tail -30

echo "--- d) No 'Unknown toolsets' or 'mistral' in startup logs ---"
docker logs hermes 2>&1 | grep -iE "unknown toolset|mistral|fallback" | head -10 || echo "  (none found — OK)"

echo ""
echo "=== DONE ==="
echo "Reminder: add /srv/docker/hermes/camofox to Borgmatic backup scope."