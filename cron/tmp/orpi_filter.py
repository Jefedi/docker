import re, json, html

# Orpi JSON-LD has price but not surface/pieces. The type (T1/T2/T3) is in the URL.
# We need to visit individual listings for surface + description (cuisine séparée, chambre fermée).
# But first, let's filter: T2+ and price <= 500

all_orpi = []
for fname, label in [('/tmp/src_a559eead.html', 'p1'), ('/tmp/orpi2.html', 'p2')]:
    s = open(fname).read()
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.DOTALL)
    if not ld: continue
    try:
        data = json.loads(ld.group(1))
    except: continue
    for item in data.get('itemListElement', []):
        url = item.get('url', '')
        price = item.get('item', {}).get('offers', {}).get('price', 0)
        # Type from URL
        type_m = re.search(r'appartement-(t\d)-', url)
        prop_type = type_m.group(1) if type_m else ''
        # ID from URL
        id_m = re.search(r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
        if not id_m:
            id_m = re.search(r'-(\d+-\d+)', url)
        listing_id = id_m.group(1) if id_m else ''
        all_orpi.append({'url': url, 'price': price, 'type': prop_type, 'id': listing_id, 'page': label})

# Filter T2+ and <=500€
cands = [l for l in all_orpi if l['type'] in ['t2','t3','t4','t5'] and l['price'] <= 500]
print(f"Orpi total: {len(all_orpi)}, T2+ <=500€: {len(cands)}")
for c in cands:
    print(f"  {c['type']} | {c['price']}€ | id={c['id']} | {c['url']}")

# Now read seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# Check which are new
new_orpi = []
for c in cands:
    seen_id = f"orpi-{c['id']}"
    if seen_id not in seen:
        new_orpi.append(c)
        print(f"  NEW: {seen_id}")
    else:
        print(f"  SEEN: {seen_id}")