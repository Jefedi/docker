import re, json, glob, os

BASE = "https://www.le-partenaire.fr"
# Parse each page: match h2 (title) with price and link by DOM order
# The h2 and the link are in the same card. Let's try to extract card-by-card.

listings = []
seen_ids = set()

for f in sorted(glob.glob('/opt/data/tmp/veille/lp_p*.html')) + ['/opt/data/tmp/veille/lp.html']:
    if not os.path.exists(f): continue
    html = open(f).read()
    
    # Split into cards. Each card contains an h2 and a link to a listing.
    # Try to find blocks between consecutive h2 occurrences.
    # Better: find all <h2> positions and extract surrounding context.
    
    h2_iter = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL))
    
    for i, m in enumerate(h2_iter):
        h2_raw = m.group(1)
        h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_raw)).strip()
        # h2_text like "Location Appartement à Le Havre 2 pièces | 40 m²"
        
        # Extract pieces and surface
        pm = re.search(r'(\d+)\s*pièces?', h2_text)
        sm = re.search(r'(\d+)\s*m²', h2_text)
        pieces = int(pm.group(1)) if pm else 0
        surface = int(sm.group(1)) if sm else 0
        
        # Look for link near this h2 - search forward up to 2000 chars
        start = m.start()
        end = h2_iter[i+1].start() if i+1 < len(h2_iter) else min(len(html), start+5000)
        block = html[start:end]
        
        link_m = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', block)
        if not link_m:
            continue
        link = link_m.group(1)
        # Extract ID from URL
        id_m = re.search(r'/(\d+)(?:\?|$|"|/)', link)
        if not id_m:
            continue
        listing_id = id_m.group(1)
        
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        # Extract price from the block
        price_m = re.search(r'(\d[\d\s.]*\d)\s*€', block)
        price = 0
        if price_m:
            price_str = price_m.group(1).replace(' ', '').replace('.', '').replace('\xa0', '')
            try: price = int(price_str)
            except: pass
        
        # Extract charges - look for "charges" pattern
        charges_m = re.search(r'charges?[^0-9]*(\d+)', block, re.IGNORECASE)
        charges = int(charges_m.group(1)) if charges_m else 0
        
        # Extract DPE - look for energy class letter
        dpe_m = re.search(r'DPE\s*[:\-]?\s*([A-G])', block, re.IGNORECASE)
        dpe = dpe_m.group(1).upper() if dpe_m else ''
        
        # Extract description text from the block
        desc_text = re.sub(r'<[^>]+>', ' ', block)
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()[:500]
        
        # Filter: T2+ (pieces >= 2), surface >= 28, price <= 500
        if pieces < 2: continue
        if surface < 28: continue
        if price > 500 or price == 0: continue
        
        full_url = BASE + link
        listings.append({
            'source': 'lp',
            'id': f"lp-{listing_id}",
            'url': full_url,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'charges': charges,
            'dpe': dpe,
            'desc': desc_text,
            'h2': h2_text,
        })

print(f"Le-Partenaire: {len(listings)} listings match T2+/28m²+/≤500€")
for l in listings:
    print(f"\n{l['id']} | T{l['pieces']} {l['surface']}m² | {l['price']}€ | charges={l['charges']} | DPE={l['dpe']}")
    print(f"  URL: {l['url']}")
    print(f"  desc: {l['desc'][:200]}")

# Save for later
with open('/opt/data/tmp/veille/lp_listings.json', 'w') as f:
    json.dump(listings, f, indent=2)