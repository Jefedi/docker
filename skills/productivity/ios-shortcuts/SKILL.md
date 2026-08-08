---
name: ios-shortcuts
title: "iOS Raccourcis — Création de Shortcuts"
description: "Guide complet pour créer des Raccourcis iOS (Shortcuts) en français : actions disponibles, manipulation d'API REST, dictionnaires JSON, variables, automatisations."
author: "Hermes Agent"
version: "1.0"
triggers:
  - "raccourci"
  - "shortcut"
  - "iOS raccourcis"
  - "raccourci iOS"
  - "automatisation iOS"
---

# iOS Raccourcis — Guide de Création

## Architecture d'un Raccourci

Un Raccourci = une séquence d'**actions**. Chaque action prend une **entrée** (optionnelle), produit une **sortie**, et la passe à l'action suivante via les **variables magiques** (représentées par `<<<>>>` dans le flux).

### Termes clés (français)
| Terme Raccourcis | Équivalent développeur |
|---|---|
| **Action** | Une étape / fonction |
| **Variable magique** | Résultat de l'action précédente, passé automatiquement |
| **Variable** | Stocke une valeur pour la réutiliser |
| **Dictionnaire** | Objet JSON `{key: value}` |
| **Feuille de partage** | Share Sheet / Entrée depuis une autre app |
| **Automatisation** | Déclenché par un événement (heure, WiFi, NFC...) |

---

## Actions Web & API REST

### Obtenir le contenu d'une URL — `GET | POST | PUT | DELETE`
**Catégorie :** Web

Configure :
- **URL** → l'endpoint complet (ex: `https://translate.jefe.ovh/translate`)
- **Méthode** → GET, POST, PUT, DELETE, PATCH
- **En-têtes** → ajouter des paires `Nom: Valeur` (ex: `Content-Type: application/json`)
- **Corps de la requête** → pour POST/PUT : JSON, Formulaire, Fichier, ou Demander
- **Traitement avancé** : suivre les redirections, timeout

**Sortie :** Le contenu de la réponse (JSON automatiquement parsé).

---

## Actions Dictionnaire / JSON

| Action (français) | Usage |
|---|---|
| **Définir un dictionnaire** | Créer un objet `{key: value}`, valeurs = variables magiques possibles |
| **Obtenir la valeur d'un dictionnaire** | Extraire une valeur par sa clé |
| **Obtenir les clés d'un dictionnaire** | Lister les clés |
| **Définir une liste / Tableau** | Créer un tableau `[a, b, c]` — le nom français exact est **Tableau** |
| **Obtenir le nombre d'éléments** | Compter les items d'une liste |
| **Obtenir un élément d'une liste** | Récupérer un élément par son index (1-indexé : 1 = premier) |

Quand une API renvoie du JSON, le résultat est automatiquement parsé → tu appliques directement **"Obtenir la valeur d'un dictionnaire"**.

### Construction JSON champ par champ (recommandé)

**PRÉFÉRER la construction champ par champ** via le menu **Corps → JSON** de l'action « Obtenir le contenu d'une URL » plutôt que de coller du JSON brut dans une action Texte. Raccourcis sérialise correctement et c'est plus fiable.

Pour un corps complexe avec des tableaux et dictionnaires imbriqués, par exemple :
```json
{"model": "hermes-agent", "stream": false, "messages": [{"role": "user", "content": "..."}]}
```

1. Ajouter un champ → Clé: `model`, Type: **Texte**, Valeur: `hermes-agent`
2. Ajouter un champ → Clé: `stream`, Type: **Booléen**, Valeur: `false`/`Faux`
3. Ajouter un champ → Clé: `messages`, Type: **Tableau**
4. Dans le tableau, ajouter **1 élément** → choisir **Dictionnaire**
5. Dans ce dictionnaire, ajouter les champs :
   - Clé: `role`, Type: **Texte**, Valeur: `user`
   - Clé: `content`, Type: **Texte**, Valeur: *(insérer variable magique)*

Les variables magiques s'insèrent par tap long sur le champ → sélectionner la variable.

### Extraction de réponse JSON chaînée

Pour extraire une valeur nichée dans une réponse complexe, chaîner les actions étape par étape. Exemple : `choices[0].message.content` de `/v1/chat/completions` :

1. **Obtenir la valeur d'un dictionnaire** → clé: `choices`
2. **Obtenir un élément d'une liste** → index: `1` (1 = premier élément dans Raccourcis)
3. **Obtenir la valeur d'un dictionnaire** → clé: `message`
4. **Obtenir la valeur d'un dictionnaire** → clé: `content`
5. **Afficher un résultat** (ou Prononcer le texte)

Les listes sont **1-indexed** dans Raccourcis, pas 0-indexed — toujours mettre `1` pour le premier élément.

---

## Actions Texte

| Action (français) | Usage |
|---|---|
| **Texte** | Créer un bloc texte (supporte les variables magiques dedans) |
| **Remplacer du texte** | Rechercher/remplacer (support regex) |
| **Fractionner du texte** | Découper par séparateur |
| **Combiner du texte** | Joindre une liste avec séparateur |
| **Encoder/Décoder une URL** | urlencode / urldecode |
| **Encoder/Décoder en Base64** | Base64 |

---

## Actions Variables

| Action | Usage |
|---|---|
| **Définir une variable** | Stocker le résultat courant dans une variable nommée |
| **Ajouter à une variable** | Ajouter à une liste existante |
| **Obtenir une variable** | Récupérer une variable définie plus tôt |

---

## Actions Conditionnelles & Boucles

**Si** — conditions : est, n'est pas, contient, commence par, supérieur à, inférieur à...
**Répéter avec chaque** — itérer sur une liste (variable `Élément de répétition`)
**Répéter** — boucle N fois

---

## Actions d'Entrée / Sortie

| Action | Usage |
|---|---|
| **Demander une entrée** | Champ libre (texte, date, nombre...) |
| **Demander un texte** | Saisie texte simple |
| **Demander une liste** | Menu déroulant |
| **Choisir dans une liste** | Sélection dans une liste |
| **Afficher un résultat** | Popup avec le résultat |
| **Afficher une notification** | Notification push locale |
| **Copier dans le presse-papier** | Copie le texte |
| **Obtenir le presse-papier** | Récupère le texte copié |

### Entrée du raccourci (Shortcut Input)
- **Disponible quand** : le raccourci est lancé depuis la **Feuille de partage**
- **Contient** : le texte/URL/fichier sélectionné
- Pour l'obtenir : **"Obtenir une variable"** → `Entrée du raccourci`

---

## Cas Pratique : Traduction avec ton LibreTranslate

### Raccourci « Traduire » (depuis la feuille de partage)

Étape par étape :

1. **Obtenir une variable** → `Entrée du raccourci`
2. **Définir une variable** → nomme-la `texteATraduire`
3. **Définir un dictionnaire** :
   - `q`: variable magique `texteATraduire`
   - `source`: `auto`
   - `target`: `fr` (ou demande)
   - `api_key`: `TA_CLE_API`
4. **Obtenir le contenu d'une URL** :
   - Méthode : `POST`
   - URL : `https://translate.jefe.ovh/translate`
   - Type de corps : `JSON`
   - Corps : variable magique du dictionnaire
   - En-têtes : `Content-Type: application/json`
5. **Obtenir la valeur d'un dictionnaire** → clé : `translatedText`
6. **Copier dans le presse-papier** (optionnel)
7. **Afficher un résultat** → `traduction`

### Avec choix de langue (menu)

Avant le dictionnaire, ajouter :
- **"Demander une liste"** : `Langue cible ?` → choix : `Français`, `Anglais`, `Espagnol`...
- Puis **"Si"** : si résultat = `Français` → définir variable `codeLangue` = `fr`
- Utiliser `codeLangue` dans le dictionnaire

---

## Partage

Dans Raccourcis → `⋮` sur le raccourci → **Partager** → **Copier le lien iCloud**.

---

## Pièges Connus

### Bug de sérialisation JSON : tableaux de dictionnaires (iOS)

**Problème :** Quand un corps JSON contient un **Tableau de Dictionnaires** (ex: `messages` = `[{"role":"user","content":"..."}]`), Shortcuts sérialise parfois les dictionnaires du tableau comme des listes. L'API reçoit une `list` au lieu d'un `dict` et plante en 500 :

```
AttributeError: 'list' object has no attribute 'get'
```

**Solution :** Utiliser l'endpoint **Responses API** — prend juste `{"input": "texte"}`, pas de tableau `messages[]`. Voir `references/hermes-api-integration.md`.

### Fichier .shortcut non signé = refusé (iOS 18+)
Apple **ne permet plus** d'importer un fichier `.shortcut` généré depuis un serveur ou un script. Il doit être **signé** via le CLI `shortcuts` de macOS.

- ❌ Fichier `.shortcut` généré en Python → bloqué : *"L'importation de raccourcis non signés n'est pas prise en charge"*
- ❌ `shortcuts sign` sur GitHub Actions (runner macOS) → **impossible** car nécessite une session iCloud active, absente sur les runners cloud
- ❌ Lien iCloud → **impossible à générer depuis un serveur**, Apple le crée quand l'utilisateur partage depuis l'app Raccourcis (`⋮` → Partager → Copier le lien iCloud)

### Options sans Mac

| Méthode | Description |
|---|---|
| **Pas à pas** | Donner les instructions action par action, l'utilisateur construit dans Raccourcis |
| **Shortcut Source Tool** | Installer le shortcut depuis routinehub.co, lui passer un JSON → il crée le shortcut sur l'iPhone directement |
| **GitHub Actions** | Générer `.shortcut` + `.json` dans un artifact, utilisateur télécharge et importe via Shortcut Source Tool |

### Workflow recommandé (utilisateur Windows + iPhone)
1. **Préférer le pas à pas** avec validation à chaque étape
2. Utiliser les **noms français exacts** des actions
3. Si l'utilisateur a GitHub : créer un repo privé avec workflow GitHub Actions (runner **ubuntu**, pas macOS) qui génère le `.shortcut` + `.json`, l'utilisateur télécharge l'artifact
4. Pour le cas où le pas à pas est trop long : **Shortcut Source Tool + JSON** comme alternative rapide

### Génération automatisée via GitHub Actions
Pattern pour générer des shortcuts programmatiquement :

1. Script Python (`generate_shortcut.py`) qui construit un dict `WFWorkflow` et l'exporte via `plistlib.dump(obj, fmt=plistlib.FMT_BINARY)` en `.shortcut` + `json.dump()` en `.json`
2. Workflow GitHub Actions sur `ubuntu-latest` (pas besoin de macOS) :
   - `actions/checkout@v4`
   - `python3 generate_shortcut.py`
   - `actions/upload-artifact@v4` avec les deux fichiers
3. L'API key (si l'app en a une) : stockée dans **GitHub Secrets** → passée en variable d'env dans le workflow
4. Ne JAMAIS utiliser de runner macOS pour signer — ça ne marche pas (iCloud requirement)

**Voir `references/github-actions-workflow.md` pour un template complet.**

**Voir `references/hermes-api-integration.md` pour le cas pratique Hermes API Server.**

---

## Authentification sur les API

**Bearer Token :**
```
En-tête → Authorization: Bearer ton_token
```

**Basic Auth :**
```
En-tête → Authorization: Basic base64(user:password)
```

**API Key dans l'URL (GET) :**
```
https://api.exemple.com/data?api_key=ton_key
```

**API Key dans le corps JSON (POST) :** (ex: LibreTranslate)
Ajouter `api_key` comme une ligne du dictionnaire JSON envoyé dans le corps :
```json
{ "q": "texte", "source": "auto", "target": "fr", "api_key": "ta_cle" }
```

---

## Automatisations

Déclencheurs disponibles : **Heure**, **WiFi**, **Bluetooth**, **NFC**, **Application**, **Arrivée/Départ**, **Chargeur**, **Réveil**, **Mode Avion**, **Ne pas déranger**, **Mode Sommeil**.

---

## Limitations

### Signature iOS 18+ (fichiers .shortcut)
Depuis iOS 18, Apple **refuse l'importation des fichiers `.shortcut` non signés**.
- **GitHub Actions** (macOS runner) : `shortcuts sign` nécessite iCloud → pas de session iCloud sur le runner → **impossible**.
- **Shortcut Source Tool** (RoutineHub #5256) : alternative pour importer depuis JSON directement sur l'iPhone. Installer Shortcut Source Tool + Shortcut Source Helper, puis choisir « Edit source and import back ».
- **Jellycuts** : Le Build & Export intègre la signature → **solution la plus simple**.

### Alternatives sans Mac
| Méthode | Marche ? | Notes |
|---|---|---|
| Étape par étape dans Raccourcis | ✅ | Long mais fiable |
| Jellycuts (code Jelly) | ✅ | Compile + signe direct |
| Fichier .shortcut généré | ❌ iOS 18+ | Bloqué par signature |
| Shortcut Source Tool | ✅ | Depuis JSON → import local |
| GitHub Actions | ❌ | Pas d'iCloud sur runner |

## Notes Importantes

1. Les noms d'actions sont **en français** automatiquement selon la langue de l'iPhone.
2. Les **variables magiques** s'insèrent en touchant longuement un champ → sélectionner la variable.
3. Pour déboguer : mettre **"Afficher un résultat"** entre les étapes.
4. Les raccourcis se synchronisent via iCloud entre iPhone, iPad et Mac.
