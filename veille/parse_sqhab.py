import re, html as h
import json

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Parse SquareHabitat: extract from JSON-LD blocks
all_sqhab = []
for fname in ['/tmp/veille/sqhab.html', '/tmp/veille/sqhab2.html']:
    html = open(fname).read()
    
    # Find all JSON-LD blocks
    ld_blocks = re.findall(r'"@type":\s*"Offer"\s*,\s*"name":\s*"([^"]+)"', html)
    
    # Alternative: find UUID and name in JSON-LD
    # Pattern: "name": "Appartement à louer - LE HAVRE, X pièces" followed by UUID
    blocks = re.finditer(r'"name":\s*"(Appartement|Studio)\s+à\s+louer\s+-\s+LE\s+HAVRE(?:,\s+(\d+)\s+pièces)?"', html)
    
    for b in blocks:
        name = b.group(0)
        prop_type = b.group(1)
        rooms = int(b.group(2)) if b.group(2) else (0 if prop_type == 'Studio' else None)
        
        # Find UUID nearby (within 2000 chars after)
        chunk = html[b.end():b.end()+3000]
        uuid_m = re.search(r'/le-havre/([a-f0-9-]{36})', chunk)
        uid = uuid_m.group(1) if uuid_m else ''
        
        if not uid:
            continue
        
        lid = f'sqhab-{uid}'
        url = f'https://www.squarehabitat.fr/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/{uid}'
        
        # Get context around the match
        ctx_start = max(0, b.start() - 1000)
        ctx_end = min(len(html), b.end() + 3000)
        ctx = html[ctx_start:ctx_end]
        ctx_text = re.sub(r'<[^>]+>', ' ', ctx)
        ctx_text = h.unescape(re.sub(r'\s+', ' ', ctx_text)).strip()
        
        # Find price
        price_m = re.search(r'(\d+)\s*€', ctx_text)
        price = int(price_m.group(1)) if price_m else None
        
        # Find surface
        surf_m = re.search(r'(\d+)[,.]?\d*\s*m[²2]', ctx_text)
        surface = int(float(surf_m.group(1).replace(',','.'))) if surf_m else None
        
        # Find postal code
        cp_m = re.search(r'"postalCode":\s*"(\d+)"', ctx)
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
            'seen': already_seen,
            'text': ctx_text[:500]
        })

# Deduplicate
seen_local = set()
unique = []
for s in all_sqhab:
    if s['id'] not in seen_local:
        seen_local.add(s['id'])
        unique.append(s)

print(f'SquareHabitat total unique: {len(unique)}')

# Filter T2+ with price <= 500
for s in unique:
    if s['rooms'] is not None and s['rooms'] >= 2:
        status = 'SEEN' if s['seen'] else 'NEW'
        print(f'{status}: {s["id"]} | rooms={s["rooms"]} | price={s["price"]} | surface={s["surface"]} | cp={s["cp"]}')
        print(f'  URL: {s["url"]}')
        print(f'  TEXT: {s["text"][:300]}')
        print()