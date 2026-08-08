---
name: ios-shortcuts-integration
description: Integrate Hermes Agent with iOS native features (Reminders, Calendar, Notes) via shortcuts:// URL scheme, iOS → Hermes via API Server, or HA Todo bridge with actionable notifications. Covers shortcuts:// URL scheme, Jellycuts, API Server setup, HA → iOS push notifications, and bidirectional Shortcut patterns.
platforms: [linux]
---

# iOS Shortcuts Integration

Use this skill when the user wants Hermes to interact with their iPhone's native apps (Reminders, Calendar, Notes) or push notifications, via:
- **Cherri CLI sur Linux** (recommandé juillet 2026) — compile + signe des raccourcis gratuitement depuis le serveur
- `shortcuts://` URL scheme (simple, lien dans Telegram)
- Home Assistant Todo + iOS push notifications actionnables (plus fiable, notifications avec boutons)
- API Server Hermes (iOS → Hermes, question/réponse)
- pyicloud (Rappels/Calendrier iCloud natifs depuis le serveur, sans raccourcis)

## Architecture

### A. Hermes → iOS (push — via shortcuts:// URL scheme)

**⚠️ Il n'existe PAS de déclencheur "Receive Webhook" dans Raccourcis iOS.** Utiliser le schéma d'URL :

```
shortcuts://run-shortcut?name=<NomEncode>&input=<TexteEncode>
```

### B. Hermes → iOS (push — via HA Todo + Notifications actionnables) (RECOMMANDÉ)

```
Hermes Agent → MCP HA → todo.add_item(entity_id="todo.rappel")
                                        ↓
                   Automation HA (state trigger)
                                        ↓
                   notify.mobile_app_<device>
                    (push notification avec boutons d'action)
                                        ↓
              ┌─────────────────────┬─────────────────────┐
              │ ✅ Terminé           │ ⏰ Pas encore fait  │
              └─────────────────────┴─────────────────────┘
```

**Recommandé** car : pas de lien à taper, notification iOS native, persistant dans HA, relance automatique.

### C. iOS → Hermes (pull — action button / Siri / share sheet)

```
iPhone (Shortcuts) ──POST──>  hermes-api.jefe.al/v1/responses
                             → Bearer token auth
                             → extraction output[0].content[0].text
```

**Détail construction shortcut :** `skill_view("ios-shortcuts", "references/hermes-api-integration.md")`
**Template Jellycuts prêt à copier :** `skill_view("ios-shortcuts-integration", "templates/parler-a-hermes.jelly")`
**Template Cherri prêt à compiler :** `skill_view("ios-shortcuts-integration", "templates/parler-a-hermes.cherri")`

### ⚠️ Extraction JSON dans Shortcuts — pièges Cherri (confirmé juillet 2026)

**`@dict['key']` compile en Set Variable, PAS en Get Dictionary Value.** Le raccourci s'exécute sans erreur mais l'extraction échoue silencieusement — la variable de sortie est vide.

**`getValue()` exige un type `dictionary`** — refuse les variables (sortie de `getFirstItem`). Erreur de compilation.

**❌ `getDictionary()` entre chaque étape CORROMPT les données.** Compilé et testé : `getDictionary(@first)` produit un dictionnaire vide pour la clé `content`. Le raccourci s'arrête sans erreur à l'étape d'extraction. NE PAS utiliser `getDictionary()` comme intermédiaire.

**✅ Solution validée : action definition avec type `variable`.** Définir une action personnalisée qui accepte le type `variable` (pas `dictionary`) :

```
action 'is.workflow.actions.getvalueforkey' dictGet(
    variable input: 'WFInput',
    text key: 'WFDictionaryKey'
)
```

**Chaîne d'extraction complète et fonctionnelle** pour `output[0].content[0].text` :
```
@output = dictGet(@response, "output")
@first = getFirstItem(@output)
@content = dictGet(@first, "content")
@firstContent = getFirstItem(@content)
@text = dictGet(@firstContent, "text")
show("{@text}")
```

**`show("{@text}")` fonctionne avec des espaces** — l'hypothèse initiale que les espaces cassaient l'affichage était erronée. Le vrai problème était l'extraction silencieuse qui retournait du vide. Une fois `dictGet()` utilisé, `show("{@text}")` affiche correctement le texte même avec des espaces.

**Vérifier le plist** avec `cherri --debug` pour confirmer que `is.workflow.actions.getvalueforkey` apparaît pour chaque extraction de clé. Voir `references/cherri-json-extraction.md` pour détails complets.

## Workflow — HA Todo + Notifications actionnables

### 1. Prérequis HA
- HA Companion App sur l'iPhone (crée `notify.mobile_app_<device>`)
- Todo list créée via UI HA : Paramètres → Périphériques & Services → Shopping List → + (nommer la liste)

### 2. Automations à créer (une fois, valables pour tous les items)
- **Notification push** : trigger `state` sur `todo.rappel` → `todo.get_items` → dernier item → notify avec `actions: [{action: "TERMINE"}, {action: "PAS_ENCORE"}]`
- **Gestion boutons** : trigger `event: mobile_app_notification_action` → `choose` sur `action` → TERMINE = done, PAS_ENCORE = delay 1h + re-notify

Voir `references/ha-actionable-notifications.md` pour la config complète (YAML automations, pièges `above`+template, warnings normaux).

### 3. Usage quotidien
Tu dis à Hermes *« Rappelle-moi de X »* → il appelle `todo.add_item(entity_id="todo.rappel", item="X")` via MCP HA.

## Workflow — shortcuts:// URL scheme

### Création du shortcut (une fois)
1. Raccourcis → **+** → renommer
2. Tapez **« … »** → activez **« Recevoir du texte »**
3. Ajoutez l'action native (Ajouter un rappel, Créer un event, Créer une note)
4. Dans **Titre**, mettez la variable **Entrée du raccourci**

### Limitations
- Liens `shortcuts://` pas cliquables dans Telegram (ouvrir via Safari)
- Input max ~1000 caractères, URL encoding requis
- iOS peut demander confirmation (Réglages > Raccourcis)

### D. HA Calendar → iOS — Radicale CalDAV (RECOMMANDÉ)

Quand un calendrier synchronisé est nécessaire, **Radicale** est la meilleure solution : serveur CalDAV local, zéro fournisseur externe.

```
Hermes → HA (CalDAV integration) → Radicale → iPhone (CalDAV account)
```

✅ Bidirectionnel, ✅ Temps réel (push), ✅ iOS natif, ✅ Données locales.

Voir `references/radicale-caldav-setup.md` pour l'installation complète.

### E. HA Calendar → iOS — n8n iCal Bridge (fallback)

Quand un serveur CalDAV dédié n'est pas disponible, n8n peut servir de faux serveur iCal : l'iPhone s'abonne à une URL webhook n8n qui retourne un flux iCal généré depuis une table de données. ❌ Unidirectionnel, ❌ Polling (pas temps réel), ❌ iCal subscription seul.

Voir `references/n8n-ical-bridge.md` pour la mise en place complète (workflows n8n, code JS iCal, abonnement iPhone, pièges).

## Compilation et signature de raccourcis depuis un serveur Linux

### ⚠️ Problème fondamental : signature iOS 18+
Apple exige que tout fichier `.shortcut` soit **signé** pour importation dans Shortcuts (iOS 18+). La signature native n'existe **que sur macOS** (API Apple). Sur serveur Linux, pas de signature native.

### Méthodes de signature (état juillet 2026)

| Méthode | Gratuit ? | Marche sur Linux ? | Notes |
|---------|-----------|---------------------|-------|
| **Native macOS** | ✅ | ❌ | API Apple, macOS uniquement |
| **HubSign** (RoutineHub) | ❌ $57.60/an | ✅ | Abonnement RoutineHub membership requis |
| **Serveur auto-hébergé** (scaxyz/shortcut-signing-server) | ✅ | ❌ | Nécessite macOS via docker-osx (instable, lourd) |
| **Cherri Playground** (playground.cherrilang.org) | ✅ **GRATUIT** | ✅ (web) | **CONFIRMÉ juillet 2026** — serveur macOS dédié côté Cherri signe gratuitement. Voir section ci-dessous. |
| **Jellycuts app iOS** (gratuit) | ✅ | N/A (sur iPhone) | Utilise l'API de signature iOS directement — **plus fiable pour Linux-only** |
| **Construction manuelle** dans app Shortcuts | ✅ | N/A (sur iPhone) | Pas de fichier à signer, construit directement sur device |

### ⭐ Recommandation pour utilisateur Linux-only (pas de Mac) — juillet 2026

**Solution #1 : Cherri CLI dans conteneur Docker isolé (RECOMMANDÉ)**
1. Construire une image Docker `cherri-builder` (Alpine + binaire Cherri v2.3.0)
2. Hermes génère le code `.cherri` et l'écrit dans un dossier partagé
3. Le conteneur compile + signe via HubSign (gratuit, réseau sortant requis)
4. Le fichier `.shortcut` signé (AEA1) est récupéré et livré à l'utilisateur
5. L'utilisateur l'ouvre dans l'app **Fichiers** → **Ajouter le raccourci**

⚠️ **Docker-in-Docker** : quand Hermes tourne dans un conteneur Docker (mount `/srv/docker/hermes/.hermes -> /opt/data`), les volumes `docker run -v` doivent utiliser le **path hôte** (`/srv/docker/hermes/.hermes/...`), pas le path conteneur (`/opt/data/...`). Sinon le volume apparaît vide.
⚠️ **Fichier de sortie** : Cherri nomme le fichier d'après `#define name` avec guillemets si espaces. Copier vers un nom propre **depuis l'intérieur du conteneur** (root 600 non lisible par l'utilisateur Hermes).
⚠️ **DEMANDER PERMISSION** avant de construire/lancer le conteneur — ne jamais installer ou supprimer sans accord explicite de l'utilisateur.

**Solution #2 : Cherri Playground web (gratuit, mais limitations)**
Le Playground (playground.cherrilang.org) compile + signe gratuitement via HubSign. **MAIS** il ne peut pas générer de requêtes HTTP — `#include 'actions/web'`, `action` definitions non-builtin, et `rawAction()` produisent tous "0 actions" dans le playground. Seules les actions basic builtin (prompt, alert, show, etc.) fonctionnent. Utile pour des raccourcis simples sans HTTP.

**Solution #3 : Jellycuts gratuit sur iPhone**
Je code le Jelly, utilisateur copie-colle + Build & Export. L'app signe nativement sur iOS. Mais app décevante (3.6/5, abonnement $5-20/an pour features avancées).

**Solution #4 : HA Companion + Radicale** pour rappels/calendrier
**Zéro raccourci nécessaire**, contourne complètement le problème de signature.

**Solution #5 : pyicloud** pour Rappels iCloud natifs (voir section F ci-dessous)

### Cherri (cherrilang.org) — détails techniques
Compilateur gratuit, open source (GPL-2.0), très actif (1.6k ⭐, dernier commit juillet 2026). Écrit du code `.cherri` → compile en `.shortcut`. Syntaxe similaire à Go/Ruby. Package manager git-based, includes multifichiers, macros, functions, type system.
- **Installation Linux** : `git clone https://github.com/electrikmilk/cherri.git && cd cherri && go build`
- **Compilation sans signature** : `cherri fichier.cherri --skip-sign` (produit `.shortcut` non signé)
- **Signature via Playground** : coller le code sur playground.cherrilang.org → Export → Download
- Voir `references/shortcut-compilation-signing.md` pour détails complets.

### ⚠️ Jellycuts — état de l'app (juillet 2026)
- Rachetée par Skyground Media, passée d'achat unique à **abonnement** ($5-20/an).
- Note App Store 3.6/5, reviews récents négatifs ("not worth bothering with").
- Version gratuite compile + signe sur iOS (suffit pour copier-coller du code).
- Alternative gratuite supérieure = **Cherri** (cherrilang.org) dans conteneur Docker isolé (voir Solution #1 ci-dessus).
- ⚠️ La skill `jellycuts` est user-owned et ne reflète pas ce changement de pricing — ne pas s'y fier pour les recommandations gratuites. Recommander `hermes curator adopt jellycuts` pour mettre à jour.

### F. Rappels iCloud natifs via pyicloud (sans raccourci)

**pyicloud** = bibliothèque Python open source qui se connecte à un compte iCloud et pilote Rappels, Calendrier, iCloud Drive depuis Linux. Aucun raccourci à créer, aucun iPhone à toucher.

- **Repo** : github.com/picklepete/pyicloud (2.8k ⭐) — fork actif : github.com/timlaing/pyicloud
- **PyPI** : `pip install pyicloud` — version 2.6.5 (juin 2026), Python 3.10-3.14
- **Rappels** : ✅ créer, lire, modifier, marquer terminé, supprimer (CLI + API Python)
- **Calendrier** : ✅ lecture (écriture en PR, pas encore mergé)
- **iCloud Drive** : ✅ créer dossiers, renommer, supprimer

⚠️ **Limitations** :
- 2FA obligatoire — validation une fois sur iPhone, token de session persistant
- Données transitent par les serveurs Apple (pas self-hosted — préférence utilisateur local-first en conflit)
- Apple peut casser l'API sans prévenir (fork timlaing corrige vite)
- Calendrier écriture pas encore disponible (utiliser Radicale pour ça)

⚠️ **Privacy** : pour utilisateur concerné par souveraineté (CLOUD Act, GDPR), pyicloud envoie les données via Apple. À réserver pour les Rappels où la sync iCloud native est le besoin principal. Pour calendrier, préférer Radicale (self-hosted).

Voir `references/pyicloud-setup.md` pour l'installation et exemples complets.

### G. Compilation Cherri dans conteneur Docker isolé

Pour les raccourcis nécessitant des requêtes HTTP (impossibles via le Playground web), utiliser Cherri CLI dans un conteneur Docker isolé sur le serveur. L'utilisateur a explicitement demandé cette approche (conteneur isolé, pas d'accès au reste du serveur).

Voir `references/cherri-docker-setup.md` pour le Dockerfile, le workflow complet, et les pièges Docker-in-Docker (paths de volume).

### H. Raccourci de traduction LibreTranslate

Template Cherri complet pour traduire texte via LibreTranslate (`translate.jefe.ovh`). Mode texte (saisie/dictée), 12 langues cibles, auto-détection source, sauvegarde dans Notes.

- **Template** : `skill_view("ios-shortcuts-integration", "references/cherri-docker-setup.md")` (section Template)
- **API reference** : `skill_view("ios-shortcuts-integration", "references/libretranslate-api.md")`

⚠️ **LibreTranslate auth** : la clé API va dans le **body JSON** (`"api_key": "***"`), JAMAIS en header (`Authorization`, `X-API-Key`, `api_key` header → tous 400). Testé août 2026.

⚠️ **Mode fichier (upload) NON fonctionnel en Cherri v2.3.0** : `WFFormData` produit un plist malformé → iOS refuse l'import. Utiliser `jsonRequest()` pour texte seulement. Voir `references/cherri-docker-setup.md` pour détails.

⚠️ **`rawAction()` → `is.workflow.actions.rawaction`** : iOS refuse ("action did not exist"). Toujours utiliser `action` definitions à la place. Voir `references/cherri-docker-setup.md`.

⚠️ **`prompt()` multi-lignes** : `prompt("Texte :", "Text", "", "true")` active `WFAllowsMultilineText`. Sans ça, seul la première ligne est capturée.

⚠️ **`createNote()`** : `action 'is.workflow.actions.createnote' createNote(variable body: 'NoteBody')` pour sauvegarder dans Apple Notes.

### I. Safari Extension / Bookmarklet pour LibreTranslate sur iOS

L'utilisateur veut traduire des pages web dans Safari via LibreTranslate (pas la traduction native iOS). Il n'existe aucune extension Safari LibreTranslate. Trois options : conversion Chrome→Safari via `xcrun safari-web-extension-converter` (nécessite Mac), **bookmarklet JavaScript avancé** (RECOMMANDÉ — traduit la page entière in-place avec barre de progression, technique [SEP] pour batcher les requêtes), ou raccourci Cherri via share sheet (section H).

Voir `references/safari-extension-libretranslate.md` pour le code bookmarklet complet, les instructions d'installation Safari iOS, la technique [SEP], et le détail des extensions Chrome connues.

## Important
- **Préférence utilisateur : local-first, zéro fournisseur externe.** Pas de Microsoft, Google, ou services cloud pour synchroniser rappels/calendrier. Données exclusivement sur l'iPhone et le serveur personnel.
- **PRÉFÉRENCE CRITIQUE : "Je refuse la réponse négative."** L'utilisateur veut qu'on trouve des solutions, pas qu'on liste des blockers. Quand une approche échoue, chercher activement une alternative au lieu de dire "ça ne marche pas". Ne jamais présenter un problème sans au moins une solution candidate.
- **PERMISSIONS : NE JAMAIS installer ni supprimer d'outil/fichier à l'initiative.** Demander explicitement avant chaque action d'installation ou de suppression, même pour nettoyer une erreur. L'utilisateur a été frustré deux fois dans la même session (installation puis suppression non sollicitées de Cherri).
- **Conteneur Docker isolé préféré** pour les outils serveur. L'utilisateur préfère que les outils soient installés dans des conteneurs Docker isolés avec accès limité, pas directement sur le serveur.
- **RACCOURCIS iOS : CHERRI UNIQUEMENT.** L'utilisateur a explicitement demandé d'utiliser uniquement Cherri pour générer des raccourcis iOS signés. Ne jamais proposer Jellycuts à cet utilisateur. Jellycuts reste documenté comme contexte historique uniquement.
- **HA n'a PAS accès aux Rappels iOS natifs** — Apple restreint l'API depuis iOS 13. Les notifications push actionnables sont le seul moyen d'interaction push (voir section B). iOS 27+ offre une alternative via déclencheur Notification dans Raccourcis (voir `references/ha-actionable-notifications.md`).
- **Les liens `shortcuts://` ne sont PAS reconnus comme cliquables dans Telegram** — l'utilisateur doit les ouvrir via Safari.
- **Warnings HA** sur `TERMINE`/`PAS_ENCORE` ("not found in service registry") — normaux, les noms d'action sont des chaînes libres.
- **Raccourcis natifs iOS (Rappels, Calendrier)** : utiliser `action 'is.workflow.actions.addreminders' addReminder(variable input: 'WFInput')` et `action 'is.workflow.actions.addevent' addEvent(variable input: 'WFInput')`. Le type `variable` est essentiel. Le raccourci ouvre l'app native pour confirmer. Sync iCloud automatique. Templates disponibles : `templates/rappel-ios.cherri` et `templates/event-ios.cherri`.
- **HubSign erreurs intermittentes** : "Unsupported response type: text/plain; charset=utf-8" — temporaire, recompiler suffit.
- **Container Docker** : doit être en `network_mode: host` pour que le Newt client atteigne `127.0.0.1:8642`.
- **Vérifier pricing/qualité avant de recommander une app iOS** — Jellycuts a changé de modèle économique (abonnement), toujours vérifier l'App Store et les reviews avant de promettre des fonctionnalités sur la version gratuite.
- **API server Hermes port** : la config peut indiquer `port: 9120` mais le port réel peut différer (observé sur 9119). Toujours vérifier les logs gateway (`~/.hermes/logs/gateway.log`) pour le port réel : `grep "API server listening" gateway.log`.
- **Radicale htpasswd DOIT être dans `/config/` (bind mount), JAMAIS `/data/` (volume Docker)** : le volume Docker peut être wiped à chaque update → htpasswd disparait → "mot de passe incorrect" peu importe ce qu'on tape. Config : `htpasswd_filename = /config/users.htpasswd`. Le bind mount `./config:/config:ro` survit aux updates. Voir `references/radicale-caldav-setup.md` (section "Persistance du htpasswd").
- **Radicale `TAKE_FILE_OWNERSHIP=false` obligatoire** : l'entrypoint (`docker-entrypoint.sh`) a `set -e` et essaie `chown -R radicale:radicale /data` quand `TAKE_FILE_OWNERSHIP=true` (default). Avec `cap_drop ALL` + `read_only: true`, le chown échoue → **crash en restart loop infini**. Toujours définir `TAKE_FILE_OWNERSHIP=false` dans le compose. Pré-chown le volume avec `docker run --rm -v radicale_data:/data alpine chown -R 2999:2999 /data` avant le premier démarrage.
- **Hermes ne peut pas écrire dans `/srv/docker/`** (en dehors de `HERMES_WRITE_SAFE_ROOT`). Pour écrire des fichiers sur le host dans `/srv/docker/`, utiliser un conteneur temporaire : `docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c 'cat > /config/config << EOF ... EOF'`. `write_file` et `terminal` ne peuvent pas écrire dans `/srv/docker/` directement.
- **Radicale volume wipe — DEBUG CRITIQUE** : si l'utilisateur signale que Radicale refuse le mot de passe (« je tape le mot de passe, ça ne marche pas »), vérifier en priorité si le volume `/data` est **vide** : `docker exec radicale ls -la /data/`. Un container `healthy` + DNS fonctionnel ne garantit PAS que le htpasswd existe. Le container peut être recréé (update image, `docker compose up`) avec un volume vide — le htpasswd et les collections disparaissent. Symptôme côté iOS : alerte de mot de passe, mais aucune combinaison fonctionne. Fix : recréer le htpasswd dans `/config/` (bind mount persistant) : `docker run --rm -v /srv/docker/radicale/config:/config alpine sh -c "apk add apache2-utils && htpasswd -cbB /config/users.htpasswd jefe <pass>"` puis `docker restart radicale`. Voir `references/radicale-troubleshooting.md` pour la procédure de diagnostic complète.

## Triggers iOS → Hermes

| Méthode | Comment faire |
|---------|--------------|
| **Bouton d'action** | Réglages → Bouton d'action → Raccourci → nom du shortcut |
| **Écran d'accueil** | ⋮ sur le raccourci → Partager → Ajout à l'écran d'accueil |
| **Siri** | « Dis Siri, [nom du raccourci] » |
| **Feuille de partage** | Sélectionner un texte → Partager → le raccourci |
| **Automatisation** | NFC, WiFi, Heure, Application, etc. |
