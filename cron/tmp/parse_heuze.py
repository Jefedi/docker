import json, re

with open('/tmp/heuze_snap3.json') as f:
    d = json.load(f)
snap = d.get('snapshot','')

# Extract HEUZE listings - same pattern as Saint Roch
listings = []
url_pattern = r'/url: (/location/[^\n,]+,(LA\d+))'
matches = re.findall(url_pattern, snap)
for url_path, la_id in matches:
    idx = snap.find(url_path)
    if idx == -1:
        continue
    context = snap[max(0, idx-500):idx+500]
    price_m = re.search(r'(\d+)\s*€\s*/mois', context)
    pieces_m = re.search(r'(\d+)\s*pi[èc]ces?', context)
    surface_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', context)
    
    price = int(price_m.group(1)) if price_m else None
    pieces = int(pieces_m.group(1)) if pieces_m else None
    surface = None
    if surface_m:
        try:
            surface = int(float(surface_m.group(1).replace(',', '.')))
        except:
            pass
    
    listings.append({
        'pieces': pieces, 'price': price, 'surface': surface,
        'url': f"https://www.heuze-immo.fr{url_path}",
        'id': la_id, 'source': 'heuze'
    })

print(f"HEUZE: {len(listings)} listings")
filtered = [l for l in listings if l.get('price') and l['price'] <= 500 and l.get('surface',0) >= 28 and l.get('pieces',0) >= 2]
print(f"Filtered: {len(filtered)}")
for l in filtered:
    print(json.dumps(l, ensure_ascii=False))

print("\nAll:")
for l in listings:
    print(f"  id={l.get('id','?')} {l.get('price','?')}€ {l.get('pieces','?')}p {l.get('surface','?')}m²")