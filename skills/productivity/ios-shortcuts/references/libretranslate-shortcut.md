# Shortcut Traduire — LibreTranslate (translate.jefe.ovh)

Construction d'un shortcut de traduction via API LibreTranslate auto-hébergée.

## Architecture du shortcut
1. **Entrée** : texte sélectionné via la Feuille de partage
2. **Variable** : stocker le texte dans `textATraduire`
3. **Dictionnaire** : construire le payload JSON
4. **Requête HTTP** : POST vers l'API
5. **Extraction** : récupérer `translatedText` du JSON réponse
6. **Affichage** : montrer le résultat

## Détail de l'API

| Propriété | Valeur |
|---|---|
| URL | `https://translate.jefe.ovh/translate` |
| Méthode | POST |
| En-têtes | `Content-Type: application/json` |
| Corps | `{"q": "...", "source": "auto", "target": "fr", "api_key": "..."}` |
| Réponse | `{"translatedText": "..."}` |
| Langues dispo | ~50 langues (en→fr, fr→en, auto, etc.) |
| Port back-end | 5000 (LibreTranslate) |
| Infra | VPS Hetzner via Pangolin |

## Clé API
- LibreTranslate tourne avec `--api-keys`
- La clé est passée dans le corps JSON : `api_key`
- Stockage : GitHub Secrets (`LT_API_KEY`) ou directement dans le dictionnaire du shortcut

## Étapes de construction (sur iPhone)

### Étape 1 — Récupérer l'entrée
Action : **Obtenir une variable** → `Entrée du raccourci`

### Étape 2 — Stocker dans une variable
Action : **Définir la variable** → nom = `textATraduire`

### Étape 3 — Construire le dictionnaire
Action : **Définir un dictionnaire**  
| Clé | Valeur |
|---|---|
| `q` | Variable magique `textATraduire` |
| `source` | `auto` |
| `target` | `fr` |
| `api_key` | [ta clé API] |

### Étape 4 — Envoyer la requête
Action : **Obtenir le contenu d'une URL**
- Méthode : POST
- URL : `https://translate.jefe.ovh/translate`
- Corps : JSON → variable magique du dictionnaire
- En-têtes : `Content-Type: application/json`

### Étape 5 — Extraire la traduction
Action : **Obtenir la valeur d'un dictionnaire** → clé = `translatedText`

### Étape 6 — Afficher
Action : **Afficher un résultat**

## Activation Feuille de partage
Dans les paramètres du shortcut (⚙️) : activer « Utiliser comme action de feuille de partage », type d'entrée = Texte.

## Variante avec choix de langue
Insérer **« Demander une liste »** après l'étape 2 avec les choix :
- Français → `fr`
- Anglais → `en`
- Espagnol → `es`
- Allemand → `de`
Puis un bloc **« Si »** pour assigner le code à une variable `codeLangue`, et utiliser cette variable dans le dictionnaire à la place de `"fr"`.
