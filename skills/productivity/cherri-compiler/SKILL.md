---
name: cherri-compiler
title: "Cherri Compiler — Patterns avancés et pièges v2.3.0"
description: "Use when compiling Cherri shortcuts with action definitions."
version: "1.0"
author: "Hermes Agent"
triggers:
  - "cherri compiler"
  - "compiler cherri"
  - "cherri action definition"
  - "cherri rawAction"
  - "cherri obsidian"
  - "cherri multiline"
---

# Cherri Compiler — Patterns avancés et pièges v2.3.0

Compilateur Cherri CLI (v2.3.0) en conteneur Docker pour générer des raccourcis iOS signés. Ce skill couvre les patterns avancés découverts en pratique, les bugs du compilo, et les intégrations URL scheme.

⚠️ Pour les bases de Cherri (syntaxe, playground, setup Docker), voir le skill `cherri-shortcuts`. Ce skill couvre uniquement les patterns avancés non documentés ailleurs.

## Action definitions — Remplacement de rawAction

### Le bug rawAction

`rawAction()` dans Cherri v2.3.0 génère l'identifiant générique `is.workflow.actions.rawaction` au lieu du vrai identifiant de l'action. iOS refuse l'import ou affiche "action did not exist". De plus, `rawAction()` avec un dict vide `{}` fait panic le compilo (`interface conversion: interface {} is nil`).

### Solution : action definitions

Définir une action personnalisée qui mappe vers le vrai identifiant iOS :

```cherri
action 'is.workflow.actions.dictatetext' dictateText(
    text language: 'WFLanguage'
)
// Usage: @texte = dictateText("fr-FR")
```

### Bibliothèque d'action definitions validées

Voir `references/action-definitions.md` pour la liste complète des action definitions testées et fonctionnelles.

### Règle : ne pas redéfinir les builtins

`openURL`, `setClipboard`, `show`, `quicklook`, `showNotification`, `prompt`, `alert`, `confirm`, `getFirstItem`, `jsonRequest` sont déjà des builtins Cherri. Les redéfinir génère une erreur "Duplicate declaration".

## Prompt multi-lignes

Le `prompt()` accepte un 4e argument `multiline` (string `"true"`) :

```cherri
@texte = prompt("Texte a traduire :", "Text", "", "true")
```

Génère `WFAllowsMultilineText: "true"` dans le plist. Sans cet argument, le prompt est single-line et tronque les textes collés avec des retours à la ligne.

⚠️ Le 2e argument `inputType` doit être `"Text"` (capital T) ou `"Speech"` (capital S). Le warning "Value same as default" est inoffensif.

## Sauvegarde Obsidian via URL scheme

L'URL scheme `obsidian://new` crée/ajoute à une note Obsidian. Pattern recommandé pour éviter les problèmes d'URL encoding avec textes longs multi-lignes :

```cherri
// 1. Contenu formaté → presse-papier
setClipboard(@noteContent)
// 2. Obsidian lit le presse-papier (clipboard=true) et crée/ajoute
openURL("obsidian://new?name=MaNote&clipboard=true&append=true&silent=true")
// 3. Remettre la traduction seule dans le presse-papier
setClipboard(@translatedText)
```

### Paramètres Obsidian URI

| Paramètre | Description |
|-----------|-------------|
| `name` | Nom de la note (fichier .md) |
| `clipboard=true` | Lire le contenu depuis le presse-papier (recommandé pour textes longs) |
| `content` | Contenu direct (alternative à clipboard, nécessite URL encoding) |
| `append=true` | Ajouter à la note si elle existe (sinon crée) |
| `silent=true` | Ne pas basculer Obsidian en premier plan |
| `vault` | Nom du vault (optionnel si un seul vault) |

### Note par jour avec variables

```cherri
@today = formatDate(CurrentDate, "Custom", "dd-MM-yyyy")
openURL("obsidian://new?name=Traductions/Traduction_{@source}-{@target}_{@today}&clipboard=true&append=true&silent=true")
```

⚠️ Obsidian doit être installé sur l'iPhone. Sans Obsidian, l'URL ne fait rien. Utiliser `name=` (PAS `path=`) pour le sous-dossier — voir la section ci-dessous.

### Paramètre `path` vs `name` (sous-dossiers Obsidian)

- `name=MaNote` → crée la note à la **racine** du vault (Obsidian ajoute `.md` automatiquement)
- `path=Traductions/MaNote` → **NE FONCTIONNE PAS** — Obsidian n'ajoute PAS `.md` avec `path=`, donc aucun fichier n'est créé. Erreur silencieuse.
- `name=Traductions/MaNote` → ✅ **SOLUTION** — Obsidian crée le sous-dossier `Traductions/` s'il n'existe pas, ET ajoute `.md` automatiquement. C'est la bonne façon de ranger les notes dans un sous-dossier.

## formatDate — NE PAS définir en action definition custom

### ❌ Le bug

Définir `action 'is.workflow.actions.formatdate'` compile sans erreur mais génère l'identifiant `is.workflow.actions.formatdate` qui **n'existe pas dans iOS**. iOS affiche "action does not exist" à l'exécution — le raccourci se bloque juste après les menus.

### ✅ Solution : built-in avec include

Utiliser le `formatDate()` built-in de Cherri avec `#include 'actions/calendar'` :

```cherri
#include 'actions/calendar'

// Usage: @today = formatDate(CurrentDate, "Custom", "dd-MM-yyyy")
```

L'identifiant correct généré est `is.workflow.actions.format.date` (avec un point avant `date`).

La signature du built-in est : `formatDate(text date, dateFormats ?dateFormat = "Short", text ?customDateFormat): text`

- 2e argument : enum `dateFormats` — doit être `"Custom"` pour utiliser un pattern personnalisé
- 3e argument : le pattern de format (ex: `"dd-MM-yyyy"`, `"yyyy-MM-dd"`)

### Lesson learned (session 2026-08-04)

Le raccourci "Traduire" plantait sur iOS avec "action does not exist" juste après les menus de langue. La cause : l'action definition custom `is.workflow.actions.formatdate` (sans point). Corrigé en remplaçant par le built-in `formatDate()` + `#include 'actions/calendar'`, qui génère `is.workflow.actions.format.date` (valide).

## Workflow de compilation complet

### Build + compile + upload NAS

```bash
# 1. Build images (une seule fois)
docker build -t cherri-builder /path/to/cherri-builder/
docker build -t cherri-smb -f Dockerfile.smb /path/to/cherri-builder/

# 2. Compiler
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-builder -c 'cd /work && cherri /work/translate.cherri 2>&1'

# 3. Vérifier le plist (debug)
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-builder -c 'cd /work && cherri /work/translate.cherri --debug 2>&1 | tail -3; for f in /work/*.plist; do cp "$f" /work/inspect.plist; break; done'

# 4. Inspection des actions (sur le host)
python3 -c "
import plistlib
with open('/opt/data/home/workspace/cherri-builder/output/inspect.plist', 'rb') as f:
    data = plistlib.load(f)
actions = data.get('WFWorkflowActions', [])
print(f'Total actions: {len(actions)}')
for i, a in enumerate(actions):
    ident = a.get('WFWorkflowActionIdentifier', '?')
    if ident not in ('is.workflow.actions.gettext', 'is.workflow.actions.setvariable', 'is.workflow.actions.nothing', 'is.workflow.actions.choosefrommenu'):
        params = a.get('WFWorkflowActionParameters', {})
        extra = ''
        if 'WFDictionaryKey' in params: extra = f\" key={params['WFDictionaryKey']}\"
        if 'URL' in params: extra = f' URL={str(params[\"URL\"])[:80]}'
        print(f'  {i}: {ident}{extra}')
"

# 5. Upload NAS
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-smb -c 'cd /work && cp "/work/\"Traduire\".shortcut" /work/upload.shortcut && smbclient "//100.64.0.1/raccourci_ios" -U "ax42-SMB%PASSWORD" -c "put /work/upload.shortcut Traduire.shortcut; ls" 2>&1; rm -f /work/upload.shortcut 2>/dev/null'
```

### Vérification signature AEA1

```bash
docker run --rm \
  -v /srv/docker/hermes/.hermes/home/workspace/cherri-builder/output:/work \
  --entrypoint sh cherri-builder -c 'head -c 4 "/work/\"Traduire\".shortcut" | od -A x -t x1'
# Doit afficher: 000000 41 45 41 31 (= "AEA1")
```

## Pitfalls

1. **`rawAction()` génère `is.workflow.actions.rawaction`** → iOS refuse. Toujours utiliser `action` definitions.
2. **`rawAction()` avec `{}` vide** → panic du compilo. Si rawAction (déconseillé), passer au moins un paramètre.
3. **`setClipboard()`, `show()`, `quicklook()`** acceptent une **variable** (`@var`), PAS une string interpolée (`"{@var}"`).
4. **Ne pas redéfinir les builtins** (`openURL`, `setClipboard`, etc.) → "Duplicate declaration".
5. **Nom du fichier de sortie** → Cherri génère `"Nom du shortcut".shortcut` (avec guillemets dans le nom). Copier : `cp "/work/\"Nom\".shortcut" /work/upload.shortcut`.
6. **`.dockerignore`** → exclure `output/` du contexte de build Docker (fichiers root illisibles font échouer le build).
7. **Volume Docker** → utiliser le chemin **hôte** (`/srv/docker/hermes/.hermes/...`), pas le chemin container (`/opt/data/...`).
8. **HubSign intermittent** → "Unsupported response type: text/plain; charset=utf-8" — temporaire, relancer la compilation.
9. **Prompt `inputType`** → `"Text"` (capital T), pas `"text"`. Warning "same as default" = inoffensif.
10. **Obsidian URL scheme** → `clipboard=true` préférable à `content=` pour les textes longs (évite l'URL encoding manuel des retours à la ligne).
11. **Action definition custom avec mauvais identifiant** → compile sans erreur mais iOS refuse l'action. **TOUJOURS** vérifier le plist après compilation (voir section "Vérification systématique" ci-dessous). Les identifiants iOS valides suivent le pattern `is.workflow.actions.<x>` avec des points comme séparateurs (ex: `format.date` pas `formatdate`).
12. **Upload SMB avec `del` avant `put`** → `NT_STATUS_DELETE_PENDING` si on supprime puis re-upload immédiatement. Soit uploader sous un nom différent (`Traduire_v2.shortcut`), soit attendre que le delete soit effective.
13. **`cp` avec guillemets dans le nom** → les fichiers Cherri ont des guillemets dans leur nom (`"Traduire".shortcut`). Le `cp` doit échapper les guillemets : `cp "/work/\"Traduire\".shortcut" /work/upload.shortcut`.
14. **Entrée du conteneur Docker Cherri** → l'entrypoint est `[cherri]`, pas `[sh]`. Pour passer des flags comme `-d`, utiliser `--entrypoint sh` : `docker run --rm --entrypoint sh cherri-builder -c 'cherri mon_raccourci.cherri -d 2>&1'`. Sans `--entrypoint sh`, les flags sont interprétés comme des arguments de fichier et affichent le help.
15. **Compilation avec `-d` (debug)** → génère un fichier `.plist` en plus du `.shortcut`. Le flag `-d` doit venir APRÈS le nom du fichier : `cherri mon_raccourci.cherri -d`. Le `.plist` permet d'inspecter les actions générées pour la vérification systématique.
16. **`if` avec variable issue de `dictGet()` → "Invalid type '' for conditional"**. Le compilateur Cherri ne peut pas déterminer le type de retour d'une `action` definition custom comme `dictGet()`. Toute condition `if @var == "text"` ou `if @var != 200` où `@var` provient d'un `dictGet()` échoue à la compilation avec : `Invalid type '' for conditional '=='  Allowed types: [text number bool action date]`. **Testé le 2026-08-05** : `@code = dictGet(@response, "code_erreur")` puis `if @code != 200` → erreur. `@erreur = dictGet(@data, "erreur")` puis `if @erreur != ""` → même erreur. **Contournement** : retirer toute condition sur des valeurs extraites via `dictGet()`. Pour la gestion d'erreurs, soit afficher directement les valeurs (l'utilisateur voit les champs vides si l'API échoue), soit utiliser un proxy intermédiaire (n8n webhook) qui valide et renvoie un type simple (bool/text) que Cherri peut tester.
17. **`jsonRequest()` avec body `{}` et headers `{}`** → fonctionne pour les POST avec query params dans l'URL. Si l'API attend les paramètres en query string (ex: `?immat=AA-123-BC&token=xxx`), passer `{}` comme 3e et 4e argument : `jsonRequest(url, 'POST', {}, {})`.
18. **`prompt()` sans `inputType`** → fonctionne correctement. Le warning "Value for action argument 'inputType' is the same as the default value" est non-bloquant. `prompt("Texte :")` suffit ; pas besoin de `prompt("Texte :", "Text")`.

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

2. Inspecter le plist sur le host avec Python :
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

### Identifiants connus invalides

| Identifiant invalide | Correct | Cause |
|---------------------|---------|-------|
| `is.workflow.actions.formatdate` | `is.workflow.actions.format.date` | Action definition custom — utiliser le built-in `formatDate()` avec `#include 'actions/calendar'` |
| `is.workflow.actions.rawaction` | (varie) | `rawAction()` — utiliser `action` definitions à la place |

## Templates

- `templates/translate.cherri` — Raccourci de traduction LibreTranslate complet avec multi-lignes, dictée, menus de langues, et sauvegarde Obsidian.
- `templates/api-immatriculation.cherri` — Raccourci d'identification de véhicule par plaque immatriculation via API SIV (apiplaqueimmatriculation.com). Pattern : POST avec query params, extraction JSON multi-niveau via dictGet, affichage formaté. Illustre le contournement du pitfall #16 (pas de condition if sur dictGet).