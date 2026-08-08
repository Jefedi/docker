# Template complet GitHub Actions pour génération de shortcuts iOS

## Structure du repo
```
mon-repo/
├── .github/
│   └── workflows/
│       └── generate-shortcut.yml
├── generate_shortcut.py
└── README.md
```

## Workflow (`.github/workflows/generate-shortcut.yml`)
```yaml
name: Générer le Raccourci

on:
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Générer le shortcut + JSON
        run: python3 generate_shortcut.py
        env:
          API_KEY: ${{ secrets.API_KEY }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: Mon-Raccourci
          path: |
            MonRaccourci.shortcut
            MonRaccourci.json
```

## Script Python (`generate_shortcut.py`)
```python
import plistlib, json, os

API_KEY = os.environ.get("API_KEY", "TA_CLE_ICI")

shortcut = {
    'WFWorkflow': {
        'WFWorkflowClientRelease': '18.0',
        'WFWorkflowClientVersion': '1302.1.3',
        'WFWorkflowIcon': {
            'WFWorkflowIconStartColor': 4282601983,
            'WFWorkflowIconGlyphNumber': 61440
        },
        'WFWorkflowImportQuestions': [],
        'WFWorkflowInputContentItemClasses': ['WFTextContentItem'],
        'WFWorkflowMinimumClientVersion': 1300,
        'WFWorkflowMinimumClientVersionString': '1300',
        'WFWorkflowOutputContentItemClasses': [],
        'WFWorkflowHasOutputFallback': False,
        'WFWorkflowTypes': ['ActionExtension'],
        'WFWorkflowHasShortcutInputVariables': True,
        'WFWorkflowName': 'Mon Raccourci',
        'WFWorkflowActions': [
            # Actions ici — voir action_identifiers.md
        ]
    }
}

with open('MonRaccourci.shortcut', 'wb') as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
with open('MonRaccourci.json', 'w') as f:
    json.dump(shortcut, f, indent=2)
```

## Actions identifiers courantes
| Action | Identifier |
|---|---|
| Récupérer l'entrée | `is.workflow.actions.getinput` |
| Définir variable | `is.workflow.actions.setvariable` (param: `WFVariableName`) |
| Définir un dictionnaire | `is.workflow.actions.dictionary` (param: `WFDictionaryKeyValuePairs`) |
| Obtenir le contenu d'une URL | `is.workflow.actions.downloadurl` (params: `WFHTTPMethod`, `WFHTTPHeaders`, `WFHTTPBodyType`, `WFURL`) |
| Obtenir la valeur d'un dictionnaire | `is.workflow.actions.getvalueforkey` (param: `WFValueForKey`) |
| Afficher un résultat | `is.workflow.actions.showresult` |
| Texte | `is.workflow.actions.text` |
| Copier dans le presse-papier | `is.workflow.actions.setclipboard` |
| Afficher une notification | `is.workflow.actions.notification` |
| Si (condition) | `is.workflow.actions.if` |
| Répéter avec chaque | `is.workflow.actions.repeat.each` |

## Limitation critique
- `shortcuts sign` (pour signer le fichier) nécessite **iCloud** — ne marche PAS sur GitHub Actions ni aucun CI cloud.
- Solution : l'utilisateur télécharge le `.json` et l'importe via **Shortcut Source Tool** (routinehub.co) sur son iPhone.
