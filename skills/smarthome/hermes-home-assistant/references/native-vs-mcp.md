# Native Hermes HA Tools vs Ha-MCP — Comparatif

Constat de session : le toolset natif `homeassistant` d'Hermes (4 outils) est très limité comparé au MCP ha-mcp (~70 outils).

## Outils natifs Hermes (sans MCP)

| Tool | Usage |
|---|---|
| `ha_call_service` | Contrôle devices |
| `ha_get_state` | Lire état d'une entité |
| `ha_list_entities` | Lister entités (filtre domaine/zone) |
| `ha_list_services` | Lister services disponibles |

Connexion via l'API REST HA (token longue durée + URL).

## MCP ha-mcp (~70 outils)

Accès complet à HA : automations, scripts, scènes, dashboards, helpers (28 types), caméras, calendriers, todos, add-ons Supervisor, HACS, radios Zigbee/Z-Wave/Matter, historique/statistiques, backups, energy dashboard, thèmes, labels, zones, Assist pipelines, logs, templates Jinja2, etc.

## Implications

- **Sans MCP** : Hermes peut juste lire/contrôler. Pas de création d'autos, dashboards, etc.
- **Avec MCP** : Hermes voit et gère tout HA comme s'il était dans l'interface.
- **Gateway Adapter** (plateforme `homeassistant` du Gateway) fonctionne indépendamment — c'est HA qui envoie des messages à Hermes, pas Hermes qui contrôle HA.
