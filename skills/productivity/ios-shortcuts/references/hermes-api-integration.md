# Hermes API Server — Intégration iOS Shortcuts

## Architecture

```
iPhone (Shortcuts) → https://hermes-api.jefe.al/v1/responses
                     → Auth: Bearer <clé_API>
                     → Corps JSON champ par champ
                  → Pangolin Newt tunnel (site 6 Hetzner)
                  → 127.0.0.1:8642 (API Server Hermes)
                  → Réponse JSON → extraction → affichage
```

## ⚠️ Pitfall : Bug de sérialisation JSON iOS Shortcuts

**Problème :** Quand on construit un corps JSON avec des **tableaux de dictionnaires** (`messages` contenant `[{"role": "user", "content": "..."}]`), iOS Shortcuts sérialise mal le dictionnaire dans le tableau — il l'envoie comme une liste au lieu d'un objet. L'API reçoit une liste là où elle attend un dict, et plante en 500 :

```
AttributeError: 'list' object has no attribute 'get'
```

**Solution :** Utiliser l'endpoint **Responses API** (`/v1/responses`) au lieu de Chat Completions (`/v1/chat/completions`). Le corps est beaucoup plus simple : juste `{"input": "texte"}` + `{"model": "hermes-agent"}` — pas de tableau `messages[]`, pas de problème de sérialisation.

## Construction du JSON champ par champ (recommandé)

**PRÉFÉRER la construction champ par champ** via le menu **Corps → JSON** plutôt que de coller du JSON brut dans une action Texte.

### Pour `/v1/responses` (RECOMMANDÉ — évite le bug de sérialisation)

| Clé | Type | Valeur |
|-----|------|--------|
| `input` | **Texte** | *(variable magique du texte saisi)* |
| `model` | **Texte** | `hermes-agent` |

Les variables magiques s'insèrent par tap long sur le champ → sélectionner la variable.

### Pour `/v1/chat/completions` (ALTERNATIVE — peut causer bug de sérialisation)

1. **model** → Texte → `hermes-agent`
2. **stream** → Booléen → `Faux`/`false`
3. **messages** → **Tableau** (créer le tableau, puis ajouter 1 élément → choisir **Dictionnaire**)
   - Dans le dictionnaire :
     - `role` → Texte → `user`
     - `content` → Texte → *(variable magique)*

## Extraction de la réponse

### Pour `/v1/responses` → `output[0].content[0].text`

Structure de la réponse :
```json
{
  "object": "response",
  "status": "completed",
  "output": [{
    "type": "message",
    "role": "assistant",
    "content": [{
      "type": "output_text",
      "text": "la réponse"
    }]
  }],
  "id": "resp_..."
}
```

Chaîne d'extraction :

| # | Action Raccourcis | Paramètre |
|---|-------------------|-----------|
| 1 | **Obtenir la valeur d'un dictionnaire** | clé: `output` |
| 2 | **Obtenir un élément d'une liste** | index: `1` |
| 3 | **Obtenir la valeur d'un dictionnaire** | clé: `content` |
| 4 | **Obtenir un élément d'une liste** | index: `1` |
| 5 | **Obtenir la valeur d'un dictionnaire** | clé: `text` |
| 6 | **Afficher un résultat** (ou Prononcer le texte) | — |

⚠️ Les listes dans Raccourcis sont **1-indexed** (pas 0-indexed) — toujours index `1` pour le premier élément.

### Pour `/v1/chat/completions` → `choices[0].message.content`

| # | Action Raccourcis | Paramètre |
|---|-------------------|-----------|
| 1 | **Obtenir la valeur d'un dictionnaire** | clé: `choices` |
| 2 | **Obtenir un élément d'une liste** | index: `1` |
| 3 | **Obtenir la valeur d'un dictionnaire** | clé: `message` |
| 4 | **Obtenir la valeur d'un dictionnaire** | clé: `content` |
| 5 | **Afficher un résultat** (ou Prononcer le texte) | — |

## Prérequis côté serveur

- `API_SERVER_ENABLED=true` dans `.env` Hermes
- `API_SERVER_KEY=<clé>` (Bearer token)
- Gateway Hermes redémarrée (avec les nouvelles vars d'env)
- API Server écoute sur `127.0.0.1:8642`
- Ressource Pangolin (site resource) pointant vers `127.0.0.1:8642`
- Client Newt/Pangolin actif côté client (iPhone avec l'app Pangolin)
- Le container Docker Hermes doit être en `network_mode: host` pour que le Newt client atteigne `127.0.0.1:8642`

## En-têtes requis

Dans l'action « Obtenir le contenu d'une URL », ajouter ces en-têtes (pas dans le corps JSON) :

| Clé | Valeur |
|-----|--------|
| `Authorization` | `Bearer <clé_API>` |
| `Content-Type` | `application/json` |

## Déclencheurs iOS possibles

- **Bouton d'action** : Réglages → Bouton d'action → Raccourci → nom du shortcut
- **Écran d'accueil** : ⋮ sur le raccourci → Partager → Ajout à l'écran d'accueil
- **Siri** : « Dis Siri, [nom du raccourci] »
- **Widget** : Widget Raccourcis → choisir le raccourci
- **Feuille de partage** : Sélectionner un texte → Partager → le raccourci
- **Automatisation** : NFC, WiFi, Heure, Application, etc.

## Débogage

1. Ajouter **« Afficher Contenu de l'URL »** juste après l'appel API pour voir la réponse brute
2. Si "Private Placeholder" → le client Pangolin n'est pas actif sur l'iPhone
3. Si 404 → vérifier le chemin de l'URL (ne pas oublier `/v1/responses` ou `/v1/chat/completions`)
4. Si 500 "Server got itself in trouble" → probablement le bug de sérialisation → passer à `/v1/responses`
5. Si "Échec de conversion Texte en Dictionnaire" → la réponse n'est pas du JSON (vérifier client Pangolin)
