# Pangolin API + Bitwarden CLI Patterns

Patterns appris lors du déploiement Technitium DNS (août 2026).

## Pangolin API — Limites de permissions

### Clé API sans permission Domain

Une clé Org avec uniquement permissions Resource + Target ne peut PAS:
- `GET /org/{orgId}/domains` → 403 "Key does not have permission"

**Workaround**: Obtenir le domain ID depuis:
1. Le dashboard Pangolin (Organization → Domains)
2. Le fichier gotchas du skill pangolin (`references/00-gotchas-jefe.md`)
3. L'API Swagger docs (`https://api.jefe.ovh/v1/docs`)

### Domain IDs peuvent devenir stale

Un domain ID stocké en mémoire/gotchas peut ne plus exister:
- `PUT /org/{orgId}/resource` retourne `"Domain with ID xxx not found"`
- Toujours vérifier via le dashboard avant utilisation

### Pattern 3 couches pour ressources HTTP sur Newt sites

Rappel critique (déjà documenté dans gotchas pangolin):
1. Public resource (org) → `PUT /org/{orgId}/resource`
2. Target (on resource) → `PUT /resource/{id}/target`
3. Site resource (on site) → `PUT /org/{orgId}/site-resource`

Sans la 3ème couche, Newt ne route pas le trafic → "no available server".

## Bitwarden CLI + Vaultwarden

### Configuration initiale

```bash
# Configurer le serveur (obligatoire pour Vaultwarden self-hosted)
npx -y @bitwarden/cli config server https://vault.jefe.al
```

### Login

```bash
# set +H obligatoire si le mot de passe contient des !
set +H
npx -y @bitwarden/cli login hermesagent@jefe.ovh '<password>' --raw
# Retourne un session token
```

### Créer un item (secure note)

```bash
set +H
export BW_SESSION="<session_token>"
echo '{"name":"Item Name","notes":"secret value","type":2,"secureNote":{"type":0}}' | base64 -w0 | npx -y @bitwarden/cli create item
```

### Récupérer un item

```bash
export BW_SESSION="<session_token>"
npx -y @bitwarden/cli get item "Item Name"
```

⚠️ Bug connu: `bw get item` peut échouer avec `EncString(InvalidTypeSymm)` sur
certaines versions de Vaultwarden. Workaround: récupérer la valeur d'une autre source.

### Session expiry

La session expire. Pour la restaurer sans re-login:
```bash
npx -y @bitwarden/cli unlock '<password>' --raw
```

### Nettoyage

Toujours supprimer les fichiers temporaires contenant des mots de passe:
```bash
shred -u /opt/data/.bw_pass || rm -f /opt/data/.bw_pass
```

## Préférence utilisateur: recherche web d'abord

Pour les questions sur des produits/technologies/services spécifiques, Jefe
préfère qu'on recherche sur internet plutôt que de synthétiser depuis la base
de connaissances. Les informations de training data peuvent être obsolètes.

**Workflow recommandé:**
1. web_search ou browser_navigate pour chercher l'info actuelle
2. Synthétiser avec sources datées
3. Citer les versions/dates exactes trouvées