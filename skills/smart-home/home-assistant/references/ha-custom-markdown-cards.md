# Custom Markdown Dashboard Cards — Pattern Fiable

## Quand utiliser ce pattern

Quand une custom card (clock-weather-card, mushroom, etc.) :
- ne rend pas correctement (page blanche, carte invisible)
- dépend d'une installation HACS fragile
- ne s'affiche pas après une mise à jour HA

→ La remplacer par une **carte markdown native** avec templates Jinja2. 100% fiable, zéro dépendance.

## Structure du pattern

```yaml
type: markdown
content: |
  {% set val = states('sensor.xxx') | float(0) %}
  {% set pct = (val / max * 100) | round(1) %}
  ## 📊 Titre

  `{{ '█' * blocks }}{{ '░' * (20 - blocks) }}` **{{ pct }} %**

  | | |
  |---|---|
  | Label | {{ val }} unit |
```

## Exemples concrets

### Carte Storage Box (données Hetzner)

```jinja2
{% set total = states('sensor.storage_box_borg_ax42_total_size') | float(0) %}
{% set used = states('sensor.storage_box_borg_ax42_total_used') | float(0) %}
{% set pct = (used / total * 100) | round(1) if total > 0 else 0 %}
{% set blocks = ((pct / 100 * 20) | round(0, 'floor')) | int %}
{% macro fmt(mb) -%}
  {%- if mb >= 1048576 -%}{{ (mb / 1048576) | round(2) }} TB
  {%- elif mb >= 1024 -%}{{ (mb / 1024) | round(1) }} GB
  {%- else -%}{{ mb | round(0) }} MB{%- endif -%}
{%- endmacro %}
## 💾 Hetzner Storage Box

🟢 **Active** · 📍 FSN1 · borg-ax42

`{{ '█' * blocks }}{{ '░' * (20 - blocks) }}` **{{ pct }} %**

**{{ fmt(used) }}** utilisés sur **{{ fmt(total) }}**
```

### Carte Météo (remplace clock-weather-card)

```jinja2
{% set w = 'weather.le_havre' %}
{% set cond = states(w) %}
{% set temp = state_attr(w, 'temperature') %}
{% set hum = state_attr(w, 'humidity') %}
{% set press = state_attr(w, 'pressure') %}
{% set wind = state_attr(w, 'wind_speed') %}
{% set gust = state_attr(w, 'wind_gust_speed') %}
{% set bearing = state_attr(w, 'wind_bearing') | int(0) %}
{% set dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'] %}
{% set idx = ((bearing + 11.25) / 22.5) | int %}
{% set dir = dirs[idx % 16] %}
{% set icon_map = {'sunny': '☀️', 'clear-night': '🌙', 'partlycloudy': '⛅', 'cloudy': '☁️', 'rainy': '🌧️', 'pouring': '⛈️', 'snowy': '❄️', 'fog': '🌫️'} %}
{% set label_map = {'sunny': 'Ensoleillé', 'partlycloudy': 'Partiellement nuageux', 'cloudy': 'Nuageux', 'rainy': 'Pluvieux'} %}
## {{ icon_map.get(cond, '🌡️') }} {{ label_map.get(cond, cond) }} — {{ temp }}°C

**Le Havre** · Météo-France

| | |
|---|---|
| 💧 Humidité | {{ hum }} % |
| 📐 Pression | {{ press }} hPa |
| 🌬️ Vent | {{ wind }} km/h {{ dir }} |
| 💨 Rafales | {{ gust }} km/h |
```

## Piège : `weather.*.forecast` est null en template

```jinja2
{% set f = state_attr('weather.le_havre', 'forecast') %}
{{ f }}  → null !!
```

L'attribut `forecast` n'est **pas accessible** via `state_attr()` en Jinja2. Les prévisions ne sont disponibles que via :
- La carte native `weather-forecast` (rendu UI uniquement)
- Le service `weather.get_forecast` (appel de service, pas template)
- L'entité `weather.forecast_*` (si créée par l'intégration)

**Conséquence** : une carte markdown météo ne peut afficher que les **conditions actuelles** (température, humidité, vent, pression), pas les prévisions. Pour les prévisions dans une carte markdown, il faudrait un template sensor qui appelle `weather.get_forecast` et stocke le résultat.

## Piège : direction du vent en Jinja2

Le calcul de la direction cardinale depuis le bearing (degrés) :

```jinja2
{% set dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'] %}
{% set idx = ((bearing + 11.25) / 22.5) | int %}
{% set dir = dirs[idx % 16] %}
```

Ne PAS utiliser un dictionnaire avec `bearing // 22 * 22` comme clé — les valeurs comme 350° donnent 342 qui n'est pas dans le dict. L'approche par index de liste avec `+ 11.25` est correcte.

## Intégration dans un swipe-card

La carte markdown se combine bien avec `simple-swipe-card` pour garder le swipe entre plusieurs cartes :

```yaml
type: custom:simple-swipe-card
cards:
  - type: markdown
    content: "...template météo..."
  - type: custom:marees-france-card
    device_id: xxx
    show_header: true
    card_type: full
```

## Workflow A/B sur dashboard

L'utilisateur aime voir les variantes directement sur HA pour comparer :

1. Ajouter les deux variantes côte à côte (sections séparées avec heading "Option A" / "Option B")
2. L'utilisateur regarde sur HA et choisit
3. Supprimer la variante non retenue via `python_transform`
4. Renommer le heading de la variante retenue

## Custom JS Cards — vraies custom cards Lovelace (alternative fiable)

### Quand utiliser

- `button-card` avec templates JS `[[[ ... ]]]` → `ButtonCardJSTemplateError` (transport MCP corrompt les backticks/`${}`)
- `clock-weather-card` → page blanche ou invisible après mise à jour HA
- Besoin d'un design premium (jauge SVG, gros chiffres, badges) que le markdown ne peut pas faire

### Workflow

1. Écrire le fichier JS (`HTMLElement` + Shadow DOM + `customElements.define`)
2. Enregistrer comme ressource inline : `ha_config_set_dashboard_resource(content=..., resource_type="module")` (max ~24KB)
3. Utiliser dans le dashboard : `type: custom:nom-de-la-card`
4. L'utilisateur fait un **hard refresh** (Ctrl+Shift+R) pour charger le module

### Structure d'une custom card JS

```javascript
class MyCard extends HTMLElement {
  setConfig(config) { this._config = { defaults, ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 5; }
  _render() {
    if (!this._hass || !this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>...</style><div>...</div>`;
  }
}
customElements.define("my-card", MyCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "my-card", name: "My Card", description: "..." });
```

### Prévisions météo en JS — `weather/subscribe_forecast`

```javascript
async _subscribeForecast() {
  await this._hass.connection.subscribeMessage(
    (msg) => { this._forecast = msg.forecast; this._render(); },
    { type: "weather/subscribe_forecast", entity_id: this._config.entity, forecast_type: "daily" }
  );
}
// Fallback : this._hass.states[entity]?.attributes?.forecast
```

### Piège : `button-card` JS templates via MCP

Les templates `[[[ ]]]` de `custom:button-card` dans `custom_fields` peuvent mal passer le transport MCP (JSON → HA storage). Les backticks, `${}`, et escapes Unicode peuvent être corrompus, causant `ButtonCardJSTemplateError`. **Solution :** créer une vraie custom card JS dédiée au lieu d'utiliser button-card avec des templates JS complexes.

### Formatage des unités en JS

```javascript
const fmt = (mb) =>
  mb >= 1048576 ? (mb / 1048576).toLocaleString("fr-FR", { maximumFractionDigits: 2 }) + " TB"
  : mb >= 1024 ? (mb / 1024).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " GB"
  : Math.round(mb) + " MB";
```

### Clic → more-info

```javascript
this.shadowRoot.querySelector(".card").onclick = () =>
  this.dispatchEvent(new CustomEvent("hass-more-info", {
    detail: { entityId: this._config.entity }, bubbles: true, composed: true,
  }));
```

## Theme-aware CSS — utiliser les variables HA

Pour que les custom cards JS s'adaptent au thème HA de l'utilisateur (ex: Graphite, Nordic Blue Dark), **ne jamais coder des couleurs en dur**. Utiliser les variables CSS HA :

```css
.card {
  background: var(--card-background-color, rgba(30, 35, 45, 0.55));
  color: var(--primary-text-color, #e7e9ee);
  border: 1px solid var(--divider-color, rgba(255,255,255,0.12));
  border-radius: var(--ha-card-border-radius, 24px);
  box-shadow: var(--ha-card-box-shadow, 0 8px 32px rgba(0,0,0,0.37));
}
.muted { color: var(--secondary-text-color, #7d8390); }
```

Variables CSS HA clés pour les cartes :

| Variable | Usage |
|----------|-------|
| `--card-background-color` | Fond de carte |
| `--primary-text-color` | Texte principal |
| `--secondary-text-color` | Texte secondaire/labels |
| `--divider-color` | Bordures, séparateurs |
| `--primary-color` | Accent (jauge, barres) |
| `--ha-card-border-radius` | Rayon des coins |
| `--ha-card-box-shadow` | Ombre |
| `--secondary-background-color` | Fond des badges/tuiles |
| `--info-color` / `--warning-color` | Barres de température |

## Animations sur custom cards JS — **RETIRÉES sur préférence utilisateur**

L'utilisateur a d'abord accepté des animations (float-in, float-icon, pulse-glow), puis a **explicitement demandé de les retirer** (session 2026-07-24). Les cartes `hetzner-storage-card` et `meteo-premium-card` sur `maison-dashboard` sont maintenant **sans aucune animation**.

**Règle :** ne PAS ajouter d'animations (float, pulse, glow, hover transforms) sur les custom cards JS sans demander. L'utilisateur préfère le rendu statique. Le glassmorphism (backdrop-filter, box-shadow) reste, mais pas le mouvement.

### CSS animation-free (version actuelle déployée)

```css
.card {
  /* glassmorphism OK, mais PAS d'animation ou transition */
  backdrop-filter: blur(16px) saturate(180%);
  background: var(--card-background-color, rgba(30, 35, 45, 0.55));
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37), inset 0 1px 1px rgba(255, 255, 255, 0.1);
  /* PAS de :hover transform, PAS de @keyframes, PAS de animation: */
}
```

### Pour retirer des animations d'une resource existante

Workflow : `ha_config_list_dashboard_resources(include_content=True)` → identifier la resource par son ID → `ha_config_set_dashboard_resource(resource_id=..., content=..., resource_type="module")` avec la version sans animations. Hard refresh requis après.

## Piège : encodage UTF-8 dans les custom cards JS

Les caractères accentués (é, è, °, ç) codés en dur dans le JS d'une custom card s'affichent mal (mojibake) quand le module est enregistré via `ha_config_set_dashboard_resource`. **Solution :** utiliser des escapes Unicode dans tout le JS :

```javascript
// MAL — affiche "HumiditÃ©" et "24Â°C"
const label = "Humidité";
const temp = a.temperature + "°C";

// BIEN — affiche correctement
const label = "Humidit\u00E9";
const temp = a.temperature + "\u00B0C";
```

Table des escapes les plus courants :

| Caractère | Escape |
|-----------|--------|
| é | `\u00E9` |
| è | `\u00E8` |
| ê | `\u00EA` |
| à | `\u00E0` |
| ç | `\u00E7` |
| ° | `\u00B0` |
| · | `\u00B7` |
| — | `\u2014` |
| ✓ | `\u2713` |
| 🔑 | `\uD83D\uDD11` |
| 💾 | `\uD83D\uDCBE` |
| ☀️ | `\u2600\uFE0F` |
| ⛅ | `\u26C5` |
| ☁️ | `\u2601\uFE0F` |

## Workflow : dashboard de test pour comparer des cartes

L'utilisateur aime voir les variantes directement sur HA. Pattern éprouvé :

1. Créer un dashboard séparé `test-dashboard` (url_path avec tiret obligatoire)
2. Mettre les variantes côte à côte (sections avec `column_span: 1`)
3. L'utilisateur regarde sur HA et choisit
4. Appliquer la variante retenue sur le dashboard principal
5. Supprimer ou garder le dashboard de test pour itérations futures

```python
ha_config_set_dashboard(
    url_path="test-dashboard",
    title="Test",
    icon="mdi:flask",
    config={"views": [{"type": "sections", "title": "Test Cards", ...}]}
)
```

## Bubble Card (HACS) — pattern alternatif préféré

L'utilisateur préfère Bubble Card (github.com/Clooos/Bubble-Card, 4.4k ⭐) pour le rendu "flottant". Déjà installé en v3.2.5.

### Types : `button` (recommandé), `cover` (pour covers/vlets), `pop-up` (flottant), `horizontal-buttons-stack` (rangée)

### Sub_buttons — afficher attributs d'entité

```yaml
type: custom:bubble-card
card_type: button
entity: weather.le_havre
name: Le Havre
icon: mdi:weather-partly-cloudy
show_state: true
sub_button:
  - name: Temp
    entity: weather.le_havre
    attribute: temperature
    show_state: true
    show_icon: true
    icon: mdi:thermometer
```

### Piège : `card_type: cover` sur entité non-cover → texte répété, valeurs brutes. Utiliser `button` à la place.

## Thèmes HACS — installation via MCP

```python
ha_get_hacs_info(action="search", category="theme", query="frosted glass")  # → repository_id
ha_manage_hacs(action="download", repository_id="NUMERIC_ID")  # PAS "owner/repo"
```

### Appliquer un thème par vue : `'theme': 'Frosted Glass Dark'` dans la config de la vue.

### Piège : `repository_id` est numérique, pas "owner/repo". Confondre installe le mauvais dépôt.

## card-mod glassmorphism sur cartes natives

Injection CSS via `card_mod` sur cartes natives (entities, gauge, markdown). **Note : utilisateur a rejeté cette approche** ("moche") vs Bubble Card.

## Préférence utilisateur (session 2026-07-22)

1. **Bubble Card** — préféré, rendu flottant
2. ~~card-mod glassmorphism~~ — rejeté
3. ~~Custom JS cards~~ — fonctionne mais "ne flotte pas assez"
4. **Markdown natif** — fiable, utilisé sur dashboard principal

Dashboard de test (`test-dashboard`) pour expérimenter avant d'appliquer sur `maison-dashboard`.

## Validation des templates

Toujours tester le template avec `ha_eval_template` avant de l'intégrer dans une carte markdown :

```
ha_eval_template(template="{% set w = 'weather.le_havre' %}{{ states(w) }}")
→ "sunny"
```

Cela évite les cartes blanches si une entité n'existe pas ou si le template a une erreur de syntaxe.