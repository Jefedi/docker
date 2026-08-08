---
name: local-business-search
description: "Find niche local services not in POI databases."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [local, business, search, kml, google-mymaps, franchise, poi, niche]
    category: research
    requires_toolsets: [terminal, browser]
---

# Local Business Search

Find niche local businesses and services that aren't in standard POI databases
(OpenStreetMap/Overpass, Google Places). Specialized franchise networks (dog
wash stations, self-service laundromats, EV chargers, specialty service
stations) often publish their locations as embedded Google My Maps or
proprietary store locators. This skill covers extraction techniques and
fallback search strategies.

## When to Use

- User asks for a specific type of service station or machine (not a salon or
  personal service) — e.g. "self-service dog wash stations", "automated bike
  repair kiosks", "coin-operated pet wash"
- OSM/Overpass doesn't have the category (the `maps` skill's `nearby` command
  returns nothing or irrelevant results)
- A franchise/network has a "Find a store" or "Nos emplacements" page with an
  embedded map
- User wants services within a radius of a specific city/location

## Key Distinction: Machine vs Salon

Users looking for "stations" or "machines" want **self-service automated
equipment** (like a car wash but for their pet/item) — NOT a salon or
grooming business where a person does the work. Always clarify this
distinction before searching. A grooming salon that offers a "baignoire en
libre-service" on reservation is NOT the same as a coin-operated machine
station open 24/7 without appointment.

## Techniques

### 1. Google My Maps KML Extraction (primary technique)

Many franchise networks embed their locations as a Google My Maps on their
website. You can extract the FULL dataset as KML and parse it
programmatically — far more complete than scraping individual pages.

**Step 1**: Navigate to the network's "locations" or "emplacements" page.

**Step 2**: Find the `<iframe>` pointing to Google My Maps:
```
https://www.google.com/maps/d/u/5/embed?mid=<MAP_ID>&...
```

**Step 3**: Fetch the KML by swapping `/embed?` for `/kml?`:
```bash
curl -s -L "https://www.google.com/maps/d/u/5/kml?mid=<MAP_ID>&forcekml=1" \
  -H "User-Agent: Mozilla/5.0" > data.kml
```

**Step 4**: Parse with Python's xml.etree:
```python
import xml.etree.ElementTree as ET
import math

tree = ET.parse('data.kml')
root = tree.getroot()
ns = {'k': 'http://www.opengis.net/kml/2.2'}

ref_lat, ref_lng = 49.4944, 0.1076  # reference point

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

**Real example**: Dogwash.fr embeds 130+ stations. KML URL:
```
https://www.google.com/maps/d/u/5/kml?mid=19US-ejjnglFBewQgSbdpzVbBNpmL-5I&forcekml=1
```

See `references/google-mymaps-kml-extraction.md` for full details.

### 2. French Municipal Sites

City websites (e.g. `lehavre.fr`) often have structured activity pages for
pet owners, listing caniparcs, recommended walking areas, clubs, and
organized activities. These are authoritative and kept up to date.

- Look for paths like `/services-au-quotidien/cadre-de-vie/animal-en-ville/`
- Content is usually in collapsible accordion sections — use `browser_click`
  to expand each section and `browser_snapshot` to read.
- Official municipal data is more reliable than commercial directories.

### 3. AllTrails and TripAdvisor

For outdoor activities (hiking, walking trails with dogs), AllTrails has
filtered lists (e.g. "dogs on leash" trails near a city). TripAdvisor has
user reviews of parks that mention dog-friendliness.

## Fallback Search Strategy

When the primary search tools fail, use this escalation ladder:

1. **web_search** — try first. If it returns "Payment Required" (Firecrawl
   credits exhausted), move to step 2.
2. **browser_navigate** to Google search — works but may render in Finnish
   if the server is in Finland. Results are still parseable from the
   accessibility tree snapshot.
3. **curl + DuckDuckGo HTML** — `https://html.duckduckgo.com/html/?q=<query>`
   with proper User-Agent and Referer headers. May rate-limit after 2-3
   queries from the same IP.
4. **curl + Bing RSS** — `https://www.bing.com/search?format=rss&q=<query>`
   — sometimes ignores the actual query and returns generic results. Test
   before trusting.
5. **Direct URL access** — if you know the franchise site, curl the
   locations page directly and parse the HTML.

### Search query patterns for French local services

```
"<service type>" "<city>" libre service self service
"<brand>" OR "<chain>" "<city>" OR "<region>"
station lavage chien libre service <city> <region>
```

## Multi-Network Enumeration

When searching for a service type (e.g. dog wash stations), there are
usually **multiple competing franchise networks** in the same market.
Finding the first one is not enough — you must enumerate ALL networks
and check each one's coverage area before presenting results.

**Workflow**:

1. Find the first network via Google search (e.g. `dogwash.fr`)
2. Extract its locations via KML (technique above)
3. Search specifically for competing networks:
   `"<service type>" OR "<brand1>" OR "<brand2>" machine station libre service`
4. For each competitor found, check their "locations" or "emplacements" page
5. Verify actual geographic coverage — some networks are single-country or
   single-region despite having a multi-language website

**Real example (dog wash stations in France)**:
- **Dogwash.fr** — 130+ stations in France, KML available ✅
- **Wash Dog BOX** (washdogmachines.com) — multi-language site but ALL
  stations are in Poland only ❌
- **LaveTonDog** (lavetondog.com) — single location in Argelès-sur-Mer ❌
- **Independent stations** — salons with outdoor machines (e.g.
  Artist'ochien Villers-Bocage, Le Coin Canin Évreux) — found via local
  news articles and Facebook posts, NOT on any franchise map

**Key lesson**: Independent/non-franchised stations are often only
discoverable via local news articles (Ouest-France, BFMTV) and Facebook
municipal pages. Search for `"<service> <city>" site:ouest-france.fr` and
check Facebook pages of local supermarkets (Leclerc, Super U, Intermarché)
which sometimes host franchise stations.

## Local Regulation Research

When the user asks about local regulations (e.g. dog rules on beaches,
parks, city streets), use this approach:

### Sources (most to least authoritative)

1. **Municipal websites** — `ville-<city>.fr` often has a
   "tranquillité publique" or "animal en ville" section with the full
   arrêté municipal. Look for paths like:
   - `/ma-ville/tranquillite-publique-2/chiens-de-1re-et-2e-categories/`
   - `/services-au-quotidien/cadre-de-vie/animal-en-ville/`

2. **Regional tourism offices** — publish PDF brochures summarizing rules
   across multiple communes. Example:
   `lehavre-etretat-tourisme.com/uploads/2024/07/Plages-autorisees-aux-chiens-saison-2024.pdf`
   These PDFs are parseable via `browser_navigate` (built-in PDF viewer
   renders text in the accessibility tree).

3. **Specialist blogs** — sites like `canitourismenormandie.com` call
   every mairie individually and publish verified regulations with links
   to the actual arrêtés municipaux. More complete than any single
   municipal site.

4. **Facebook municipal pages** — cities announce new facilities (e.g.
   dog beaches, caniparcs) on Facebook before updating their website.

### Pattern

```
# For each commune of interest:
1. Check ville-<city>.fr for the arrêté
2. Check the regional tourism office for a summary PDF
3. Cross-reference with specialist blogs
4. For beaches: search "<city> plage chien interdit autorisé"
```

## Pitfalls

- **DDG rate-limiting**: DuckDuckGo HTML search blocks after 2-3 rapid
  queries. Space out requests or use browser instead.
- **Bing language**: Bing may return results in Finnish/Estonian when the
  server is in Finland. The search results are still there but the UI
  language differs. Use `browser_navigate` to Google instead.
- **Bing RSS ignoring queries**: `bing.com/search?format=rss&q=<query>`
  sometimes ignores the actual query and returns generic trending results.
  Do NOT trust Bing RSS for targeted searches — use browser Google instead.
- **KML ExtendedData fields**: The `lat`/`lng` fields in ExtendedData may
  be empty strings. Always handle with `float(x or '0')`.
- **Maps skill is bundled**: The `maps` skill (OSM/Overpass) cannot be
  extended with custom POI categories. This skill complements it for
  niche categories not in OSM.
- **Franchise data freshness**: KML data may lag behind reality. Always
  note the export date if available and recommend calling to confirm.
- **Competitor coverage illusion**: A franchise website with a `.com/fr/`
  French section does NOT mean they have stations in France. Always
  check the actual locations table/list, not just the marketing page.
- **Presenting partial results**: When the user asks for services "around
  <city>", search ALL networks and independent stations before presenting.
  Presenting only the first network found is incomplete — the user may
  know of a closer station from a competitor you didn't check.

## Verification

After extracting locations, verify at least the nearest result by:
1. Searching for the business name + city on Google via browser
2. Checking if the address still exists on Google Maps
3. Noting the data source date for the user

## See Also

- `maps` skill — for standard POI searches (restaurants, pharmacies, etc.)
  via OpenStreetMap/Overpass API
- `references/google-mymaps-kml-extraction.md` — detailed KML parsing
  reference with the Dogwash.fr real example
- `references/dog-wash-stations-normandy.md` — complete 2026 dataset of
  dog wash stations in Normandy + beach regulations for Étretat, Deauville,
  Fécamp, and Côte Fleurie communes