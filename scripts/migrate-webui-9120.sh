#!/bin/bash
set -euo pipefail

# Migration WebUI: port 8787 → 9120
# Lancé par Hermès après obtention de l'accès Docker

OLD_CONTAINER="hermes-webui"
IMAGE="ghcr.io/nesquena/hermes-webui:latest"
HERMES_HOME="${HOME}/.hermes"

echo "=== Migration WebUI vers port 9120 ==="

# 1. Stopper l'ancien conteneur WebUI (port 8787)
echo "[1/5] Stop ancien conteneur WebUI..."
docker stop "$OLD_CONTAINER" 2>/dev/null && docker rm "$OLD_CONTAINER" 2>/dev/null || echo "  (déjà stoppé)"

# 2. Stopper le vieux dashboard s6 si jamais il est revenu
echo "[2/5] Vérification: rien sur le port 9120..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9120/ 2>/dev/null | grep -q '^[2-3]'; then
  echo "  ATTENTION: quelque chose répond sur 9120 — abandon"
  exit 1
fi
echo "  OK, port libre"

# 3. Pull l'image WebUI
echo "[3/5] Pull image WebUI..."
docker pull "$IMAGE"

# 4. Lancer le nouveau conteneur WebUI sur 9120
echo "[4/5] Démarrage WebUI sur 0.0.0.0:9120..."
docker run -d \
  --name "$OLD_CONTAINER" \
  --restart unless-stopped \
  --network host \
  -v "${HERMES_HOME}:/home/hermeswebui/.hermes" \
  -e HERMES_WEBUI_HOST=0.0.0.0 \
  -e HERMES_WEBUI_PORT=9120 \
  -e HERMES_WEBUI_PASSWORD='UcRBZICrVU7ZQDW6+26lIINz' \
  -e HERMES_WEBUI_SKIP_ONBOARDING=1 \
  -e HERMES_WEBUI_STATE_DIR=/home/hermeswebui/.hermes/webui \
  "$IMAGE"

# 5. Vérifier
echo "[5/5] Vérification..."
sleep 3
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9120/ 2>/dev/null | grep -q '^[2-3]'; then
  echo "✅ WebUI démarré sur http://127.0.0.1:9120"
else
  echo "❌ WebUI ne répond pas — check: docker logs hermes-webui"
  exit 1
fi

echo "=== Migration terminée ==="