# Action Definitions Cherri v2.3.0 — Validées

Ces action definitions remplacent `rawAction()` qui génère `is.workflow.actions.rawaction` (identifiant invalide iOS).

## Format général

```cherri
action 'is.workflow.actions.<identifiant>' nomFunction(
    <type> <paramCherri>: '<paramIOS>'
)
```

- `<type>` : `text`, `variable`, `number`, `bool`
- `<paramCherri>` : nom local du paramètre dans le code Cherri
- `<paramIOS>` : clé du paramètre dans le plist WFWorkflowActionParameters

## Actions validées

### dictatetext — Dictée vocale

```cherri
action 'is.workflow.actions.dictatetext' dictateText(
    text language: 'WFLanguage'
)
// Usage: @texte = dictateText("fr-FR")
```

Génère : `is.workflow.actions.dictatetext` avec `WFLanguage: "fr-FR"` ✅

### documentpicker.getFile — Sélecteur de fichier

```cherri
action 'is.workflow.actions.documentpicker.getFile' pickFile(
    text fileType: 'WFFileType'
)
// Usage: @fichier = pickFile("public.item")
```

Génère : `is.workflow.actions.documentpicker.getFile` avec `WFFileType: "public.item"` ✅

### documentpicker.scan — Scanner de document

```cherri
action 'is.workflow.actions.documentpicker.scan' scanDoc(
    text documentType: 'WFDocumentType'
)
// Usage: @fichier = scanDoc("public.item")
```

Génère : `is.workflow.actions.documentpicker.scan` avec `WFDocumentType: "public.item"` ✅

### getcontentsofurl — Requête HTTP

```cherri
action 'is.workflow.actions.getcontentsofurl' fetchURL(
    text url: 'URL',
    text method: 'WFHTTPMethod',
    variable formData: 'WFFormData'
)
// Usage: @resp = fetchURL("https://example.com/api", "POST", @formData)
```

Génère : `is.workflow.actions.getcontentsofurl` avec URL, method, WFFormData ✅

⚠️ Pour les requêtes JSON simples, préférer `jsonRequest()` (builtin) qui génère `is.workflow.actions.downloadurl`.

### documentstorage.savefile — Enregistrer un fichier

```cherri
action 'is.workflow.actions.documentstorage.savefile' saveFile(
    variable file: 'WFFile'
)
// Usage: saveFile(@downloadedFile)
```

Génère : `is.workflow.actions.documentstorage.savefile` avec `WFFile` ✅

### formatdate — ❌ NE PAS utiliser en action definition

```cherri
// ❌ NE PAS FAIRE ÇA — l'identifiant is.workflow.actions.formatdate N'EXISTE PAS dans iOS
action 'is.workflow.actions.formatdate' formatDate(
    variable date: 'WFDate',
    text format: 'WFDateFormat'
)
```

Génère : `is.workflow.actions.formatdate` — **invalide pour iOS** ("action does not exist") ❌

### ✅ Solution : built-in formatDate avec #include 'actions/calendar'

```cherri
#include 'actions/calendar'
// Usage: @today = formatDate(CurrentDate, "Custom", "dd-MM-yyyy")
```

Génère : `is.workflow.actions.format.date` (avec un point) — **valide** ✅

La signature du built-in est : `formatDate(text date, dateFormats ?dateFormat = "Short", text ?customDateFormat): text`
- 2e argument : enum `dateFormats` (`"None"`, `"Short"`, `"Medium"`, `"Long"`, `"Relative"`, `"RFC 2822"`, `"ISO 8601"`, `"Custom"`)
- 3e argument : pattern custom (quand `dateFormat = "Custom"`)

### createnote — Créer une note (app Notes)

```cherri
action 'is.workflow.actions.createnote' createNote(
    variable body: 'NoteBody'
)
// Usage: createNote(@noteContent)
```

Génère : `is.workflow.actions.createnote` avec `NoteBody` ✅

⚠️ Pour Obsidian, utiliser `openURL("obsidian://new?...")` (builtin) au lieu de `createNote`.

### getvalueforkey — Extraction dictionnaire (CRITIQUE)

```cherri
action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)
// Usage: @value = dictGet(@response, "key")
```

Génère : `is.workflow.actions.getvalueforkey` avec `WFDictionaryKey` ✅

⚠️ Le type doit être `variable` (pas `dictionary`) pour accepter la sortie d'autres actions.

## Builtins — NE PAS redéfinir

Ces fonctions sont déjà disponibles sans `action` definition. Les redéfinir → "Duplicate declaration".

| Builtin | Action iOS générée |
|---------|-------------------|
| `jsonRequest(url, method, body, headers)` | `is.workflow.actions.downloadurl` |
| `openURL(url)` | `is.workflow.actions.openurl` |
| `setClipboard(variable)` | `is.workflow.actions.setclipboard` |
| `show(variable)` | `is.workflow.actions.showresult` |
| `quicklook(variable)` | `is.workflow.actions.previewdocument` |
| `showNotification(body, title, sound)` | `is.workflow.actions.notification` |
| `prompt(text, inputType, default, multiline)` | `is.workflow.actions.ask` |
| `alert(text, title)` | `is.workflow.actions.alert` |
| `confirm(text, title)` | `is.workflow.actions.confirm` |
| `getFirstItem(variable)` | `is.workflow.actionsgetitemfromlist` |
| `getLastItem(variable)` | `is.workflow.actions.getlastitemfromlist` |
| `getListItem(variable, index)` | `is.workflow.actionsgetitemfromlist` |

## Testing

Après compilation, vérifier le plist pour confirmer qu'aucun identifiant invalide n'apparaît :

```python
import plistlib
with open('inspect.plist', 'rb') as f:
    data = plistlib.load(f)
actions = data.get('WFWorkflowActions', [])
suspicious = []
for i, a in enumerate(actions):
    ident = a.get('WFWorkflowActionIdentifier', '')
    if 'rawaction' in ident:
        suspicious.append((i, ident, 'rawaction found'))
    if 'formatdate' in ident and 'format.date' not in ident:
        suspicious.append((i, ident, 'formatdate without dot — use built-in formatDate()'))
    if not ident.startswith('is.workflow.actions.'):
        suspicious.append((i, ident, 'invalid prefix'))
if suspicious:
    for i, ident, reason in suspicious:
        print(f'❌ Action {i}: {ident} — {reason}')
else:
    print(f'✅ {len(actions)} actions, toutes valides')
```