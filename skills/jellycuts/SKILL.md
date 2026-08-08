---
name: jellycuts
title: "Jellycuts & Langage Jelly"
description: "Guide complet du langage Jelly pour Jellycuts iOS : syntaxe exacte des fonctions Shortcuts Standard, dictionnaires JSON, appels API REST, conditions, boucles, menus, export."
author: "Hermes Agent"
version: "1.1"
triggers:
  - "jellycuts"
  - "jelly"
  - "langage jelly"
  - "jellycut"
  - "raccourci jelly"
  - "jelly code"
---

# Jellycuts & Langage Jelly

Jellycuts = app iOS qui compile du code **Jelly** en raccourcis Shortcuts signés, directement sur l'iPhone.

## Structure

```jelly
import Shortcuts
#Color: red, #Icon: shortcuts

text(text: "Hello World!") >> introduction
alert(alert: "${introduction}")
```

- `import Shortcuts` — OBLIGATOIRE en première ligne
- `#Color:`, `#Icon:` — métadonnées (couleur + icône)
- `fonction(param: valeur)` — appel d'une action Shortcuts
- `>> variable` — capture la sortie en **variable magique** (immuable)
- `"${variable}"` — interpolation dans une chaîne

### ⚠️ Règle importante : noms des variables globales
Les espaces dans les noms de variables sont **dépréciés** :
- `Shortcut Input` ❌ → `ShortcutInput` ✅
- `Current Date` ❌ → `CurrentDate` ✅ (vérifier si besoin)

---

## Variables

```jelly
var texte = "Hello"
var nombre = 42
var liste = ["a", "b", "c"]

x = "Nouvelle valeur"      // réaffectation
x += " ajouté"             // transforme en tableau (Add to Variable)

var multiligne = """
Ligne 1
Ligne 2
"""
```

### Variables globales (immuables)
| Variable | Usage |
|---|---|
| `ShortcutInput` | Entrée du raccourci |
| `Clipboard` | Presse-papier |
| `CurrentDate` | Date actuelle |
| `Ask` | Demander à l'utilisateur |

### Type casting
```jelly
var input = ShortcutInput.as(Text)
var dict = ShortcutInput.as(Dictionary)
```
Types : `Text`, `Number`, `Boolean`, `Dictionary`, `Date`, `URL`, `File`, `Image`, `PDF`, `Contact`, `Location`, `RichText`

---

## Actions API REST — `downloadURL`

**Nom exact :** `downloadURL` (PAS `contentsOfURL`)

### Paramètres (vérifiés depuis source OpenJelly)

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `url` | String | ✅ | URL de l'endpoint |
| `method` | Enum | ✅ | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `headers` | Dictionary | ✅ | Ex: `{"Content-Type": "application/json"}` |
| `requestType` | Enum | ✅ | `Json`, `Form`, `File` |
| `requestJSON` | Dictionary | ✅ | Body JSON (dictionnaire inline ou variable) |
| `requestVar` | Variable | ✅ | Variable de sortie (même que `>>`) |

**💡 Astuce :** `requestJSON` accepte les dictionnaires **inline** avec interpolation `${}`. Le `dictionary(json: "...")` n'est pas obligatoire.

```jelly
// POST avec inline dictionary (recommandé)
downloadURL(url: "https://translate.jefe.ovh/translate", method: POST, headers: {}, requestType: Json, requestJSON: {"q": "${text}", "source": "auto", "target": "fr", "api_key": "..."}, requestVar: response) >> response

// Alternative avec variable dictionnaire construite
dictionary(json: "{\"key\": \"${var}\"}") >> body
downloadURL(url: "https://api.exemple.com/submit", method: POST, headers: {"Content-Type": "application/json"}, requestType: Json, requestJSON: body, requestVar: result) >> result
```

### ⚠️ `extractTextFromImage` — OCR photo
Cette action existe mais est marquée comme **macOS 12 seulement** dans Jellycuts.
**Solution :** Jellycuts → ⚙️ Settings → activer **« Use functions from any version »**.

---

## Dictionnaires

### Créer via `dictionary(json: "...")`
```jelly
dictionary(json: "{\"name\": \"Toto\", \"age\": \"30\"}") >> monDict
```

Avec une variable en interpolation :
```jelly
var nom = "Toto"
dictionary(json: "{\"name\": \"${nom}\", \"age\": \"30\"}") >> monDict
```

### Extraire une valeur — `valueFor`
**Nom exact :** `valueFor` (PAS `getValueForKey`)

| Paramètre | Type | Description |
|---|---|---|
| `key` | String | La clé à extraire |

Le dictionnaire vient de l'entrée magique (l'action précédente).

```jelly
valueFor(key: "translatedText") >> traduction
```

---

## Afficher

| Fonction | Usage |
|---|---|
| `showResult(text: "${variable}")` | Popup résultat |
| `alert(alert: "${variable}")` | Alerte avec bouton OK |
| `quicklook(variable)` | Aperçu rapide |
| `sendNotification(body: "...", title: "...")` | Notification push |

---

## Conditions

```jelly
if(variable .contains "texte") {
    showResult(text: "OK")
} else {
    showResult(text: "Pas OK")
}
```

| Opérateur | Équivalent |
|---|---|
| `==` | Est égal à |
| `!=` | N'est pas |
| `.contains` | Contient |
| `!contains` | Ne contient pas |
| `.beginsWith` / `.endsWith` | Commence/finit par |
| `<` `>` `<=` `>=` | Comparaison numérique |
| `.between 1...10` | Entre 1 et 10 |
| `== nil` / `!= nil` | A / n'a pas de valeur |

---

## Boucles

```jelly
// Repeat simple
repeat(5) {
    // Repeat Index dispo
}

// Repeat Each (forEach)
repeatEach(maListe) {
    quicklook(Repeat Item)
    // Repeat Index aussi dispo
}
```

---

## Menus (choix utilisateur)

```jelly
menu("Choisis une option", ["Option 1", "Option 2"]) {
  case("Option 1"):
    showResult(text: "Un")
  case("Option 2"):
    showResult(text: "Deux")
}
```

---

## Cas concret : LibreTranslate (version corrigée)

```jelly
import Shortcuts
#Color: blue, #Icon: globe

var textToTranslate = ShortcutInput

dictionary(json: "{\"q\": \"${textToTranslate}\", \"source\": \"auto\", \"target\": \"fr\", \"api_key\": \"CLE_API_ICI\"}") >> body

downloadURL(url: "https://translate.jefe.ovh/translate", method: POST, requestType: Json, requestJSON: body, headers: {"Content-Type": "application/json"}, requestVar: body) >> apiResponse

valueFor(key: "translatedText") >> translated

showResult(text: "${translated}")
```

### Avec menu de sélection de langue

```jelly
menu("Langue cible", ["Anglais", "Espagnol", "Allemand", "Italien"]) {
  case("Anglais"):
    var lang = "en"
  case("Espagnol"):
    var lang = "es"
  case("Allemand"):
    var lang = "de"
  case("Italien"):
    var lang = "it"
}

dictionary(json: "{\"q\": \"${textToTranslate}\", \"source\": \"auto\", \"target\": \"${lang}\", \"api_key\": \"CLE_API_ICI\"}") >> body

downloadURL(url: "https://translate.jefe.ovh/translate", method: POST, requestType: Json, requestJSON: body, headers: {"Content-Type": "application/json"}, requestVar: body) >> apiResponse

valueFor(key: "translatedText") >> translated
showResult(text: "${translated}")
```

---

## Autres fonctions utiles (noms exacts depuis source)

| Fonction | Action Shortcuts correspondante |
|---|---|
| `text(text: "...")` | Text |
| `dictionary(json: "...")` | Dictionary |
| `downloadURL(...)` | Get Contents of URL |
| `valueFor(key: "...")` | Get Value For Key |
| `showResult(text: "...")` | Show Result |
| `alert(alert: "...")` | Send Alert |
| `notification(body: "...", title: "...")` | Send Notification |
| `runShortcut(name: "...", input: var)` | Run Shortcut |
| `quicklook(var)` | Quick Look |
| `url(url: "...")` | URL |
| `getURL(url: "...")` | Get URL |
| `encode(text: "...")` | Encode Base64 |
| `decode(base64: "...")` | Decode Base64 |
| `decode(base64: "...")` | Decode Base64 |
| `dictateText()` | Dictate Text (reconnaissance vocale) |
| `selectPhoto()` | Select Photo (galerie) |
| `takePhoto()` | Take Photo (appareil) |
| `extractTextFromImage(image: var)` | Extract Text From Image (OCR — nécessite réglage iOS) |
| `selectFile()` | Select File (sélecteur de fichiers) |
| `getTextFrom(input: var)` | Get Text From Input (.txt, .docx, .html, etc.) |
| `getTextFromPDF(input: var)` | Get Text From PDF |
| `setClipboard(variable: var)` | Set Clipboard (copier dans presse-papier) |
| `exit(var)` | Exit Shortcut |
| `wait(seconds: 5)` | Wait |
| `chooseFrom(list: [items], prompt: "...")` | Choose From List |

---

## Métadonnées (Couleur & Icône)

```jelly
#Color: red
#Icon: shortcuts
```

**Couleurs :** `red, orange, tangerine, yellow, green, teal, lightblue, blue, navy, grape, purple, pink, grayblue, graygreen, graybrown`

**Icônes :** 200+ disponibles dont `shortcuts, globe, car, house, bell, gear, heart, star, lightningbolt, camera, rocket, wifi, cloud, magnifyingglass, clock, musicnote, envelope, calendar, folder, pencil, trashcan, lock, key, trophy, magicwand, paintbrush, paperclip, scissors, hammer, wrench, speedometer, gauge, network`, etc. L'auto-complétion de l'app les liste toutes.

---

## Workflow de développement

1. **Créer un fichier** dans Jellycuts → `+` → `Nouveau Jellycut`
2. **Écrire le code** Jelly
3. **Build & Export** → compile, signe et envoie dans l'app Shortcuts
4. **Configurer le partage** : dans Shortcuts → `⋯` sur le raccourci → Activer **Feuille de partage**
5. **Tester** : sélectionner du texte → Partager → ton raccourci

### Débogage
- L'onglet **Terminal** dans Jellycuts montre les erreurs de compilation
- Si une fonction n'est pas trouvée, vérifie son nom exact (auto-complétion en tapant les premières lettres)
- Si une variable n'existe pas → utilisation de `>>` manquante, ou `var` absent
- Si `requestVar` manque → `downloadURL` ne compile pas sans ce paramètre

---

## Pitfalls / Bugs connus

### ⚠️ `requestJSON` n'accepte PAS un dictionnaire construit avec `setValue`
Faire `setValue(key:..., dictionary: body)` puis `requestJSON: body` → **« Unable to find valid JSON »**.
**✅ Solution :** Toujours utiliser un **dictionnaire inline** pour `requestJSON` :
```jelly
requestJSON: {"q": "${text}", "source": "auto", "target": "fr"}
```

### ⚠️ `extractTextFromImage` est marqué macOS 12+ et bloque sur iOS 18
Jellycuts marque cette OCR comme macOS only.
**✅ Solution :** Jellycuts → ta **Project Settings** (⚙️ du projet) → activer **« Use functions from any version »**.

### ⚠️ Espaces dans les variables globales dépréciés
`Shortcut Input` → erreur/warning « Spaces in variable names have been deprecated ».
**✅ Solution :** Utiliser `ShortcutInput` (sans espace, camelCase).

### ⚠️ `valueFor` requiert les deux paramètres
`valueFor(key: "translatedText")` tout seul → warning.
**✅ Solution :** Le dictionnaire vient de l'entrée magique de l'action précédente — tu n'as pas besoin de repasser `dictionary:` explicitement si la magie est bien chainée, mais si warning, ajoute `valueFor(key: "translatedText", dictionary: apiResponse)`.

### ⚠️ `selectPhoto` pour la galerie, `takePhoto` pour l'appareil
- `selectPhoto()` → sélection dans l'album photo (types, multiple en option)
- `takePhoto()` → déclenche l'appareil photo (camera, preview, count en option)

### ⚠️ Warnings optionnels = inoffensifs
Des warnings comme « Could not find any content for parameter language in dictateText » ou « parameter count in takePhoto » sont juste des paramètres optionnels non renseignés. Ça compile et ça marche.

---

## Notes importantes
- `import Shortcuts` TOUJOURS en première ligne
- **Les noms de fonctions sont en camelCase** : `showResult`, `downloadURL`, `valueFor`, `runShortcut`
- **Les noms de variables globales : SANS espaces** : `Shortcut Input` → `ShortcutInput` ✅
- Les variables magiques (`>> nom`) sont **immuables** — pour muter, copier dans `var`
- `Build & Export` gère la signature automatiquement
- Auto-complétion intégrée : tape `downloadURL(` pour voir les paramètres
- **Paramètres projets** : Jellycuts → ⚙️ Project Settings → « Use functions from any version » (nécessaire pour certaines actions comme l'OCR)
