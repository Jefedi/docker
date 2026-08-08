import json, re

with open('/tmp/seloger1_snap.json') as f:
    d = json.load(f)
snap = d.get('snapshot', '')

# Find all links to listings
links = re.findall(r'link "([^"]+)":\s*\n\s*- /url: (https://www\.seloger\.com/annonces/locations/[^\s]+)', snap)

# Also find price and surface info near each link
lines = snap.split('\n')
listings = []
for i, line in enumerate(lines):
    if 'annonces/locations/' in line and 'link' in line:
        m = re.search(r'/url: (https://[^\s]+)', line)
        url = m.group(1) if m else 'NONE'
        title_m = re.search(r'link "([^"]+)"', line)
        title = title_m.group(1) if title_m else ''
        
        # Look in surrounding lines for price and surface
        context = ' '.join(lines[max(0,i-2):i+10])
        price_m = re.search(r'(\d[\d\s]*)\s*€\s*/mois', context)
        surface_m = re.search(r'(\d+[,\d]*)\s*m²', context)
        rooms_m = re.search(r'(\d+)\s*pièce', context)
        
        price = price_m.group(1).strip() if price_m else '?'
        surface = surface_m.group(1) if surface_m else '?'
        rooms = rooms_m.group(1) if rooms_m else '?'
        
        listings.append({
            'title': title[:200],
            'url': url,
            'price': price,
            'surface': surface,
            'rooms': rooms
        })

# Deduplicate by URL
seen_urls = set()
unique = []
for l in listings:
    if l['url'] not in seen_urls:
        seen_urls.add(l['url'])
        unique.append(l)

for l in unique:
    # Extract listing ID from URL
    id_m = re.search(r'/(\d+)\.htm', l['url'])
    seloger_id = f"seloger-{id_m.group(1)}" if id_m else 'seloger-?'
    print(f"ID: {seloger_id}")
    print(f"  Title: {l['title']}")
    print(f"  Price: {l['price']} | Rooms: {l['rooms']} | Surface: {l['surface']}m²")
    print(f"  URL: {l['url'][:100]}")
    print()