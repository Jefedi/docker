# Debug AniList — Token expiré

Quand l'utilisateur dit "j'ai rien sur AniList" mais que CrossWatch montre des items dans son état, le token OAuth est probablement expiré.

## Vérifier le token

```python
import json, sys, subprocess
sys.path.insert(0, '/root/.hermes/mcp')
from crosswatch_server import _req

cfg = _req('GET', '/api/config')
token = cfg['anilist']['access_token']

# Test direct via GraphQL
query = '{"query":"query { MediaListCollection(userId: 7241861, type: ANIME) { lists { name entries { media { id title { romaji english } } } } } }"}'
with open('/tmp/anilist_query.json', 'w') as f:
    f.write(query)

result = subprocess.run(
    ["curl", "-s", "-X", "POST", "https://graphql.anilist.co",
     "-H", f"Authorization: Bearer ***     "-H", "Content-Type: application/json",
     "-d", "@/tmp/anilist_query.json"],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

**Réponse si valide** : `{"data": {"MediaListCollection": {...}}}` avec des entrées

**Réponse si expiré** : `{"data": null, "errors": [{"message": "Invalid token"}]}`

## Réparer

1. Aller sur l'UI CrossWatch : `https://crosswatch.jefe.ovh`
2. Settings → AniList → Disconnect puis reconnect via OAuth
3. Relancer un sync : `sync_run()` puis `sync_run_summary()`

## Détails du compte AniList de Jefe

- User ID: 7241861
- Username: jefe59
- Flow: OAuth2 (client_id + client_secret + access_token)
- Pas de refresh token automatique (`refresh: False` dans l'auth provider config)
