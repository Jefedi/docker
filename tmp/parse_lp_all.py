#!/usr/bin/env python3
"""Parse Le-Partenaire.fr all pages - extract T2+ listings with prices."""
import re, html as h, json

all_listings = []

for page in range(1, 6):
    fname = f'/tmp/scrape/lp{page}.html'
    try:
        raw = open(fname, 'r', errors='replace').read()
    except:
        continue
    
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', raw, re.S)
    links_raw = re.findall(r'href="(/immobilier/location/appartement/havre/76600/[^\"]+)"', raw)
    seen_links = []
    for l in links_raw:
        if l not in seen_links:
            seen_links.append(l)
    
    for i, (h2_text, link) in enumerate(zip(h2s, seen_links)):
        clean = re.sub(r'<[^>]+>', '', h2_text).strip()
        clean = h.unescape(clean)
        m = re.search(r'(\d+)\s*pi[èe]ce[s]?\s*\|\s*(\d+)\s*m', clean)
        rooms = int(m.group(1)) if m else 0
        surface = int(m.group(2)) if m else 0
        listing_id = link.split('/')[-1]
        
        # Extract price and description
        id_pos = raw.find(listing_id)
        price = 0
        description = ''
        if id_pos >= 0:
            chunk = raw[id_pos:id_pos+5000]
            price_match = re.search(r'<span class="prix">(\d[\d\s\xa0]*)\s*€</span>', chunk)
            if price_match:
                price_str = re.sub(r'[\s\xa0]', '', price_match.group(1))
                try:
                    price = int(price_str)
                except:
                    pass
            desc_match = re.search(r'<p class="card-text crop-text-4"[^>]*>(.*?)</p>', chunk, re.S)
            if desc_match:
                description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                description = h.unescape(description)
        
        all_listings.append({
            'source': 'lp',
            'page': page,
            'rooms': rooms,
            'surface': surface,
            'price': price,
            'id': f'lp-{listing_id}',
            'link': f'https://www.le-partenaire.fr{link}',
            'description': description[:600],
        })

# Filter: T2+ (2+ pièces), price <= 500, surface >= 28
print("=== T2+ listings with price <= 500, surface >= 28 ===")
matching = []
for l in all_listings:
    if l['rooms'] >= 2 and l['price'] > 0 and l['price'] <= 500 and l['surface'] >= 28:
        matching.append(l)
        print(json.dumps(l, ensure_ascii=False))

print(f"\n=== Total T2+ matching: {len(matching)} ===")

print("\n=== T2+ with price > 500 (for reference) ===")
for l in all_listings:
    if l['rooms'] >= 2 and l['price'] > 500:
        print(f"  {l['id']}: {l['price']}€ {l['surface']}m² {l['rooms']}p")

print("\n=== T2+ with price 0 (price not extracted) ===")
for l in all_listings:
    if l['rooms'] >= 2 and l['price'] == 0:
        print(f"  {l['id']}: {l['surface']}m² {l['rooms']}p - {l['description'][:100]}")