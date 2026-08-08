import json, re

with open('/tmp/seloger1_snap.json') as f:
    d = json.load(f)
snap = d.get('snapshot', '')

# Parse link titles which contain all the info: "Appartement à louer - Le Havre - XXX € - N pièces, N chambre, XX m², ..."
lines = snap.split('\n')
listings = []
for line in lines:
    if 'link "Appartement' in line and 'à louer' in line:
        # Extract title
        title_m = re.search(r'link "([^"]+)"', line)
        title = title_m.group(1) if title_m else ''
        
        # Extract URL
        url_m = re.search(r'/url: (https://[^\s]+)', line)
        url = url_m.group(1).rstrip('\\') if url_m else 'NONE'
        
        # Parse title for price, rooms, surface
        price_m = re.search(r'(\d[\d\s]*)\s*\u20ac', title)
        rooms_m = re.search(r'(\d+)\s*pi\u00e8ce', title)
        surf_m = re.search(r'(\d+[,\d]*)\s*m\u00b2', title)
        chambre_m = re.search(r'(\d+)\s*chambre', title)
        
        price = int(price_m.group(1).replace(' ', '')) if price_m else 0
        rooms = int(rooms_m.group(1)) if rooms_m else 0
        surface_str = surf_m.group(1).replace(',', '.') if surf_m else '0'
        surface = float(surface_str) if surface_str else 0
        chambres = int(chambre_m.group(1)) if chambre_m else 0
        
        # Extract listing ID
        id_m = re.search(r'/(\d+)\.htm', url)
        lid = f"seloger-{id_m.group(1)}" if id_m else ''
        # Also check for alphanumeric IDs
        if not lid:
            id_m2 = re.search(r'/([A-Z0-9]+)\?', url)
            if id_m2:
                lid = f"seloger-{id_m2.group(1)}"
        
        listings.append({
            'id': lid,
            'title': title,
            'url': url,
            'price': price,
            'rooms': rooms,
            'surface': surface,
            'chambres': chambres
        })

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# Filter: T2+, <=500€, >=28m²
for l in listings:
    is_new = l['id'] not in seen_ids
    qualifies = l['price'] <= 500 and l['rooms'] >= 2 and l['surface'] >= 28
    if qualifies:
        print(f"{'*** NEW ***' if is_new else 'SEEN'} {l['id']}: {l['price']}€ | {l['rooms']}p | {l['surface']}m² | {l['title'][:100]}")
        print(f"  URL: {l['url'][:120]}")
        print()