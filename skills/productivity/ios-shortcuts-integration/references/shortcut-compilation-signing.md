# Compilation et signature de raccourcis iOS depuis Linux

Recherche menée juillet 2026 — état de l'art pour utilisateurs Linux-only (pas de Mac).

## Le problème

Apple exige que tout fichier `.shortcut` soit **signé** pour importation dans l'app Shortcuts (iOS 18+).
La signature native utilise une API Apple disponible **uniquement sur macOS**.
Sur serveur Linux, impossible de signer nativement.

## Solutions de signature

### 1. Native macOS
- Gratuit, fiable
- **macOS uniquement** — pas disponible sur Linux
- `shortcuts sign --mode people-who-know-me -i input.shortcut -o output.shortcut`

### 2. ⭐ Cherri Playground (playground.cherrilang.org) — CONFIRMÉ GRATUIT juillet 2026
- Compilateur Cherri en ligne avec **serveur macOS dédié** qui signe les shortcuts gratuitement
- **Flow confirmé** : coder `.cherri` → coller sur playground.cherrilang.org → Export → Download Shortcut → fichier signé
- Aucun compte, aucune app à installer, aucun paiement
- L'article GigaZine (mai 2026) confirme : "Clicking 'Download Shortcut' will download a shortcut signed by HubSign, which you can then save and transfer to your iPhone"
- Roadmap Cherri : feature "Mac web server to sign Shortcuts made using Playground" = **complété ✅**
- ⚠️ `cherri --hubsign` en CLI a des erreurs (mai 2026), mais le **Playground web** utilise son propre serveur — ça marche
- **C'est la solution recommandée pour Linux-only**

### 3. ⭐⭐ Cherri CLI sur Linux + HubSign (CONFIRMÉ GRATUIT juillet 2026)

**Découverte majeure (30 juillet 2026)** : Le binaire Cherri CLI sur Linux **compile ET signe via HubSign gratuitement** — sans compte RoutineHub, sans macOS, sans VM.

**Installation (binaire précompilé, pas besoin de Go) :**
```bash
curl -sL "https://github.com/electrikmilk/cherri/releases/download/v2.3.0/cherri_linux-x86_64.zip" -o /tmp/cherri.zip
python3 -c "import zipfile; zipfile.ZipFile('/tmp/cherri.zip').extractall('/tmp/')"
chmod +x /tmp/cherri
/tmp/cherri -v  # → Cherri Compiler v2.3.0
```

**Compilation + signature (une commande) :**
```bash
cherri mon_raccourci.cherri
# → Signing using HubSign service...
# → Shortcut Signing Powered By RoutineHub
# → Fichier .shortcut signé (format AEA1) généré dans le cwd
```

**Vérifié** : fichier de sortie 22KB, header `AEA1` (signature Apple valide), importable sur iOS 18+.

**⚠️ Le `#include` fonctionne en CLI** (pas dans le Playground web) — c'est la méthode préférée pour les raccourcis complexes utilisant `jsonRequest()` et les actions web.

**Le fichier de sortie** : Cherri nomme le fichier selon `#define name` (avec espaces). Utiliser `--output chemin/fichier.shortcut` pour contrôler le nom, ou renommer après coup.

### 4. HubSign (RoutineHub) — service direct
- Service web de signature hébergé par RoutineHub
- **Payant pour usage direct** : RoutineHub membership requis ($57.60-$200/an)
- 7 jours d'essai gratuit
- **MAIS** Cherri CLI et Playground l'utilisent gratuitement (le coût est absorbé par Cherri)
- Erreurs intermittent signalées mai 2026, mais **fonctionne en juillet 2026** avec v2.3.0
- Source : https://routinehub.co/membership/

### 4. Serveur auto-hébergé (scaxyz/shortcut-signing-server)
- Open source (Unlicense), 30 ⭐ sur GitHub
- **Mais nécessite macOS** — utilise docker-osx (macOS virtualisé dans Docker)
- docker-osx = instable, lourd, nécessite KVM, UI/VNC pour login macOS
- Dernier commit : octobre 2023 — projet inactif
- Non recommandé

### 5. Jellycuts app iOS (gratuit)
- L'app tourne **sur iOS**, utilise l'API de signature Apple directement
- Build & Export → raccourci signé apparaît dans Shortcuts
- Version gratuite compile et signe
- **Pas besoin de Mac ni de serveur externe**
- Inconvénient : app qualité moyenne (3.6/5), modèle abonnement ($5-20/an), langage limité
- Mais pour copier-coller du code et appuyer sur Build, ça suffit
- ⚠️ Ne pas recommander sans réserve — vérifier d'abord si Cherri Playground suffit

### 6. Construction manuelle dans app Shortcuts
- Aucun fichier à signer — construit directement sur device
- Pas de Mac, pas d'app tierce
- Inconvénient : fastidieux pour les raccourcis complexes (API REST, JSON)

### 7. docker-osx (macOS VM sur Linux)
- Gratuit, fonctionne si KVM disponible
- **Lourd** : 4-8GB RAM, ~30GB disk, setup initial VNC obligatoire
- Légalité gris (Apple EULA limite à 2 VMs sur hardware Apple)
- Utilisateur a refusé cette option — trop complexe

## Cherri — détails techniques

- **Repo** : github.com/electrikmilk/cherri (1.6k ⭐, GPL-2.0)
- **Actif** : commits quotidiens, dernière release v2.3.0 (mai 2026)
- **Langage** : syntaxe similaire à Go/Ruby
- **Features** : includes multifichiers, macros, functions, type system, package manager git-based
- **Installation Linux (binaire précompilé)** : télécharger `cherri_linux-x86_64.zip` depuis GitHub releases, extraire, `chmod +x`. Pas besoin de Go.
- **Installation Linux (from source)** : `git clone https://github.com/electrikmilk/cherri.git && cd cherri && go build`
- **Compilation + signature sur Linux** : `cherri fichier.cherri` → compile ET signe via HubSign automatiquement (gratuit, confirmé juillet 2026)
- **Compilation sans signature** : `cherri fichier.cherri --skip-sign` (produit `.shortcut` non signé)
- **Signature via Playground** : coller le code sur playground.cherrilang.org → Export → Download
- **Le Playground web a des limitations** que la CLI n'a pas (voir section limitations ci-dessous) — **préférer la CLI** pour les raccourcis complexes

## ⚠️ Cherri Playground — limitations du compilateur WASM (testé juillet 2026)

Le Playground utilise une version WebAssembly du compilateur Cherri. Il a des limitations importantes découvertes en testant réellement :

### `rawAction()` ne fonctionne PAS dans le Playground
- Génère silencieusement **"0 actions"** sans message d'erreur
- Les `rawAction()` qui marchent en CLI native sont ignorées par le compilateur WASM
- **Solution** : utiliser uniquement les actions standards Cherri (`alert`, `prompt`, `show`, `url`, etc.)

### `jsonRequest()` — règles strictes
- Le paramètre `body` doit être un **littéral dictionnaire inline**, pas une variable
  - ✅ `jsonRequest("url", 'POST', {"input": "{@question}"}, {...})`
  - ❌ `@body = {"input": "..."}; jsonRequest("url", 'POST', @body, ...)` → erreur "Shortcuts does not allow variable values for this argument"
- Les enums `HTTPMethod` doivent être en **string entre quotes** : `'POST'` pas `POST`
  - ❌ `jsonRequest("url", POST, ...)` → "Undefined reference 'POST'"
  - ✅ `jsonRequest("url", 'POST', ...)`

### `#include` déjà inclus par défaut
- Le Playground inclut déjà `actions/web` et `actions/basic` par défaut
- Ajouter `#include 'actions/web'` → erreur "Path 'actions/web' has already been included"
- **Solution** : ne pas mettre d'`#include` dans le Playground

### UI du Playground — guide des boutons
| Bouton | Icône | Fonction |
|--------|-------|----------|
| **Compiler** | marteau (hammer) | Compile le code .cherri → affiche les actions générées |
| **Export** | flèche montante (square_arrow_up) | Ouvre le dialogue Export avec "Download Shortcut" |
| **Import** | cloud_download | Ouvre un dialogue pour importer un shortcut depuis un lien iCloud |
| **Partager** | link | Génère un lien partageable |

### Flow confirmé par test réel (juillet 2026)
1. Coller code Cherri dans l'éditeur (gauche)
2. Cliquer **marteau** → "Compiler Output" affiche les actions (ou "Compiler Error" si problème)
3. Cliquer **flèche montante** → dialogue "Export" avec bouton "Download Shortcut"
4. Cliquer **Download Shortcut** → affiche **"Signing..."** pendant ~3 secondes
5. Le texte revient à "Download Shortcut" = **fichier signé téléchargé** ✅
6. Signature "Powered By HubSign" — mais **gratuit** (le Playground utilise son propre serveur macOS)

### Code minimal qui compile dans le Playground
```cherri
/* Hello, Cherri! */
#define glyph smileyFace
#define color yellow
@message = "Hello!"
alert("Message: {@message}", "Alert")
```

### Code qui ne compile PAS dans le Playground (à éviter)
- `rawAction(...)` → 0 actions silencieusement
- `#include 'actions/web'` → "already been included"
- Variables pour `body` de `jsonRequest()` → "does not allow variable values"
- Enums sans quotes (`POST` au lieu de `'POST'`) → "Undefined reference"

## Cherri vs Jellycuts — comparaison

| Critère | Cherri | Jellycuts |
|---------|--------|-----------|
| Prix | 100% gratuit | Freemium (abonnement $5-20/an) |
| Open source | Oui (GPL-2.0, 1.6k ⭐) | Partiel (OpenJelly) |
| Plateforme | CLI (macOS/Linux) + macOS IDE + VS Code | App iOS uniquement |
| Signature | macOS native ou **Playground web gratuit** | iOS native (gratuit) |
| Développement | Sur serveur/desktop | Sur iPhone |
| Includes/fichiers | ✅ `#include` | ❌ |
| Version control | ✅ (fichiers .cherri dans git) | ❌ |
| Package manager | ✅ (git-based) | ❌ |
| Active dev | Très actif (commits quotidiens) | Aux abonnés absents |
| Qualité | Bien documenté, communauté positive | 3.6/5 App Store |

## Conclusion pratique pour Linux-only — juillet 2026

**Pour créer des raccourcis sans Mac :**
1. **⭐⭐ Cherri CLI sur Linux** = meilleure solution (gratuit, compile + signe via HubSign, supporte `#include` et `jsonRequest()`, code sur serveur)
2. **⭐ Cherri Playground web** = alternative si pas de serveur Linux (gratuit mais limitations : pas de `#include`, pas de `rawAction`)
3. **Jellycuts gratuit** = alternative si l'utilisateur veut tout faire sur iPhone sans serveur
4. **Construction manuelle** = pour 2-3 raccourcis simples

**Pour éviter complètement les raccourcis :**
- **pyicloud** pour Rappels iCloud natifs (créer des rappels depuis le serveur, sync iCloud native)
- **HA Companion App** pour rappels push (notifications actionnables)
- **Radicale** pour sync calendrier CalDAV bidirectionnelle
- Ces trois solutions ne nécessitent AUCUN raccourci à créer/signer

## Recommandation workflow
1. Commencer par pyicloud + HA Companion + Radicale (zéro raccourci, couvre 80% des besoins)
2. Si raccourcis nécessaires (Siri, bouton d'action) : Cherri Playground, je code, utilisateur colle sur Playground web
3. Jellycuts en fallback si Playground inaccessible

## Notes serveur (spécifique Jefe)

- **API server Hermes** : config indique `port: 9120` mais port réel peut différer (observé 9119). Vérifier : `grep "API server listening" ~/.hermes/logs/gateway.log`
- **Clé API server** : stockée dans `.env` (`API_SERVER_KEY=...`), pas dans `config.yaml` (`gateway.api_server.extra.key` est une clé différente — celle du config.yaml a été rejetée)
- **Radicale** : container `tomsquest/docker-radicale` en read-only rootfs, UID 2999. Config + htpasswd en bind mount `/srv/docker/radicale/config/` (PERSISTANT). `TAKE_FILE_OWNERSHIP=false` requis pour éviter restart loop. HA CalDAV integration : mot de passe alphanumérique SANS caractères spéciaux ($&!*#^ causent invalid_auth). Créer calendrier VEVENT via MKCALENDAR pour que HA crée l'entité `calendar.*`. Voir `references/radicale-caldav-setup.md` pour setup complet.
- **Home Assistant** : `network_mode: host` requis, port 8123. Image `ghcr.io/home-assistant/home-assistant:stable`