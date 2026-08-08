# Le-Partenaire.fr — URL Extraction and Matching

## Overview

Le-Partenaire.fr is the best automated source for French real estate data because:
- It includes DPE, charges copro, vendu/loué status, and taxe foncière on the search page
- It does NOT block automated scraping (unlike leboncoin/DataDome)
- Individual ad pages are accessible

## Two-Step Extraction

### Step 1: Get Listing Text Data via web_extract

```python
url = "https://www.le-partenaire.fr/immobilier/vente/appartement/le-havre/76600?prix-max=90000"
# web_extract returns the page content in markdown format
# This gives you: price, surface, rooms, DPE, charges, vendu/loué status, description
```

The search results page shows ~18-20 listings per page. web_extract typically captures ~16 before truncation.

### Step 2: Get Actual URLs via browser_console

Navigate to the same URL with the browser, then extract "Voir l'annonce" links:

```javascript
// Extract all "Voir l'annonce" hrefs in DOM order
Array.from(document.querySelectorAll('a[href*="/immobilier/vente/appartement/"]'))
  .filter(a => a.textContent.includes('Voir'))
  .slice(0, 25)
  .map(a => a.href)
```

This returns an array like:
```
[
  "https://www.le-partenaire.fr/immobilier/vente/appartement/havre/76600/1pieces/23226047",
  "https://www.le-partenaire.fr/immobilier/vente/appartement/havre/76600/3pieces/24052203",
  ...
]
```

### 🚨 SAFER APPROACH: Extract Both Headings and URLs from Browser (Single Pass)

The safest way to avoid mismatches is to extract both h2 headings AND URLs from the browser together:

```javascript
// Extract title + URL pairs in one pass — MATCH BY DOM ORDER
Array.from(document.querySelectorAll('h2')).map((h, i) => {
  const parent = h.closest('[class]') || h.parentElement;
  const voirLink = parent.querySelector('a[href*="/immobilier/vente/appartement/"]');
  return {
    idx: i,
    title: h.textContent.trim(),
    url: voirLink ? voirLink.href : 'NONE'
  };
}).slice(0, 25)
```

This returns objects like:
```json
[
  {"idx": 0, "title": "Vente Appartement à Le Havre 1 pièce | 30m²", "url": "https://.../1pieces/23226047"},
  {"idx": 1, "title": "Vente Appartement à Le Havre 3 pièces | 45m²", "url": "https://.../3pieces/24052203"},
  ...
]
```

**Why this matters:** If you use web_extract for text and browser for URLs separately, the page might render differently (e.g., ad removed mid-page, dynamic loading changing order). Extracting both from the same DOM snapshot guarantees correct matching.

### Step 3 (Alternative): Verify by Visiting the URL

When in doubt about a match, navigate to the individual ad page and check the title:

```
browser_navigate(url="https://www.le-partenaire.fr/immobilier/vente/appartement/havre/76600/1pieces/23654387")
// Title: "Vente Appartement à le Havre 1 pièce - 35m²" → price 108,000€
```

## Verified URL-to-Listing Mapping (May 2026)

To get the ACTUAL current mapping (not a stale snapshot), always use the browser single-pass extraction above. The table below is a reference example from one point in time and WILL CHANGE as new listings are added or old ones expire.

| # | h2 Title | Price | URL (last segment) |

| # | h2 Title | Price | URL (last segment) |
|---|----------|-------|-------------------|
| 1 | 1p 30m² | 69,000€ | /1pieces/23226047 |
| 2 | 3p 45m² | 149,000€ | /3pieces/24052203 |
| 3 | 4p 96m² | 330,000€ | /4pieces/24056405 |
| 4 | 2p 43m² | 145,000€ | /2pieces/23912097 |
| 5 | 4p 79m² | 198,000€ | /4pieces/23295307 |
| 6 | 2p 50m² | 89,000€ | /2pieces/23740336 |
| 7 | 4p 129m² | 910,000€ | /4pieces/22734071 |
| 8 | 5p 110m² | 399,990€ | /5pieces/23640132 |
| 9 | 2p 45m² | 189,900€ | /2pieces/23413796 |
| 10 | 3p 73m² | 71,000€ | /3pieces/22682688 |
| 11 | 1p 37m² | 70,000€ | /1pieces/22253230 |
| 12 | 2p 34m² | 112,000€ | /2pieces/23910459 |
| 13 | 2p 55m² | 152,000€ | /2pieces/23276827 |
| 14 | 1p 14m² | 50,500€ | /1pieces/22030795 |
| 15 | 1p 35m² | 108,000€ | /1pieces/23654387 |
| 16 | 2p 40m² | 75,000€ | /2pieces/23911201 |
| 17+ | (truncated in web_extract) | varies | /2/3pieces/... |

## Common Mistakes

1. **Assuming price filter is respected.** The page sometimes shows listings above the price-max filter. Always check each listing's actual price.
2. **Guessing the URL number.** Don't construct URLs from listing data — the ID number has no relationship to price or position. You MUST extract the href from the DOM.
3. **Using browser for text data.** The browser is slow for getting listing text data. Use web_extract for the text, browser only for the href extraction.