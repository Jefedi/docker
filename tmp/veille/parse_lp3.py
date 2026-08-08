import re, json, glob, os

BASE = "https://www.le-partenaire.fr"
listings = []
seen_ids = set()

for f in sorted(set(glob.glob('/opt/data/tmp/veille/lp_p*.html') + ['/opt/data/tmp/veille/lp.html'])):
    if not os.path.exists(f): continue
    html = open(f).read()
    
    # Split into cards by "item-annonce" class
    cards = re.split(r'class="card w-100 mb-5 item-annonce"', html)
    
    for card in cards[1:]:  # skip first (before first card)
        # h2
        h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
        if not h2_m: continue
        h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_m.group(1))).strip()
        # h2_text like "Location Appartement à Le Havre 2 pièces | 40 m²"
        
        pm = re.search(r'(\d+)\s*pièces?', h2_text)
        sm = re.search(r'(\d+)\s*m²', h2_text)
        pieces = int(pm.group(1)) if pm else 0
        surface = int(sm.group(1)) if sm else 0
        
        # link
        link_m = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', card)
        if not link_m: continue
        link = link_m.group(1)
        id_m = re.search(r'/(\d+)(?:\?|$|"|/)', link)
        if not id_m: continue
        listing_id = id_m.group(1)
        
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        # price
        price_m = re.search(r'<span class="prix">([\d\s&nbsp;.]+)€</span>', card)
        if not price_m:
            price_m = re.search(r'class="prix[^"]*">([\d\s&nbsp;.]+)\s*€', card)
        price = 0
        if price_m:
            ps = price_m.group(1).replace('&nbsp;', '').replace(' ', '').replace('.', '').replace('\xa0', '')
            try: price = int(ps)
            except: pass
        
        # description
        desc_m = re.search(r'<p class="card-text[^"]*"[^>]*>(.*?)</p>', card, re.DOTALL)
        desc = ""
        if desc_m:
            desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', desc_m.group(1))).strip()
        
        # DPE
        dpe_m = re.search(r'DPE\s+([A-G])', desc)
        dpe = dpe_m.group(1) if dpe_m else ''
        
        # charges
        charges_m = re.search(r'charges?\s*(?:comprises|:)?\s*(?:de\s+)?(\d+)', desc, re.IGNORECASE)
        charges = int(charges_m.group(1)) if charges_m else 0
        
        # meublé?
        meuble = 'meubl' in desc.lower()
        
        full_url = BASE + link
        
        # Filter: T2+ (pieces >= 2), surface >= 28, price <= 500
        if pieces < 2: continue
        if surface < 28: continue
        if price > 500 or price == 0: continue
        
        listings.append({
            'source': 'lp',
            'id': f"lp-{listing_id}",
            'url': full_url,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'charges': charges,
            'dpe': dpe,
            'meuble': meuble,
            'desc': desc[:800],
            'h2': h2_text,
        })

print(f"Le-Partenaire: {len(listings)} listings match T2+/28m²+/≤500€")
for l in listings:
    print(f"\n{'='*60}")
    print(f"{l['id']} | T{l['pieces']} {l['surface']}m² | {l['price']}€/mois | DPE={l['dpe']} | meublé={l['meuble']}")
    print(f"  URL: {l['url']}")
    print(f"  desc: {l['desc'][:300]}")

with open('/opt/data/tmp/veille/lp_listings.json', 'w') as f:
    json.dump(listings, f, indent=2)