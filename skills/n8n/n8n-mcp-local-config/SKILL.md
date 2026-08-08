---
name: n8n-mcp-local-config
category: n8n
description: Configurer un serveur MCP n8n local pour éviter les blocages externes et garantir l’utilisation du cookie complet.
---

# MCP n8n local – configuration et dépannage

## Objectif
Installer et configurer **n8n** pour qu’il utilise un MCP local (`http://localhost:5678/mcp-server/http`) plutôt qu’un serveur hébergé via Pangolin. Ce mode contourne les restrictions d’authentification et les erreurs 403/401 que le serveur externe (Pangolin) a introduites.

## Prérequis
- Un serveur MCP local fonctionnel (ex : `n8n-mcp` en mode HTTP, lancé sur le même hôte que Hermes).
- Le **token complet** MCP valide (JWT généré par le serveur local). Doit rester secret ; ne pas le placer en clair dans la config.
- Maven / Python (Pas requis pour la configuration) – un environnement Docker est suffisant.

## Étapes de configuration

1. **Obtenir le token MCP**
   ```bash
   export N8N_MCP_TOKEN=$(< /opt/data/.env.n8n_mcp_token)
   ```
   La variable `N8N_MCP_TOKEN` doit contenir le JWT complet, pas tronqué.

2. **Modifier `config.yaml` du profil n8n**
   ```yaml
   mcp_servers:
     n8n-mcp:
       url: http://localhost:5678/mcp-server/http
       timeout: 180
       connect_timeout: 30
       headers:
         Authorization: Bearer ${N8N_MCP_TOKEN}
   ```
   - `url` doit pointer vers l’API HTTP locale.
   - Le header `Authorization` est nécessaire pour chaque requête.
   - Évitez la syntaxe `Bearer eyJhbG...` tronquée; utilisez l’interpolation `${N8N_MCP_TOKEN}`.

3. **Redémarrer le gateway Hermes**
   ```bash
   hermes -p n8n gateway stop
   hermes -p n8n gateway run
   ```
   Vérifiez les logs (`/opt/data/profiles/n8n/logs/gateway.log`) : un `gateway running` et `✓ telegram connected` indique le succès.

4. **Tester l’envoi d’une requête MCP**
   ```bash
   curl -s -w '\nHTTP_CODE: %{http_code}' \
     -X POST \"http://localhost:5678/mcp-server/http\" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $N8N_MCP_TOKEN" \
     -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}'
   ```
   Un code `200` confirme la bonne connexion.

## Pondérations de dépannage
- **401/403** – Vérifiez que `N8N_MCP_TOKEN` est complet et non tronqué.
- **404** – Le URL local est incorrect. Testez `curl http://localhost:5678/mcp-server/http` : vous devriez obtenir un JSON Basic LSP Framework.
- **Échec du gateway** – Consultez `gateway.log`; les erreurs “MCP server failed initial connection” indiquent généralement un timeout ou un mauvais header.
- **Pangolin redirection** – Si vous utilisez toujours l’URL Pangolin, il suffit de changer `url` pour le local et relancer.

## Utiliser l'API MCP n8n — patterns et gotchas

### Format SSE obligatoire
Le serveur MCP n8n répond en Server-Sent Events. Toute requête `curl` doit inclure :
```
-H "Accept: application/json, text/event-stream"
```
Sans ce header → `406 Not Acceptable`.

Les réponses sont au format `event: message\ndata: {json}` — parser avec `grep "^data:" | python3 -c "..."`.

### Découvrir les paramètres valides d'un nœud
`validate_node_config` est l'outil clé pour découvrir quels paramètres un nœud accepte **avant** de l'ajouter à un workflow. Envoyer une config de test et lire les erreurs :
- Les erreurs listent les valeurs attendues (ex: `expected one of: "get", "getUserPlaylists", ...`)
- Quand un `resource` semble invalide, le message d'erreur liste toutes les valeurs valides

Exemple : le nœud `n8n-nodes-base.spotify` v1 affiche `resource: "player"` comme seule valeur valide au premier essai, mais en testant `resource: "playlist"` + `operation: "getUserPlaylists"`, la validation passe. **Le validateur révèle les options par discriminateur (resource+operation combos).**

### Credentials sur les nœuds
- `n8n-nodes-base.httpRequest` **n'accepte pas** `spotifyOAuth2Api` comme credential.
- `n8n-nodes-base.code` **n'accepte pas** non plus de credentials externes.
- Les nœuds natifs (`n8n-nodes-base.spotify`) acceptent `spotifyOAuth2Api` — utiliser `setNodeCredential` dans `update_workflow` ou laisser l'auto-assignement fonctionner.
- `update_workflow` auto-assigne les credentials si le nœud supporte le type et qu'une credential du même type existe.

### update_workflow : opérations atomiques
- Toutes les opérations dans un seul appel `update_workflow` sont appliquées atomiquement.
- Ordre : `addNode` d'abord, puis `setNodeCredential`, puis `addConnection`.
- `addConnection` requiere que source et target existent déjà (soit préexistants, soit ajoutés dans le même batch).
- Max 100 opérations par appel.

### Spotify node v1 — ressources et opérations valides
| resource | operation | Notes |
|---|---|---|
| `playlist` | `getUserPlaylists` | `returnAll: true` pour toutes les playlists |
| `playlist` | `getTracks` | `id: "={{ $json.playlist_id }}"`, `returnAll: true` |
| `library` | `getLikedTracks` | `returnAll: true` (ancien format, fonctionne en production) |
| `myData` | `getFollowingArtists` | `returnAll: true` (ancien format) |

**Piège :** Les anciens nœuds créés sans le paramètre `operation` génèrent des warnings de validation mais fonctionnent toujours en production. Ne pas casser ces nœuds en les "corrigeant".

### Publier après modification
Après `update_workflow`, toujours `publish_workflow` pour activer la version en production.

### ⚠️ Editor lock
`update_workflow` échoue avec `"Cannot modify workflow while it is being edited by a user in the editor."` si l'utilisateur a le workflow ouvert dans l'UI n8n. Demander à l'utilisateur de fermer l'onglet du workflow, puis réessayer. Pas de workaround côté API.

## AI Agent — Architecture mémoire et tools

### Nodes Memory vs Nodes Tool — distinction critique
Le slot "Memory" de l'AI Agent n'accepte **que** les nodes avec une connexion de type `ai_memory` :
- Window Buffer (Simple Memory)
- Postgres Chat Memory
- Redis Chat Memory
- MongoDB Chat Memory
- Xata

Les **community nodes comme Mem0** (`@mem0/n8n-nodes-mem0`) sont des nodes d'action standard (`group: ['transform']`, `usableAsTool: true`). Ils apparaissent dans la liste des **Tools** de l'AI Agent, **PAS** dans la liste Memory. Ils se connectent en `ai_tool`, pas en `ai_memory`.

**Conséquence :** Mem0 ne remplace pas le slot Memory. Il s'utilise en complément :
- **Postgres Chat Memory** → contexte de conversation (slot Memory)
- **Mem0 en tool** → mémoires long-terme, extraction de faits (slot Tool)

### Customiser le system prompt d'un AI Agent
Le node AI Agent (`@n8n/n8n-nodes-langchain.agent`) a un paramètre `options.systemMessage` qui accepte du texte long + expressions n8n (`{{ $now }}` pour la date dynamique). On peut injecter un system prompt riche (profil utilisateur, infra, préférences, mémoires) via `updateNodeParameters` :

```python
mcp__n8n_mcp__update_workflow(
    workflowId="<id>",
    operations=[{
        "type": "updateNodeParameters",
        "nodeName": "<agent node name>",
        "parameters": {
            "options": {
                "systemMessage": "=<role>...</role>\n<user_profile>...</user_profile>\n<infra_context>...</infra_context>\n{{ $now }}"
            }
        },
        "replace": False
    }],
    versionName="System prompt personnalisé",
    versionDescription="..."
)
```

Le `=` en début de systemMessage indique une expression n8n (évalué), pas du texte literal.

### Renommer un node ne change pas son type
`renameNode` change le `name` affiché mais garde le `type` d'origine. Un node `memoryBufferWindow` renommé "Chat Memory (Postgres)" reste un Window Buffer. Pour changer le type, il faut `removeNode` + `addNode` avec le nouveau type + `addConnection`.

### Installer un community node
Les community nodes s'installent via : Settings → Community Nodes → Install from npm → `@package/name`. Après installation, ils apparaissent dans la liste des nodes (section community, pas dans les sections natives n8n).

Voir `references/mem0-self-hosted-deploy.md` pour le déploiement Docker de Mem0.

### Data Tables — pièges et manipulation directe

#### Les Data Tables doivent exister avant upsert/insert
n8n ne crée **pas** automatiquement une Data Table si elle n'existe pas. Un `upsert` ou `insert` sur une table inexistante → `Validation error with data table request: unknown column name '<col>'`.

**Diagnostic :** Lister les tables existantes via le conteneur n8n :
```bash
docker exec n8n-n8n-1 node -e "
const sqlite = require('sqlite3').Database;
const db = new sqlite('/home/node/.n8n/database.sqlite');
db.all('SELECT id, name FROM data_table', (err, rows) => {
  rows.forEach(r => console.log(r.id, r.name));
  db.close();
});
"
```

#### Les noms de colonnes doivent matcher exactement
Une table peut avoir `tracks_count` (pas `track_count`). Toujours vérifier les colonnes existantes avant de mapper :
```bash
docker exec n8n-n8n-1 node -e "
const sqlite = require('sqlite3').Database;
const db = new sqlite('/home/node/.n8n/database.sqlite');
db.all('SELECT name, type FROM data_table_column WHERE dataTableId = \"<id>\"', (err, rows) => {
  rows.forEach(r => console.log(r.name, '(' + r.type + ')'));
  db.close();
});
"
```

#### Ajouter des colonnes à une Data Table existante
Deux étapes obligatoires — INSERT métadonnées + ALTER TABLE physique :
```javascript
// 1. Insérer dans data_table_column (attention: "index" est réservé SQLite → quoter)
db.run('INSERT INTO data_table_column (id, name, type, "index", dataTableId) VALUES (?, ?, ?, ?, ?)',
  [uuid, colName, colType, idx, dataTableId]);

// 2. Ajouter la colonne physique à la table de stockage
db.run('ALTER TABLE data_table_user_<dataTableId> ADD COLUMN <colName> TEXT');
```

#### Schéma de la table data_table_column
| Colonne | Type | Notes |
|---|---|---|
| id | varchar(36) | UUID PK |
| name | varchar(128) | Nom de colonne |
| type | varchar(32) | string, number, boolean, date |
| index | INTEGER | Position (⚠️ réservé SQLite — toujours quoter `"index"`) |
| dataTableId | varchar(36) | FK vers data_table.id |
| createdAt/updatedAt | datetime | Auto |

#### Créer une Data Table manuellement
Si une table n'existe pas, il faut la créer depuis l'UI n8n (Data Tables → New) ou via l'API REST n8n (nécessite `X-N8N-API-KEY` header — le token MCP ne fonctionne pas comme API key).

Voir `references/data-table-db-manipulation.md` pour le script complet de manipulation DB.

## Références
- [« Troubleshoot 401 – MCP n8n local »](/n8n/mcp-local-config/references/401.md)
- [« MCP API patterns — curl, SSE, validate_node_config »](/n8n/mcp-local-config/references/mcp-api-patterns.md)
- [« Data Table DB manipulation — scripts et patterns »](/n8n/mcp-local-config/references/data-table-db-manipulation.md)

---

### À retenir
- Toujours garder le token complet. Évitez de copier-coller la version tronquée (`eyJhbGci...`).
- Pour un tunnel local fiable, utilisez `https://<hostname>:<port>/mcp-server/http` avec un certificats valide ou `http` si vous faites du `localhost`.
- Le gateway doit être arrêté puis redémarré pour que les nouveaux paramètres prenne‑ils effet.
