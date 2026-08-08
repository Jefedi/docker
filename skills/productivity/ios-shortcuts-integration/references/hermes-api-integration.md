# Hermes API Server — iOS Shortcuts Integration

## Architecture

L'API Server Hermes expose un endpoint OpenAI-compatible. iOS Shortcuts POSTe dessus via l'action "Obtenir le contenu d'une URL".

```
iPhone (Shortcuts) ──POST──> hermes-api.jefe.al/v1/responses
                            → Bearer token auth
                            → Hermes API Server (port variable, vérifier logs gateway)
                            → JSON response → extraction → affichage
```

## Endpoint recommandé: `/v1/responses` (Responses API)

Plus simple que `/v1/chat/completions` car :
- Corps JSON simple : `{"input": "texte"}` (model optionnel, défaut hermes-agent)
- Pas besoin de construire l'objet `messages` avec `role` et `content`
- Pas de bug de sérialisation iOS avec les tableaux de dictionnaires

### ⚠️ Endpoints selon le point d'accès (confirmé juillet 2026)

| Point d'accès | URL | Notes |
|---------------|-----|-------|
| **Local** (port 9119) | `http://127.0.0.1:9119/v1/responses` | Port réel peut différer de config.yaml — vérifier logs gateway |
| **Via Pangolin** | `https://hermes.jefe.al/api/v1/responses` | Préfixe `/api` ajouté par le proxy Pangolin |

Le port configuré dans `config.yaml` (`gateway.api_server.port: 9120`) peut différer du port réel (observé sur 9119). Toujours vérifier :
```bash
docker exec hermes grep "api_server.*listening" /opt/data/logs/gateway.log | tail -1
```

### Clé API

Utiliser la clé du fichier `.env` (`API_SERVER_KEY`), pas celle de `config.yaml` (`gateway.api_server.extra.key`) — elles peuvent différer. Le gateway charge la clé du `.env` au démarrage.

## Construction du shortcut iOS

### URL
```
POST https://hermes.jefe.al/api/v1/responses
```

### En-têtes (Headers)
| Clé | Valeur |
|-----|--------|
| `Authorization` | `Bearer hermes-ios-shortcut-a80ac18a29ed5d62` |
| `Content-Type` | `application/json` |

⚠️ `Content-Type` doit être un **En-tête**, pas un champ du corps JSON.

### Corps JSON (corps → JSON, champ par champ)
| Clé | Type | Valeur |
|-----|------|--------|
| `input` | Texte | (variable magique du "Demander un texte") |
| `model` | Texte | `hermes-agent` |

### Extraction de la réponse

La réponse a cette structure :
```json
{
  "object": "response",
  "status": "completed",
  "output": [
    {"type": "message", "role": "assistant",
     "content": [
       {"type": "output_text", "text": "Réponse ici"}
     ]
    }
  ]
}
```

**Étapes d'extraction dans Shortcuts (construction manuelle) :**
1. Obtenir la valeur d'un dictionnaire → clé : `output`
2. Obtenir un élément d'une liste → index : `1`
3. Obtenir la valeur d'un dictionnaire → clé : `content`
4. Obtenir un élément d'une liste → index : `1`
5. Obtenir la valeur d'un dictionnaire → clé : `text`
6. Afficher un résultat

**Étapes d'extraction en Cherri (compilé) :**
⚠️ Ne PAS utiliser `@dict['key']` — cela compile en `setvariable` (copie) au lieu de `getvalueforkey` (extraction). Utiliser `getValue()` explicitement avec `getDictionary()` avant chaque accès.

```
@dict = getDictionary(@response)
@output = getValue(@dict, "output")
@first = getFirstItem(@output)
@firstDict = getDictionary(@first)
@content = getValue(@firstDict, "content")
@firstContent = getFirstItem(@content)
@firstContentDict = getDictionary(@firstContent)
@text = getValue(@firstContentDict, "text")
```

⚠️ **Espaces dans `show("{@text}")`** : peut échouer silencieusement si la variable contient des espaces. Le raccourci s'arrête sans erreur. Préférer `quicklook(@text)` ou `show(@text)`.

Voir `references/cherri-json-extraction.md` pour le diagnostic complet (vérification du plist).

### Déclencheurs
| Méthode | Comment faire |
|---------|--------------|
| **Bouton d'action** | Réglages → Bouton d'action → Raccourci → nom du shortcut |
| **Écran d'accueil** | ⋮ sur le raccourci → Partager → Ajout à l'écran d'accueil |
| **Siri** | « Dis Siri, [nom du raccourci] » |
| **Feuille de partage** | Sélectionner un texte → Partager → le raccourci |

## Pièges connus

### `Content-Type: application/json` mal placé
Ne PAS mettre Content-Type comme un champ du corps JSON. C'est un en-tête HTTP. S'il est dans le corps au lieu des en-têtes, l'API reçoit la requête mais peut mal parser le body.

### Erreur `list' object has no attribute 'get'`
Ce bug arrive avec `/v1/chat/completions` quand Shortcuts sérialise mal le tableau `messages`. Solution : utiliser `/v1/responses` à la place.

### Erreur 500 "Server got itself in trouble"
- Vérifier que `Content-Type: application/json` est bien dans les en-têtes
- Vérifier que l'URL complète inclut le path (pas seulement le domaine)
- Vérifier que le body est bien formé

### Shortcuts affiche le JSON brut au lieu du texte
Les étapes d'extraction sont incomplètes. Vérifier qu'on a bien les 6 étapes : output → [0] → content → [0] → text.

### Le chemin d'URL doit être complet
L'URL doit être `https://hermes-api.jefe.al/v1/responses` (ou `/v1/chat/completions`). Juste le domaine sans path = 404.

### ⚠️ "Échec de conversion Format RTF en Dictionnaire" — Pangolin intercept

**Symptôme :** Erreur rouge entre le bloc "Obtenir le contenu de l'URL" et "Obtenir la valeur d'un dictionnaire" : *"Raccourcis n'a pas pu effectuer la conversion de Format RTF en Dictionnaire"*.

**Root cause :** Pangolin intercepte la requête et renvoie une **page HTML** (302 redirect / login) au lieu de JSON. Shortcuts reçoit du HTML, tente de le parser comme dictionnaire → échec.

**Causes (vérifier dans cet ordre) :**

1. **Méthode HTTP = GET au lieu de POST** — Déplier les options avancées du bloc "Obtenir le contenu de l'URL". La méthode doit être **POST**. En GET sans headers, Pangolin renvoie du HTML.
2. **Headers manquants** — `Authorization: Bearer <clé>` ET `Content-Type: application/json` doivent être dans les **En-têtes** (pas dans le corps). Sans Bearer, Pangolin rejette → page de login HTML.
3. **API_SERVER_KEY non configurée** — Vérifier `env | grep API_SERVER`. Si vide → API server désactivé, rien à proxyer.
4. **Mauvais hostname** — Utiliser `hermes-api.jefe.al` (pas `hermes.jefe.al` qui pointe vers le dashboard). Mauvais hostname = autre service = HTML.

**Diagnostic rapide côté serveur :**
```bash
# Vérifier que l'API server est activé
env | grep API_SERVER

# Vérifier le port réel (ne pas se fier à config.yaml)
docker exec hermes grep "api_server.*listening" /opt/data/logs/gateway.log | tail -1

# Tester local (bypass Pangolin) — remplacer <port> par le port réel des logs
curl -s -o /dev/null -w "HTTP %{http_code} | CT: %{content_type}\n" \
  http://127.0.0.1:<port>/v1/responses -X POST \
  -H "Content-Type: application/json" -H "Authorization: Bearer <clé>" \
  -d '{"model":"hermes-agent","input":"test"}'

# Tester via Pangolin (depuis l'extérieur)
curl -s -o /dev/null -w "HTTP %{http_code} | CT: %{content_type}\n" \
  https://hermes-api.jefe.al/v1/responses -X POST \
  -H "Content-Type: application/json" -H "Authorization: Bearer <clé>" \
  -d '{"model":"hermes-agent","input":"test"}'
# CT: text/html → Pangolin intercepte (mauvais headers/clé)
# CT: application/json → API OK, problème côté Shortcuts
```

**Fix :** Déplier les options du bloc URL dans le shortcut → Méthode: **POST**, En-têtes: `Authorization` + `Content-Type`, Corps: **JSON** (`input` + `model`), URL: `hermes-api.jefe.al/v1/responses`.

## Infrastructure
- API Server : port configuré dans `config.yaml` sous `gateway.api_server.port` (ex: 9120)
- ⚠️ **Le port réel peut différer du port configuré** — toujours vérifier les logs gateway :
  ```bash
  docker exec hermes grep "api_server.*listening" /opt/data/logs/gateway.log | tail -1
  # Ex: "API server listening on http://0.0.0.0:9119" (port réel = 9119, pas 9120)
  ```
- Bind `0.0.0.0` (network_mode: host), donc accessible via `127.0.0.1` du host
- Gateway en `network_mode: host` (Docker), donc `127.0.0.1` du container = `127.0.0.1` du host
- Ressource Pangolin privée : `hermes-api.jefe.al` sur site 6 (Hetzner), alias `100.96.128.19`
- La clé API est définie dans `.env` : `API_SERVER_KEY=hermes-ios-shortcut-...`
- ⚠️ **La clé dans `config.yaml` (`gateway.api_server.extra.key`) peut différer de celle dans `.env` (`API_SERVER_KEY`)** — toujours utiliser la clé du `.env`, c'est celle que le gateway charge au démarrage

### Diagnostic : API server ne répond pas sur le port attendu
1. Vérifier que le gateway tourne : `hermes gateway status`
2. **Vérifier le port réel dans les logs** (pas la config) : `grep "listening" /opt/data/logs/gateway.log | tail -1`
3. Tester local : `curl -s -H "Authorization: Bearer $API_SERVER_KEY" http://127.0.0.1:<port réel>/v1/responses -X POST -H "Content-Type: application/json" -d '{"input":"test"}'`
4. Si `HERMES_DASHBOARD=false` dans l'environnement Docker, le service dashboard s6 est inactif MAIS l'api_server du gateway peut quand même tourner (c'est un platform adapter séparé du dashboard)
5. Vérifier la clé : `grep API_SERVER_KEY /opt/data/.env` — ne pas utiliser la clé de `config.yaml` qui peut être obsolète
