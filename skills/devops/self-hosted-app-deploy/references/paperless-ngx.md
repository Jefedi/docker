# Paperless-ngx

Document management avec OCR (Tesseract), consommation automatique depuis dossier, MariaDB backend, Tika+Gotenberg pour Office docs.

## Stack

- **broker**: Redis (ou Valkey pour licence open-source) — Celery broker pour tasks OCR
- **db**: MariaDB 12
- **tika**: Apache Tika — parsing Office documents
- **gotenberg**: Conversion HTML→PDF pour .eml etc.
- **paperless**: paperlessngx/paperless-ngx:3.x

## Compose de référence

Basé sur `docker-compose.mariadb-tika.yml` officiel, adapté pour l'homelab :

```yaml
name: paperless

services:
  broker:
    image: redis:8.2.1  # ou valkey/valkey:9-alpine (fork open-source)
    command: redis-server --save 3600 1 --appendonly yes
    volumes:
      - ./redis:/data
    restart: unless-stopped

  db:
    image: mariadb:12.0.2
    environment:
      MARIADB_ROOT_PASSWORD: ${PAPERLESS_DB_PASS}
      MARIADB_DATABASE: paperless
      MARIADB_USER: paperless
      MARIADB_PASSWORD: ${PAPERLESS_DB_PASS}
    volumes:
      - ./db:/var/lib/mysql
    restart: unless-stopped

  tika:
    image: apache/tika:2.9.1.0
    restart: unless-stopped

  gotenberg:
    image: gotenberg/gotenberg:7.10
    command:
      - gotenberg
      - --chromium-disable-javascript=true
      - --chromium-allow-list=file:///tmp/.*
    restart: unless-stopped

  paperless:
    image: paperlessngx/paperless-ngx:3.0.5
    container_name: paperless
    ports:
      - "127.0.0.1:8005:8000"
    environment:
      PAPERLESS_REDIS: redis://broker:6379
      PAPERLESS_DBENGINE: mariadb
      PAPERLESS_DBHOST: db
      PAPERLESS_DBPORT: "3306"
      PAPERLESS_DBUSER: paperless
      PAPERLESS_DBPASS: ${PAPERLESS_DB_PASS}
      PAPERLESS_ADMIN_USER: ${PAPERLESS_ADMIN_USER}
      PAPERLESS_ADMIN_PASSWORD: ${PAPERLESS_ADMIN_PASS}
      PAPERLESS_TIKA_ENABLED: "1"
      PAPERLESS_TIKA_ENDPOINT: http://tika:9998
      PAPERLESS_TIKA_GOTENBERG_ENDPOINT: http://gotenberg:3000
      PAPERLESS_URL: https://paperless.jefe.al
      PAPERLESS_CSRF_TRUSTED_ORIGINS: https://paperless.jefe.al
      PAPERLESS_TIME_ZONE: Europe/Paris
      PAPERLESS_OCR_LANGUAGE: fra+eng
      USERMAP_UID: "1000"
      USERMAP_GID: "1000"
      PAPERLESS_CONSUMER_RECURSIVE: "true"
      PAPERLESS_CONSUMER_POLLING_INTERVAL: "30"
      PAPERLESS_CONSUMER_DUPLICATE_HANDLING: skip
    volumes:
      - ./data:/usr/src/paperless/data
      - /mnt/paperless-nfs/media:/usr/src/paperless/media
      - /mnt/paperless-nfs/export:/usr/src/paperless/export
      - /mnt/paperless-nfs/Paperless:/usr/src/paperless/consume
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    depends_on:
      - db
      - broker
```

## NFS → polling obligatoire

Le dossier `consume` est sur NFS (`/mnt/paperless-nfs/Paperless`). inotify **ne fonctionne pas sur NFS** — Paperless ne détectera pas les nouveaux fichiers.

**Solution** : `PAPERLESS_CONSUMER_POLLING_INTERVAL: "30"` (polling toutes les 30s).

**NE PAS utiliser** `PAPERLESS_CONSUMER_INOTIFY_DELAY` — cette variable n'existe pas dans la doc Paperless. Elle est silencieusement ignorée.

## Redis log spam (save 300 100)

Par défaut Redis sauvegarde le RDB si ≥100 changements en 300s. Paperless génère facilement 100+ changements Celery toutes les 5 min → spam de logs `Background saving started/terminated with success`.

**Fix** : `command: redis-server --save 3600 1 --appendonly yes`
- Snapshot seulement si 1 changement en 1h
- AOF persistence (plus sûr, remplace les snapshots fréquents)
- Fork CoW reste minimal (DB ~0 MB)

## Valkey vs Redis

L'officiel Paperless utilise maintenant `valkey/valkey:9-alpine` (fork open-source Linux Foundation, Redis a changé de licence). Redis 8.x fonctionne mais question souveraineté, Valkey est préférable.

## Versions

- Gotenberg officiel: 8.34 (fonctionne avec 7.10, flags compatibles)
- Tika officiel: `latest` (pinning 2.9.1.0 OK pour reproductibilité)
- Paperless-ngx: 3.0.5 pinné

## Variables importantes

| Variable | Valeur | Notes |
|---|---|---|
| `PAPERLESS_OCR_LANGUAGE` | `fra+eng` | Format ISO 639-2 (3 lettres) |
| `PAPERLESS_CONSUMER_RECURSIVE` | `true` | Scanner les sous-dossiers |
| `PAPERLESS_CONSUMER_POLLING_INTERVAL` | `30` | **Obligatoire sur NFS** |
| `PAPERLESS_CONSUMER_DUPLICATE_HANDLING` | `skip` | Skip les doublons |
| `PAPERLESS_URL` | `https://paperless.jefe.al` | Pour reverse proxy |
| `USERMAP_UID/GID` | `1000` | Permissions NFS |

## Documentation

- Setup: https://docs.paperless-ngx.com/setup/
- Config: https://docs.paperless-ngx.com/configuration/
- Compose officiels: https://github.com/paperless-ngx/paperless-ngx/tree/main/docker/compose