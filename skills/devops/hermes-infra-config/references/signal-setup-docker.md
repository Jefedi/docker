# Signal Messenger — Setup in Docker-in-Docker Hermes

Configuration de Signal comme plateforme de messagerie pour Hermes quand Hermes
tourne lui-même dans un conteneur Docker (Docker-in-Docker avec socket monté).

## Architecture

```
Hermes container (s6-overlay)          signal-api container
  gateway/platforms/signal.py  ──→     bbernhard/signal-cli-rest-api
  appelle /api/v1/check (health)       expose /v1/about, /v1/qrcodelink, etc.
  appelle /v1/receive/{number} (SSE)    mode: json-rpc-native
        │                                        │
        └─ HTTP via Docker bridge IP ────────────┘
           (PAS 127.0.0.1 — conteneurs séparés!)
```

Un **proxy shim** (`signal-proxy`) est nécessaire entre Hermes et signal-api
pour mapper l'endpoint de health check `/api/v1/check` → `/v1/about`.

## Déploiement

### 1. Conteneur signal-cli-rest-api

```bash
docker run -d --name signal-api --restart unless-stopped \
  -p 127.0.0.1:8089:8080 \
  -v /srv/docker/signal-cli/config:/home/.local/share/signal-cli \
  -e MODE=json-rpc-native \
  bbernhard/signal-cli-rest-api:latest
```

Vérifier que l'API démarre :
```bash
curl -s http://127.0.0.1:8089/v1/about
# {"versions":["v1","v2"],"build":2,"mode":"json-rpc","version":"0.100",...}
```

### 2. Linker le compte Signal (QR code)

⚠️ **Le endpoint `/v1/qrcodelink` est un GET, pas un POST.** La doc
officielle (bbernhard.github.io/signal-cli-rest-api) montre bien GET, mais
plusieurs guides tiers mentionnent POST à tort.

```bash
# GET — génère un PNG QR code
curl -s "http://127.0.0.1:8089/v1/qrcodelink?device_name=HermesAgent" -o /tmp/signal-qr.png
```

Le QR code expire au bout de ~2-3 minutes. Si l'utilisateur obtient
"Impossible d'associer le service — la réponse reçue n'est pas valide",
régénérer un QR frais.

Sur le téléphone : Signal → Paramètres → Appareils liés → Ajouter un appareil → scanner.

Vérifier le linkage :
```bash
curl -s http://127.0.0.1:8089/v1/accounts
# ["+337****5858"]  ← le numéro apparaît (masqué par redactor Hermes)
```

### 3. Configuration .env Hermes

```env
SIGNAL_HTTP_URL=http://10.0.0.X:8080   # IP du proxy shim (voir section 4)
SIGNAL_ACCOUNT=+337XXXXXXXXX            # Numéro E.164 — DOIT être écrit manuellement
SIGNAL_ALLOWED_USERS=+337XXXXXXXXX      # Même numéro
```

⚠️ **PITFALL CRITIQUE — Redactor masque les numéros de téléphone** :
Hermes masque les numéros de téléphone dans TOUT stdout (docker exec, curl,
python3, cat, grep, sed). Toute tentative programmatique de lire le numéro
depuis accounts.json et l'écrire dans .env échoue — le numéro masqué
`+337****5858` finit dans le fichier au lieu du vrai numéro.

**Solution** : l'utilisateur doit éditer `.env` manuellement et taper son
numéro au clavier. L'agent ne peut pas faire cette étape.

### 4. Proxy shim pour le health check

⚠️ **PITFALL — Health check 404** :
Le code Hermes (`gateway/platforms/signal.py`) appelle
`GET {http_url}/api/v1/check` pour son health check. Mais signal-cli-rest-api
n'expose PAS `/api/v1/check` — seulement `/v1/about`. Résultat : le health
check retourne 404, Signal échoue à se connecter, et Hermes retry en boucle.

```
gateway.platforms.signal: Signal adapter initialized: url=http://10.0.0.4:8080
gateway.run: Connecting to signal...
gateway.platforms.signal: Signal: health check failed (status 404)
gateway.run: ✗ signal failed to connect
```

**Le code Hermes est read-only** (`/opt/hermes/gateway/platforms/signal.py` est
monté en lecture seule dans le conteneur). On ne peut pas patcher le fichier.

**Solution** : déployer un proxy Python léger qui mappe `/api/v1/check` →
`/v1/about` et laisse tout le reste passer tel quel :

```bash
docker run -d --name signal-proxy --restart unless-stopped \
  --network bridge \
  -e TARGET=http://10.0.0.4:8080 \
  python:3.11-slim python3 -c "
import http.server, urllib.request, os
TARGET = os.environ['TARGET']
class Proxy(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        url = TARGET + self.path.replace('/api/v1/check', '/v1/about')
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            self.send_response(resp.status)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())
    def do_POST(self):
        url = TARGET + self.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(url, data=body, method='POST')
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            self.send_response(resp.status)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())
    def log_message(self, *a): pass
http.server.HTTPServer(('0.0.0.0', 8080), Proxy).serve_forever()
"
```

Puis `SIGNAL_HTTP_URL` pointe vers l'IP du proxy (ex: `http://10.0.0.5:8080`),
PAS vers signal-api directement.

## Pitfalls Docker-in-Docker

### 127.0.0.1 ne marche pas entre conteneurs

signal-api bind sur `127.0.0.1:8089` de l'hôte. Depuis le conteneur Hermes,
`127.0.0.1` pointe vers le conteneur lui-même, pas l'hôte. Et signal-api
n'est pas sur le même réseau Docker qu'Hermes.

**Solution** : utiliser l'IP du conteneur sur le bridge Docker :
```bash
docker inspect signal-api --format '{{range $net, $config := .NetworkSettings.Networks}}{{$config.IPAddress}}{{end}}'
# ex: 10.0.0.4
```

Puis `SIGNAL_HTTP_URL=http://10.0.0.4:8080` (port interne 8080, pas le port
mappé 8089).

### Ports déjà utilisés

Vérifier les ports avant de bind :
```bash
docker ps --filter "publish=8089" --format "{{.Names}} {{.Ports}}"
```

SearXNG ou un autre service peut occuper le port choisi. Avoir un plan B
(port 8090, etc.) ou ne pas binder sur localhost (juste utiliser l'IP du
bridge).

### Gateway restart impossible depuis l'agent

L'agent tourne dans le process gateway. `hermes gateway restart` depuis
l'agent tue la session elle-même :
```
Blocked: command cannot restart or stop the gateway from inside the gateway process.
```

**Solution** : l'utilisateur doit lancer `hermes gateway restart` ou
`docker restart <hermes-container>` depuis un terminal séparé.

## ⚠️ PROBLÈME NON RÉSOLU — Incompatibilité SSE vs WebSocket

⚠️ **signal-cli-rest-api est INCOMPATIBLE avec Hermes pour la réception de messages.**

Le health check peut passer (avec le proxy shim), les logs montrent
"Signal SSE: connected" en boucle, mais **Hermes ne reçoit JAMAIS les
messages entrants**. Voici pourquoi :

### La cause racine

| Composant | Endpoint attendu | Protocole | Endpoint réel signal-cli-rest-api |
|-----------|-----------------|-----------|-----------------------------------|
| Hermes health check | `/api/v1/check` | HTTP GET | n'existe pas → 404 |
| Hermes SSE listener | `/api/v1/events?account=...` | **SSE** (Server-Sent Events, streaming HTTP) | n'existe pas → 404 |
| signal-cli-rest-api receive | `/v1/receive/{number}` | **WebSocket** (upgrade) | existe mais protocole différent |

Le code Hermes (`signal.py` ligne ~428) fait :
```python
url = f"{self.http_url}/api/v1/events?account={quote(self.account, safe='')}"
async with self.client.stream("GET", url, headers={"Accept": "text/event-stream"}, timeout=None)
```

Mais signal-cli-rest-api n'expose pas `/api/v1/events` en SSE. Son endpoint
`/v1/receive/{number}` utilise **WebSocket** (négociation `Upgrade: websocket`),
pas SSE. Le proxy Python shim ne résout pas ce problème car :
1. Il ne connaît pas `/api/v1/events` (returns 404 from signal-api)
2. Même si on mappe `/api/v1/events` → `/v1/receive/{number}`, le protocole
   est incompatible (SSE vs WebSocket)

### Logs symptomatiques

```
Signal SSE: connected     ← répété toutes les 2 secondes (reconnexion en boucle)
Signal SSE: connected
Signal SSE: connected     ← jamais "message received"
```

L'envoi fonctionne (via `/v2/send` REST) mais la réception est impossible.

### Pistes de résolution (non testées)

1. **signal-cli daemon natif** (pas signal-cli-rest-api) — expose `/api/v1/events`
   en SSE natif via `signal-cli daemon --http`. C'est ce que Hermes attend.
   Nécessite Java 17+ installé sur l'hôte (pas dans un conteneur).

2. **Wrapper WebSocket→SSE** — un proxy qui se connecte en WebSocket à
   signal-cli-rest-api `/v1/receive/{number}` et re-expose les messages en
   SSE sur `/api/v1/events`. Plus complexe mais reste en Docker.

3. **Patcher signal-cli-rest-api** — forker et ajouter un endpoint SSE.
   Le projet est en Go (framework Gin).

4. **Vérifier les modes** — le mode `normal` (vs `json-rpc-native`) expose
   peut-être `/v1/receive` en polling REST simple au lieu de WebSocket.
   Non testé.

**Statut août 2026** : signal-cli-rest-api + proxy shim = health check OK,
envoi OK, mais **réception KO**. La solution passe probablement par
signal-cli daemon natif sur l'hôte.

## Vérification

```bash
# 1. Health check via proxy
curl -s -o /dev/null -w "%{http_code}" http://10.0.0.5:8080/api/v1/check
# 200

# 2. Logs gateway
grep -i "signal" /opt/data/logs/gateway.log | tail -10
# Chercher: "Signal adapter initialized" sans "health check failed"
# ⚠️ "Signal SSE: connected" en boucle = problème SSE (voir ci-dessus)

# 3. Test d'envoi (fonctionne)
ACCOUNT=$(grep "^SIGNAL_ACCOUNT=" /opt/data/.env | cut -d= -f2)
curl -s -X POST http://10.0.0.4:8080/v2/send \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Test\",\"number\":\"$ACCOUNT\",\"recipients\":[\"$ACCOUNT\"]}"

# 4. Test de réception (ne fonctionne pas avec signal-cli-rest-api)
# Envoyer un message depuis Signal → "Note to self"
# Hermes ne répondra pas — voir section "PROBLÈME NON RÉSOLU" ci-dessus
```

## Limitations connues de Signal

- Pas de TTS audio (Signal ne supporte pas les replies audio)
- Pas d'édition de messages (les tool progress bubbles sont supprimés)
- Limite pièces jointes : 100 MB
- Le mode `json-rpc-native` est recommandé (lance signal-cli en interne)
- **Réception de messages incompatible** avec signal-cli-rest-api (SSE vs WebSocket)