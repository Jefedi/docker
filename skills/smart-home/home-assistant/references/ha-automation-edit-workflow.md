# HA — Automation/Script Bulk Edit Workflow

Trouver et corriger un service cassé (ex: notify renommé) dans toutes les automatisations et scripts.

## Use case

Le notify du mobile app change de nom quand l'iPhone est renommé dans iOS :
- `notify.mobile_app_iphone_de_zef` → `notify.mobile_app_iphone_du_zef`

HA ne prévient pas — l'automation reste avec l'ancien nom et échoue silencieusement (ou affiche un popup "action inconnue").

## Workflow

### 1. Trouver le nouveau nom de service

```bash
# Lister tous les notify services disponibles
curl -s -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_list_services","arguments":{"domain":"notify"}},"id":1}' | grep '^data:' | sed 's/^data: //'
```

### 2. Chercher toutes les références à l'ancien service

```bash
# ha_search fouille: entities + automations + scripts + scenes + helpers
curl -s -H "..." -X POST "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_search","arguments":{"query":"iphone_de_zef"}},"id":1}'
```

**Raccourci popup HA :** si l'utilisateur envoie une capture d'écran du popup d'erreur, le message contient directement l'entity_id (`automation.nasa_apod_photo_astronomique_du_jour`). Pas besoin de `ha_search` — appelle `ha_config_get_automation` directement avec cet ID.

Le résultat contient :
- `entities[]` — entités dont le nom correspond
- `automations[]` — automations dont la config contient le terme (avec `match_in_config: true`)
- `scripts[]`, `scenes[]`, `helpers[]`

### 3. Obtenir la config complète de chaque automation

```bash
curl -s -H "..." -X POST "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_get_automation","arguments":{"identifier":"automation.f1_session_dans_30_minutes"}},"id":1}'
```

**Paramètre :** `identifier` (l'entité complète `automation.xxx`).
**Attention blueprint :** la config est dans `config.use_blueprint.input.notification_actions[]` — pas dans `config.actions[]`.

### 4. Modifier l'automation

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ha_config_set_automation",
    "arguments": {
      "identifier": "automation.xxx",
      "config": { "... config complète modifiée ..." },
      "config_hash": "hash_retourné_par_get"
    }
  },
  "id": 2
}
```

**Piège config_hash :** toujours renvoyer le `config_hash` reçu du GET. Sans ça, l'update échoue (ou crée un doublon).

**💡 config_hash vide passe quand même :** si le GET retourne un `config_hash` vide (`""`), passe-le quand même dans le SET — l'update réussit. Mais ne l'omets pas du payload (risque de duplicata).

**Stratégie patch :** convertir la config en JSON string, faire un `str.replace('ancien', 'nouveau')` (avec `ensure_ascii=False` pour préserver les emojis), re-parser en dict, et envoyer.

### ⚠️ Piège critique : suivre la chaîne — les scripts appelés par automations

**Le piège qui a coûté 2 sessions :** une automation peut utiliser `action: script.xxx` sans jamais mentionner directement le notify cassé. Le `notify.mobile_app_*` est dans la config du **script** appelé, pas dans l'automation.

Exemple concret :
- L'automation `📡 Webhook → Beszel Adapter` utilise `action: script.notification_central`
- `ha_search(query="iphone_de_zef")` trouve l'automation ✅
- On patch l'automation, mais elle ne contient pas le notify → **rien ne change**
- Le notify cassé est en fait dans `script.notification_central`, qui n'a pas été patché ❌
- Le popup HA persiste : "utilise une action inconnue"

**Workflow complet** :
1. Lancer `ha_search(query="ancien_nom")` — répare tout ce qui est trouvé
2. **Ensuite**, pour chaque automation qui utilise `script.xxx`, inspecter ce script avec `ha_config_get_script(script_id="xxx")`
3. Chercher spécifiquement les scripts "hub" centraux : `notification_central`, `notifications_centralisées`, etc.
4. Convertir la config du script en JSON string, `str.replace('ancien', 'nouveau')`, et envoyer via `ha_config_set_script`

**Indice que ce piège est en jeu :** après avoir patché toutes les automations et scripts trouvés par `ha_search`, le popup HA persiste pour une automation qui utilise `action: script.xxx`. C'est le signe certain que l'action cassée est dans le script.

### 5. Scripts — API légèrement différente

```bash
# GET
curl -s -H "..." -X POST "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_get_script","arguments":{"script_id":"envoi_liste_courses"}},"id":1}'

# SET — utilise script_id PAS identifier
curl -s -H "..." -X POST "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_set_script","arguments":{"script_id":"envoi_liste_courses","config":{...},"config_hash":"..."}},"id":2}'
```

**Piège :** `ha_config_get_script` prend `script_id` (sans préfixe `script.`). `ha_config_set_script` prend aussi `script_id`.

**Piège double nesting :** le GET renvoie `config.script_id.config.sequence[]` — attention au double niveau `config`.

## Commandes utiles

```bash
# Vérifier qu'un service notify existe bien
ha_list_services(domain="notify")

# Chercher TOUTES les références cross-config
ha_search(query="ancien_nom")

# Obtenir config automation (avec blueprint)
ha_config_get_automation(identifier="automation.xxx")

# Obtenir config script
ha_config_get_script(script_id="nom_sans_prefixe")

# Mettre à jour automation
ha_config_set_automation(identifier="automation.xxx", config={...}, config_hash="...")

# Mettre à jour script
ha_config_set_script(script_id="nom_sans_prefixe", config={...}, config_hash="...")
```
