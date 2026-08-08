# Radicale Troubleshooting — Diagnostic complet

## Symptôme : « Radicale refuse le mot de passe sur iPhone »

L'utilisateur tape son mot de passe CalDAV sur l'iPhone (Réglages → Calendrier → Comptes → CalDAV), mais l'auth échoue. Le compte avait déjà fonctionné auparavant.

## Diagnostic — ordre de vérification

### 1. Container en route ?
```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep radicale
```
Si `Restarting` → probablement `TAKE_FILE_OWNERSHIP` non désactivé. Vérifier : `docker logs radicale --tail 30` → si `chown: /data: Permission denied` en boucle, c'est ça.

### 2. Volume /data vide ? (CAUSE LA PLUS PROBABLE)
```bash
docker exec radicale ls -la /data/
```
Si vide (pas de `users.htpasswd`, pas de `collections/`) → le volume a été wiped lors d'un recréation du container (update image, `docker compose up` après modif config, etc.).

**Le container peut être `healthy` avec un volume vide** — le healthcheck curl `localhost:5232` répond 302 même sans auth configurée.

### 3. htpasswd existe dans /config/ ?
```bash
docker exec radicale cat /config/users.htpasswd
```
Si le fichier n'existe pas → le htpasswd n'a jamais été créé dans le bind mount, ou le bind mount est vide.

### 4. Config pointe vers /config/ ou /data/ ?
```bash
docker exec radicale cat /config/config
```
Vérifier : `htpasswd_filename = /config/users.htpasswd` (PAS `/data/users.htpasswd`).

Si `htpasswd_filename = /data/users.htpasswd` → **ancienne config**, le htpasswd est dans le volume et peut disparaître. Corriger le config pour pointer vers `/config/`.

### 5. DNS / Pangolin routing
```bash
curl -sI https://ical.jefe.al 2>&1 | head -5
# Doit retourner 302 redirect vers /.web
```
Si 404 → le domaine n'est pas configuré dans Pangolin. Si connexion refusée → Newt client down.

### 6. Config file présent ?
```bash
docker exec radicale cat /config/config
# Vérifier : [auth] type = htpasswd, htpasswd_filename = /config/users.htpasswd
```
Si le bind mount `/srv/docker/radicale/config` est vide sur le host → la config a été perdue.

## Fix : Recréer le htpasswd dans /config/ (bind mount persistant)

```bash
# Via temp container (Hermes ne peut pas écrire dans /srv/docker/ directement)
docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c "
  apk add --no-cache apache2-utils
  htpasswd -cbB /config/users.htpasswd jefe NOUVEAU_MOT_DE_PASSE
"
docker restart radicale
```

⚠️ Le mot de passe original a été tapé interactivement (`htpasswd -c`) et n'est **jamais stocké en clair** — seule le hash bcrypt est dans le fichier. Si le volume est wiped, le mot de passe est irrécupérable. Il faut en créer un nouveau.

## Fix : TAKE_FILE_OWNERSHIP crash en restart loop

Si les logs montrent `chown: /data: Permission denied` en boucle et le container `Restarting` :

1. Ajouter `TAKE_FILE_OWNERSHIP=false` dans `environment:` du compose
2. Pré-chown le volume : `docker run --rm -v radicale_data:/data alpine chown -R 2999:2999 /data`
3. Recréer le container

## Fix : Recréer le dossier config sur le host

Si `/srv/docker/radicale/` est vide (plus de compose, plus de config) :

```bash
# Via temp container (Hermes ne peut pas écrire dans /srv/docker/ directement)
docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c '
cat > /config/config << "EOF"
[server]
hosts = 0.0.0.0:5232

[auth]
type = htpasswd
htpasswd_filename = /config/users.htpasswd
htpasswd_encryption = bcrypt

[storage]
filesystem_folder = /data/collections
EOF
'
```

Et recréer le compose.yaml :

```bash
docker run --rm -v /srv/docker/radicale:/work alpine sh -c '
cat > /work/compose.yaml << "ENDOFFILE"
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
ENDOFFILE
'
```

## Vérification post-fix

```bash
# Tester l'auth depuis le serveur
curl -s -u "jefe:NOUVEAU_MOT_DE_PASSE" https://ical.jefe.al/.web/ | head -5
# Doit retourner le HTML du web UI (pas "Access forbidden")

# Test CalDAV PROPFIND
curl -s -u "jefe:NOUVEAU_MOT_DE_PASSE" -X PROPFIND -H "Depth: 0" http://127.0.0.1:5232/jefe/ | head -5
# Doit retourner XML multistatus

# Vérifier les logs Radicale pour requêtes auth
docker logs radicale --tail 10 2>&1
# Doit voir les requêtes avec 200 OK (pas 401 Unauthorized)
```

## Pièges spécifiques à l'intégration HA CalDAV

1. **Mot de passe avec caractères spéciaux → `invalid_auth`** : Le config flow HA rejette les mots de passe contenant `$`, `&`, `!`, `*`, `#`, `^`. La lib `caldav` Python les accepte quand on l'appelle directement (`docker exec home-assistant python3 -c "import caldav; ..."`), mais le config flow les passe mal. **Utiliser alphanumérique + tirets uniquement**.

2. **HA CalDAV ne crée des entités QUE pour VEVENT** : Si le seul calendrier Radicale est VTODO (tâches), `calendar.*` n'apparaîtra jamais. Créer un calendrier VEVENT via `MKCALENDAR` :
   ```bash
   curl -s -u "jefe:PASS" -X MKCALENDAR -H "Content-Type: application/xml" \
     -d '<mkcalendar xmlns="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav"><set><prop><displayname>Hermes</displayname><C:supported-calendar-component-set><C:comp name="VEVENT"/></C:supported-calendar-component-set></prop></set></mkcalendar>' \
     http://127.0.0.1:5232/jefe/hermes/
   ```

3. **MCP HA `ha_set_integration` peut échouer avec `cannot_connect`** même si la connexion fonctionne. Solution : utiliser l'API REST HA directement (POST `/api/config/config_entries/flow` puis `/api/config/config_entries/flow/{flow_id}`). Nécessite un JWT construit depuis `/config/.storage/auth` (voir `references/radicale-caldav-setup.md` section "Méthode 2").

4. **Heredoc bash mangled par `docker exec`** : `docker exec home-assistant python3 << 'EOF'` peut produire un output vide sans erreur. Solution : écrire le script dans un fichier local, `docker cp` dans HA, puis `docker exec python3 /tmp/script.py`.

5. **HA REST API 401 avec `HASS_TOKEN` de `.env`** : Le token dans `.env` peut être tronqué ou placeholder. Construire un JWT valide depuis `/config/.storage/auth` en lisant le `token_id` et `jwt_key` du refresh token `long_lived_access_token`.

6. **Reload config entry via WebSocket** : Après création du calendrier VEVENT, reload l'intégration via WebSocket `call_service` `homeassistant.reload_config_entry` avec `service_data: {entry_id: "..."}`.

## Pièges spécifiques à tomsquest/docker-radicale

1. **read_only: true** → les env vars `RADICALE_CONFIG_*` ne marchent PAS. Utiliser un fichier config monté en `:ro`.
2. **TAKE_FILE_OWNERSHIP** : défaut `true`, lance `chown -R /data` qui échoue avec `cap_drop ALL` + `read_only`. L'entrypoint a `set -e` → **crash en restart loop**. Toujours mettre `TAKE_FILE_OWNERSHIP=false`.
3. **UID 2999** → `docker cp` ne marche pas (rootfs read-only). Utiliser `docker exec --user 2999:2999 -i` avec pipe stdin, ou un temp container.
4. **Volume vs bind mount** : le `compose.yaml` utilise `radicale_data:/data` (volume Docker) pour les collections, et `./config:/config:ro` (bind mount) pour la config + htpasswd. Le bind mount survit aux updates ; le volume peut être wiped.
5. **htpasswd dans /data/ vs /config/** : TOUJOURS mettre `htpasswd_filename = /config/users.htpasswd` (bind mount persistant). Si dans `/data/` (volume), le htpasswd disparaît à la prochaine update → "mot de passe incorrect" sur l'iPhone.
6. **Container recréé ≠ volume recréé** : `docker inspect radicale --format '{{.Created}}'` vs `docker volume inspect radicale_radicale_data --format '{{.CreatedAt}}'`. Si le container est plus récent que le volume, le volume a survécu mais peut être vide.
7. **htpasswd -c** : le flag `-c` CRÉE (écrase) le fichier. Sans `-c`, `htpasswd` refuse de créer un fichier inexistant. Toujours utiliser `-c` pour un nouveau fichier.
8. **Hermes ne peut pas écrire dans `/srv/docker/`** : utiliser `docker run --rm -v /srv/docker/radicale:/work alpine sh -c '...'` pour écrire des fichiers sur le host.