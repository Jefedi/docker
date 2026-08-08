---
name: cherri-shortcuts
title: "Cherri — Raccourcis iOS signes"
description: "Use when creating signed iOS Shortcuts via Cherri."
version: "1.0"
author: "Hermes Agent"
triggers:
  - "cherri"
  - "raccourci cherri"
  - "shortcut cherri"
  - "playground cherri"
  - "compiler raccourci"
  - "signer raccourci"
---

# Cherri — Compiler des raccourcis iOS signés

## Principe

Cherri = langage de programmation qui compile vers un fichier `.shortcut` Apple signé.
Le **Playground** (https://playground.cherrilang.org/) permet de compiler + signer **gratuitement** depuis un navigateur, sans macOS, sans compte, sans app.

## Flow pour l'utilisateur

1. Hermes génère le code `.cherri`
2. L'utilisateur va sur https://playground.cherrilang.org
3. Il colle le code dans l'éditeur
4. Il clique sur le **marteau** (hammer) pour compiler
5. Il clique sur la **flèche montante** (square_arrow_up) pour exporter
6. Il clique sur **Download Shortcut** → signature via HubSign (~3s)
7. Le fichier `.shortcut` signé (format AEA1) se télécharge
8. L'utilisateur l'ouvre dans l'app **Fichiers** → **Ajouter le raccourci**

## Playground — Limitations critiques

### ❌ `#include` ne génère PAS d'actions dans le playground

Le compilateur web du playground (compilation côté serveur via POST `/compile`) ne charge **pas** les includes de la même façon que le CLI. Un code avec `#include 'actions/web'` compile sans erreur mais produit **"This Shortcut contains 0 actions"**.

### ✅ Actions de base (basic) — automatiquement incluses

Ces actions fonctionnent dans le playground SANS `#include` :
- `prompt(text, ?inputType, ?defaultValue, ?multiline)` — Demander une entrée
- `alert(text, ?title)` — Alerte avec bouton OK
- `confirm(text, ?title)` — Alerte avec OK + Annuler
- `show(text)` — Afficher un résultat
- `showNotification(text body, ?title, ?playSound, ?attachment)` — Notification
- `quicklook(variable)` — Aperçu rapide
- `output(text)` — Stop et output
- `stop()` — Arrêter le raccourci
- `wait(number)` — Attendre N secondes
- `comment(rawtext)` — Commentaire
- `number(variable)`, `text(...)`, `list(...)`, `count(...)`, `typeOf(...)`
- Dictionnaires : `getDictionary`, `getValue(dict, key)`, `setValue(dict, key, value)`, `getKeys`, `getValues`
- Listes : `chooseFromList`, `getFirstItem`, `getLastItem`, `getListItem`, `list(...)`
- `nothing()` — Effacer la sortie courante

### 🟡 `action` definitions — partiellement fonctionnel dans le playground

Les action definitions fonctionnent pour les actions **builtin** (ex: `action 'alert'`) mais **ne génèrent PAS d'actions** pour les identifiants non-builtin (ex: `is.workflow.actions.downloadurl`). Le playground compile l'action definition sans erreur mais produit "0 actions".

**Testé le 2026-07-30** : `action 'is.workflow.actions.downloadurl'` → 0 actions dans le playground.
**Testé le 2026-07-30** : `action 'alert'` → ✅ génère une action "Show alert" dans le playground.

### ❌ Requêtes HTTP dans le playground — NON fonctionnel

Il n'y a **aucun moyen** de faire une requête HTTP dans le playground web :
- `#include 'actions/web'` + `jsonRequest()` → 0 actions
- `action 'is.workflow.actions.downloadurl'` → 0 actions
- `rawAction("is.workflow.actions.downloadurl", ...)` → 0 actions

Pour les raccourcis qui nécessitent des requêtes HTTP, il faut **soit** utiliser le CLI Cherri (à installer sur le serveur — demander permission), **soit** construire le raccourci manuellement dans l'app Shortcuts sur iPhone.

### ❌ `rawAction` — ne génère PAS d'actions dans le playground

Malgré la doc, `rawAction()` compile mais produit "0 actions" dans le playground.

## Syntaxe Cherri — Référence rapide

### Définitions

```
#define name "Mon Raccourci"
#define glyph shortcuts
#define color blue
```

Couleurs : red, orange, yellow, green, blue, purple, pink, gray, etc.
Glyphe : shortcuts, bell, star, globe, calendar, clock, envelope, etc.

### Variables

```
@maVar = "texte"
@maVar = 42
@maVar = true
@maVar = {"key": "value"}
@maVar = ["item1", "item2"]
```

### Constants (magic variables)

```
const resultat = prompt("Question ?")
show("{resultat}")
```

### Interpolation

```
@nom = "Hermes"
@message = "Bonjour {@nom} !"
```

### Accès dictionnaire

```
@dict = {"name": "test"}
@valeur = @dict['name']
```

### Conditions

```
if @var == "test" {
    alert("OK")
} else {
    alert("Pas OK")
}
```

Opérateurs : `==`, `!=`, `contains`, `!contains`, `beginsWith`, `endsWith`, `>`, `>=`, `<`, `<=`
Multiple : `&&` (And), `||` (Or)

### Boucles

```
repeat i for 5 {
    alert("Iteration {@i}")
}

for item in @maListe {
    show("{item}")
}
```

### Menus

```
menu "Choisir" {
    item "Option 1":
        alert("Un")
    item "Option 2":
        alert("Deux")
}
```

### Globals

```
@input = ShortcutInput
@date = CurrentDate
@clipboard = Clipboard
@device = Device
```

### Ask Each Time

```
wait(Ask: 'Combien de secondes ?')
@nom = "Mon nom est {Ask}"
```

## Extraction JSON — CRITIQUE

### ❌ `@var['key']` ne génère PAS d'action "Get Dictionary Value"

La syntaxe `@response['output']` compile en `setvariable` (copie de variable) et NON en `getvalueforkey`. L'extraction ne se fait jamais.

### ❌ `getValue(@var, "key")` exige un type `dictionary`, pas `variable`

`getValue()` refuse les variables (sortie de `getFirstItem`, etc.) — erreur de compilation : "Invalid variable value for argument 'dictionary'".

### ❌ `getDictionary()` entre chaque étape corrompt les données

Ajouter `getDictionary()` avant chaque `getValue()` compile, mais Shortcuts retourne du vide à l'extraction (testé : step 6 "content" = vide). Le parsing intermédiaire perd les clés.

### ✅ Solution : action definition avec type `variable`

Définir une action personnalisée qui accepte le type `variable` (pas `dictionary`) :

```
action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)
```

Puis l'utiliser pour chaque extraction :
```
@output = dictGet(@response, "output")
@first = getFirstItem(@output)
@content = dictGet(@first, "content")
@firstContent = getFirstItem(@content)
@text = dictGet(@firstContent, "text")
show("{@text}")
```

Vérifié le 2026-07-30 : génère bien 3 actions `getvalueforkey` avec les clés correctes, et le texte s'affiche dans Shortcuts.

## Signature

- Le playground signe via **HubSign** (RoutineHub) — gratuit, sans compte
- Le fichier généré est au format **AEA1** (Apple Encrypted Archive)
- Le bouton "Download Shortcut" affiche "Signing..." pendant ~3s puis télécharge le fichier

## Conteneur Docker Cherri (setup serveur)

Un conteneur Docker isolé compile et signe les raccourcis. Le conteneur n'a accès qu'au dossier de travail, pas au reste du serveur.

### Images

- `cherri-builder` — Alpine + binaire Cherri v2.3.0 (compilation + signature HubSign)
- `cherri-smb` — cherri-builder + samba-client (upload direct vers NAS)

### Compilation + upload NAS

```bash
# Le code .cherri est dans /opt/data/home/workspace/cherri-builder/output/
# Le NAS est accessible via SMB: //100.64.0.1/raccourci_ios

docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh \
  cherri-smb -c '
    cd /work
    rm -f /work/*Hermes*.shortcut /work/*.plist 2>/dev/null
    cherri /work/parler_hermes.cherri 2>&1
    for f in /work/*Hermes*.shortcut; do cp "$f" /work/upload.shortcut; break; done
    smbclient "//100.64.0.1/raccourci_ios" -U "ax42-SMB%<password>" \
      -c "put /work/upload.shortcut Parler_Hermes.shortcut; ls" 2>&1
    rm -f /work/*Hermes*.shortcut /work/*.plist /work/upload.shortcut 2>/dev/null
  '
```

⚠️ Le volume mount doit utiliser le chemin **hôte** (`/srv/docker/hermes/.hermes/...`), pas le chemin container (`/opt/data/...`), car Docker tourne sur le host.

### Inspection du plist (debug)

Pour vérifier les actions générées :
```bash
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-builder -c '
    cd /work
    cherri /work/mon_raccourci.cherri --debug 2>&1 | tail -3
    for f in /work/*.plist; do cp "$f" /work/inspect.plist; break; done
  '
# Puis sur le host:
python3 -c "
import plistlib
with open('/opt/data/home/workspace/cherri-builder/output/inspect.plist', 'rb') as f:
    data = plistlib.load(f)
for i, a in enumerate(data.get('WFWorkflowActions', [])):
    ident = a.get('WFWorkflowActionIdentifier', '?')
    params = a.get('WFWorkflowActionParameters', {})
    extra = ''
    if 'WFDictionaryKey' in params: extra = f\" key={params['WFDictionaryKey']}\"
    if 'WFItemSpecifier' in params: extra = f\" spec={params['WFItemSpecifier']}\"
    print(f'  {i}: {ident}{extra}')
"
```

## Raccourci "Parler a Hermes" — Code final fonctionnel

```cherri
#include 'actions/web'

#define name "Parler a Hermes"
#define glyph shortcuts
#define color blue

action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)

@question = prompt("Pose ta question a Hermes :")

@response = jsonRequest("https://hermes.jefe.al/api/v1/responses", 'POST', {"input": "{@question}"}, {"Authorization": "Bearer hermes-ios-shortcut-a80ac18a29ed5d62", "Content-Type": "application/json"})

@output = dictGet(@response, "output")
@first = getFirstItem(@output)
@content = dictGet(@first, "content")
@firstContent = getFirstItem(@content)
@text = dictGet(@firstContent, "text")

show("{@text}")
```

### Points clés du code final
1. `#include 'actions/web'` — requis pour `jsonRequest()` (CLI uniquement, pas le playground)
2. `action 'is.workflow.actions.getvalueforkey' dictGet(variable, text)` — CRITIQUE : le type `variable` (pas `dictionary`) permet d'accepter la sortie de `getFirstItem()`
3. `jsonRequest(url, 'POST', {body}, {headers})` — body doit être un littéral inline (pas une variable)
4. Extraction : `output` → `getFirstItem` → `content` → `getFirstItem` → `text` (3x dictGet + 2x getFirstItem)
5. `show("{@text}")` — affiche le texte extrait

## Vérification systématique des actions (OBLIGATOIRE)

**APRÈS chaque compilation et AVANT d'uploader/distribuer un raccourci**, inspecter le plist généré pour vérifier que TOUS les identifiants d'actions sont des identifiants iOS valides.

### Procédure

1. Compiler avec `-d` pour générer le plist :
```bash
docker run --rm --entrypoint sh \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder:/work \
  -w /work/output \
  cherri-builder -c 'cherri mon_raccourci.cherri -d 2>&1' | tail -3
```

2. Inspecter le plist avec Python :
```python
import plistlib
with open('chemin/vers/shortcut.plist', 'rb') as f:
    data = plistlib.load(f)
actions = data.get('WFWorkflowActions', [])
suspicious = []
for i, a in enumerate(actions):
    ident = a.get('WFWorkflowActionIdentifier', '?')
    if not ident.startswith('is.workflow.actions.'):
        suspicious.append((i, ident))
    if 'rawaction' in ident:
        suspicious.append((i, ident))
    # formatdate sans point = invalide (le vrai = format.date)
    if 'formatdate' in ident and 'format.date' not in ident:
        suspicious.append((i, ident))
if suspicious:
    print(f"⚠️ {len(suspicious)} ACTIONS INVALIDES:")
    for i, ident in suspicious:
        print(f"  {i}: {ident}")
else:
    print(f"✅ {len(actions)} actions, toutes valides")
```

3. Si une action est suspecte, la corriger dans le `.cherri` et recompiler.

### Règles de validation des identifiants

- **Format valide** : `is.workflow.actions.<identifiant_en_minuscules_avec_points>`
- **Identifiants connus invalides** (générés par des action definitions custom incorrectes) :
  - `is.workflow.actions.formatdate` → utiliser le built-in `formatDate()` avec `#include 'actions/calendar'` (génère `is.workflow.actions.format.date`)
  - `is.workflow.actions.rawaction` → ne JAMAIS utiliser `rawAction()`, toujours `action` definitions
- **Si une action definition custom génère un identifiant qui n'existe pas dans iOS**, iOS affichera "action does not exist" à l'exécution. Pour vérifier si un identifiant est valide : `cherri --action=<nom>` liste les actions connues.

## Signature

- Le CLI signe via **HubSign** (RoutineHub) — gratuit, sans compte
- Le playground signe aussi via HubSign (bouton Export → Download Shortcut)
- Le fichier généré est au format **AEA1** (Apple Encrypted Archive)
- Vérifier : `python3 -c "print(open('file.shortcut','rb').read(4))"` → `b'AEA1'`

## Playground vs CLI

| Feature | Playground web | CLI (conteneur Docker) |
|---------|---------------|----------------------|
| Actions de base (alert, prompt, show) | ✅ | ✅ |
| `#include 'actions/web'` (jsonRequest) | ❌ 0 actions | ✅ |
| `rawAction()` | ❌ 0 actions | ✅ |
| `action` definitions (builtin) | ✅ | ✅ |
| `action` definitions (non-builtin) | ❌ 0 actions | ✅ |
| Signature HubSign | ✅ | ✅ |
| Upload direct NAS | ❌ | ✅ (avec cherri-smb) |

**Conclusion** : Pour les raccourcis avec requêtes HTTP, utiliser le CLI en conteneur Docker. Le playground ne fonctionne que pour les raccourcis simples (alertes, prompts, conditions, boucles).

## Pitfalls

1. **`#include` dans le playground** → "0 actions". Utiliser le CLI en conteneur.
2. **`rawAction()` dans le playground** → "0 actions". Utiliser `action` definitions.
3. **`@var['key']`** → compile en `setvariable` (copie), PAS en `getvalueforkey` (extraction). Utiliser `dictGet()`.
4. **`getValue()` avec variable** → erreur compilation. Utiliser `dictGet()` avec type `variable`.
5. **`getDictionary()` intermédiaire** → corrompt les données, retourne vide. Ne PAS utiliser entre les extractions.
6. **Dictionnaires en paramètre** → doivent être des littéraux inline, pas des variables.
7. **Variables globales avec espaces** → déprécié, utiliser camelCase (`ShortcutInput` pas `Shortcut Input`).
8. **Enums en paramètre** → utiliser string avec quotes simples (`'POST'` pas `POST`).
9. **Accents dans `#define name`** → éviter, utiliser sans accents.
10. **Nom du fichier de sortie** → Cherri génère un fichier avec le nom du shortcut entre guillemets (`"Parler a Hermes".shortcut`). Copier avec `for f in /work/*Hermes*.shortcut; do cp "$f" /work/upload.shortcut; break; done`.
11. **Volume Docker** → utiliser le chemin hôte (`/srv/docker/hermes/.hermes/...`), pas le chemin container (`/opt/data/...`).
12. **NE JAMAIS installer Cherri sur le serveur sans demander explicitement a l'utilisateur.**
13. **NE JAMAIS supprimer des fichiers sans demander explicitement a l'utilisateur.**
14. **`rawAction()` génère `is.workflow.actions.rawaction` au lieu du vrai identifiant** → iOS refuse l'action ("action did not exist"). **TOUJOURS** utiliser `action` definitions au lieu de `rawAction()`. Exemple : `action 'is.workflow.actions.dictatetext' dictateText(text language: 'WFLanguage')` puis `@texte = dictateText("fr-FR")`. Ne JAMAIS utiliser `rawAction("is.workflow.actions.dictatetext", {})` — ça compile mais crashe sur iOS.
15. **`rawAction()` avec dict vide `{}` fait panic le compilo** → `interface conversion: interface {} is nil`. Si on doit utiliser rawAction (déconseillé), toujours passer au moins un paramètre. Mais préférer `action` definitions.
16. **`setClipboard()`, `show()`, `quicklook()`** acceptent une **variable** (`@var`), PAS une string interpolée (`"{@var}"`). String interpolée = erreur de compilation "Invalid value (text) for argument 'value' (variable)".
17. **`formatDate()` nécessite `#include 'actions/calendar'`**. NE JAMAIS définir une action custom `action 'is.workflow.actions.formatdate'` — l'identifiant est **invalide pour iOS** ("action does not exist"). L'identifiant correct généré par le built-in est `is.workflow.actions.format.date` (avec un point). Utiliser : `formatDate(CurrentDate, "Custom", "dd-MM-yyyy")` — le 2e arg est l'enum `dateFormats` ("Custom"), le 3e est le pattern.