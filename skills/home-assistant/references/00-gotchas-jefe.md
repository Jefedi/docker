# Home Assistant — Jefe's Field Knowledge

## Infrastructure

- HA OS sur jTower (Freebox v8). Docker network_mode:host pour Hermes.
- Add-ons installés: Music Assistant, Studio Code Server, Mosquitto, Tailscale, chrony, Matter Server, Mealie/Bonap, Pangolin CLI, Newt, Terminal & SSH, AirCast, ha-mcp.
- Dashboards: `maison-dashboard` (Bubble Card, thème Graphite, custom JS hetzner-storage-card + meteo-premium-card), `test-dashboard`.
- HACS installé avec Bubble Card, card-mod, mushroom, button-card, apexcharts-card, clock-weather-card, mini-media-player.

## Connexion Hermes ↔ HA

- Trois méthodes: MCP ha-mcp (primaire), API REST, Webhooks.
- Le serveur MCP `ha-mcp` tourne comme add-on HA (slug `81f33d0f_ha_mcp`).
- Outils MCP disponibles: ha_call_service, ha_get_state, ha_search, ha_get_overview, ha_config_set_automation, ha_config_set_script, ha_config_set_helper, ha_config_set_dashboard, ha_config_set_scene, ha_eval_template, ha_get_history, ha_get_logs, etc.

## Conventions

- Répondre en français pour les questions infra/HA/monitoring.
- HA monitoring: silence ABSOLU — pas de réponse, ni emoji, ni ack. Les vagues = Beszel intermittent.
- Rappels HA: script every 1min sur `todo.rappel`. Courses sur `todo.liste_dachats`.
- Apple TV Séjour: `media_player.sejour_sejour` + `remote.sejour_sejour`. Apps: Jellyfin/Spotify/Streamyfin.
- iOS Shortcut: POST /v1/responses. `todo.add_item` sur `todo.liste_dachats`.

## Entités clés

- Personnes: `person.jefe`, `person.alex` (device trackers: `sensor.jefe_place`, `sensor.alex_place`)
- Apple TV: `media_player.sejour_sejour`, `remote.sejour_sejour`
- Todo lists: `todo.liste_dachats` (courses), `todo.rappel` (rappels)
- Poubelles: `input_boolean.sortie_poubelle_noire`, `input_boolean.sortie_poubelle_jaune`
- Travail: `binary_sensor.capteur_de_journee_de_travail`
- F1: `binary_sensor.f1_race_week`
- Météo: `weather.le_havre`
- Marées: device `ceca8d024095fd74e984795093c3bc99` (card `marees-france-card`)
- Storage Box: `sensor.storage_box_borg_ax42` + capteurs suffixés

## Dashboard custom cards

- `hetzner-storage-card`: carte premium Storage Box Hetzner (borg-ax42). Resource inline JS.
- `meteo-premium-card`: carte météo avec prévisions. Resource inline JS.
- `marees-france-card`: carte marées (HACS community).
- `simple-swipe-card`: swipe entre météo et marées.
- Universal Remote Card (Nerwyn): télécommande Apple TV avec custom_actions Jellyfin/Spotify/Streamyfin.

## Gotchas

- **JAMAIS restart HA sans confirmation explicite**.
- **JAMAIS supprimer torrents** (règle générale).
- OIDC Pocket ID retiré du dashboard le 2026-07-22.
- Music Assistant: librespot bug `audio key 0 1` = Spotify change le protocole de clés audio, rollout par compte. Pas de fix définitif (issue #1649 librespot).
- zeroconf warnings sur interface Tailscale = normal si Tailscale tombe brièvement.
- HA 502 sur MA = restart HA ponctuel, auto-récupéré.
- `ha_config_set_automation` / `ha_config_set_script`: préférer les triggers/conditions/actions natifs aux templates Jinja dans les positions de logique. Templates OK seulement dans `data.*`, messages de notification, `event_data`, et `variables`.
- `ha_reload_core(target="all")` pour recharger après édition YAML sans restart complet.
- `ha_search` cherche simultanément dans le registry ET dans les configs (automations, scripts, scenes, helpers, dashboards).