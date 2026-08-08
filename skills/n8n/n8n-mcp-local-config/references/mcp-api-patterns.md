# n8n MCP API — patterns détaillés

## Connection setup

Le serveur MCP n8n est accessible via `config.yaml` :
```yaml
mcp_servers:
  n8n-mcp:
    url: https://n8n.jefe.ovh/mcp-server/http
    headers:
      Authorization: Bearer ${MCP_N8N_MCP_API_KEY}
```

L'env var `MCP_N8N_MCP_API_KEY` contient le JWT complet.

## curl — template de base

```bash
curl -s -X POST "https://n8n.jefe.ovh/mcp-server/http" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $MCP_N8N_MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"TOOL_NAME","arguments":{...}},"id":N}'
```

**Sans `Accept: application/json, text/event-stream` → 406 Not Acceptable.**

## Parser la réponse SSE

```bash
... | grep "^data:" | python3 -c "
import sys, json
line = sys.stdin.readline().strip()
if line.startswith('data: '):
    data = json.loads(line[6:])
    sc = data.get('result',{}).get('structuredContent',{})
    print(json.dumps(sc, indent=2, ensure_ascii=False))
"
```

## Outils MCP disponibles (résumé)

| Tool | Usage |
|---|---|
| `search_workflows` | Filtrer par nom, tag, projet |
| `get_workflow_details` | Structure complète : nœuds, connexions, groups |
| `update_workflow` | Opérations atomiques (addNode, addConnection, setNodeCredential, etc.) |
| `publish_workflow` | Activer la version en production |
| `validate_node_config` | Valider un nœud avant ajout — révèle les paramètres valides via erreurs |
| `search_executions` | Historique d'exécution par workflow/status |
| `get_execution` | Détails d'une exécution (includeData=true pour inputs/outputs) |
| `list_credentials` | Lister les credentials avec filter |
| `create_workflow_from_code` | Créer via SDK code (requires validate_workflow first) |
| `get_sdk_reference` | Référence SDK pour create_workflow_from_code |

## validate_node_config — découverte par erreurs

Le validateur révèle les options valides via ses messages d'erreur. Stratégie :

1. Envoyer une config minimale avec le type de nœud
2. Lire les erreurs — elles listent les valeurs attendues
3. Itérer avec les bonnes valeurs jusqu'à `valid: true`

Exemple concret avec `n8n-nodes-base.spotify` v1 :
- Essai 1: `resource: "playlist"` → erreur "expected one of: player"
- Essai 2: `resource: "player"` → erreur liste toutes les operations dont `getUserPlaylists`
- Essai 3: `resource: "playlist", operation: "getUserPlaylists"` → **valid: true**

Le premier essai échoue parce que le discriminateur `operation` n'est pas fourni. Une fois `operation` ajouté, le `resource` "playlist" devient valide.

## update_workflow — ordre des opérations

```
1. addNode (tous les nouveaux nœuds)
2. setNodeCredential (si credentials nécessaires)
3. addConnection (source → target, les deux doivent exister)
4. addTags / setWorkflowMetadata / setWorkflowSettings
```

Atomique : si une opération échoue, rien n'est sauvé.

## Credentials — compatibilité

| Node type | spotifyOAuth2Api | httpHeaderAuth | httpBearerAuth |
|---|---|---|---|
| n8n-nodes-base.spotify | ✅ | ❌ | ❌ |
| n8n-nodes-base.httpRequest | ❌ | ✅ | ✅ |
| n8n-nodes-base.code | ❌ | ❌ | ❌ |
| n8n-nodes-base.dataTable | N/A | N/A | N/A |

**Pour appeler l'API Spotify depuis n8n : utiliser le nœud natif `n8n-nodes-base.spotify`, pas HTTP Request.**

## Data Tables — patterns

Les Data Tables n8n servent de stockage persistant pour les backups.

- `operation: "upsert"` avec `matchType: "allConditions"` et `filters.conditions` pour la clé de déduplication
- `dataTableId`: `{ "__rl": true, "mode": "name", "value": "table_name" }`
- `columns.schema`: définir chaque colonne avec `canBeUsedToMatch: true` pour les colonnes qui servent de clé

Exemple de dédup sur deux colonnes (track_id + playlist_id) :
```json
"filters": {
  "conditions": [
    {"keyName": "track_id", "keyValue": "={{ $json.track_id }}"},
    {"keyName": "playlist_id", "keyValue": "={{ $json.playlist_id }}"}
  ]
}
```

## Workflow Spotify Backup — structure (IDq7NyfY6iXAdvzj)

Branche titres likés :
```
Schedule Trigger → Get Liked Tracks → Transform → Store (spotify_saved_tracks)
```

Branche artistes :
```
Schedule Trigger → Get Followed Artists → Transform → Store (spotify_followed_artists)
```

Branche playlists (ajoutée 2026-08-01) :
```
Schedule Trigger → Get Playlists → Transform → Store (spotify_playlists)
                                      → Get Playlist Tracks → Transform → Store (spotify_playlist_tracks)
```

Nettoyage :
```
Store Liked Tracks → Get All Backup Tracks → Find Orphaned Tracks → Delete Orphaned Tracks
```

Catégories dans `spotify_playlist_tracks` :
- `rap_hiphop` : nom de playlist contient "rap", "hip", "hop"
- `liked` : nom contient "liked", "cœur", "coeur"
- `playlist` : défaut