# Radicale CalDAV — Serveur de calendrier local

## Quand utiliser

Quand l'utilisateur veut synchroniser un calendrier entre HA et son iPhone **sans passer par un fournisseur externe** (Google, Microsoft, iCloud). Radicale est un serveur CalDAV/CardDAV open-source, ultra-léger.

**Avantages vs n8n iCal bridge :**
- Synchronisation bidirectionnelle (l'iPhone peut ajouter des events aussi)
- iOS supporte CalDAV nativement (pas juste iCal subscription)
- Pas de limite de rafraîchissement (iCal subscription = polling)
- HA peut créer des events directement via l'intégration CalDAV

## Architecture

```
Hermes Agent → HA (CalDAV integration)
                                    ↓
                          Radicale (CalDAV server)
                          port 5232, htpasswd auth
                                    ↓
                    iPhone → Réglages → Calendrier → Comptes CalDAV
                                    ↓
                          Rappels iOS natifs synchronisés
```

## Docker Compose (production-grade, persistant)

```yaml
services:
  radicale:
    image: tomsquest/docker-radicale:latest
    container_name: radicale
    restart: unless-stopped
    ports:
      - "127.0.0.1:5232:5232"
    volumes:
      - radicale_data:/data
      - ./config:/config:ro
    init: true
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
      - KILL
    pids_limit: 50
    mem_limit: 256M
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:5232"]
      interval: 30s
      retries: 3
      start_period: 10s
    environment:
      - TZ=Europe/Paris
      - TAKE_FILE_OWNERSHIP=false

volumes:
  radicale_data:
```

### Fichier de config `/srv/docker/radicale/config/config`

```ini
[server]
hosts = 0.0.0.0:5232

[auth]
type = htpasswd
htpasswd_filename = /config/users.htpasswd
htpasswd_encryption = bcrypt

[storage]
filesystem_folder = /data/collections
```

### ⚠️ CRITIQUE : Persistance du htpasswd

**Le htpasswd DOIT être dans `/config/` (bind mount), JAMAIS dans `/data/` (volume Docker).**

- `/config/` est un bind mount (`./config:/config:ro`) → fichiers sur le host → **survivent aux updates** du container
- `/data/` est un volume Docker → peut être **wiped** à chaque recréation du container (update image, `docker compose up`, etc.)

Si `htpasswd_filename` pointe vers `/data/users.htpasswd`, le fichier peut disparaître à la prochaine update → Radicale exige un mot de passe mais aucun ne marche → "mot de passe incorrect" peu importe ce que l'utilisateur tape.

### ⚠️ CRITIQUE : `TAKE_FILE_OWNERSHIP=false`

L'entrypoint (`docker-entrypoint.sh`) contient `set -e` et essaie `chown -R radicale:radicale /data` quand `TAKE_FILE_OWNERSHIP=true` (default). Avec `cap_drop ALL` + `read_only: true`, le chown échoue → **crash en restart loop infini**.

**Solution** : toujours définir `TAKE_FILE_OWNERSHIP=false` dans le compose. Le volume `/data` doit être pré-chown en UID 2999 avant le premier démarrage :

```bash
docker run --rm -v radicale_data:/data alpine chown -R 2999:2999 /data
```

## Setup complet (from scratch)

```bash
# 1. Créer les dossiers sur le host
mkdir -p /srv/docker/radicale/config

# 2. Écrire compose.yaml et config/config (voir ci-dessus)

# 3. Créer le htpasswd (via temp container car /srv/docker pas accessible depuis Hermes)
docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c "
  apk add --no-cache apache2-utils
  htpasswd -cbB /config/users.htpasswd jefe MOT_DE_PASSE_ICI
"

# 4. Pré-chown le volume
docker run --rm -v radicale_data:/data alpine chown -R 2999:2999 /data

# 5. Démarrer
docker compose -f /srv/docker/radicale/compose.yaml up -d
```

### ⚠️ Écriture de fichiers sur `/srv/docker/` depuis le conteneur Hermes

Le conteneur Hermes n'a pas accès à `/srv/docker/` (en dehors de `HERMES_WRITE_SAFE_ROOT`). Pour écrire des fichiers sur le host dans `/srv/docker/`, utiliser un conteneur temporaire avec le bind mount :

```bash
docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c '
  cat > /config/config << "EOF"
  ... contenu ...
  EOF
'
```

`write_file` et `terminal` ne peuvent pas écrire dans `/srv/docker/` directement.

## Authentification

L'image tomsquest/docker-radicale utilise des **variables d'environnement** (`RADICALE_CONFIG_*`) pour la config SAUF quand `read_only: true` est activé — dans ce cas, il faut monter un fichier `config/` en volume.

L'auth htpasswd supporte bcrypt, argon2 (meilleure sécurité). L'utilisateur `jefe` voit tous les calendriers créés.

## Connexion HA → Radicale

### ⚠️ CRITIQUE : Mot de passe sans caractères spéciaux

Le config flow CalDAV de HA **rejette les mots de passe contenant `$`, `&`, `!`, `*`, `#`, `^`** même si curl les accepte. La lib `caldav` Python fonctionne avec ces caractères quand on l'appelle directement, mais le config flow HA les passe mal → `invalid_auth`.

**Utiliser un mot de passe alphanumérique avec tirets/underscores uniquement** : `Radicale-Jefe-2026-Xk9mNq` ✅ / `Dy%!@PLq...` ❌

### ⚠️ CRITIQUE : HA CalDAV ne crée des entités QUE pour les calendriers VEVENT

L'intégration CalDAV de HA ignore les calendriers VTODO (tâches). Il faut un calendrier **VEVENT** pour que `calendar.hermes` apparaisse.

**Créer un calendrier VEVENT via MKCALENDAR :**
```bash
curl -s -u "jefe:PASSWORD" -X MKCALENDAR -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
  <mkcalendar xmlns="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
    <set><prop>
      <displayname>Hermes</displayname>
      <C:supported-calendar-component-set><C:comp name="VEVENT"/></C:supported-calendar-component-set>
    </prop></set>
  </mkcalendar>' \
  http://127.0.0.1:5232/jefe/hermes/
```

Vérifier les calendriers existants :
```bash
curl -s -u "jefe:PASSWORD" -X PROPFIND -H "Depth: 1" -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?><propfind xmlns="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav"><prop><displayname/><resourcetype/><C:supported-calendar-component-set/></prop></propfind>' \
  http://127.0.0.1:5232/jefe/
```

### Méthode 1 : Via l'interface HA (manuel)

1. **Paramètres → Périphériques & Services → Ajouter une intégration → CalDAV**
2. URL : `http://127.0.0.1:5232` (si HA sur même host, network_mode: host)
3. Utilisateur : `jefe`
4. Mot de passe : alphanumérique uniquement (voir ci-dessus)
5. Décocher "Verify SSL" si HTTP (pas HTTPS)

### Méthode 2 : Via API REST HA (programmatique)

Quand le MCP HA est unavailable ou pour automatiser. Nécessite un JWT construit depuis le fichier auth de HA.

#### Construction du JWT (depuis le conteneur HA)

```python
# S'exécute DANS le conteneur HA : docker exec home-assistant python3 -c "..."
import json, time, hmac, hashlib, base64

with open("/config/.storage/auth", "r") as f:
    auth_data = json.load(f)
tokens = auth_data.get("data", {}).get("refresh_tokens", [])
for t in tokens:
    if t.get("client_name") == "Hermes Agent":  # ou autre LLT
        token_id = t.get("id")
        jwt_key = t.get("jwt_key")
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"iss": token_id, "iat": now, "exp": now + 3600}
        def b64(d):
            return base64.urlsafe_b64encode(d).rstrip(b"=")
        h = b64(json.dumps(header).encode())
        p = b64(json.dumps(payload).encode())
        msg = h + b"." + p
        sig = b64(hmac.new(jwt_key.encode(), msg, hashlib.sha256).digest())
        print((msg + b"." + sig).decode())
        break
```

#### Créer l'intégration CalDAV via REST API

```python
# 1. Init flow → POST /api/config/config_entries/flow
data = json.dumps({"handler": "caldav", "step_id": "user", "data": {
    "url": "http://127.0.0.1:5232",
    "username": "jefe",
    "password": "Radicale-Jefe-2026-Xk9mNq"
}}).encode()
req = urllib.request.Request("http://127.0.0.1:8123/api/config/config_entries/flow",
    data=data, headers={"Authorization": "Bearer " + jwt, "Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
flow_id = json.loads(resp.read())["flow_id"]

# 2. Submit form data → POST /api/config/config_entries/flow/{flow_id}
# ⚠️ Data PLATE (pas nested), contrairement à l'init
data2 = json.dumps({
    "url": "http://127.0.0.1:5232",
    "username": "jefe",
    "password": "Radicale-Jefe-2026-Xk9mNq",
    "verify_ssl": False
}).encode()
req2 = urllib.request.Request(f"http://127.0.0.1:8123/api/config/config_entries/flow/{flow_id}",
    data=data2, headers={"Authorization": "Bearer " + jwt, "Content-Type": "application/json"})
resp2 = urllib.request.urlopen(req2)
result = json.loads(resp2.read())
# result["type"] == "create_entry" = succès
```

#### Reload + créer un événement de test via WebSocket

```python
# Reload après création du calendrier VEVENT :
await ws.send_json({
    "id": 1, "type": "call_service",
    "domain": "homeassistant", "service": "reload_config_entry",
    "service_data": {"entry_id": "<entry_id>"}
})

# Créer un event :
await ws.send_json({
    "id": 2, "type": "call_service",
    "domain": "calendar", "service": "create_event",
    "service_data": {
        "entity_id": "calendar.hermes",
        "summary": "Test",
        "start_date_time": "2026-08-03T10:00:00",
        "end_date_time": "2026-08-03T11:00:00"
    }
})
```

Une fois connectée, l'intégration crée `calendar.hermes` (VEVENT) et potentiellement `todo.<name>` (VTODO). On peut créer des events via `calendar.create_event`.

## Connexion iPhone

1. **Réglages → Calendrier → Comptes → Ajouter → Autre → Ajouter un compte CalDAV**
2. Serveur : `ical.jefe.al` (via Pangolin)
3. Utilisateur : `jefe`
4. Mot de passe
5. ✅ Le calendrier apparaît dans l'app Calendrier iOS

## Usage avec Hermes

Une fois le CalDAV connecté :

```python
# Créer un event calendrier
ha_call_service(
    domain="calendar",
    service="create_event",
    entity_id="calendar.hermes",
    data={
        "summary": "Rendez-vous dentiste",
        "start_date_time": "2026-07-15 14:00:00",
        "end_date_time": "2026-07-15 15:00:00",
        "description": "Cabinet du Dr. Martin"
    }
)
```

L'iPhone synchronise automatiquement via CalDAV (push, pas de polling).

## Pièges

| Problème | Cause | Solution |
|----------|-------|----------|
| `additional properties 'radicale' not allowed` | `services:` manquant dans compose.yaml | Ajouter `services:` au début |
| `htpasswd: not found` | Image Alpine minimaliste | `apk add apache2-utils` dans le container |
| `cannot modify file, use -c` | Premier utilisateur | `htpasswd -c /config/users.htpasswd jefe` |
| Config vars ignorées | `read_only: true` incompatible avec env vars | Utiliser un fichier `config/` monté en volume |
| 500 sur create_event | Calendrier externe read-only | Vérifier que le calendrier CalDAV supporte CREATE_EVENT |
| `chown: /data: Permission denied` + restart loop | `TAKE_FILE_OWNERSHIP` defaults to true, `set -e` crash | `TAKE_FILE_OWNERSHIP=false` dans env |
| Mot de passe refusé après update container | htpasswd dans `/data/` (volume wiped) | Mettre htpasswd dans `/config/` (bind mount) |
| `docker cp` échoue avec `container rootfs is marked read-only` | Container en read-only mode | Écrire via `docker exec --user 2999:2999 -i` (stdin pipe) ou via temp container |
| Hermes ne peut pas écrire dans `/srv/docker/` | En dehors de `HERMES_WRITE_SAFE_ROOT` | Utiliser `docker run --rm -v <host_path>:<container_path> alpine sh -c '...'` |
| Volume `/data` vide après recréation | Volume Docker recréé sans les données | Le volume persiste nominalement, mais peut être wiped si le container est supprimé puis recréé. Le htpasswd doit être dans le bind mount `/config/` |
| HA config flow `invalid_auth` avec mot de passe complexe | Caractères `$&!*#^` dans le mot de passe passent mal dans le config flow HA (mais fonctionnent avec curl) | Utiliser un mot de passe alphanumérique avec tirets/underscores uniquement |
| `calendar.hermes` n'apparaît pas après intégration | Le calendrier Radicale est VTODO (tâches), HA ne crée des entités que pour VEVENT | Créer un calendrier VEVENT via `MKCALENDAR` (voir section ci-dessus) |
| MCP HA `ha_set_integration` retourne `cannot_connect` pour CalDAV | Le config flow via MCP peut échouer silencieusement même si la connexion fonctionne | Utiliser l'API REST HA directement (voir Méthode 2) ou l'interface HA |
| `docker exec home-assistant python3 << 'HEREDOC'` produit output vide | Heredoc bash mangled par docker exec | Écrire le script dans un fichier `/tmp/script.py`, le `docker cp` dans HA, puis `docker exec python3 /tmp/script.py` |
| HA REST API 401 avec le token de `.env` | Le `HASS_TOKEN` dans `.env` peut être tronqué/placeholder | Construire un JWT depuis `/config/.storage/auth` (voir section JWT) |

### Vérifier que Radicale fonctionne

```bash
# Test auth locale
curl -s -u "jefe:MOT_DE_PASSE" http://127.0.0.1:5232/.web/ | head -3

# Test CalDAV PROPFIND
curl -s -u "jefe:MOT_DE_PASSE" -X PROPFIND -H "Depth: 0" http://127.0.0.1:5232/jefe/ | head -5

# Test externe (via Pangolin)
curl -sI -u "jefe:MOT_DE_PASSE" https://ical.jefe.al/.web/ | head -3
# HTTP/2 200 = OK
```

## Setup complet de l'intégration HA (résumé programmatique)

Quand le MCP HA est unavailable ou pour automatiser complètement :

1. **Vérifier que HA atteint Radicale** : `docker exec home-assistant curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5232/.web/` → 200
2. **Créer un calendrier VEVENT** via `MKCALENDAR` (voir section ci-dessus)
3. **Construire un JWT** depuis `/config/.storage/auth` (voir section "Méthode 2 / Construction du JWT")
4. **Init flow** : `POST /api/config/config_entries/flow` avec `{"handler": "caldav", "step_id": "user", "data": {...}}`
5. **Submit flow** : `POST /api/config/config_entries/flow/{flow_id}` avec data PLATE (pas nested) : `{"url": "...", "username": "...", "password": "...", "verify_ssl": false}`
6. **Reload entry** via WebSocket : `call_service` `homeassistant.reload_config_entry` avec `{"entry_id": "..."}`
7. **Vérifier entités** : `GET /api/states` → filtrer `calendar.*`
8. **Créer un event de test** via WebSocket : `call_service` `calendar.create_event` avec `{"entity_id": "calendar.hermes", "summary": "Test", "start_date_time": "...", "end_date_time": "..."}`

⚠️ Le mot de passe dans l'étape 4-5 DOIT être alphanumérique avec tirets uniquement. Les caractères `$&!*#^` causent `invalid_auth` dans le config flow HA.