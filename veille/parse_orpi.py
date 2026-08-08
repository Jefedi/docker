import re, html as h
import json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Parse Orpi JSON-LD
all_orpi = []
for page in [1,2,3,4,5,6]:
    fname = f'/tmp/veille/orpi{"" if page==1 else page}.html'
    try:
        html = open(fname).read()
    except:
        continue
    
    # Find ItemList JSON-LD
    script_m = re.search(r'\{"@context":"https://[^}]*"itemListElement":\[(.*?)\]\}', html, re.DOTALL)
    if not script_m:
        # Try broader search
        script_m = re.search(r'"itemListElement":\[(.*?)\]\}', html, re.DOTALL)
    
    if script_m:
        items_str = script_m.group(1) if script_m else ''
        # Find all URLs
        urls = re.findall(r'"url":"(https://www\.orpi\.com/annonce-location[^"]+)"', items_str)
        for url in urls:
            # Extract ID from URL
            # URL pattern: /annonce-location-appartement-tX-le-havre-76600-XXXXX-XXXXXX-XXX/
            id_m = re.search(r'-(\d+-\d+-\d+)$', url.rstrip('/'))
            # Also try UUID pattern
            uuid_m = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url)
            
            if id_m:
                lid = f'orpi-{id_m.group(1)}'
            elif uuid_m:
                lid = f'orpi-{uuid_m.group(1)}'
            else:
                # Use URL slug
                slug = url.rstrip('/').split('/')[-1]
                lid = f'orpi-{slug}'
            
            all_orpi.append({'id': lid, 'url': url, 'seen': lid in seen_ids})
    
    # Also find "name": "Location Appartement" with prices
    # Find price patterns
    blocks = re.findall(r'"url":"(https://www\.orpi\.com/annonce-location[^"]+)".*?"name":"([^"]+)"', html, re.DOTALL)
    for url, name in blocks:
        # Find price near this block
        idx = html.find(url)
        chunk = html[idx:idx+5000]
        price_m = re.search(r'"price":\s*"(\d+)"', chunk)
        price = int(price_m.group(1)) if price_m else None
        
        # Find rooms from URL: "appartement-tX"
        rooms_m = re.search(r'appartement-t(\d)', url, re.I)
        rooms = int(rooms_m.group(1)) if rooms_m else None
        
        # Extract ID
        id_m = re.search(r'-(\d+-\d+-\d+)$', url.rstrip('/'))
        uuid_m = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url)
        
        if id_m:
            lid = f'orpi-{id_m.group(1)}'
        elif uuid_m:
            lid = f'orpi-{uuid_m.group(1)}'
        else:
            slug = url.rstrip('/').split('/')[-1]
            lid = f'orpi-{slug}'
        
        already_seen = lid in seen_ids
        
        # Update or add
        for o in all_orpi:
            if o['id'] == lid:
                o['name'] = name
                o['price'] = price
                o['rooms'] = rooms
                break
        else:
            all_orpi.append({'id': lid, 'url': url, 'name': name, 'price': price, 'rooms': rooms, 'seen': already_seen})

# Deduplicate
seen_local = set()
unique = []
for o in all_orpi:
    if o['id'] not in seen_local:
        seen_local.add(o['id'])
        unique.append(o)

print(f'Orpi total unique: {len(unique)}')
for o in unique:
    status = 'SEEN' if o.get('seen') else 'NEW'
    rooms = o.get('rooms', '?')
    price = o.get('price', '?')
    print(f'{status}: {o["id"]} | rooms={rooms} | price={price} | URL={o["url"]}')