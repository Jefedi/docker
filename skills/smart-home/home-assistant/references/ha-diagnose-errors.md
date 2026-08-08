# HA Diagnose — trouver les erreurs et indisponibilités

Workflow systématique pour diagnostiquer les erreurs sur l'instance Home Assistant via le MCP.

## Prérequis

- MCP HA fonctionnel (ex: `https://ha-mcp.jefe.al/private_TOKEN`)
- Python 3 (recommandé) ou curl

## 1. Vue d'ensemble des domaines

```python
import json, http.client, ssl

url_path = "/private_TOKEN"
host = "ha-mcp.jefe.al"

def call_mcp(method, params):
    payload = {
        "jsonrpc": "2.0", "method": "tools/call",
        "params": {"name": method, "arguments": params},
        "id": 1
    }
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(host, 443, context=ctx, timeout=15)
    conn.request('POST', url_path, body=body, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    })
    resp = conn.getresponse()
    raw = resp.read().decode()
    conn.close()
    for line in raw.split('\n'):
        if line.startswith('data: '):
            data = json.loads(line[6:])
            if 'result' in data and data.get('id') == 1:
                content = data['result']['content'][0]['text']
                try:
                    return json.loads(content)
                except:
                    return content
    return raw

# Obtenir les stats par domaine
overview = call_mcp("ha_get_overview", {})
```

**Piège** : `ha_get_overview` ne prend PAS de paramètre `detailed`. L'appel sans argument retourne les domain_stats avec states_summary.

Lecture du résultat :
- `domain_stats[<domain>].states_summary` → liste les états (`unavailable`, `on`, `off`, etc.) avec leur count
- `domain_stats[<domain>].entities` → échantillon d'entités du domaine (souvent tronqué)

## 2. Identifier les entités indisponibles

```python
# Lister tous les domaines avec des unavailable
for domain, stats in overview.get('domain_stats', {}).items():
    states = stats.get('states_summary', {})
    if 'unavailable' in states:
        n = states['unavailable']
        total = stats['count']
        print(f"  {domain}: {n}/{total} unavailable")
```

## 3. Chercher des entités cassées par requête

```python
# Chercher les entités d'un domaine spécifique
result = call_mcp("ha_search", {"query": "update.", "limit": 100})

# Filtrer les indisponibles
for e in result.get('entities', []):
    if e.get('state') == 'unavailable':
        print(f"  ❌ {e['entity_id']} - {e.get('friendly_name')}")
```

**Piège** : `ha_search` ne prend pas `domain_filter` — le filtrage par domaine se fait via le préfixe dans la query (ex: `"update."`, `"media_player."`).

## 4. Inspecter une entité spécifique

```python
etat = call_mcp("ha_get_state", {"entity_id": "update.beszel_hub_update"})
```
Regarder les champs clés :
- `state` → `"unavailable"`, `"on"`, `"off"`, etc.
- `attributes.restored` → `true` si l'entité est une relique d'une intégration qui n'existe plus
- `last_changed` → depuis quand c'est dans cet état

## 5. Vérifier les services disponibles

```python
result = call_mcp("ha_list_services", {"domain": "notify"})
```

## Pièges connus

### MCP via shell curl
Les tokens JWT dans l'URL et les payloads JSON avec emojis causent des problèmes de quoting en bash. Toujours préférer Python + `http.client` avec `.encode('utf-8')`.

### Entités « restored »
Une entité avec `attributes.restored = true` signifie que HA a restauré l'entité depuis une session précédente mais l'intégration n'est plus active. Ces entités sont des orphelines — impossible de les contacter.

### 450+ sensors unavailable
HA peut accumuler des sensors `unavailable` pour des conteneurs Docker arrêtés, des services hors-ligne, ou des intégrations défaillantes. Ça n'indique pas toujours un vrai problème — certains conteneurs sont intentionnellement stoppés (test-watcher, etc.).

### Apple TV — 125 media_players unavailable
Les intégrations Apple TV créent une entité par service (par ex. 4 Apple TV → 4 media_player + 2 remote), mais si les appareils sont éteints ils passent `unavailable`. S'ils ont été retirés du réseau mais pas supprimés de HA, ils restent indéfiniment.

## Outils MCP qui N'EXISTENT PAS sur ce serveur

Ne pas perdre de temps à essayer ces noms d'outils (retournent "Unknown tool") :
- `ha_get_system_log` / `ha_get_log` / `ha_get_logbook`
- `ha_get_persistent_notifications` / `ha_get_notifications`
- `ha_get_config` / `ha_config_get_config`
- `ha_get_states` / `ha_list_config_entries`
- `ha_get_health`
- `ha_get_updates`
- `ha_search_entities` (utiliser `ha_search` à la place)
- `ha_deep_search`
- `list_tools`

→ Impossible de lire les logs ou les notifications persistantes via ce MCP. Utiliser les endpoints REST HA directement avec un token pour ça.
