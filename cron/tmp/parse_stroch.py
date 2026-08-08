import json, re

with open('/tmp/stroch_snap3.json') as f:
    d = json.load(f)
snap = d.get('snapshot','')

# Extract Saint Roch listings - parse the link text directly
listings = []
# Find all URL patterns with LA IDs
url_pattern = r'/url: (/location/[^\n,]+,(LA\d+))'
matches = re.findall(url_pattern, snap)
for url_path, la_id in matches:
    # Find price near this URL - look for PRICE €/mois CC
    idx = snap.find(url_path)
    if idx == -1:
        continue
    # Get surrounding text (500 chars before and after)
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
        'url': f"https://www.saintrochimmo.com{url_path}",
        'id': la_id, 'source': 'stroch'
    })

print(f"Saint Roch: {len(listings)} listings")
filtered = [l for l in listings if l.get('price',999) and l.get('price',999) <= 500 and l.get('surface',0) >= 28 and l.get('pieces',0) >= 2]
print(f"Filtered: {len(filtered)}")
for l in filtered:
    print(json.dumps(l, ensure_ascii=False))

print("\nAll:")
for l in listings:
    print(f"  id={l.get('id','?')} {l.get('price','?')}€ {l.get('pieces','?')}p {l.get('surface','?')}m²")