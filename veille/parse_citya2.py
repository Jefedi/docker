import re, html as h
import json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Parse Citya all pages
all_citya = []
for fname in ['/tmp/veille/citya.html', '/tmp/veille/citya2.html', '/tmp/veille/citya3.html']:
    html = open(fname).read()
    cards = re.split(r'class="property-card', html)
    for c in cards[1:]:
        id_m = re.search(r'data-itemId="([^"]+)"', c)
        name_m = re.search(r'data-itemName="([^"]+)"', c)
        price_m = re.search(r'data-price="([^"]+)"', c)
        
        item_id = id_m.group(1) if id_m else ''
        name = name_m.group(1) if name_m else ''
        price = int(price_m.group(1)) if price_m else None
        
        rooms_m = re.search(r'(\d+)\s*pièce', name)
        rooms = int(rooms_m.group(1)) if rooms_m else None
        surface_m = re.search(r'([\d.]+)m', name)
        surface = int(float(surface_m.group(1))) if surface_m else None
        
        # Find link
        link_m = re.search(r'href="(https://www\.citya\.com/annonces/location/[^"]+)"', c)
        if not link_m:
            link_m = re.search(r'href="(/annonces/location/[^"]+)"', c)
        link = link_m.group(1) if link_m else ''
        if link and not link.startswith('http'):
            link = 'https://www.citya.com' + link
        
        # If no explicit link, construct from ID
        if not link and item_id:
            link = f'https://www.citya.com/annonces/location/appartement/le-havre-76351/{item_id}'
        
        lid = f'citya-{item_id}' if item_id else ''
        
        # Get text
        text = re.sub(r'<[^>]+>', ' ', c[:4000])
        text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
        
        all_citya.append({
            'id': lid,
            'name': name,
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': link,
            'text': text,
            'seen': lid in seen_ids
        })

# Deduplicate
seen_local = set()
unique = []
for l in all_citya:
    if l['id'] not in seen_local:
        seen_local.add(l['id'])
        unique.append(l)

print(f'Citya total unique: {len(unique)}')

# Filter T2+ <= 500€ >= 28m²
candidates = []
for l in unique:
    if not l['rooms'] or l['rooms'] < 2:
        continue
    if not l['surface'] or l['surface'] < 28:
        continue
    if not l['price'] or l['price'] > 500:
        continue
    
    l['status'] = 'SEEN' if l['seen'] else 'NEW'
    candidates.append(l)

print(f'\nCandidates (T2+, <=500€, >=28m²): {len(candidates)}')
new = [c for c in candidates if c['status'] == 'NEW']
seen = [c for c in candidates if c['status'] == 'SEEN']
print(f'  NEW: {len(new)}')
print(f'  SEEN: {len(seen)}')

for c in new:
    print(f'\nNEW: {c["id"]} | {c["name"]} | {c["price"]}€ | {c["surface"]}m² | {c["rooms"]}p')
    print(f'  URL: {c["url"]}')
    print(f'  TEXT: {c["text"][:300]}')

for c in seen:
    print(f'SEEN: {c["id"]} | {c["name"]} | {c["price"]}€ | {c["surface"]}m²')