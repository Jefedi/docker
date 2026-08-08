# Repo Reconnaissance — Real Example

## Target: `jlpouffier/home-assistant-config`

A 57-star HA config repo. The user asked for a detailed topo of what's inside.

### Step 1: Overview

```python
web_extract(urls=["https://github.com/jlpouffier/home-assistant-config"])
```

Result: README (2 lines), file tree (top level), 57 stars, 14 forks, 934 commits,
default branch `master`, HA version 2026.3.2. Last commit 4 months ago by Claude.

Then fetched `README.md` and `configuration.yaml` — found that the config uses
`packages: !include_dir_named packages` (modular approach) and
`themes: !include_dir_merge_named themes`.

### Step 2: Enumerate packages directory

`web_extract` hit Firecrawl rate limit after ~10 calls. Switched to curl + GitHub API:

```bash
for pkg in chaban_delmas_bridge chores heating weather networking update logs data_persistency workday music_assistant; do
  echo "=== $pkg ==="
  curl -s "https://api.github.com/repos/jlpouffier/home-assistant-config/contents/packages/$pkg" \
    | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f['name']) for f in data] if isinstance(data, list) else print(data.get('message','err'))" 2>/dev/null
done
```

This revealed all 18 package files in a single terminal call.

### Step 3: Bulk fetch raw files

15+ files fetched in a single terminal call (30s timeout):

```bash
for f in "packages/chaban_delmas_bridge/rest_integration.yaml" \
         "packages/cars/tesla/tessie.yaml" \
         "packages/chores/binary_sensor_chores.yaml" \
         "packages/heating/time_tracking.yaml" \
         "packages/weather/next_rain.yaml" \
         "packages/networking/http.yaml" \
         "packages/update/sensor_pending_updates.yaml" \
         "packages/home_occupancy/binary_sensor_home_occupied.yaml" \
         "packages/air_conditionning/koolnova.yaml" \
         "packages/air_quality/sensor_unified_air_quality_sensors.yaml" \
         "packages/battery/low_batteries.yaml" \
         "packages/doors/binary_sensor_is_front_door_recently_open.yaml" \
         "packages/appliances/washing_machine/binary_sensor_is_washing_machine_running.yaml" \
         "packages/music_assistant/fetch_playlist_tracks.yaml" \
         "packages/workday/today.yaml" \
         "packages/workday/tomorrow.yaml" \
         "packages/logs/logger.yaml" \
         "packages/data_persistency/recorder.yaml"; do
  echo "========== $f =========="
  curl -s "https://raw.githubusercontent.com/jlpouffier/home-assistant-config/master/$f"
  echo
done
```

### Step 4: ESPHome files

Fetched ESPHome configs separately (they needed `head` for truncation):

```bash
echo "=== esphome/climatisation-mitsubishi.yaml ==="
curl -s "https://raw.githubusercontent.com/jlpouffier/home-assistant-config/master/esphome/climatisation-mitsubishi.yaml" | head -100
echo "=== esphome/washing-machine-companion.yaml ==="
curl -s "https://raw.githubusercontent.com/jlpouffier/home-assistant-config/master/esphome/washing-machine-companion.yaml" | head -80
# ... etc
```

### Analysis Structure

The final topo was organized as:
1. **L'auteur** — inferred from username + repo content (Bordeaux area, French config)
2. **Packages** — grouped by category (confort, électroménager, maison, extérieur, infra)
3. **Automations** — extracted from `automations.yaml` (head -300 for first batch)
4. **ESPHome** — 5 devices with their purpose
5. **Themes, templates, blueprints** — brief mention
6. **Ce qui ressort** — synthesis: maturity, quality of life focus, ecosystem integration

### Key Observations from This Repo

- **Modbus TCP native** for AC (KoolNova) — no custom integration, uses HA's built-in modbus
- **Open data integration** — Bordeaux Métropole API for bridge closures, Météo-France for rain
- **Template sensors with triggers** — modern HA pattern using `trigger: state` + `actions: variables`
- **ESPHome custom devices** — washing machine companion with touchscreen, standing desk UART reader
- **`!secret` pattern** — all secrets externalized, expected practice
- **Claude Code commits** — author uses Claude Code for maintenance (commit messages reference Claude sessions)
- **Disabled files** — `clio.yaml.disabled` shows a car integration that was deactivated