# Pattern terminal _req pour CrossWatch API

Quand les MCP tools ne sont pas directement exposés dans Hermes, utiliser le module Python directement :

```bash
CW_BASE_URL="https://crosswatch.jefe.ovh" \
CW_COOKIE="cw_auth=qtLymCxqhFylisH3i2Hr5sZRBzbrK3EX5jrW73QqZS0" \
python3 -c "
import json, sys
sys.path.insert(0, '/root/.hermes/mcp')
from crosswatch_server import _req

# GET
data = _req('GET', '/api/pairs')
print(json.dumps(data, indent=2))

# POST with body
result = _req('POST', '/api/run', json={'label': 'Sync manuel'})
print(json.dumps(result, indent=2))

# PUT with body
result = _req('PUT', '/api/pairs/pair_xxx', json={...})
"
```

## Endpoints utilisés dans cette session

| Endpoint | Method | Usage |
|----------|--------|-------|
| `/api/provider-instances` | GET | Lister les providers configurés |
| `/api/pairs` | GET | Lister les paires de sync |
| `/api/pairs` | POST | Créer une nouvelle paire |
| `/api/pairs/{id}` | PUT | Modifier une paire existante |
| `/api/run` | POST | Lancer un sync (⚠️ pas `/api/sync/run`) |
| `/api/run/summary` | GET | Voir le résultat du dernier sync |
