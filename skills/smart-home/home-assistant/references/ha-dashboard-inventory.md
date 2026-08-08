# HA Dashboard Inventory — guide pratique

## Workflow

1. **Lister les dashboards storage**
   ```
   ha_config_get_dashboard(list_only=True)
   ```
   Retourne la liste des dashboards en mode `storage` avec leur `id`, `title`, `url_path`, `mode`.

2. **Pour chaque dashboard, récupérer la config complète** (vues + cartes)
   ```
   ha_config_get_dashboard(url_path="<url_path>")
   ```
   Le champ `config.views[].title` donne les onglets. Un dashboard peut avoir plusieurs vues que l'utilisateur appelle abusivement "dashboards".

3. **Lister les ressources Lovelace** (cartes custom, CSS inline)
   ```
   ha_config_list_dashboard_resources()
   ```
   Permet de détecter les cartes inline `[inline]` qui sont des custom elements JS/CSS attachés au dashboard.

## Distinction clé

| Ce que dit l'utilisateur | Ce que c'est vraiment |
|-------------------------|----------------------|
| "dashboard Traduction" | Vue/onglet dans un dashboard existant |
| "dashboard Radarr" | Vue/onglet (iframe FlightRadar) dans un dashboard existant |
| "dashboard Map" | Dashboard storage séparé avec 1 vue |
| "dashboard Maison" | Dashboard principal avec 5+ vues |
| "dashboard Formule 1" | Dashboard storage séparé avec 2 vues |

## Contraintes de suppression

- **Storage dashboards** : supprimables via `ha_config_delete_dashboard(url_path="...")`
- **Default dashboard** (`lovelace`) : non supprimable via MCP
- **YAML-mode dashboards** : non supprimables via MCP
- La suppression d'un dashboard supprime son agencement mais **pas les entités** — les capteurs, switches, automatisations restent intacts.

## Zones sur la carte — workflow de nettoyage

Les zones géographiques (magasins, lieux divers) polluent la carte par défaut. Workflow :

1. **Lister les zones**
   `ha_get_zone()` retourne `zones[]` avec `id`, `name`, `latitude`, `longitude`.

2. **Identifier les zones à garder** (maison, domicile proches) vs à supprimer (magasins, loisirs).

3. **Supprimer les zones inutiles**
   `ha_remove_zone(zone_id="auchan_le_havre")`
   Utiliser l'`id` retourné par `ha_get_zone`, PAS le `name`.

**Piège zone système** : la zone "Maison" par défaut n'apparaît PAS dans `ha_get_zone()` — elle est créée automatiquement par HA et ne peut pas être supprimée.

## Piège parsing : wrapper `data` dans les réponses MCP

Quand on appelle `ha_search`, le `content[0].text` peut contenir `{"data": {...}}` au lieu des résultats directs :

```python
content = json.loads(data['result']['content'][0]['text'])
if 'data' in content:
    content = content['data']  # déballer
results = content.get('results', [])
```

## Pièges rencontrés

1. **Header Accept obligatoire** : le MCP HA rejette en 406 sans `Accept: application/json, text/event-stream`
2. **SSE parsing** : les réponses sont en Server-Sent Events, pas en JSON brut. Extraire les lignes `data:`.
4. **Ne pas confondre vues et dashboards** : un dashboard peut avoir 5 vues (Jefe, Traduction, Courses, Espace, Radarr par exemple) — l'utilisateur perçoit chaque vue comme un "dashboard" séparé.
5. **`url_path` avec tiret obligatoire** pour créer un nouveau dashboard storage : `maison-dashboard` ✅, `maison` ❌.
6. **Auto-création du lovelace** : si tous les dashboards storage sont supprimés, HA recrée un dashboard `lovelace` vide par défaut. Impossible à supprimer via MCP. Solution : créer un nouveau storage dashboard — dès qu'un seul existe, HA l'affiche comme page par défaut.
7. **`ha_call_service` utilise `data`** : le paramètre s'appelle `data`, pas `service_data`. Ex : `{"data":{"brightness":255}}`.
8. **`visible` dans les vues** : une vue avec `visible: []` (tableau vide) est visible par tous. `visible: [{"user": "UUID"}]` restreint à un utilisateur spécifique.
9. **`ha_get_overview` pas de `group_by`** : `{"group_by": "area"}` retourne `Bad Gateway`. Utiliser `ha_get_device(area_id=...)` à la place.\n10. **Python http.client + emojis** : quand la config contient des emojis, `http.client.HTTPSConnection` plante car il encode le body en latin-1. Solution : `body = json.dumps(payload, ensure_ascii=False).encode('utf-8')`.\n11. **Plusieurs SSE events** : certains outils MCP envoient des notifications de progression PUIS le résultat. Toujours filtrer par `'result' in data and data.get('id') == target_id`.
