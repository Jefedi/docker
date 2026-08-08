# Data Table DB Manipulation — Scripts et Patterns

## Accès à la DB SQLite n8n depuis le conteneur

Le conteneur n8n n'a pas `sqlite3` ni `python3`. Utiliser le module `sqlite3` de Node.js :
```bash
docker exec n8n-n8n-1 npm install --no-save sqlite3  # one-time
```

## Lister toutes les Data Tables
```bash
docker exec n8n-n8n-1 node -e "
const sqlite = require('sqlite3').Database;
const db = new sqlite('/home/node/.n8n/database.sqlite');
db.all('SELECT id, name, projectId FROM data_table', (err, rows) => {
  rows.forEach(r => console.log(r.id, r.name, r.projectId));
  db.close();
});
"
```

## Lister les colonnes d'une Data Table
```bash
docker exec n8n-n8n-1 node -e "
const sqlite = require('sqlite3').Database;
const db = new sqlite('/home/node/.n8n/database.sqlite');
db.all('SELECT name, type FROM data_table_column WHERE dataTableId = \"<ID>\"', (err, rows) => {
  rows.forEach(r => console.log(r.name, '(' + r.type + ')'));
  db.close();
});
"
```

## Ajouter des colonnes à une Data Table existante
```javascript
const sqlite = require('sqlite3').Database;
const crypto = require('crypto');
const db = new sqlite('/home/node/.n8n/database.sqlite');

function addColumn(dataTableId, colName, colType) {
  return new Promise((resolve, reject) => {
    db.get('SELECT COALESCE(MAX("index"),0) as maxIdx FROM data_table_column WHERE dataTableId = ?', 
      [dataTableId], (err, row) => {
      if (err) { reject(err); return; }
      const idx = (row?.maxIdx || 0) + 1;
      const id = crypto.randomUUID();
      db.run('INSERT INTO data_table_column (id, name, type, "index", dataTableId) VALUES (?, ?, ?, ?, ?)',
        [id, colName, colType, idx, dataTableId], function(err2) {
          if (err2) reject(err2);
          else resolve(idx);
        });
    });
  });
}

async function main() {
  // 1. Add metadata
  await addColumn('<dataTableId>', 'category', 'string');
  
  // 2. Add physical column to storage table
  db.run('ALTER TABLE data_table_user_<dataTableId> ADD COLUMN category TEXT', (err) => {
    console.log(err ? 'ALTER: ' + err.message : 'ALTER: OK');
    db.close();
  });
}
main().catch(e => console.log('Error:', e.message));
```

## Pièges clés
- **`"index"` est un mot réservé SQLite** — toujours quoter avec guillemets doubles
- **Deux étapes obligatoires** : INSERT dans `data_table_column` + `ALTER TABLE` sur `data_table_user_<id>`
- **Le token MCP n'est pas une API key n8n** — l'API REST n8n nécessite `X-N8N-API-KEY` header
- **Les Data Tables ne s'auto-créent pas** — un upsert sur une table inexistante échoue avec `unknown column name`
- **`n8n user-management:reset`** dans le conteneur réinitialise les utilisateurs — NE PAS exécuter accidentellement