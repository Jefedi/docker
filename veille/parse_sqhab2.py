import re, html as h
import json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

all_sqhab = []
for fname in ['/tmp/veille/sqhab.html', '/tmp/veille/sqhab2.html']:
    html = open(fname).read()
    
    # Find all "name": "Appartement à louer - LE HAVRE, X pièces" or "Studio à louer - LE HAVRE"
    for m in re.finditer(r'"name":\s*"((?:Appartement|Studio)\s+à\s+louer\s+-\s+LE\s+HAVRE(?:,\s+(\d+)\s+pièces)?)"', html):
        name = m.group(1)
        prop_type = 'Studio' if 'Studio' in name else 'Appartement'
        rooms = int(m.group(2)) if m.group(2) else (0 if prop_type == 'Studio' else None)
        
        # Find UUID nearby (search within 5000 chars after)
        chunk = html[m.end():m.end()+5000]
        uuid_m = re.search(r'/le-havre/([a-f0-9-]{36})', chunk)
        uid = uuid_m.group(1) if uuid_m else ''
        
        if not uid:
            continue
        
        lid = f'sqhab-{uid}'
        url = f'https://www.squarehabitat.fr/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/{uid}'
        
        # Find price - look for "price" : "XXX" in JSON-LD
        price_chunk = html[m.start():m.start()+5000]
        price_m = re.search(r'"price":\s*"(\d+)"', price_chunk)
        price = int(price_m.group(1)) if price_m else None
        
        # Also look for "priceCurrency"
        
        # Find surface
        surf_m = re.search(r'(\d+)[,.]?\d*\s*m[²2]\b', price_chunk)
        surface = int(float(surf_m.group(1).replace(',','.'))) if surf_m else None
        
        # Find postal code
        cp_m = re.search(r'"postalCode":\s*"(\d+)"', price_chunk)
        cp = cp_m.group(1) if cp_m else ''
        
        already_seen = lid in seen_ids
        
        all_sqhab.append({
            'id': lid,
            'name': name,
            'rooms': rooms,
            'price': price,
            'surface': surface,
            'cp': cp,
            'url': url,
            'seen': already_seen
        })

# Deduplicate
seen_local = set()
unique = []
for s in all_sqhab:
    if s['id'] not in seen_local:
        seen_local.add(s['id'])
        unique.append(s)

print(f'SquareHabitat total unique: {len(unique)}')
for s in unique:
    status = 'SEEN' if s['seen'] else 'NEW'
    print(f'{status}: {s["id"]} | name={s["name"]} | rooms={s["rooms"]} | price={s["price"]} | surface={s["surface"]} | cp={s["cp"]}')