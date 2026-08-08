---
name: home-assistant
description: >
  Home Assistant documentation expert and natural language control layer.
  Covers automations, scripts, templates, dashboards, configuration, energy,
  triggers, conditions, actions, voice control, installation, and all core
  domains (light, switch, climate, cover, media_player, vacuum, lock, etc.).
  Maps natural language requests to HA services and entities. Trigger words:
  home assistant, hass, ha, automatisation, lumière, volet, thermostat,
  aspirateur, scène, script, dashboard, trigger, condition, action, entity,
  sensor, switch, climate, cover, light, lock, vacuum, media player, alarm,
  automation, template, jinja, config.yaml.
---

# Home Assistant Skill

## Mental Model

Home Assistant is an open-source home automation platform that connects
devices and services via **integrations**. The core building blocks are:

- **Entities**: things you can control or monitor (lights, sensors, switches…)
- **Domains**: entity types (light, switch, climate, cover, sensor…)
- **Services**: actions you call on entities (light.turn_on, climate.set_temperature…)
- **Automations**: trigger → condition → action flows
- **Scripts**: reusable action sequences (no triggers)
- **Scenes**: snapshots of entity states to recall
- **Dashboards**: Lovelace UI with cards, views, sections
- **Helpers**: input_boolean, input_number, input_select, counter, timer, etc.

The **MCP tools** (ha_call_service, ha_search, ha_get_state, ha_get_overview,
ha_config_set_automation, etc.) are the primary interface for controlling HA
from Hermes. This skill provides the **knowledge layer**: what service to call,
what entity to target, how to structure automation YAML, and how to map natural
language to HA actions.

## Natural Language → HA Action Mapping

When the user asks something in natural language, resolve it to HA actions:

### Control requests

| User says (FR) | Domain.Service | Typical data |
|---|---|---|
| "allume/éteins la lumière [zone]" | light.turn_on / light.turn_off | entity_id or area_id |
| "ouvre/ferme les volets [zone]" | cover.open_cover / cover.close_cover | entity_id or area_id |
| "mets le chauffage à X°C" | climate.set_temperature | temperature, entity_id |
| "démarre/arrête l'aspirateur" | vacuum.start / vacuum.return_to_base | entity_id |
| "verrouille/déverrouille la porte" | lock.lock / lock.unlock | entity_id |
| "active la scène [nom]" | scene.turn_on | entity_id |
| "exécute le script [nom]" | script.turn_on | entity_id |
| "active/désactive l'alarme" | alarm_control_panel.alarm_arm_away / alarm_disarm | entity_id, code |
| "joue/pause/mets suivant" | media_player.media_play/pause/next | entity_id |
| "monte/baisse le volume" | media_player.volume_set | volume_level |
| "allume/éteins la prise" | switch.turn_on / switch.turn_off | entity_id |
| "mets le ventilateur à X%" | fan.set_percentage | percentage |
| "définit l'humidité à X%" | humidifier.set_humidity | humidity |
| "ajoute [item] à la liste" | todo.add_item | entity_id, summary |
| "crée un événement" | calendar.create_event | entity_id, summary, start, end |

### Query requests

| User says (FR) | Tool | What to do |
|---|---|---|
| "quelle est la température [zone]" | ha_get_state | Search sensor.temperature in area |
| "quels appareils sont hors ligne" | ha_get_overview | Filter unavailable entities |
| "que se passe-t-il" | ha_get_overview | Summary of active states |
| "historique de [entité]" | ha_get_history | entity_id + time range |
| "quelles automations existent" | ha_search | domain_filter=automation |
| "cherche [terme]" | ha_search | query=term |

### Entity resolution strategy

1. **Use `ha_search`** with the user's words as query. It searches entity names,
   aliases, and areas simultaneously.
2. If multiple matches, prefer the one in the mentioned area/zone.
3. If no match, try synonyms: "salon" → "living room", "séjour" → "living room".
4. For area-based commands, use `area_id` in the service target instead of
   individual entity_ids.
5. **Never guess entity IDs** — always search first.

## Routing Table

Load the reference file that matches the question domain. Always open the file
before answering.

| Question domain | Reference file(s) |
|---|---|
| Automation basics, triggers, conditions, actions | `docs__automation.markdown`, `docs__automation__basics.markdown` |
| Automation triggers (all types) | `docs__automation__trigger.markdown`, `triggers__state.markdown`, `triggers__time.markdown`, `triggers__numeric_state.markdown`, `triggers__sun.sunset.markdown` |
| Automation conditions | `docs__automation__condition.markdown` |
| Automation actions (services) | `docs__automation__action.markdown`, `docs__automation__services.markdown` |
| Automation modes (single, restart, queued, parallel) | `docs__automation__modes.markdown` |
| Automation YAML syntax | `docs__automation__yaml.markdown` |
| Automation troubleshooting | `docs__automation__troubleshooting.markdown` |
| Automation blueprints | `docs__automation__using_blueprints.markdown`, `docs__blueprint.markdown` |
| Scripts | `docs__scripts.markdown`, `docs__scripts__perform-actions.markdown`, `docs__scripts__conditions.markdown` |
| Scenes | `docs__scene.markdown`, `docs__scene__editor.markdown` |
| Templates / Jinja2 | `docs__templating__introduction.markdown`, `docs__templating__states.markdown`, `docs__templating__syntax.markdown` |
| Template patterns | `docs__templating__patterns.markdown`, `docs__templating__loops-and-conditions.markdown` |
| Template dates & times | `docs__templating__dates-and-times.markdown` |
| Template debugging | `docs__templating__debugging.markdown`, `docs__templating__errors.markdown` |
| Configuration (YAML, packages, secrets) | `docs__configuration.markdown`, `docs__configuration__yaml.markdown`, `docs__configuration__secrets.markdown` |
| Configuration: splitting, packages | `docs__configuration__splitting_configuration.markdown`, `docs__configuration__packages.markdown` |
| Entities & domains reference | `docs__configuration__entities_domains.markdown`, `docs__configuration__state_object.markdown` |
| Customizing devices | `docs__configuration__customizing-devices.markdown` |
| Events | `docs__configuration__events.markdown` |
| Organizing: areas, floors, labels, categories | `docs__organizing.markdown`, `docs__organizing__areas.markdown`, `docs__organizing__floors.markdown`, `docs__organizing__labels.markdown`, `docs__organizing__categories.markdown` |
| Energy dashboard | `docs__energy.markdown` + `docs__energy__*.markdown` |
| Dashboards (Lovelace) | `dashboards__*.markdown` (43 card types) |
| Dashboard cards reference | `more-info__*.markdown` (39 entity attribute docs) |
| Voice control / Assist | `voice__index.markdown`, `voice__custom_sentences.markdown`, `voice__aliases.markdown` |
| Authentication, MFA | `docs__authentication.markdown`, `docs__authentication__providers.markdown` |
| Installation | `installation__*.markdown` |
| Getting started | `getting-started__*.markdown` |
| Common tasks | `common-tasks__*.markdown` |
| FAQ | `faq__*.markdown` |
| Tools (dev tools, check config) | `docs__tools.markdown`, `docs__tools__dev-tools.markdown` |
| Troubleshooting | `docs__troubleshooting_general.markdown` |
| Z-Wave | `docs__z-wave__controllers.markdown` |
| **Specific service action** | `actions__<domain>.<service>.markdown` (e.g. `actions__light.turn_on.markdown`) |
| **Specific trigger** | `triggers__<domain>.<event>.markdown` (e.g. `triggers__light.turned_on.markdown`) |
| **Specific condition** | `conditions__<type>.markdown` (e.g. `conditions__state.markdown`) |
| **Jefe's field knowledge** | `00-gotchas-jefe.md` |

## Service Action Quick Reference

Core domains and their most common services:

| Domain | Key services |
|---|---|
| light | turn_on, turn_off, toggle |
| switch | turn_on, turn_off, toggle |
| climate | set_temperature, set_hvac_mode, set_fan_mode, set_preset_mode, toggle, turn_on, turn_off |
| cover | open_cover, close_cover, stop_cover, set_cover_position, set_cover_tilt_position, toggle |
| fan | turn_on, turn_off, toggle, set_percentage, set_preset_mode, oscillate |
| lock | lock, unlock, open |
| vacuum | start, pause, return_to_base, clean_spot, locate |
| media_player | play_media, media_play, media_pause, media_next, media_previous, volume_set, select_source |
| alarm_control_panel | alarm_arm_away, alarm_arm_home, alarm_arm_night, alarm_disarm, alarm_trigger |
| scene | turn_on |
| script | turn_on, turn_off, toggle |
| automation | turn_on, turn_off, toggle, trigger |
| input_boolean | turn_on, turn_off, toggle |
| input_number | set_value, increment, decrement |
| input_select | select_option, select_next, select_previous |
| input_text | set_value |
| input_datetime | set_datetime |
| timer | start, pause, cancel, change |
| counter | increment, decrement, reset, set_value |
| todo | add_item, remove_item, update_item |
| calendar | create_event, get_events |
| camera | snapshot, record, turn_on, turn_off |
| humidifier | set_humidity, set_mode, turn_on, turn_off |
| water_heater | set_temperature, set_operation_mode |
| homeassistant | restart, stop, reload_all, toggle, turn_on, turn_off, update_entity |
| group | set, remove, reload |
| button | press |

## Behavior Rules

1. **Always search before acting.** Use `ha_search` to find the correct
   entity_id. Never guess entity IDs from memory — names change.
2. **Prefer native constructs over templates** in automations/scripts. Use
   `condition: state` instead of `{{ is_state(...) }}`, `condition: numeric_state`
   instead of `{{ states('x') | float > N }}`, etc.
3. **Never restart HA without explicit user confirmation.**
4. **Open the reference file** before answering questions about configuration
   syntax, trigger types, condition types, or service data. Do not answer from
   memory about YAML structure or available options.
5. **Use `ha_eval_template`** to test Jinja2 templates before embedding them in
   automations. Catch syntax errors early.
6. **For natural language requests**: identify the intent (control vs query),
   search for matching entities, resolve the target, call the service. If
   ambiguous, ask the user.
7. **For area-based commands**: use `target: {area_id: "..."}` in service calls
   to affect all entities of the right domain in that area.

## Validation Questions

1. **Q: How do I turn on all lights in the living room?**
   A: Use `ha_search(query="living room", domain_filter="light")` to find
   entities, then call `light.turn_on` with `target: {area_id: "living_room"}`
   or with the specific entity_ids found.

2. **Q: What's the difference between `script.turn_on` and `automation.trigger`?**
   A: `script.turn_on` starts a script's action sequence. `automation.trigger`
   fires an automation as if its trigger fired — it evaluates conditions and
   runs actions only if conditions pass. A script has no conditions gate
   (unless you add them in the sequence).

3. **Q: Should I use `{{ states('sensor.temp') | float > 25 }}` or
   `condition: numeric_state` in an automation?**
   A: Always use `condition: numeric_state` with `entity_id` and `above: 25`.
   Native conditions are validated at config load and fail loudly. Template
   conditions fail silently at runtime and obscure intent.