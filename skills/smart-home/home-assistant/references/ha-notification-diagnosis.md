# HA — Notification Diagnosis via MCP

Diagnostiquer les erreurs de notification (notify services, ntfy, Discord, push iOS) via le MCP HA.

## Architecture Notification Centrale

Toutes les notifications passent par `script.notification_central` qui envoie en parallèle :
1. **Push iPhone** → `notify.mobile_app_iphone_du_zef` (iOS, avec Critical Alerts)
2. **Discord embed** → `notify.test_ai` (custom integration, routage par channel_id)
3. **Doublon #urgent** Discord si severity=critical

## Workflow de diagnostic

### 1. Lister tous les notify services disponibles

```bash
ha_list_services(domain="notify")
```

Retourne tous les services notify enregistrés. Attention : certains sont des **entity-based** (ntfy, mobile_app) et d'autres des **platform-based** (test_ai, jtower) sans entité dédiée.

### 2. Vérifier l'état des entités notify

```bash
ha_search(query="notify.", limit=50)
```

⚠️ **Piège ntfy :** les entités `notify.xxx` de l'intégration ntfy sont TOUJOURS en état `unknown` — c'est normal. Le vrai statut se lit sur les entités `event.xxx` jumelles :

```bash
ha_get_state(entity_id="event.crowdsec")
# → state=unknown  → le topic ne reçoit rien
# → state=2026-07-05T...  → timestamp = le topic fonctionne
```

### 3. Vérifier le serveur ntfy

```bash
ha_get_state(entity_id="sensor.ntfy_statut")
# → up | down

# Tous les sensors ntfy
ha_search(query="ntfy", limit=50)
```

Sensors clés : `ntfy_statut`, `ntfy_temps_de_reponse`, `ntfy_jefe_ovh_reserved_topics_remaining`.

### 4. Inspecter le script notification_central

```bash
ha_config_get_script(script_id="notification_central")
```

C'est là que sont configurés tous les targets de notification. Vérifier les actions :
- `notify.mobile_app_iphone_du_zef` — push iOS
- `notify.test_ai` — Discord (entity-less custom integration)
- `notify.xxx` — ntfy topics (si ajoutés)

**Piège chaîne :** une automation peut appeler `script.notification_central` sans mentionner directement le notify. Le notify cassé est dans le script, pas dans l'automation. Toujours suivre la chaîne.

### 5. Inspecter les automatisations qui utilisent notify

```bash
# Trouver toutes les automations référençant un notify
ha_search(query="notify.", limit=50)
# → résultat avec entities[], automations[], scripts[]

# Config détaillée d'une automation
ha_config_get_automation(identifier="automation.webhook_notification_centrale")
# → voir l'action qui appelle script.notification_central

# Config détaillée d'un script
ha_config_get_script(script_id="notification_central")
```

### 6. Vérifier l'état des updates (souvent lié aux notifs)

```bash
ha_search(query="unavailable", limit=100)
# Filtre les update.* avec state=unavailable
```

Un `update.xxx` avec `restored: true` signifie que l'intégration n'est plus active mais les entités persistent.

## Outils MCP existants sur ce serveur

### ✅ Existent
| Outil | Usage |
|-------|-------|
| `ha_get_overview` | Stats : domaines, entités, états |
| `ha_get_state` | État détaillé d'une entité |
| `ha_search(query=..., limit=...)` | Recherche dans entities + automations + scripts |
| `ha_get_device(entity_id=...)` | Infos device d'une entité |
| `ha_list_services(domain=...)` | Services disponibles |
| `ha_config_get_automation(identifier=...)` | Config automation |
| `ha_config_set_automation(identifier=..., config=..., config_hash=...)` | Update automation |
| `ha_config_remove_automation(identifier=...)` | Delete automation |
| `ha_config_get_script(script_id=...)` | Config script |
| `ha_config_set_script(script_id=..., config=..., config_hash=...)` | Update script |
| `ha_call_service(domain=..., service=..., data=...)` | Appel service |
| `ha_config_get_dashboard(url_path=...)` | Dashboard config |
| `ha_config_set_dashboard(url_path=..., config=...)` | Dashboard create/edit |
| `ha_config_delete_dashboard(url_path=...)` | Delete dashboard |
| `ha_config_list_dashboard_resources` | Resources Lovelace |
| `ha_eval_template(template=...)` | Test templates Jinja2 |
| `ha_get_zone` | Zones géographiques |
| `ha_remove_zone(zone_id=...)` | Delete zone |

### ❌ N'EXISTENT PAS (pièges)
Ces noms d'outils ne marchent pas sur ce serveur MCP :
- `ha_get_system_log` / `ha_get_log` — pas de log MCP
- `ha_get_persistent_notifications` / `ha_get_notifications`
- `ha_get_config` / `ha_config_get_config`
- `ha_get_states` / `ha_list_config_entries`
- `ha_get_health`
- `ha_get_updates`
- `ha_search_entities` (utiliser `ha_search` à la place)
- `ha_deep_search`
- `list_tools`

## Indicateurs de notify cassé

| Symptôme | Cause probable |
|----------|---------------|
| `notify.xxx` = `unknown` avec `event.xxx` = timestamp | Normal (ntfy fonctionne) |
| `notify.xxx` = `unknown` ET `event.xxx` = `unknown` | Topic ntfy mort |
| `notify.mobile_app_*` = timestamp | ✅ Fonctionne |
| Service notify existe mais pas d'entité | Platform-based (test_ai, jtower) |
| Automation trace error "action inconnue" | Nom de notify a changé |

## Référence : les notify services de cette instance

| Service | Type | État |
|---------|------|------|
| `notify.mobile_app_iphone_du_zef` | Entity (mobile_app) | ✅ Actif |
| `notify.mobile_app_sm_a556e` | Entity (mobile_app) | ✅ Actif |
| `notify.test_ai` | Platform (custom) | Service registered |
| `notify.jtower` | Platform (custom) | Service registered |
| `notify.signal` | Service (integration) | Service registered |
| `notify.persistent_notification` | Service (built-in) | ✅ |
| `notify.xxx` (beszel, crowdsec, headscale, n8n, paperless, qbit, radarr, seerr, sonarr, urgent) | Entity (ntfy) | Voir event.xxx |

## Résolution courante

- **Notify renommé** (iPhone renommé dans iOS) → `ha_search(query="ancien_nom")` → patch automations + scripts
- **ntfy topic mort** → Vérifier le service qui push vers ce topic (Docker container down, config changée)
- **test_ai (Discord) mort** → Token Discord expiré, impossible à vérifier via MCP (entity-less)
- **Beszel Hub down** → `update.beszel_hub_update` with `restored: true` → restart le conteneur Beszel Hub
