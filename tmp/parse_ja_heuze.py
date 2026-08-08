#!/usr/bin/env python3
"""Parse JA listings page for F2+ listings with prices and details."""
import re, html as h, json

raw = open('/tmp/scrape/ja_listings.html','r',errors='replace').read()

# Find all listing blocks - JA uses article or div elements for each listing
# Let's find all listing URLs with their surrounding text
listing_urls = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/a-louer-[^"]+)"', raw)
unique_urls = []
for u in listing_urls:
    if u not in unique_urls:
        unique_urls.append(u)

# For each listing URL, find the surrounding text for price/surface info
# JA listings have titles in the URL slug itself
f2_plus = []
for url in unique_urls:
    slug = url.split('/a-louer-')[-1].replace('.html', '')
    # Check if it's F2+ (not F1, not garage, not local commercial, not chambre)
    if ('f1' in slug and 'f1-' in slug) or 'garage' in slug or 'parking' in slug or 'local-commercial' in slug or 'local-professionnel' in slug or 'chambre' in slug:
        continue
    # Check for F2, F3, F4, F5, F6
    if re.search(r'f[2-6]|type-f[2-6]', slug, re.I):
        # Find the listing in the HTML to get price
        pos = raw.find(url)
        if pos >= 0:
            chunk = raw[pos:pos+5000]
            text = re.sub(r'<[^>]+>', ' ', chunk)
            text = h.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            # Find price
            price_match = re.search(r'(\d[\d\s\xa0]*)\s*€\s*(?:/mois|/ mois|mois)', text)
            price = 0
            if price_match:
                price_str = re.sub(r'[\s\xa0]', '', price_match.group(1))
                try:
                    price = int(price_str)
                except:
                    pass
            # Find surface
            surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text)
            surface = 0
            if surface_match:
                try:
                    surface = int(float(surface_match.group(1).replace(',', '.')))
                except:
                    pass
            
            f2_plus.append({
                'url': url,
                'slug': slug,
                'price': price,
                'surface': surface,
                'text': text[:400],
            })

print(f"=== F2+ listings from Jullien & Allix: {len(f2_plus)} ===")
for l in f2_plus:
    print(f"\n  Price: {l['price']}€ Surface: {l['surface']}m²")
    print(f"  URL: {l['url']}")
    print(f"  Text: {l['text'][:200]}")

# Also check HEUZE and SAINT ROCH more carefully - they seem to use JS to render
# Let's look for data in script tags or JSON
print("\n\n=== HEUZE - looking for data in JSON/script ===")
raw_heuze = open('/tmp/scrape/heuze_listings.html','r',errors='replace').read()
# Find JSON data blocks
json_blocks = re.findall(r'(?:listings|biens|annonces|properties)\s*[:=]\s*(\[.*?\])', raw_heuze, re.S)
print(f"JSON blocks found: {len(json_blocks)}")
# Also look for listing URLs in the Heuze format
heuze_listing_links = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', raw_heuze)
print(f"Heuze listing links: {len(heuze_listing_links)}")
# Try broader pattern
heuze_all_links = re.findall(r'href="([^"]*location[^"]*appartement[^"]*)"', raw_heuze, re.I)
unique_heuze = list(set(heuze_all_links))
for l in unique_heuze[:20]:
    if len(l) > 20:
        print(f"  {l}")

print("\n\n=== SAINT ROCH - looking for data ===")
raw_stroch = open('/tmp/scrape/stroch_listings.html','r',errors='replace').read()
stroch_links = re.findall(r'href="(/location/appartement/[^"]+)"', raw_stroch, re.I)
unique_stroch = list(set(stroch_links))
print(f"Saint Roch listing links: {len(unique_stroch)}")
for l in unique_stroch[:20]:
    if len(l) > 20:
        print(f"  https://www.saintrochimmo.com{l}")