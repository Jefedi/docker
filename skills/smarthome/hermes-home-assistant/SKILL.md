---
name: hermes-home-assistant
description: "Connecter Hermes Agent à Home Assistant — trois méthodes d'intégration pour des notifications intelligentes et du contrôle bidirectionnel."
author: Hermes Agent
created_by: agent
tags: [home-assistant, hermes, integration, notifications, webhook, gateway, cron, automation]
---

# Hermes ↔ Home Assistant Integration

Trois méthodes pour connecter HA à Hermes, par ordre de sophistication.

## Méthodes

### 0. MCP HA Tools (recommandé pour l'interaction directe)

Via le serveur MCP `ha-mcp`, Hermes accède à l'ensemble de l'API HA : états, services, automatisations, helpers, dashboards, notifications, intégrations. Pas de gateway, pas de webhook, pas de token LLM pour les events entrants. **Idéal pour les actions ponctuelles** (allumer une lumière, créer un rappel, créer une automatisation, diagnostiquer un problème).

**Setup :** Configurer `ha-mcp` dans `config.yaml` du profil. Le serveur MCP se connecte à HA via WebSocket/REST.

**Cas d'usage typiques :**
- Contrôle (lumière, climat, switch) : `ha_call_service(domain="light", service="turn_on")`
- Todo/rappel : `ha_call_service(domain="todo", service="add_item", entity_id="todo.rappel")`
- Création automations : `ha_config_set_automation(config={...})`
- Calendrier : `ha_call_service(domain="calendar", service="create_event")`
- Diagnostics : `ha_get_state()`, `ha_search()`, `ha_get_automation_traces()`

**Interfaçage notifications iOS actionnables :** voir le skill `ios-shortcuts-integration`, section B.

- **Rappels programmés (todo + notifications push) :** voir `references/reminder-automation-patterns.md` — deux approches pour créer un système de rappels centralisé avec `due_datetime` sur les items todo, sans multiplier les automations. Charger ce fichier quand l'utilisateur demande « rappelle-moi de X [date/heure] ».
- **Pipeline Assist avec Mistral + LiteLLM (STT + TTS + Conversation) :** voir `references/ha-mistralai-integration.md` — **solution recommandée** via l'intégration `HA_MistralAI` (SnarfNL/HA_MistralAI, HACS) qui gère STT Voxtral + TTS Mistral + Conversation nativement. Remplace les integrations séparées `openai_stt` + `openai_tts` (qui souffraient de problèmes de YAML ignoré, voix non configurable, entry non persistée). Architecture : STT/TTS via API Mistral directe, conversation via LiteLLM (glm-5.2). Voir aussi `references/ha-assist-pipeline-litellm.md` pour l'ancienne approche (openai_stt + openai_tts) et ses pièges détaillés.

### 1. Gateway Adapter (bidirectionnel, recommandé pour événements entrants)

Le Gateway Hermes inclut une plateforme Home Assistant qui se connecte à HA via WebSocket. HA envoie les changements d'état en temps réel → Hermes analyse → répond sur Telegram (ou autre plateforme connectée) ou via notification persistante HA.

**Setup :**

**1. Créer un Long-Lived Access Token** dans HA (Profil → Jetons d'accès longue durée)

**2. Ajouter dans `~/.hermes/.env` :**
```bash
HASS_TOKEN=votre-token-jwt
HASS_URL=http://supervisor/core    # ou http://homeassistant.local:8123
```
Le toolset `homeassistant` (4 outils : `ha_list_entities`, `ha_get_state`, `ha_list_services`, `ha_call_service`) s'active automatiquement quand `HASS_TOKEN` est présent.

**3. Configurer les événements dans `config.yaml` :**
```yaml
platforms:
  homeassistant:
    enabled: true
    extra:
      watch_domains:          # Domaines à surveiller
        - binary_sensor
        - climate
        - sensor
        - alarm_control_panel
        - lock
        - event
      ignore_entities:        # Entités bruyantes à ignorer
        - sensor.uptime
        - sensor.cpu_usage
        - sensor.memory_usage
      cooldown_seconds: 30    # Cooldown entre 2 events pour une même entité
```
⚠️ **Par défaut, aucun événement n'est forwardé** — au moins `watch_domains`, `watch_entities` ou `watch_all: true` est requis.

**4. Redémarrer le gateway :**
```bash
hermes gateway restart
```

**Event formatting automatique :**

| Domaine | Format |
|---|---|
| `climate` | "HVAC mode changed from 'off' to 'heat' (current: 21, target: 23)" |
| `sensor` | "changed from 21°C to 22°C" |
| `binary_sensor` | "triggered" / "cleared" |
| `light`, `switch`, `fan` | "turned on" / "turned off" |
| `alarm_control_panel` | "alarm state changed from 'armed_away' to 'triggered'" |

**Exemple concret :** porte d'entrée s'ouvre → Hermes reçoit l'event, analyse l'heure, vérifie l'alarme, et peut t'alerter intelligemment sur Telegram.

**Domaines bloqués (sécurité) :** `shell_command`, `command_line`, `python_script`, `pyscript`, `hassio`, `rest_command`

**Avantages :** temps réel, bidirectionnel, réponse IA contextualisée, zéro automation HA nécessaire

### 2. Webhook (unidirectionnel, HA → Hermes)

`hermes webhook subscribe` crée un endpoint HTTP. HA POST un payload, Hermes exécute.

**Avantages :** simple, pas besoin de restart gateway
**Inconvénients :** unidirectionnel, URL accessible depuis HA

### 3. Cron Hermes (Hermes scrute HA)

`hermes cron create "every 15m" --skills home-assistant-mcp --prompt "Analyse ma domotique..."`

**Avantages :** zéro config HA, diagnostics complexes
**Inconvénients :** pas temps réel, consommation tokens

## Comparatif

| Critère | Gateway | Webhook | Cron |
|---------|:-------:|:-------:|:----:|
| Temps réel | ✅ | ✅ | ❌ |
| Bidirectionnel | ✅ | ❌ | ✅ |
| Config HA | Webhook auto | rest_command | Aucune |
| Tokens LLM | Sur événement | Sur événement | Chaque tick |

## Bonnes pratiques

- Donner du **contexte dans le message** pour une meilleure réponse
- Utiliser des `input_text` helpers pour passer des données structurées
- Mettre des **cooldowns** (`for:` en trigger HA) pour éviter le spam
- Scénariser par type d'événement (alarme, fuite, batterie, température)
- **Événements de monitoring :** voir `references/monitoring-event-handling.md` — distinguer un glitch de monitoring d'une vraie panne, réponse minimale aux variations normales, réponse synthétique aux pannes de monitoring.
- **Sync calendrier/tâches CalDAV (Radicale) :** voir `references/caldav-sync.md` — architecture multi-appareils iOS ↔ Radicale ↔ HA ↔ n8n, sync bidirectionnelle des todo entities HA avec des VTODOs CalDAV, webhook iOS Shortcuts pour ajouter des events.
