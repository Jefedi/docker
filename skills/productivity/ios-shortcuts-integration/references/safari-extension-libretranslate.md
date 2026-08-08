# Safari Extension / Bookmarklet for LibreTranslate on iOS

## État des lieux (août 2026)

Il n'existe **aucune** extension Safari (iOS ou macOS) pour LibreTranslate, ni sur l'App Store, ni sur GitHub. Toutes les extensions LibreTranslate existantes ciblent Chrome/Firefox.

## Extensions Chrome/Firefox connues

| Repo | Navigateur | Manifest | Notes |
|------|-----------|----------|-------|
| `anyblabla/LibreTranslate` | Chrome/Vivaldi | V3 | **Meilleur candidat** — en français, configurable (URL instance + clé API), GPL-2.0, code propre |
| `dzalyvadnyi/libretranslate-chrome-extension` | Chrome | V3 | MIT, minimal, bon point de départ |
| `K-Francis-H/libretranslate-unofficial-ff-extension` | Firefox | V2 | Inactif depuis 2022 |
| `hugopeixoto/libretranslate-firefox` | Firefox | V2 | Inactif depuis 2022 |

## Option 1 — Convertir l'extension Chrome en extension Safari (nécessite Mac)

Apple fournit `xcrun safari-web-extension-converter` qui transforme une extension Chrome/Firefox (Manifest V2 ou V3) en projet Xcode pour Safari.

```bash
git clone https://github.com/anyblabla/LibreTranslate.git
xcrun safari-web-extension-converter /chemin/vers/LibreTranslate
```

Génère un projet Xcode complet (container app + extension Safari). Signer avec un compte Apple Developer gratuit (suffisant pour usage personnel). Inconvénient : nécessite Mac + Xcode, re-signature tous les 7 jours en gratuit.

## Option 2 — Bookmarklet avancé (RECOMMANDÉ — zéro dépendance)

Bookmarklet JavaScript qui traduit la **page entière in-place** : remplace le texte des éléments DOM par leur traduction, avec barre de progression. Utilise la technique [SEP] pour batcher les requêtes (10 éléments par requête).

### Prérequis

**CORS** : LibreTranslate doit avoir `access-control-allow-origin: *`. Vérifier :
```bash
curl -s -I -X OPTIONS https://translate.jefe.ovh/translate \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
# Doit contenir: access-control-allow-origin: *
```

**Clé API** : `53e04e31-de93-4b49-a0e4-891b1806fc8d` (UUID complet — le préfixe `53e04e31` seul retourne "Invalid API key").

**Format** : `text` (pas `html`) — évite que LibreTranslate ne casse le DOM. On remplace `innerHTML` directement.

### Technique [SEP] — batch de traductions

Pour réduire le nombre de requêtes API, grouper plusieurs textes en une seule requête :
1. Joindre les textes avec `\n[SEP]\n` comme séparateur
2. Envoyer en une seule requête `q` avec `format: "text"`
3. Splitter la réponse par `\n[SEP]\n` pour récupérer chaque traduction

Testé et validé : 3 textes envoyés ensemble → 3 traductions correctes retournées, séparées par `\n[SEP]\n`.

### Le bookmarklet complet

```javascript
javascript:(function(){var API='https://translate.jefe.ovh/translate';var KEY='53e04e31-de93-4b49-a0e4-891b1806fc8d';var TARGET='fr';var blocks=document.querySelectorAll('p,li,h1,h2,h3,h4,h5,h6,td,th,div,span,a,article,section,blockquote,figcaption,caption,label,button');var texts=[];var els=[];for(var i=0;i<blocks.length;i++){var t=blocks[i].innerText.trim();if(t.length>3&&t.length<5000&&blocks[i].children.length<=20){texts.push(t);els.push(blocks[i])}}var total=texts.length;var overlay=document.createElement('div');overlay.style.cssText='position:fixed;top:0;left:0;right:0;background:#2563eb;color:white;padding:8px;font-size:13px;z-index:999999;font-family:sans-serif;text-align:center';overlay.textContent='🌐 LibreTranslate: 0/'+total;document.body.appendChild(overlay);function chunk(a,n){var r=[];for(var i=0;i<a.length;i+=n)r.push(a.slice(i,i+n));return r}var chunks=chunk(texts.map(function(t,i){return{text:t,el:els[i]}}),10);var ci=0;function nextChunk(){if(ci>=chunks.length){overlay.textContent='🌐 Traduction terminée ✓ ('+total+' éléments)';setTimeout(function(){overlay.remove()},2000);return}var chunk_=chunks[ci];ci++;overlay.textContent='🌐 '+(ci*10)+'/'+total;var combined=chunk_.map(function(c){return c.text}).join('\n[SEP]\n');fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:combined,source:'auto',target:TARGET,format:'text',api_key:KEY})}).then(function(r){return r.json()}).then(function(d){if(d.translatedText){var parts=d.translatedText.split('\n[SEP]\n');for(var j=0;j<chunk_.length;j++){if(parts[j]&&chunk_[j].el){chunk_[j].el.innerHTML=parts[j]}}}nextChunk()}).catch(function(e){overlay.textContent='❌ Erreur: '+e;setTimeout(function(){overlay.remove()},3000)})}nextChunk()})();
```

### Installation sur Safari iOS

1. **Activer la barre des favoris** : Safari → Paramètres → onglets → Afficher la barre des favoris = ON
2. **Créer un favori temporaire** : Partager → Ajouter aux favoris
3. **Modifier le favori** : Favoris (icône 📕) → maintiens le favori → Modifier
4. **Renommer** : `🌐 FR` (ou autre)
5. **Coller le code** : Remplacer l'URL par le bookmarklet complet (commence par `javascript:(function(){...})();`)
6. **Sauvegarder** → aller sur une page en anglais → tap le favori

### Détails techniques

- **Sélecteurs DOM** : `p,li,h1-h6,td,th,div,span,a,article,section,blockquote,figcaption,caption,label,button`
- **Filtres** : texte > 3 chars, < 5000 chars, ≤ 20 enfants (évite les containers complexes)
- **Chunk size** : 10 éléments par requête (compromis latence/charge API)
- **Format** : `text` (pas `html`) → remplace `innerHTML` directement
- **Progress overlay** : div fixe en haut, z-index 999999, auto-supprimé après 2s

### Variante — texte sélectionné uniquement

Remplacer la collecte DOM par `window.getSelection().toString()` pour traduire juste un passage.

### Variante — autre langue cible

Changer `var TARGET='fr'` → `en`, `es`, `de`, etc.

## Option 3 — Raccourci iOS via Cherri (share sheet)

Voir section H du SKILL.md principal. Le raccourci Cherri traduit du texte sélectionné via share sheet, mais ne traduit pas une page Safari entière in-place.

## Recommandation

Pour utilisateur sans Mac, LibreTranslate self-hosted à `translate.jefe.ovh` :
- **Option 2 (bookmarklet)** : mise en place en 2 minutes, traduction page entière in-place, gratuit
- **Option 3 (Cherri)** : si déjà dans le workflow raccourcis — texte sélectionné uniquement
- **Option 1 (xcrun)** : si accès Mac — vraie extension Safari native