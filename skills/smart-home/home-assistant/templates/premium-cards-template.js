/* Template : deux custom cards Lovelace premium (météo + storage)
   À adapter : entity IDs, couleurs, champs.
   Enregistrer via : ha_config_set_dashboard_resource(content=..., resource_type="module")
   Ou copier dans /config/www/ et enregistrer comme /local/xxx.js
*/

const CARD_CSS = `
  :host { display: block; }
  .card {
    background: linear-gradient(160deg, #171a22 0%, #12141b 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 24px;
    color: #e7e9ee;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    font-family: var(--primary-font-family, Roboto, system-ui, sans-serif);
    cursor: pointer;
  }
  .muted { color: #7d8390; }
  .row { display: flex; justify-content: space-between; align-items: center; }
`;

// Format MB → GB/TB lisible
const fmt = (mb) =>
  mb >= 1048576 ? (mb / 1048576).toLocaleString("fr-FR", { maximumFractionDigits: 2 }) + " TB"
  : mb >= 1024 ? (mb / 1024).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " GB"
  : Math.round(mb) + " MB";

/* ── Carte Storage avec jauge SVG circulaire ── */
class StorageCard extends HTMLElement {
  setConfig(config) { this._config = { prefix: "sensor.storage_box_borg_ax42", ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 5; }
  _st(suffix) {
    const id = suffix ? `${this._config.prefix}_${suffix}` : this._config.prefix;
    return this._hass.states[id]?.state;
  }
  _num(suffix) { return parseFloat(this._st(suffix)) || 0; }
  _render() {
    if (!this._hass || !this._config) return;
    const total = this._num("total_size"), used = this._num("total_used");
    const free = this._num("free_space"), data = this._num("data_size");
    const snap = this._num("snapshot_size");
    const pct = total ? (used / total) * 100 : 0;
    const circ = 2 * Math.PI * 54;
    const active = this._st() === "active";
    // ... render SVG circle, data rows, etc.
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${CARD_CSS}</style>
      <div class="card">...</div>`;
    this.shadowRoot.querySelector(".card").onclick = () =>
      this.dispatchEvent(new CustomEvent("hass-more-info", {
        detail: { entityId: this._config.prefix }, bubbles: true, composed: true,
      }));
  }
}
customElements.define("storage-card", StorageCard);

/* ── Carte Météo avec prévisions (subscribe_forecast) ── */
const WICONS = { sunny: "☀️", "clear-night": "🌙", cloudy: "☁️", partlycloudy: "⛅", rainy: "🌧️" };
const WLABELS = { sunny: "Ensoleillé", "clear-night": "Nuit claire", cloudy: "Nuageux", partlycloudy: "Partiellement nuageux" };

class MeteoCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("entity requis");
    this._config = { forecast_days: 3, ...config };
  }
  set hass(hass) { this._hass = hass; this._subscribeForecast(); this._render(); }
  getCardSize() { return 5; }
  async _subscribeForecast() {
    if (this._sub || !this._hass) return;
    this._sub = true;
    try {
      await this._hass.connection.subscribeMessage(
        (msg) => { this._forecast = msg.forecast; this._render(); },
        { type: "weather/subscribe_forecast", entity_id: this._config.entity, forecast_type: "daily" }
      );
    } catch (e) {
      this._forecast = this._hass.states[this._config.entity]?.attributes?.forecast;
    }
  }
  _render() {
    if (!this._hass || !this._config) return;
    const ent = this._hass.states[this._config.entity];
    if (!ent) return;
    const a = ent.attributes;
    const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSO","SO","OSO","O","ONO","NO","NNO"];
    const dir = dirs[Math.round((a.wind_bearing || 0) / 22.5) % 16];
    // ... render gros chiffre, badges, prévisions rows
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${CARD_CSS}</style>
      <div class="card">...</div>`;
    this.shadowRoot.querySelector(".card").onclick = () =>
      this.dispatchEvent(new CustomEvent("hass-more-info", {
        detail: { entityId: this._config.entity }, bubbles: true, composed: true,
      }));
  }
}
customElements.define("meteo-card", MeteoCard);

window.customCards = window.customCards || [];
window.customCards.push(
  { type: "storage-card", name: "Storage Card", description: "Carte stockage avec jauge SVG" },
  { type: "meteo-card", name: "Météo Card", description: "Carte météo premium avec prévisions" }
);