import re, json, html

# SquareHabitat: Block 3 is the ItemList - extract all listings with UUID, price, name
s = open('/tmp/src_a8dd5e22.html').read()
ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.DOTALL)
for b in ld_blocks:
    try:
        data = json.loads(b)
        if data.get('@type') == 'ItemList' and 'itemListElement' in data:
            print(f"Found ItemList with {len(data['itemListElement'])} items")
            for item in data['itemListElement']:
                product = item.get('item', {})
                name = product.get('name', '')
                offers = product.get('offers', {})
                price = offers.get('price', 0)
                # Extract UUID from image URL
                images = product.get('image', [])
                if isinstance(images, list) and images:
                    uuid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', images[0])
                    uuid = uuid_m.group(1) if uuid_m else ''
                else:
                    uuid = ''
                # Pieces from name
                pm = re.search(r'(\d+)\s*pi[èc]', name)
                pieces = int(pm.group(1)) if pm else 0
                if 'studio' in name.lower():
                    pieces = 1
                print(f"  {pieces}p | {price}€ | uuid={uuid} | {name}")
    except Exception as e:
        pass

# Now filter
print("\n=== SquareHabitat candidates (T2+, <=500€) ===")
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

for b in ld_blocks:
    try:
        data = json.loads(b)
        if data.get('@type') == 'ItemList' and 'itemListElement' in data:
            for item in data['itemListElement']:
                product = item.get('item', {})
                name = product.get('name', '')
                offers = product.get('offers', {})
                price = offers.get('price', 0)
                images = product.get('image', [])
                if isinstance(images, list) and images:
                    uuid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', images[0])
                    uuid = uuid_m.group(1) if uuid_m else ''
                else:
                    uuid = ''
                pm = re.search(r'(\d+)\s*pi[èc]', name)
                pieces = int(pm.group(1)) if pm else 0
                if 'studio' in name.lower():
                    pieces = 1
                if pieces >= 2 and price <= 500:
                    seen_id = f"sqhab-{uuid}"
                    status = "NEW" if seen_id not in seen else "SEEN"
                    # Need to get surface - check if it's in the HTML near this UUID
                    idx = s.find(uuid)
                    surf = ''
                    if idx >= 0:
                        block = s[max(0,idx-500):idx+1500]
                        sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
                        if sm: surf = sm.group(1)
                    print(f"  {status}: {seen_id} | {pieces}p | {price}€ | {surf}m² | {name}")
    except:
        pass