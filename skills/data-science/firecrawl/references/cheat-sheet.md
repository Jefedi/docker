# 🔥 Firecrawl — Cheat Sheet Scraping

**Firecrawl** = API pour scraper, crawler et chercher sur le web, avec sortie Markdown/HTML prête pour les LLMs.

## 🔑 Démarrage rapide

```bash
# 1. Clé API : https://firecrawl.dev → Sign Up (gratuit, sans CB)
# 2. Installer le SDK Python
pip install firecrawl-py
```

## 📦 SDK Python

```python
from firecrawl import Firecrawl

# Soit via variable d'env FIRECRAWL_API_KEY
firecrawl = Firecrawl()

# Soit explicitement
firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")
```

---

## 🎯 1. Scraper une page unique

```python
result = firecrawl.scrape(
    "https://example.com",
    formats=["markdown"]        # markdown, html, rawHtml, screenshot, links, extract
)

print(result.markdown)          # Contenu en markdown
print(result.metadata.title)    # Titre de la page
print(result.metadata.source_url)
```

**Avec extraction LLM** (extraction de champs précis) :

```python
result = firecrawl.scrape(
    "https://example.com/product",
    formats=["markdown", "extract"],
    extract_options={
        "schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "price": {"type": "string"},
                "in_stock": {"type": "boolean"}
            }
        }
    }
)
print(result.extract)  # Données structurées JSON
```

**CURL équivalent :**
```bash
curl -X POST https://api.firecrawl.dev/v2/scrape \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown"]
  }'
```

### Options utiles du scrape

| Option | Description |
|--------|-------------|
| `onlyMainContent: true` | Ignore nav, footer, sidebar |
| `formats: ["markdown"]` | Sortie markdown propre |
| `formats: ["extract"]` | Extraction LLM structurée |
| `waitFor: 3000` | Attend 3s (pages JS lourdes) |
| `mobile: true` | Vue mobile |
| `timeout: 30000` | Timeout (ms) |
| `includeTags: ["article", "h1"]` | Garde seulement ces balises |
| `excludeTags: ["nav", "footer"]` | Exclut ces balises |
| `blockAds: true` | Bloque les pubs |
| `removeBase64Images: true` | Nettoie les images en base64 |

---

## 🗺️ 2. Mapper un site (trouver toutes les URLs)

```python
urls = firecrawl.map("https://example.com", limit=50)
print(urls.links)  # Liste des URLs trouvées
```

**CURL :**
```bash
curl -X POST https://api.firecrawl.dev/v2/map \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "limit": 50}'
```

---

## 🕸️ 3. Crawler tout un site

```python
# Automatique (bloque jusqu'à la fin)
job = firecrawl.crawl(
    url="https://docs.firecrawl.dev",
    limit=25,
    poll_interval=2,
    timeout=120,
    scrape_options={"formats": ["markdown"]}
)

for doc in job.data:
    print(doc.metadata.source_url)
    print(doc.markdown[:200])
```

**Non-bloquant :**
```python
job = firecrawl.start_crawl(url="https://example.com", limit=100)
crawl_id = job.id
print(f"Crawl lancé : {crawl_id}")

status = firecrawl.get_crawl_status(crawl_id)
print(f"Statut : {status.status} — {status.completed}/{status.total} pages")

firecrawl.cancel_crawl(crawl_id)  # Arrêter
```

**CURL :**
```bash
# Lancer
curl -X POST https://api.firecrawl.dev/v2/crawl \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "limit": 25}'

# Vérifier statut
curl https://api.firecrawl.dev/v2/crawl/<JOB_ID> \
  -H "Authorization: Bearer ***"
```

### Options du crawl

| Option | Description |
|--------|-------------|
| `limit` | Nombre max de pages |
| `maxDepth` | Profondeur max (2 = pages liées depuis pages liées) |
| `allowDomains` | `["example.com"]` — ne sort pas du domaine |
| `allowPaths` | `["/blog/*"]` — seulement le blog |
| `sitemap: "only"` | Crawle seulement les URLs du sitemap |
| `excludePaths` | `["/tag/*"]` — ignore les tags |

---

## 🔍 4. Search + Scrape combiné

```python
results = firecrawl.search(
    query="firecrawl python sdk",
    limit=5,
    scrape_options={"formats": ["markdown"]}  # Scrape auto les résultats
)

for page in results.data:
    print(f"• {page.title} — {page.url}")
```

**CURL :**
```bash
curl -X POST https://api.firecrawl.dev/v2/search \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{
    "query": "votre recherche",
    "limit": 5,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
```

### Filtres de recherche

| Option | Description |
|--------|-------------|
| `includeDomains` | `["github.com"]` — seulement GitHub |
| `excludeDomains` | `["pinterest.com"]` |
| `sources: ["news"]` | Actualités uniquement |
| `country: "FR"` | Géolocalisation France |
| `tbs: "qdr:d"` | Résultats du jour |

---

## 📋 5. Batch Scrape (plusieurs URLs)

```python
job = firecrawl.batch_scrape(
    urls=["https://example.com/a", "https://example.com/b", "https://example.com/c"],
    formats=["markdown"],
    poll_interval=2,
    timeout=120
)

for doc in job.data:
    print(f"{doc.metadata.source_url} → {len(doc.markdown)} chars")
```

---

## 📄 6. Parse (fichiers locaux)

```python
from firecrawl.v2.types import ParseOptions

with open("rapport.pdf", "rb") as f:
    parsed = firecrawl.parse(
        f.read(),
        filename="rapport.pdf",
        content_type="application/pdf",
        options=ParseOptions(formats=["markdown"])
    )
print(parsed.markdown)
```

---

## 🌐 7. Async (asynchrone)

```python
import asyncio
from firecrawl import AsyncFirecrawl

async def main():
    fc = AsyncFirecrawl(api_key="fc-API-KEY")
    doc = await fc.scrape("https://example.com", formats=["markdown"])
    print(doc["markdown"])

asyncio.run(main())
```

---

## 🧠 8. Extraction LLM avancée (Agent)

```bash
curl -X POST https://api.firecrawl.dev/v2/agent \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Trouve les prix et disponibilités des iPhone 16 sur les sites marchands français",
    "maxUrls": 10,
    "scrapeOptions": {"formats": ["markdown", "extract"]}
  }'
```

---

## 🧪 9. Tarifs (2025-2026)

| Plan | Prix | Credits/mois | Pages |
|------|------|-------------|-------|
| **Free** | **0€** | 100–500 crédits | ~100-500 pages |
| Hobby | $16/mois | 5k crédits | ~5k pages |
| Standard | $83/mois | 30k crédits | ~30k pages |
| Scale | $333/mois | 150k crédits | ~150k pages |

1 crédit = 1 page scrapée/crawlée. Pas de CB sur le free plan. Le nombre exact de crédits gratuits varie selon la date d'inscription (100 à 500).

---

## 🚀 10. Workflows typiques

### Petite extraction rapide
```bash
curl -s -X POST https://api.firecrawl.dev/v2/scrape \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}' \
  | jq '.data.markdown' | head -100
```

### Crawler un blog et tout garder en markdown
```python
pages = firecrawl.crawl("https://blog.example.com", limit=50)
for i, doc in enumerate(pages.data):
    with open(f"page_{i}.md", "w") as f:
        f.write(doc.markdown)
```

### Surveiller des prix quotidiennement
```python
prix = firecrawl.scrape(
    "https://site-marchand.fr/produit",
    formats=["extract"],
    extract_options={
        "schema": {
            "properties": {
                "prix": {"type": "string"},
                "disponible": {"type": "boolean"}
            }
        }
    },
    waitFor=2000  # Si chargement JS
)
```

---

## 💡 Pro Tips

- `onlyMainContent: true` → supprime nav/footer/pub, économise les crédits
- Scrape + Search combo → Firecrawl peut scraper automatiquement les résultats de recherche
- `waitFor` pour les SPAs (React, Vue) qui chargent le contenu en JS
- Formats multiples : `["markdown", "html", "screenshot"]` en un seul appel
- Firecrawl gère le JS → pas besoin de puppeteer/playwright en plus
- `storeInCache: true` → pas re-scrapé si déjà fait
- Export markdown = parfait pour alimenter des RAG / LLMs
