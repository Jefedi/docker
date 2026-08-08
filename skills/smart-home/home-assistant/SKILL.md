---
name: home-assistant
description: Connecter, interroger et contrôler une instance Home Assistant via son API REST — états, entités, lumières, switches, automatisations, scripts.
---

# Home Assistant — API REST

Interagir avec une instance Home Assistant via son API REST. Couvre la connexion, la découverte d'entités, la lecture d'états et le contrôle d'entités (lumières, switches, scripts, etc.).

## Prérequis

- URL de l'instance HA (ex: `http://100.64.0.8:8123`)
- Long-Lived Access Token (Paramètres → Comptes → Tokens d'accès → Créer un token)
- curl ou Python + requests

## Connexion

### Test basique

```bash
curl -s http://HA_URL:8123/api/ \
  -H "Authorization: Bearer VOTRE_TOKEN"
# → 200 OK si valide
```

### Piège : trusted_proxies

Si HA est derrière un reverse proxy (Pangolin, nginx, etc.) avec `trusted_proxies` activé, les requêtes directes sont rejetées en **403**. Solution : ajouter le header `X-Forwarded-For` avec l'IP du proxy :

```bash
curl -s http://HA_URL:8123/api/states \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "X-Forwarded-For: 127.0.0.1"
```

### Token JWT — manipulation en Python

Les tokens JWT contiennent des points (`.`), tirets (`-`), underscores (`_`) qui compliquent le passage en bash. Toujours les lire depuis un fichier :

```python
token = open('/tmp/ha_token.txt').read().strip()
auth = 'Authorization: Bearer ' + token
```

Ne PAS utiliser `$token` dans une f-string ou un heredoc bash — le `$` casse l'expansion.

## Opérations courantes

### Lister toutes les entités

```python
import subprocess, json
token = open('/tmp/ha_token.txt').read().strip()
auth = 'Authorization: Bearer ' + token
r = subprocess.run(['curl', '-s', 'http://HA_URL:8123/api/states',
    '-H', auth, '-H', 'X-Forwarded-For: 127.0.0.1'],
    capture_output=True, text=True, timeout=10)
data = json.loads(r.stdout)
```

### Grouper par domaine

```python
from collections import defaultdict
by_domain = defaultdict(list)
for e in data:
    domain = e['entity_id'].split('.')[0]
    by_domain[domain].append((e['entity_id'], e['state']))
for domain in sorted(by_domain.keys()):
    print(f"{domain} ({len(items)})")
```

### Contrôler une entité (allumer/éteindre)

```python
import subprocess, json
token = open('/tmp/ha_token.txt').read().strip()
auth_hdr = 'Authorization: Bearer ' + token
api = 'http://HA_URL:8123'

r = subprocess.run(['curl', '-s', '-X', 'POST',
    f'{api}/api/services/light/turn_on',
    '-H', auth_hdr,
    '-H', 'X-Forwarded-For: 127.0.0.1',
    '-H', 'Content-Type: application/json',
    '-d', '{"entity_id": "light.tapo_l530"}'],
    capture_output=True, text=True, timeout=10)
```

Appels de service courants :

| Service | Endpoint |
|---------|----------|
| Allumer lumière | `POST /api/services/light/turn_on` |
| Éteindre lumière | `POST /api/services/light/turn_off` |
| Switch on | `POST /api/services/switch/turn_on` |
| Switch off | `POST /api/services/switch/turn_off` |
| Exécuter script | `POST /api/services/script/turn_on` |
| Activer scène | `POST /api/services/scene/turn_on` |
| Démarrer aspirateur | `POST /api/services/vacuum/start` |
| Retour base aspirateur | `POST /api/services/vacuum/return_to_base` |

### Lire l'état d'une entité spécifique

```bash
curl -s http://HA_URL:8123/api/states/light.tapo_l530 \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "X-Forwarded-For: 127.0.0.1"
```

### Récupérer la config HA

```bash
curl -s http://HA_URL:8123/api/config \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "X-Forwarded-For: 127.0.0.1"
```

## Pièges

- **trusted_proxies** : si 403, toujours ajouter `X-Forwarded-For: 127.0.0.1`
- **Token JWT en bash** : le `$` dans le token peut être interprété par le shell. Préférer un fichier + lecture Python.
- **Timeout** : HA avec beaucoup d'entités (>2000) peut mettre 2-5s à répondre. Mettre timeout=15.
- **SyntaxError en Python** : ne pas utiliser `f'Authorization: Bearer $token'` (le `$` n'est pas Python) → utiliser `'Authorization: Bearer ' + token`.
- **Entités indisponibles** : beaucoup d'entités peuvent être `unavailable` — vérifier le champ `state` avant d'agir.\n- **rate limiting** : HA n'a pas de rate limit explicite mais éviter >10 req/s.\n\n## Références liées\n\n- `references/ha-dashboard-inventory.md` — workflow d'inventaire des dashboards HA : lister, inspecter les vues, distinguer dashboards vs onglets, contraintes de suppression.
- `references/ha-maintenance-checkup.md` — workflow de vérification des mises à jour : HA updates, APT système, Docker.
- `references/ha-automation-edit-workflow.md` — chercher et corriger un service/notify cassé dans toutes les automatisations et scripts via le MCP.
- `references/ha-diagnose-errors.md` — workflow pour trouver les entités indisponibles, erreurs intégrations, restored entities avec le MCP.
- `references/ha-notification-diagnosis.md` — diagnostiquer les erreurs de notification (ntfy, Discord test_ai, push iOS, notification_central).
- `references/ha-passive-monitoring.md` — trier les notifications HA en temps réel, distinguer les vrais problèmes des sondes qui flappent, savoir quand investiguer vs. accuser réception.
- `references/ha-custom-markdown-cards.md` — pattern fiable pour cartes dashboard 100% markdown (remplace custom cards cassées) ; piège `weather.forecast` null en template ; direction du vent en Jinja2 ; workflow A/B sur dashboard ; custom JS cards Lovelace (alternative à button-card/clock-weather-card) ; **theme-aware CSS (variables HA)** ; **animations RETIRÉES sur préférence utilisateur (rendu statique)** ; **piège encodage UTF-8 en JS** ; **dashboard de test pour comparer des cartes**.
- `references/ha-music-assistant.md` — diagnostiquer Music Assistant (librespot audio key error, Spotify relogin, HA 502, zeroconf/Tailscale, Last.fm 0 folders, MusicBrainz rate limit).
- `references/ha-metrics-dashboard.md` — pattern pour pousser des métriques externes (scripts, containers) vers HA via input_number helpers + cron, avec dashboard gauges/graphs colorés.
- `templates/premium-cards-template.js` — template de custom cards Lovelace en JS natif (météo + storage avec jauge SVG). À adapter et enregistrer via `ha_config_set_dashboard_resource`.

---

## Variante : MCP Server (HA via serveur FastMCP/SSE)

Si HA est exposé via un serveur MCP (ex: `ha-mcp.jefe.al`), les appels se font en **JSON-RPC sur HTTP avec SSE** plutôt qu'avec l'API REST directe.

### Connexion au serveur MCP

```bash
# Test de connexion (via hermes)
hermes mcp test <server_name>

# Appel direct via curl
curl -s -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"TOOL_NAME","arguments":{}},"id":1}'
```

**Important** : le header `Accept: application/json, text/event-stream` est OBLIGATOIRE. Sans ça, le serveur répond 406.

## Custom JS Cards — alternative aux custom cards HACS

Quand les custom cards HACS (clock-weather-card, button-card, etc.) ne rendent pas correctement ou que l'utilisateur veut un design premium sur-mesure, on peut créer de **vraies custom cards Lovelace en JS natif**.

### Workflow

1. Écrire le fichier JS (custom element `HTMLElement` avec Shadow DOM)
2. L'enregistrer comme **ressource dashboard inline** via `ha_config_set_dashboard_resource(content=..., resource_type="module")`
3. Utiliser la carte dans le dashboard avec `type: custom:nom-de-la-card`

### Enregistrement de la ressource

```python
ha_config_set_dashboard_resource(
    content="... code JS ...",
    resource_type="module"
)
# → resource_id retourné, ~24KB max
```

### Structure minimale d'une custom card JS

```javascript
class MyCard extends HTMLElement {
  setConfig(config) { this._config = config; }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 5; }
  _render() {
    if (!this._hass || !this._config) return;
    const state = this._hass.states[this._config.entity];
    if (!state) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>...</style><div>...</div>`;
  }
}
customElements.define("my-card", MyCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "my-card", name: "My Card", description: "..." });
```

### Piège : `button-card` JS templates → `ButtonCardJSTemplateError`

La custom card `button-card` (HACS) supporte les templates JS `[[[ ... ]]]` dans `custom_fields`, mais le transport via MCP (JSON → HA storage) peut corrompre les backticks, `${}` ou les séquences d'échappement Unicode, causant une erreur `ButtonCardJSTemplateError` à l'affichage.

**Solution fiable :** si le code JS template de button-card échoue, créer une vraie custom card Lovelace (fichier JS dédié enregistré comme ressource inline) au lieu d'utiliser button-card avec des templates JS complexes.

### Piège : `weather/subscribe_forecast` pour les prévisions

L'attribut `forecast` n'est pas accessible en template Jinja2 (`null`). Pour les prévisions dans une custom card JS, utiliser l'abonnement WebSocket :

```javascript
async _subscribeForecast() {
  await this._hass.connection.subscribeMessage(
    (msg) => { this._forecast = msg.forecast; this._render(); },
    { type: "weather/subscribe_forecast", entity_id: this._config.entity, forecast_type: "daily" }
  );
}
```

Avec fallback sur l'attribut legacy :
```javascript
this._forecast = this._hass.states[this._config.entity]?.attributes?.forecast;
```

### Cache navigateur

Après avoir enregistré une nouvelle ressource JS, l'utilisateur doit faire un **hard refresh** (Ctrl+Shift+R) ou fermer/rouvrir l'app HA pour que le module se charge.

## Bubble Card (HACS) — cartes minimalistes avec pop-up

**Repository :** github.com/Clooos/Bubble-Card (4.4k ⭐, déjà installé chez cet utilisateur en v3.2.5)

Bubble Card est la custom card préférée de l'utilisateur pour le rendu "flottant". Elle offre plusieurs `card_type` :

### Types de cartes Bubble Card

| card_type | Usage |
|-----------|-------|
| `button` | Carte rectangulaire avec icône, nom, état + sub_buttons |
| `cover` | Variante avec style "cover" (fond coloré) |
| `pop-up` | Pop-up flottant qui s'ouvre au tap (masqué par défaut) |
| `horizontal-buttons-stack` | Rangée de boutons horizontaux |
| `media-player` | Contrôle lecteur média |

### Configuration type — button avec sub_buttons

```yaml
type: custom:bubble-card
card_type: button
entity: weather.le_havre
name: Le Havre
icon: mdi:weather-partly-cloudy
show_state: true
show_name: true
show_icon: true
show_last_changed: false
tap_action:
  action: more-info
sub_button:
  - name: Temp
    entity: weather.le_havre
    attribute: temperature
    show_state: true
    show_icon: true
    icon: mdi:thermometer
  - name: Hum
    entity: weather.le_havre
    attribute: humidity
    show_state: true
    show_icon: true
    icon: mdi:water-percent
```

### Piège : `card_type: cover` sur une entité non-cover

Le `card_type: cover` est conçu pour les volets/covers. Sur une entité `weather.*` ou `sensor.*`, le rendu peut être incorrect (texte répété, valeurs brutes). Préférer `card_type: button` pour les entités non-cover.

### Pop-up Bubble Card

```yaml
type: custom:bubble-card
card_type: pop-up
entity: sensor.storage_box_borg_ax42
name: Storage Box Detail
icon: mdi:harddisk
hash: "#storage-popup"
```

Le `hash` doit être unique. Le pop-up est masqué et s'ouvre quand on navigue vers l'ancre `#storage-popup`.

## Thèmes HACS — installation et application

### Installer un thème via MCP

```python
# 1. Chercher le thème dans HACS
ha_get_hacs_info(action="search", category="theme", query="frosted glass")
# → repository_id

# 2. Installer
ha_manage_hacs(action="download", repository_id="1012545675")
```

### Appliquer un thème par vue

```python
# Dans la config d'une vue dashboard :
view = {
    'type': 'sections',
    'title': 'Frosted Glass',
    'path': 'frosted',
    'theme': 'Frosted Glass Dark',  # ← thème appliqué à cette vue uniquement
    ...
}
```

### Piège : repository_id vs repository

`ha_manage_hacs(action="download")` prend `repository_id` (numérique HACS ID), PAS `repository` (owner/repo string). Confondre les deux installe le mauvais dépôt. Toujours faire un `ha_get_hacs_info(action="search")` d'abord pour récupérer le bon `repository_id`.

## card-mod glassmorphism sur cartes natives HA

Alternative aux custom JS cards : injecter du CSS glassmorphism via `card_mod` sur des cartes natives (entities, gauge, markdown).

```yaml
type: entities
title: Météo - Le Havre
entities:
  - type: attribute
    entity: weather.le_havre
    attribute: temperature
    name: Température
card_mod:
  style: |
    ha-card {
      backdrop-filter: blur(16px) saturate(180%);
      -webkit-backdrop-filter: blur(16px) saturate(180%);
      background: rgba(30, 35, 45, 0.4) !important;
      border: 1px solid rgba(255, 255, 255, 0.12) !important;
      border-radius: 24px !important;
      box-shadow: 0 8px 32px rgba(0,0,0,0.37), inset 0 1px 1px rgba(255,255,255,0.1) !important;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    ha-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 16px 48px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.15) !important;
    }
```

**Note :** l'utilisateur a trouvé le rendu card-mod glassmorphism "moche" comparé à Bubble Card. Préférer Bubble Card pour le rendu flottant.

## Préférence utilisateur — ordre des approches dashboard

Après tests extensifs (session 2026-07-22), l'ordre de préférence pour les cartes dashboard :

1. **Bubble Card** (HACS) — préféré, rendu flottant natif, pop-ups
2. ~~Frosted Glass card-mod~~ — rejeté ("moche, ça rend pas beau")
3. ~~Custom JS cards (premium-cards.js)~~ — fonctionne mais ne "flotte" pas assez
4. **Markdown natif** — fiable, utilisé sur le dashboard principal (Storage Box, Météo)

Toujours proposer Bubble Card en premier pour de nouvelles cartes. Le dashboard de test (`test-dashboard`) sert à expérimenter avant d'appliquer sur le dashboard principal (`maison-dashboard`).

## Validation des templates

Toujours tester le template avec `ha_eval_template` avant de l'intégrer dans une carte markdown :

```
ha_eval_template(template="{% set w = 'weather.le_havre' %}{{ states(w) }}")
→ "sunny"
```

Cela évite les cartes blanches si une entité n'existe pas ou si le template a une erreur de syntaxe.

```python
import sys, json
raw = sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data: '):
        data = json.loads(line[6:])
        # data['result']['content'][0]['text'] contient le payload
        result = json.loads(data['result']['content'][0]['text'])
        break
```

### Inventaire des dashboards

Les dashboards HA sont de deux types : **storage** (modifiable via UI/MCP) et **YAML/default** (non supprimables via MCP).

```bash
# Lister tous les dashboards storage
curl -s -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_get_dashboard","arguments":{"list_only":true}},"id":1}'
```

**Piège** : un dashboard peut contenir plusieurs **vues (views)**. Ce que l'utilisateur appelle "dashboard Traduction" ou "dashboard Radarr" peut être une vue/onglet dans un dashboard existant. Toujours vérifier la config détaillée :

```bash
# Config détaillée d'un dashboard (avec ses vues)
curl -s -H "..."
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_get_dashboard","arguments":{"url_path":"mon-dashboard"}},"id":1}'
```

Le champ `config.views[].title` liste les onglets à l'intérieur du dashboard.

### Suppression d'un dashboard storage

```bash
curl -s -H "..."
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_delete_dashboard","arguments":{"url_path":"mon-dashboard"}},"id":1}'
```

**Piège** : les dashboards mode YAML et le dashboard par défaut (`lovelace`) ne peuvent PAS être supprimés via MCP. Seuls les dashboards en mode `storage` le peuvent.

### Appel MCP depuis Python (pour grosses configs / emoji)

Quand la config du dashboard est volumineuse (>2KB) ou contient des emojis, le shell curl peut avoir des soucis de quoting. Solution : Python + http.client :

```python
import json, http.client, ssl

payload = {
    'jsonrpc': '2.0', 'method': 'tools/call',
    'params': {
        'name': 'ha_config_set_dashboard',
        'arguments': {
            'url_path': 'mon-dashboard',
            'title': 'Mon Dashboard',
            'icon': 'mdi:home',
            'config': {"views": [...]}
        }
    },
    'id': 1
}

# CRITIQUE : encoder en UTF-8 bytes (http.client utilise latin-1 par defaut)
body = json.dumps(payload, ensure_ascii=False).encode('utf-8')

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('ha-mcp.jefe.al', 443, context=ctx)
conn.request('POST', '/private_TOKEN', body=body, headers={
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
})
resp = conn.getresponse()
print(resp.read().decode())
conn.close()
```

**Piège** : `HTTPSConnection` encode en latin-1. Les emojis lèvent `UnicodeEncodeError`. Toujours `.encode('utf-8')`.

### Piège : notifications intermédiaires SSE

Certains outils MCP (ha_deep_search) envoient des notifications AVANT le résultat. Plusieurs lignes `data:` pour un même id. Toujours itérer TOUTES les lignes et ne garder que celle avec `"result"` + l'id attendu :

```python
for line in raw.split('\n'):
    if line.startswith('data: '):
        data = json.loads(line[6:])
        if 'result' in data and data.get('id') == target_id:
            content = json.loads(data['result']['content'][0]['text'])
            if 'data' in content: content = content['data']
            break
```

### Piège : `ha_get_overview` n'a PAS de paramètre `group_by`

`{"group_by": "area"}` retourne `Bad Gateway`. Utiliser `ha_get_device(area_id=...)` ou `ha_search(query=..., area_filter=...)` à la place.

**Piège auto-création** : quand TOUS les dashboards storage sont supprimés, HA recrée automatiquement un dashboard `lovelace` vide. Ce dashboard par défaut prend la place de la page d'accueil, mélangé dans la sidebar. Y'a pas moyen de le virer via MCP — solution : créer un nouveau dashboard storage avec hyphen dans l'URL (cf. création ci-dessous). Si un seul dashboard storage existe, HA l'utilise comme page par défaut.

### Création d'un dashboard storage

```bash
curl -s -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_config_set_dashboard","arguments":{"url_path":"mon-dashboard","title":"Mon Dashboard","icon":"mdi:home","show_in_sidebar":true,"config":{"views":[...]}}},"id":1}'
```

**Règle absolue** : le `url_path` doit contenir un **tiret** (`-`). `mon-dashboard` ✅ — `mondashboard` ❌ — `maison` ❌. 
- Exception : `url_path="lovelace"` ou `"default"` pour éditer le dashboard système (mais ça ne marche pas toujours — cf. erreur "Unknown config specified").

**Contrôle de visibilité** : les `views` d'un dashboard peuvent avoir un champ `visible` optionnel. Si absent, la vue est visible par tous. Pour restreindre :

```json
"visible": [{"user": "17e16b8ec7af407e9d5615881a75b1a9"}]
```

Où l'ID est celui de l'utilisateur HA. Omettre `visible` = visible par tous.

### `ha_config_set_dashboard` — mode `python_transform` et BestPracticeKey

#### BestPracticeKey (obligatoire en mode strict)

Les outils d'écriture HA (`ha_config_set_dashboard`, `ha_config_set_automation`, `ha_config_set_script`, `ha_config_set_scene`, `ha_config_set_helper`) nécessitent une **clé d'accusé de lecture** quand le mode best-practices strict est activé.

**Workflow :**
1. Appeler `ha_get_skill_guide(skill='home-assistant-best-practices')` (sans args ou avec `file='SKILL.md'`)
2. Récupérer la clé dans la réponse : `Acknowledgment key: I-HAVE-READ-THE-BEST-PRACTICES-GUIDE-xxxxxxxx`
3. Passer cette clé comme paramètre `BestPracticeKey` à l'appel d'écriture

**Piège :** la clé **rotate périodiquement**. Ne pas stocker en mémoire — la re-lire à chaque session. Passer `MandatoryBPS=false` sur les appels suivants dans la même session pour éviter de re-recevoir le contenu du skill.

#### `python_transform` — édition chirurgicale d'un dashboard existant

Pour modifier un dashboard existant sans remplacer toute la config, utiliser `python_transform` au lieu de `config` :

```python
# 1. GET le dashboard pour obtenir config_hash
dash = ha_config_get_dashboard(url_path="maison-dashboard")
config_hash = dash["config_hash"]

# 2. Appliquer une transformation Python sur la config existante
ha_config_set_dashboard(
    url_path="maison-dashboard",
    config_hash=config_hash,       # OBLIGATOIRE pour python_transform
    python_transform="config['views'].append({...nouvelle_vue...})"
)
```

**Règles python_transform :**
- `config` est la variable contenant la config complète du dashboard
- Accès dict/list standard : `config['views'][0]['cards'][1]['icon'] = 'mdi:x'`
- Pas d'imports, pas de `def`, pas de `try/except`, pas de `while`
- Comprehensions et lambdas OK
- Operations courantes : `.append()`, `del config[...]`, `config['key'] = value`

**Avantage vs `config` (remplacement complet) :** `python_transform` ne touche que ce qu'on modifie — pas de risque d'écraser les vues/cartes existantes.

#### Exemple : ajouter une vue avec carte markdown templated

```python
config['views'].append({
    'type': 'sections',
    'title': 'Storage Box',
    'path': 'storage-box',
    'icon': 'mdi:harddisk',
    'max_columns': 2,
    'sections': [
        {
            'type': 'grid',
            'column_span': 1,
            'cards': [
                {
                    'type': 'heading',
                    'heading': 'Titre section',
                    'icon': 'mdi:text'
                },
                {
                    'type': 'markdown',
                    'content': "{% set val = states('sensor.xxx') | float(0) %}\n## Titre\n\nValeur: {{ val }}"
                }
            ]
        }
    ]
})
```

**Piège emoji dans python_transform :** les emojis dans les strings Python du transform doivent utiliser des escapes Unicode (`\U0001F4BE` pour 💾, `\U0001F7E2` pour 🟢) car le transport MCP peut mal gérer l'UTF-8 direct dans les paramètres.

**Piège `config_hash` :** toujours utiliser celui du dernier GET. Si le dashboard a été modifié entre le GET et le SET, le hash ne matche plus → erreur `RESOURCE_LOCKED`. Re-faire un GET.

### `ha_call_service` — paramètre `data`

Le paramètre du service data s'appelle **`data`**, pas `service_data`, pas `service_data_object` :

**Piège update.install** : les entités `update.*` monitorées par HA (ex: conteneurs Docker, images) peuvent avoir `can_install: true` sans que HA puisse réellement les installer. Vérifier avec `ha_get_state(entity_id="update.xxx")` — si l'appel `update.install` échoue en 500, l'entité est monitor-only. Il faut mettre à jour le conteneur Docker manuellement.

```json
{"name":"ha_call_service","arguments":{"domain":"light","service":"turn_on","entity_id":"light.tapo_l530","data":{"brightness":255}}}
```

Sans `data`, appeler avec `service_data` donne une erreur `Unexpected keyword argument`.

### Gestion des zones (carte)

Les zones HA (`ha_get_zone`) sont les emplacements géographiques qui apparaissent sur la carte par défaut. Pour les auditer et les nettoyer :

```bash
# Lister toutes les zones
curl -s -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_get_zone","arguments":{}},"id":1}'
```

**Piège** : certaines zones sont des zones système (`home`, zone par défaut) qui n'apparaissent PAS dans la liste `ha_get_zone` mais existent toujours sur la carte. Seules les zones créées par l'utilisateur sont listées et supprimables.

```bash
# Supprimer une zone (ex: magasins, lieux inutiles)
curl -s -H "..." -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_remove_zone","arguments":{"zone_id":"auchan_le_havre"}},"id":1}'
```

Le `zone_id` est le champ `id` retourné par `ha_get_zone` (ex: `auchan_le_havre`, `carrefour_le_havre`).

### Recherche d'entités via MCP

```bash
# Recherche par texte libre dans les noms d'entités
curl -s -H "..." -X POST "https://MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ha_search","arguments":{"query":"light","limit":30}},"id":1}'
```

**Piège** : le nom du tool est `ha_search` (PAS `ha_search_entities`). Il prend `query` (texte libre) et `limit`. Les anciens paramètres `domain_filter` et `area_filter` n'existent pas sur tous les serveurs MCP HA — utiliser `ha_search(query="light.living_room")` pour filtrer par domaine.

**Piège parsing — wrapper `data`** : quand `ha_search` renvoie ses résultats, le contenu peut avoir une structure `{"data": {...}}` enveloppant les vrais résultats. Toujours vérifier et déballer :

```python
content = json.loads(data['result']['content'][0]['text'])
if 'data' in content:
    content = content['data']  # déballer le wrapper
results = content.get('results', [])
```

### Outils MCP HA utiles pour l'audit

| Outil | Usage |
|-------|-------|
| `ha_get_overview` | Vue d'ensemble : stats entités, domaines, zones |
| `ha_get_state` | État d'une ou plusieurs entités |
| `ha_search(query=..., limit=...)` | Recherche d'entités par texte libre (nom, domaine) |
| `ha_get_device(area_id=...)` | Périphériques par pièce, avec infos intégration |
| `ha_config_get_dashboard(list_only=true)` | Liste des dashboards |
| `ha_config_get_dashboard(url_path="...")` | Config détaillée d'un dashboard (vues, cartes) |
| `ha_config_delete_dashboard` | Supprimer un dashboard storage |
| `ha_config_set_dashboard(url_path=..., config=...)` | Créer ou modifier un dashboard |
| `ha_get_zone` | Zones géographiques (zones map) |
| `ha_remove_zone(zone_id=...)` | Supprimer une zone |
| `ha_config_list_dashboard_resources` | Resources Lovelace (cartes custom, CSS inline) |
| `ha_deep_search(query=...)` | Recherche dans automatisations/scripts/scenes |
| `ha_eval_template(template=...)` | Tester des templates Jinja2 |
| `ha_list_services(domain=...)` | Services disponibles pour un domaine |
| `ha_call_service(domain=..., service=..., data=...)` | Exécuter un service HA |

### Automation & Script CRUD (MCP)

```bash
# Obtenir la config complète d'une automation
ha_config_get_automation(identifier="automation.xxx")
# → retourne config + config_hash (OBLIGATOIRE pour la mise à jour)

# Mettre à jour une automation
ha_config_set_automation(identifier="automation.xxx", config={...}, config_hash="...")

# Supprimer une automation
ha_config_remove_automation(identifier="automation.xxx")

# Obtenir/configurer un script
ha_config_get_script(script_id="mon_script")  # sans préfixe script.
ha_config_set_script(script_id="mon_script", config={...}, config_hash="...")
```

**Piège `config_hash` :** toujours renvoyer celui reçu du GET. Sans ça, l'update échoue ou crée un doublon.

**Piège blueprint :** la config est dans `config.use_blueprint.input.notification_actions[]`, pas dans `config.actions[]`.

**Piège double nesting script :** le GET d'un script renvoie `config.script_id.config.sequence[]` — attention au double niveau `config`.

**Piège chaîne automation→script :** une automation qui utilise `action: script.xxx` peut cacher l'action cassée dans le script appelé. `ha_search` trouve l'automation, mais le notify est dans le script. Toujours suivre la chaîne : patch l'automation → inspecte son script → patch le script. Voir `references/ha-automation-edit-workflow.md` section « Piège critique : suivre la chaîne ».

## Assist Pipeline — STT / TTS / Conversation via Mistral + LiteLLM

### Architecture

Pipeline "LiteLLM GLM-5.2 + Mistral STT/TTS" :
- **STT** : `stt.mistral_ai_stt_mistral_ai_stt_voxtral` (Voxtral Mini, API Mistral directe)
- **Conversation** : `conversation.extended_openai_conversation` (LiteLLM → glm-5.2)
- **TTS** : `tts.mistral_ai_tts_mistral_ai_tts` (Voxtral TTS, API Mistral directe)

### Intégration HA_MistralAI (SnarfNL/HA_MistralAI)

Installe l'intégration tout-en-un qui gère STT Voxtral + TTS Mistral + conversation Mistral nativement.

```python
# 1. Ajouter le repo HACS
ha_manage_hacs(action="add_repository", repository="SnarfNL/HA_MistralAI", category="integration")
# 2. Installer
ha_manage_hacs(action="download", repository_id="1163518287")
# 3. Restart HA
ha_restart(confirm=True)
# 4. Ajouter l'intégration avec la clé API Mistral
ha_set_integration(domain="mistral_conversation", config={"api_key": "MISTRAL_API_KEY"})
```

L'intégration crée automatiquement :
- `stt.mistral_ai_stt_*` (Voxtral STT)
- `tts.mistral_ai_tts_*` (Mistral TTS avec voix dynamiques)
- `conversation.mistral_ai_conversation` (agent conversationnel Mistral)

### Création du pipeline Assist

```python
ha_manage_pipeline(
    action="update",
    pipeline_id="PIPELINE_ID",
    name="LiteLLM GLM-5.2 + Mistral STT/TTS",
    language="fr",
    stt_engine="stt.mistral_ai_stt_mistral_ai_stt_voxtral",
    stt_language="fr-FR",
    conversation_engine="conversation.extended_openai_conversation",
    tts_engine="tts.mistral_ai_tts_mistral_ai_tts",
    tts_language="fr-FR"
)
```

### Piège : LiteLLM ne route pas l'audio Mistral

LiteLLM ne sait pas mapper le provider `mistral/` pour les endpoints audio. Erreur : `Unable to map the custom llm provider=mistral`.

**Solution** : utiliser `model: openai/...` avec `api_base: https://api.mistral.ai/v1` dans la config LiteLLM. L'API Mistral est compatible OpenAI.

```yaml
# Avant (marche pas pour l'audio)
- model_name: voxtral-tts
  litellm_params:
    model: mistral/voxtral-mini-tts-latest
    api_key: os.environ/MISTRAL_API_KEY

# Après (marche)
- model_name: voxtral-tts
  litellm_params:
    model: openai/voxtral-mini-tts-latest
    api_base: https://api.mistral.ai/v1
    api_key: os.environ/MISTRAL_API_KEY
  model_info:
    mode: audio_speech
    output_cost_per_character: 0.000016
```

### Piège : STT YAML vs default_config

Le custom component `openai_stt` (einToast/openai_stt_ha) utilise `config_flow: false` — config YAML uniquement. Mais `default_config:` gère déjà `stt` via config entries, donc le YAML `stt:` est ignoré.

**Solution** : utiliser `HA_MistralAI` qui crée le STT via config flow natif.

### Piège : openai_tts config flow à 2 étapes

Le custom component `openai_tts` (sfortis/openai_tts) a un config flow à 2 étapes : (1) modèle, (2) voix+audio. Le MCP ne peut compléter que la 1ère étape. La voix reste à `shimmer` (défaut OpenAI) qui n'existe pas sur Mistral → 404.

**Solution** : utiliser `HA_MistralAI` qui gère le TTS nativement avec voix dynamiques.

### Voix Mistral TTS disponibles (FR)

| Slug | Nom | Genre |
|------|-----|-------|
| `fr_marie_neutral` | Marie - Neutral | Femme |
| `fr_marie_happy` | Marie - Happy | Femme |
| `fr_marie_sad` | Marie - Sad | Femme |
| `fr_marie_excited` | Marie - Excited | Femme |
| `fr_marie_curious` | Marie - Curious | Femme |
| `fr_marie_angry` | Marie - Angry | Femme |

Récupérer la liste : `curl -s "https://api.mistral.ai/v1/audio/voices?limit=100" -H "Authorization: Bearer $MISTRAL_API_KEY"`

### Piège : conteneur LiteLLM bind mount read-only

Si le conteneur LiteLLM a un bind mount `:ro` sur `/app/config.yaml`, impossible de modifier la config depuis l'intérieur. Recréer le conteneur avec `:rw` :

```bash
docker stop litellm && docker rm litellm
docker run -d --name litellm --restart unless-stopped \
  --network litellm_default -p 127.0.0.1:4000:4000 \
  -v /srv/docker/litellm/config.yaml:/app/config.yaml:rw \
  -e MISTRAL_API_KEY=... -e LITELLM_MASTER_KEY=... \
  ghcr.io/berriai/litellm:main-stable --config /app/config.yaml --port 4000
```

## Règles Jefe — HA

### Rappels & courses
- Script HA tourne every 1min sur `todo.rappel`
- Courses: `todo.add_item` sur `todo.liste_dachats`

### Monitoring — silence ABSOLU
- **JAMAIS** répondre aux notifs HA monitoring (pas de texte, pas d'emoji, pas d'ack)
- Vagues d'alertes = Beszel intermittent, ne pas investiguer

## Vérification

```bash
# Test rapide REST
curl -s -o /dev/null -w "%{http_code}" http://HA_URL:8123/api/ \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "X-Forwarded-For: 127.0.0.1"
# → 200

# Compter les entités
curl -s http://HA_URL:8123/api/states ... | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin))} entities')"

# Test MCP
hermes mcp test ha-mcp 2>&1 | grep "Tools discovered"
# → "✓ Tools discovered: 80"
```
