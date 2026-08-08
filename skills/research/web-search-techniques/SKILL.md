---
name: web-search-techniques
description: "Rechercher sur le web quand Firecrawl, DDG ou Bing plantent."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web, search, google, duckduckgo, bing, curl, browser, fallback, research]
    category: research
    requires_toolsets: [terminal, browser]
---

# Web Search Techniques

Quand `web_search` (Firecrawl) ou `web_extract` plantent (Payment Required,
credits exhausted), utiliser ce ladder de fallbacks pour trouver l'info.

## Ladder de fallbacks (du plus simple au plus désespéré)

### 1. web_search / web_extract (essayer d'abord)
- Si erreur "Payment Required" → passer au fallback 2

### 2. browser_navigate → Google Search
- `browser_navigate` vers `https://www.google.com/search?q=<query>`
- Le snapshot contient les résultats (titres, snippets, liens)
- ⚠️ Le serveur peut être en Finlande → UI en finnois/allemand mais les
  résultats sont lisibles dans le snapshot
- Les liens `[eN]` permettent de cliquer directement vers les résultats
- **Méthode la plus fiable** quand elle marche

### 3. curl + DuckDuckGo HTML
```bash
curl -s "https://html.duckduckgo.com/html/?q=<query>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://duckduckgo.com/" > /tmp/ddg.html
```
Puis parser:
```python
import re
html = open('/tmp/ddg.html').read()
results = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</div>', html, re.DOTALL)
for t, s in zip(results, snippets):
    t = re.sub(r'<[^>]+>', '', t).strip()
    s = re.sub(r'<[^>]+>', '', s).strip()
    print(f'{t}\n   {s}')
```

⚠️ **DDG rate-limit**: bloque après 2-3 requêtes rapides depuis la même IP.
Si `len(html) < 14000` et pas de résultats → bloqué. Espacer les requêtes.

### 4. curl + Bing RSS (à éviter)
```bash
curl -s "https://www.bing.com/search?format=rss&q=<query>" -H "User-Agent: Mozilla/5.0" > /tmp/bing.xml
```
⚠️ **Bing RSS ignore souvent la query** et renvoie des résultats génériques
(assurance voyage, "what is a query" en néerlandais). NE PAS FAIRE CONFIANCE
pour des recherches ciblées. Utile uniquement pour discovery très large.

### 5. curl direct vers un site connu
Si on connaît le site cible (ex: dogwash.fr, ville-fecamp.fr):
```bash
curl -s -L "<url>" -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text)
for kw in ['keyword1', 'keyword2']:
    idx = text.lower().find(kw.lower())
    if idx >= 0:
        print(f'--- {kw} ---')
        print(text[max(0,idx-80):idx+200])
"
```

⚠️ **Sécurité**: le security scan peut flaguer `curl | python3` comme HIGH.
C'est un faux positif — le contenu est lu passivement, pas exécuté.
Approuver via smart approval.

## Techniques spéciales

### Google My Maps KML Extraction

Quand un site a une carte "Trouvez le point le plus proche" avec un iframe
Google My Maps, on peut extraire TOUTES les données en KML.

**Étape 1**: Trouver l'iframe dans le HTML:
```bash
curl -s -L "<url>" | grep -oP 'src="https://www.google.com/maps/d/[^"]*"'
```

**Étape 2**: Remplacer `/embed?` par `/kml?` et ajouter `&forcekml=1`:
```
https://www.google.com/maps/d/u/5/kml?mid=<MAP_ID>&forcekml=1
```

**Étape 3**: Parser le KML:
```python
import xml.etree.ElementTree as ET
import math

tree = ET.parse('data.kml')
root = tree.getroot()
ns = {'k': 'http://www.opengis.net/kml/2.2'}

ref_lat, ref_lng = 49.4944, 0.1076  # point de référence

for pm in root.findall('.//k:Placemark', ns):
    name = pm.find('k:name', ns).text or ''
    ext = {}
    for d in pm.findall('.//k:Data', ns):
        key = d.get('name')
        val = d.find('k:value', ns)
        if val is not None:
            ext[key] = val.text or ''
    addr = ext.get('address', '')
    city = ext.get('city', '')
    zip_code = ext.get('zip', '')
    lat = float(ext.get('lat', '0') or '0')
    lng = float(ext.get('lng', '0') or '0')
    dist = math.sqrt((lat - ref_lat)**2 + (lng - ref_lng)**2) * 111
    if dist < 150:
        print(f'{name} — {round(dist,1)} km — {addr}, {city} ({zip_code})')
```

### PDF via browser_navigate
Les PDFs officiels (ex: brochures tourisme) sont rendus par le viewer
intégré du navigateur. Le snapshot contient le texte du PDF — pas besoin
de télécharger/parser séparément.

### Pages avec accordéons
Les sites municipaux (lehavre.fr, etc.) utilisent des sections repliables.
Utiliser `browser_click` sur les boutons d'accordéon, puis
`browser_snapshot(full=true)` pour lire le contenu déployé.

## Quand le navigateur plante (410/500)

Le browser peut crasher (410 Gone, 500 Internal). Solutions:
1. Réessayer `browser_navigate` avec une nouvelle URL (le tab se recrée)
2. Si ça persiste, basculer sur curl + parsing
3. Ne pas boucler sur la même URL qui plante — changer d'approche

## Query patterns pour recherches en français

```
# Services locaux:
"<service>" "<ville>" libre service self service
"<brand>" OR "<chain>" "<ville>" OR "<region>"

# Réglementations:
règlement <sujet> <ville> <règle> <restriction>
"<sujet>" site:<authority-site>.fr

# Multi-villes:
"<keyword>" <ville1> OR <ville2> OR <ville3>
```

## Pitfalls

- **Firecrawl credits**: web_search et web_extract utilisent Firecrawl.
  Quand les credits sont épuisés, erreur "Payment Required". Pas de solution
  sauf recharger le compte — utiliser les fallbacks curl/browser.
- **DDG rate-limit**: ~2-3 requêtes max avant blocage. Délai ~30s entre
  requêtes si nécessaire.
- **Bing RSS unreliable**: ignore souvent la query. Ne pas utiliser pour
  recherche ciblée.
- **Bing language**: serveur en Finlande → UI en finnois. Les résultats
  sont quand même dans la langue de la query.
- **Google bot detection**: Google peut bloquer curl direct. Utiliser
  browser_navigate à la place.
- **curl | python3 security flag**: faux positif — approuver via smart
  approval. Le contenu est lu, pas exécuté.
- **Browser tab crashes**: en cas d'erreur 410/500, ne pas boucler —
  changer de méthode (curl ou nouvelle URL).

## Verification

Après avoir trouvé une info via fallback, vérifier avec une seconde source
quand possible — surtout pour des données qui peuvent être obsolètes
(horaires, fermetures, changements de réglementation).