# HA Metrics Dashboard Pattern — External Data → HA Helpers → Dashboard

Pattern for pushing metrics from an external system (Hermes container, scripts, etc.)
into Home Assistant for live dashboard display. Used for Voxtral/LiteLLM token tracking.

## Architecture

```
External script → JSON file → Cron agent → ha_call_service(input_number.set_value) → HA dashboard
```

## Steps

### 1. Create input_number helpers

Use `ha_config_set_helper(helper_type="input_number", ...)` with:
- `min_value`, `max_value`, `step`, `unit_of_measurement`
- `icon` (MDI icon)
- `name` (friendly name)

Requires `BestPracticeKey` on first call (see dashboard-guide). Use `MandatoryBPS=false`
on subsequent calls in the same session.

### 2. Write a metrics exporter script

Python script that:
- Reads data from source (JSON file, API, etc.)
- Aggregates into a flat dict of numbers
- Writes to a JSON file for the cron to read

### 3. Create a cron job to push values

`*/5 * * * *` — agent-driven, silent (no user notification on success).

The cron prompt should:
1. Run the exporter script
2. Parse the JSON output
3. Call `ha_call_service("input_number", "set_value", entity_id="...", data={"value": N})`
   for each metric
4. Be SILENT — do not send any message to the user

### 4. Create the dashboard

Use `ha_config_set_dashboard` with `sections` view type.

**Gauge card** — colored severity zones:

```json
{
  "type": "gauge",
  "entity": "input_number.my_metric",
  "min": 0,
  "max": 100,
  "unit": "%",
  "severity": {
    "green": 0,
    "yellow": 70,
    "red": 90
  }
}
```

**Tile card** — compact metric display:

```json
{
  "type": "tile",
  "entity": "input_number.my_metric",
  "name": "My Metric",
  "icon": "mdi:counter",
  "grid_options": {"columns": 4}
}
```

**History graph** — colored per-entity lines (24h):

```json
{
  "type": "history-graph",
  "entities": [
    {"entity": "input_number.metric_a", "name": "A", "color": "#7e57c2"},
    {"entity": "input_number.metric_b", "name": "B", "color": "#26c6da"}
  ],
  "hours_to_show": 24,
  "grid_options": {"columns": "full", "rows": 4}
}
```

**Markdown card** — computed values via Jinja2:

```json
{
  "type": "markdown",
  "content": "**Restant:** {{ 100 - (states('input_number.my_metric') | float(0)) | round(1) }}%"
}
```

### Layout tips

- Use `column_span: 2` on sections for two-column desktop layout
- `max_columns: 4` on the view for responsive grid
- Give graph cards `"columns": "full"` + fixed `"rows"` so they don't get squeezed
- Group related metrics in the same section with a `heading` card

## BestPracticeKey workflow

1. `ha_get_skill_guide(skill='home-assistant-best-practices')` → get the key
2. Pass as `BestPracticeKey` on `ha_config_set_helper` and `ha_config_set_dashboard`
3. The key rotates hourly — re-read if session spans multiple hours
4. `MandatoryBPS=false` skips the skill content on subsequent calls