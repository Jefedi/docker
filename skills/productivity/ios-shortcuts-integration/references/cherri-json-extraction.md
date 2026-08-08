# Cherri — Extraction JSON dans Shortcuts (confirmé juillet 2026)

## Le problème en 3 niveaux

### Niveau 1 : `@dict['key']` ≠ extraction

`@dict['key']` compile en `is.workflow.actions.setvariable` (copie de variable) et NON en `is.workflow.actions.getvalueforkey`. L'extraction ne se fait jamais. Le raccourci s'exécute sans erreur mais la variable de sortie est identique à l'entrée (copie, pas extraction de clé).

### Niveau 2 : `getValue()` exige un type `dictionary`

`getValue(@var, "key")` refuse les variables — erreur de compilation : "Invalid variable value of action 'getValue()' (variable) for argument 'dictionary' (dictionary)". La fonction exige un argument de type `dictionary`, mais `getFirstItem()` retourne un type `variable`.

### Niveau 3 : `getDictionary()` intermédiaire corrompt les données

Ajouter `getDictionary()` avant chaque `getValue()` compile sans erreur, mais Shortcuts retourne du VIDE à l'extraction. Testé avec alert() à chaque étape :

- Step 5 : `getDictionary(@first)` → contient des données ✅
- Step 6 : `getValue(@firstDict, "content")` → VIDE ❌

Le parsing intermédiaire `detect.dictionary` perd les clés du dictionnaire original.

### ✅ Solution : action definition avec type `variable`

Définir une action personnalisée qui accepte le type `variable` au lieu de `dictionary` :

```
action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)
```

Le type `variable` accepte n'importe quelle sortie d'action (y compris `getFirstItem()`). Le compilateur génère bien `is.workflow.actions.getvalueforkey` avec `WFInput` contenant la variable et `WFDictionaryKey` contenant la clé.

### Chaîne d'extraction validée

```
@output = dictGet(@response, "output")
@first = getFirstItem(@output)
@content = dictGet(@first, "content")
@firstContent = getFirstItem(@content)
@text = dictGet(@firstContent, "text")
show("{@text}")
```

Génère : 3× `getvalueforkey` + 2× `getitemfromlist` + 1× `showresult` = extraction complète.

### Mythe réfuté : les espaces ne sont PAS le problème

Hypothèse initiale : `show("{@text}")` cassait avec des espaces dans la variable.
Réalité : l'extraction (`getDictionary()` + `getValue()`) retournait du vide, donc `show()` affichait du vide. Avec `dictGet()`, `show("{@text}")` affiche correctement le texte même avec des espaces.

## Diagnostic

Compiler avec `--debug` et inspecter le plist :

```python
import plistlib
with open('inspect.plist', 'rb') as f:
    data = plistlib.load(f)
actions = data.get('WFWorkflowActions', [])
print(f'Total actions: {len(actions)}')
for i, a in enumerate(actions):
    ident = a.get('WFWorkflowActionIdentifier', '?')
    params = a.get('WFWorkflowActionParameters', {})
    extra = ''
    if 'WFDictionaryKey' in params:
        extra = f" key={params['WFDictionaryKey']}"
    print(f'  {i}: {ident}{extra}')
```

Si `is.workflow.actions.getvalueforkey` n'apparaît pas, l'extraction ne se fera pas. Si `is.workflow.actions.detect.dictionary` apparaît entre les extractions, les données seront corrompues.

## Debug avec alert() étape par étape

Quand l'extraction échoue silencieusement, ajouter un `alert()` après chaque étape :

```
alert("1/ response: {@response}", "Step 1")
@output = dictGet(@response, "output")
alert("2/ output: {@output}", "Step 2")
@first = getFirstItem(@output)
alert("3/ first: {@first}", "Step 3")
// etc.
```

L'alerte qui affiche du vide indique exactement où l'extraction casse.

## API Hermes — endpoint correct

- Local : `http://127.0.0.1:9119/v1/responses` (vérifier le port réel dans les logs)
- Via Pangolin : `https://hermes.jefe.al/api/v1/responses` (préfixe `/api` ajouté par Pangolin)
- Clé API : `API_SERVER_KEY` du fichier `.env` (pas `config.yaml`)
- Headers requis : `Authorization: Bearer <clé>` + `Content-Type: application/json`
- Body : `{"input": "question ici"}`
- Réponse : `output[0].content[0].text` contient le texte de la réponse

## Actions natives iOS via action definitions

### Rappels (Add New Reminder)

```
action 'is.workflow.actions.addreminders' addReminder(
    variable input: 'WFInput'
)

@titre = prompt("Titre du rappel :")
addReminder(@titre)
```

Le raccourci ouvre l'app Rappels pour confirmer. Sync iCloud automatique.

### Calendrier (Add New Event)

```
action 'is.workflow.actions.addevent' addEvent(
    variable input: 'WFInput'
)

@titre = prompt("Titre de l'event :")
addEvent(@titre)
```

Le raccourci ouvre l'app Calendrier pour confirmer. Sync iCloud ou Radicale (CalDAV).

### Pattern général pour actions natives non-implémentées

```
action 'is.workflow.actions.<IDENTIFIER>' customAction(
    variable input: 'WFInput',
    text ?key: 'WFParameterKey'
)
```

Le type `variable` est essentiel pour accepter la sortie d'autres actions. Le type `dictionary` échouera si l'entrée vient de `getFirstItem()` ou d'une autre action retournant un type `variable`.