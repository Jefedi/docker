import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/orpi.html').read()
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
data = json.loads(scripts[0].strip())
items = data['itemListElement']

# Get all listing URLs (with UUID) in order
listing_links = re.findall(r'href="(/annonce-location-appartement-[^"]+)"', raw)
print(f"Listing links: {len(listing_links)}")
for l in listing_links:
    print(f"  {l}")

# Extract UUID from each link
link_uuids = []
for l in listing_links:
    m = re.search(r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', l)
    if m:
        link_uuids.append(m.group(1))

# Extract UUID from each JSON-LD item's image URL
item_uuids = []
for item in items:
    p = item.get('item', item)
    img = p.get('image', '')
    if isinstance(img, list) and img:
        img = img[0]
    m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})--', img)
    if m:
        item_uuids.append(m.group(1))
    else:
        item_uuids.append('')

print(f"\nItem UUIDs: {item_uuids}")
print(f"Link UUIDs: {link_uuids}")

# Match by UUID
listings = []
for i, item in enumerate(items):
    p = item.get('item', item)
    price = p.get('offers', {}).get('price', 0)
    item_uid = item_uuids[i] if i < len(item_uuids) else ''
    
    # Find matching link
    url = ''
    uid = ''
    for j, luid in enumerate(link_uuids):
        if luid == item_uid:
            url = 'https://www.orpi.com' + listing_links[j]
            uid = luid
            break
    
    # Also extract pieces from URL
    pm = re.search(r'appartement-(t\d)', url.lower())
    pieces_str = pm.group(1) if pm else ''
    pieces = 0
    if pieces_str:
        pieces = int(pieces_str[1])
    
    listings.append({
        'source': 'orpi',
        'id': f"orpi-{uid}" if uid else f"orpi-{i}",
        'url': url,
        'pieces': pieces,
        'price': price,
        'surface': 0,
        'uid': uid,
    })

print(f"\nOrpi listings: {len(listings)}")
for l in listings:
    print(f"  {l['id']} | {l['pieces']}p | {l['price']}€ | {l['url']}")

# Filter T2+ ≤500€
matches = [l for l in listings if l['pieces'] >= 2 and 0 < l['price'] <= 500]
print(f"\nT2+ ≤500€: {len(matches)}")
for m in matches:
    print(f"  {m['id']} | {m['pieces']}p | {m['price']}€ | {m['url']}")

with open('/opt/data/tmp/veille/orpi_listings.json', 'w') as f:
    json.dump(listings, f, indent=2)