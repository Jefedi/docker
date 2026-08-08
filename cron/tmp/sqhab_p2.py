import re, json, html

# Parse SquareHabitat page 2
s = open('/tmp/sqhab2.html').read()
ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.DOTALL)
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

print("=== SquareHabitat page 2 ===")
for b in ld_blocks:
    try:
        data = json.loads(b)
        if data.get('@type') == 'ItemList' and 'itemListElement' in data:
            print(f"Items: {len(data['itemListElement'])}")
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
                    print(f"  {status}: {seen_id} | {pieces}p | {price}€ | {name}")
    except:
        pass