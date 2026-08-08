# Cherri Docker Container Setup (confirmé juillet 2026)

## Dockerfile de base (cherri-builder)

```dockerfile
FROM alpine:latest

RUN apk add --no-cache ca-certificates curl unzip

RUN curl -sL "https://github.com/electrikmilk/cherri/releases/download/v2.3.0/cherri_linux-x86_64.zip" -o /tmp/cherri.zip && \
    unzip -o /tmp/cherri.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/cherri && \
    rm /tmp/cherri.zip

WORKDIR /workspace
ENTRYPOINT ["cherri"]
```

## Dockerfile avec SMB (cherri-smb) — pour upload sur NAS

```dockerfile
FROM cherri-builder:latest
RUN apk add --no-cache samba-client
WORKDIR /workspace
ENTRYPOINT ["cherri"]
```

## Build

```bash
docker build -t cherri-builder /path/to/cherri-builder/
docker build -t cherri-smb -f Dockerfile.smb /path/to/cherri-builder/
```

## Usage — compile + sign + upload to NAS SMB

```bash
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

## Key points

- **Volume path**: must use HOST path (`/srv/docker/hermes/.hermes/...`), not container path (`/opt/data/...`). Find with `docker inspect hermes --format '{{json .Mounts}}'`.
- **Network**: container needs outbound access for HubSign signing (routinehub.co). Do NOT use `--network none`.
- **File permissions**: cherri runs as root in the container, output files are root:root 600. Must `chmod 644` and copy to clean filename from INSIDE the container.
- **File naming**: cherri names output after `#define name` — if name has spaces, the filename gets quotes (e.g. `"Parler a Hermes".shortcut`). Always copy to a clean name: `for f in /work/*Hermes*.shortcut; do cp "$f" /work/upload.shortcut; break; done`.
- **Isolation**: container has no access to Docker socket, no access to other services, only the mounted volume.
- **SMB file deletion**: `del` in smbclient can fail with `NT_STATUS_DELETE_PENDING` if file is locked (user has it open in Files app). Use a new filename for each upload instead of trying to overwrite.
- **HubSign intermittent errors**: "Unsupported response type: text/plain; charset=utf-8" — temporary, retry the compilation.
- **DEMANDER PERMISSION** avant de construire/lancer le conteneur — ne jamais installer ou supprimer sans accord explicite de l'utilisateur.
- **`.dockerignore` requis** — les fichiers root-owned dans `output/` (`.shortcut` root:root 600, `_processed.cherri` root:root 600) bloquent le build context avec `error checking context: no permission to read`. Créer un `.dockerignore` contenant `output/` et les `Dockerfile*`. Le build n'a pas besoin du contenu de `output/` — seulement le Dockerfile et les sources.
- **`rawAction()` avec dict vide `{}` → PANIC du compilateur** (v2.3.0, confirmé août 2026) — `rawAction("is.workflow.actions.dictatetext", {})` crashe avec `panic: interface conversion: interface {} is nil, not map[string]interface {}` dans `raw_actions.go:28`. **Solution : toujours passer au moins un paramètre**, même bidon : `rawAction("is.workflow.actions.dictatetext", {"WFLanguage": "fr-FR"})`, `rawAction("is.workflow.actions.documentpicker.scan", {"WFDocumentType": "public.item"})`. Sans paramètre réel connu, mettre `{"WF": "placeholder"}` suffit.
- **`rawAction()` génère `is.workflow.actions.rawaction` au lieu du vrai identifiant** (confirmé août 2026) — iOS refuse l'action ("action did not exist"). **Solution : TOUJOURS utiliser `action` definitions** : `action 'is.workflow.actions.dictatetext' dictateText(text language: 'WFLanguage')` puis `@texte = dictateText("fr-FR")`. L'`action` definition génère le bon identifiant iOS.
- **`WFFormData` (upload de fichier) produit un plist MALFORMÉ** (confirmé août 2026) — `WFFormData` est sérialisé en `WFTextTokenAttachment` au lieu d'un tableau de form data, même via `action` definitions. iOS refuse l'import du raccourci. **Aucun workaround en Cherri v2.3.0 pour l'upload multipart.** Utiliser `jsonRequest()` pour texte seulement, ou construire manuellement dans Shortcuts.
- **`setClipboard()`, `show()`, `quicklook()` refusent les strings interpolés** — `setClipboard("{@var}")` → `Invalid value "{@var}" (text) for argument 'value' (variable)`. **Solution : passer la variable nue** : `setClipboard(@var)`, `show(@var)`, `quicklook(@var)`.
- **`prompt()` multi-lignes** — `prompt("Texte :", "Text", "", "true")` → `WFAllowsMultilineText: true`. Le 4e argument doit être la string `"true"`. Sans ça, seul la première ligne est capturée.
- **`createNote()` pour sauvegarder dans Notes** — `action 'is.workflow.actions.createnote' createNote(variable body: 'NoteBody')` puis `createNote(@noteContent)`. Sauvegarde dans l'app Notes native iOS.

## Verification

```python
# Check the signed shortcut is valid AEA1 format
with open('parler_hermes.shortcut', 'rb') as f:
    data = f.read()
assert data[:4] == b'AEA1', "Not a signed shortcut"
print(f"✅ Signed shortcut: {len(data)} bytes")
```

## Plist inspection (debug)

```bash
# Generate plist with --debug
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-builder -c '
    cd /work
    cherri /work/mon_raccourci.cherri --debug 2>&1 | tail -3
    for f in /work/*.plist; do cp "$f" /work/inspect.plist; break; done
  '

# Parse on host
python3 -c "
import plistlib
with open('/opt/data/home/workspace/cherri-builder/output/inspect.plist', 'rb') as f:
    data = plistlib.load(f)
actions = data.get('WFWorkflowActions', [])
print(f'Total actions: {len(actions)}')
for i, a in enumerate(actions):
    ident = a.get('WFWorkflowActionIdentifier', '?')
    params = a.get('WFWorkflowActionParameters', {})
    extra = ''
    if 'WFDictionaryKey' in params: extra = f\" key={params['WFDictionaryKey']}\"
    if 'WFItemSpecifier' in params: extra = f\" spec={params['WFItemSpecifier']}\"
    print(f'  {i}: {ident}{extra}')
"
```

Expected actions for a Hermes API shortcut with dictGet():
- `is.workflow.actions.ask` — prompt
- `is.workflow.actions.downloadurl` — HTTP POST
- `is.workflow.actions.getvalueforkey` — Get Dictionary Value (×3, for output/content/text)
- `is.workflow.actions.getitemfromlist` — Get First Item (×2)
- `is.workflow.actions.showresult` — display

If `is.workflow.actions.getvalueforkey` is missing, the extraction will fail silently.
If `is.workflow.actions.detect.dictionary` appears between extractions, data will be corrupted (use dictGet() instead of getDictionary()+getValue()).

## Template: raccourci Traduire (LibreTranslate)

### ⚠️ Mode fichier (upload) — NON FONCTIONNEL en Cherri v2.3.0

**Testé août 2026** : `rawAction` ET `action` definitions avec `WFFormData` produisent un plist malformé. `WFFormData` est sérialisé en `WFTextTokenAttachment` (référence de variable) au lieu d'un tableau de form data. iOS refuse l'import du raccourci.

**Aucun workaround existant en Cherri v2.3.0 pour l'upload multipart de fichiers.** Pour les raccourcis nécessitant upload de fichier :
- Construire manuellement dans l'app Shortcuts sur iPhone
- Ou utiliser `jsonRequest()` pour texte seulement

### `rawAction()` génère `is.workflow.actions.rawaction` au lieu du vrai identifiant

**Testé août 2026** : `rawAction("is.workflow.actions.dictatetext", {"WFLanguage": "fr-FR"})` compile, mais l'action générée a l'identifiant `is.workflow.actions.rawaction` (générique). iOS refuse : "action did not exist".

**Solution : TOUJOURS utiliser `action` definitions au lieu de `rawAction()`** :
```
action 'is.workflow.actions.dictatetext' dictateText(text language: 'WFLanguage')
@texte = dictateText("fr-FR")
```

### `prompt()` multi-lignes

`prompt("Texte :", "Text", "", "true")` → `WFAllowsMultilineText: true`. Le 4e argument (`multiline`) doit être la string `"true"`. Sans ça, seul la première ligne est capturée.

### `createNote()` pour sauvegarder dans Apple Notes

```
action 'is.workflow.actions.createnote' createNote(variable body: 'NoteBody')
createNote(@noteContent)
```

### Code complet du template translate.cherri (version fonctionnelle texte + dictée + Notes)

```cherri
#include 'actions/web'
#include 'actions/sharing'

#define name "Traduire"
#define glyph globe
#define color purple

action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)

action 'is.workflow.actions.dictatetext' dictateText(
    text language: 'WFLanguage'
)

action 'is.workflow.actions.createnote' createNote(
    variable body: 'NoteBody'
)

const API_URL = "https://translate.jefe.ovh"
const API_KEY = "YOUR_API_KEY_HERE"

menu "Mode de traduction" {
    item "Saisir du texte":
        @texte = prompt("Texte a traduire :", "Text", "", "true")
        @mode = "texte"
    item "Dicter (voix)":
        @texte = dictateText("fr-FR")
        @mode = "texte"
}

// ... menus langues source/target ...

@response = jsonRequest("{API_URL}/translate", 'POST', {"q": "{@texte}", "source": "{@source}", "target": "{@target}", "format": "text", "api_key": "{API_KEY}"}, {"Content-Type": "application/json"})
@translatedText = dictGet(@response, "translatedText")
setClipboard(@translatedText)

@noteContent = "Traduction {@source} -> {@target}

Original :
{@texte}

Traduction :
{@translatedText}"

createNote(@noteContent)
showNotification("Traduction copiee et sauvegardee dans Notes", "Traduire", true)
show(@translatedText)
```

Points clés spécifiques à LibreTranslate :
- `api_key` dans le **body JSON**, jamais en header (Authorization/X-API-Key → 400)
- `action` definitions pour dictée/Notes — JAMAIS `rawAction()` (génère `is.workflow.actions.rawaction`)
- `setClipboard(@var)` / `show(@var)` / `quicklook(@var)` — variable nue, pas interpolée
- `prompt("...", "Text", "", "true")` pour multi-lignes