import re, html as htmllib, json

# Parse SquareHabitat - match JSON-LD items with URL links by position
raw = open('/opt/data/tmp/veille/sqhab.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
s = scripts[6]
data = json.loads(s.strip())
items = data.get('itemListElement', [])

# Get URL links in order from the HTML
url_links = re.findall(r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/[0-9a-f-]+)"', raw)

# Get surfaces in order
surfaces = re.findall(r'(\d+[,.]?\d*)\s*m²', htmllib.unescape(raw))

# Also find pieces info from the JSON-LD names
listings = []
for i, item in enumerate(items):
    p = item.get('item', {})
    name = p.get('name', '')
    price = p.get('offers', {}).get('price', 0)
    
    # Extract pieces from name
    pm = re.search(r'(\d+)\s*pièces?', name)
    pieces = int(pm.group(1)) if pm else (0 if 'Studio' in name else 0)
    if 'Studio' in name:
        pieces = 1
    
    # Match URL by position
    url = ''
    if i < len(url_links):
        url = 'https://www.squarehabitat.fr' + url_links[i]
    
    # Extract UUID from URL
    uuid_m = re.search(r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
    uid = uuid_m.group(1) if uuid_m else ''
    
    print(f"  #{i+1}: {name} | {price}€ | pieces={pieces} | uid={uid}")
    listings.append({
        'source': 'sqhab',
        'id': f"sqhab-{uid}" if uid else f"sqhab-{i}",
        'url': url,
        'pieces': pieces,
        'price': price,
        'surface': 0,  # need to fetch individual pages
        'name': name,
    })

with open('/opt/data/tmp/veille/sqhab_listings.json', 'w') as f:
    json.dump(listings, f, indent=2)

print(f"\nSquareHabitat: {len(listings)} listings")
# Filter T2+ ≤500€
matches = [l for l in listings if l['pieces'] >= 2 and 0 < l['price'] <= 500]
print(f"T2+ ≤500€: {len(matches)}")
for m in matches:
    print(f"  {m['id']} | {m['name']} | {m['price']}€ | {m['url']}")