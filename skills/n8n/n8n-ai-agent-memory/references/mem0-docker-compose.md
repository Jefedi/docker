# Mem0 Docker-Compose Modifications

## Changes needed on the official `server/docker-compose.yaml`

The official compose from `github.com/mem0ai/mem0` needs 4 modifications before it works on Jefe's infra:

### 1. Bind all ports to 127.0.0.1 (never 0.0.0.0)

```diff
- "8888:8000"
+ "127.0.0.1:8888:8000"

- "8432:5432"
+ "127.0.0.1:8432:5432"

- "3000:3000"
+ "127.0.0.1:3101:3000"   # 3101 because port 3000 is taken by DockHand
```

### 2. Remove the `.:/app` volume mount (line ~16)

```diff
  volumes:
    - ./history:/app/history
-   - .:/app
```

This is a dev-mode hot-reload mount. It overwrites the Dockerfile's COPY steps at runtime.
Docker creates directories for files that don't exist in the host path (e.g., `init-db.sh` becomes a directory).
After removal, alembic finds its config (`alembic.ini`) and migrations run correctly.

### 3. Remove the `init-db.sh` volume mount (line ~48)

```diff
  volumes:
    - postgres_db:/var/lib/postgresql/data
-   - ./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
```

Same issue: Docker creates a directory instead of mounting the file.
Instead, create the `mem0_app` database manually after Postgres starts:

```bash
docker compose up -d postgres
sleep 5
docker exec mem0-dev-postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE mem0_app;"
```

### 4. Update DASHBOARD_URL in the mem0 environment

```diff
- DASHBOARD_URL=http://localhost:3000
+ DASHBOARD_URL=http://localhost:3101
```

## sed one-liner (all changes at once)

```bash
sed -i \
  -e 's|"8888:8000"|"127.0.0.1:8888:8000"|' \
  -e '/- \.:\/app/d' \
  -e 's|"8432:5432"|"127.0.0.1:8432:5432"|' \
  -e '/- \.\/init-db.sh:\/docker-entrypoint-initdb.sh/d' \
  -e 's|"3000:3000"|"127.0.0.1:3101:3000"|' \
  -e 's|DASHBOARD_URL=http://localhost:3000|DASHBOARD_URL=http://localhost:3101|' \
  docker-compose.yaml
```

## Startup sequence

```bash
# 1. Start Postgres alone
docker compose up -d postgres

# 2. Wait for healthy, then create mem0_app DB
sleep 5
docker exec mem0-dev-postgres-1 psql -U postgres -d postgres -c "CREATE DATABASE mem0_app;"

# 3. Start everything
docker compose up -d
```

## Verification

```bash
docker compose ps
# All 3 containers should be Up:
# mem0-dev-mem0-1           Up        127.0.0.1:8888->8000/tcp
# mem0-dev-postgres-1       Healthy   127.0.0.1:8432->5432/tcp
# mem0-dev-mem0-dashboard-1 Healthy   127.0.0.1:3101->3000/tcp

# Check API
curl -s http://localhost:8888/docs | head -5

# Test memory add
curl -s -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test memory"}], "user_id": "test"}'
```

## Connect n8n to Mem0 (persistent network)

### Manual (lost on restart)

```bash
docker network connect mem0-dev_mem0_network n8n-n8n-1
```

### Permanent — edit n8n's compose.yaml

**Location**: `/srv/docker/n8n/compose.yaml` (NOT `docker-compose.yaml`)

Add `mem0-dev_mem0_network` to the n8n service networks block:
```yaml
    networks:
      - n8n-net
      - shared-translate
      - shared-db
      - mem0-dev_mem0_network   # Add this
```

Add to the top-level networks section:
```yaml
networks:
  n8n-net:
  shared-translate:
    external: true
  shared-db:
    external: true
  mem0-dev_mem0_network:       # Add this
    external: true
```

⚠️ **Do NOT use sed for this** — sed multi-line insertions break YAML indentation and can create duplicate `external: true` entries. Edit manually or use `write_file`. If sed corrupts the file, restore from backup: `cp compose.yaml.bak.otel-* compose.yaml`.

**Backups available**: `compose.yaml.bak.otel-20260702`, `compose.yaml.bak.20260503-164323`, `compose.yaml.pre-watchtower`.

Apply with:
```bash
docker compose -f /srv/docker/n8n/compose.yaml up -d --force-recreate
```

In the n8n Mem0 node credential, set the API URL to `http://mem0:8000` (container name on the shared network).

### AUTH_DISABLED + n8n credential

`AUTH_DISABLED=true` accepts requests WITHOUT Authorization header. But n8n's Mem0 node credential requires a non-empty API key. When a Bearer token IS sent, Mem0 returns `{"detail":"Invalid or expired token."}` even with auth disabled.

**Fix**: Create a real API key via the Mem0 dashboard (port 3101) and use it in the n8n credential. Note: the dashboard admin creation may fail with "Network Error" if `NEXT_PUBLIC_API_URL` is localhost and the browser is remote.