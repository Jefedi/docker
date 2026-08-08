import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/sqhab.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
s = scripts[6]
data = json.loads(s.strip())
items = data.get('itemListElement', [])
print(f"SquareHabitat items: {len(items)}")

# Also find listing URLs from the HTML page
page = htmllib.unescape(raw)
# Look for links to individual listings
url_links = re.findall(r'href="(/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/[^"?]+)"', page)
print(f"URL links: {len(url_links)}")
for u in url_links[:20]:
    print(f"  {u}")

# Also look for UUID patterns in the page
uuids_in_page = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', page)
print(f"\nUUIDs in page: {len(set(uuids_in_page))}")
for u in list(set(uuids_in_page))[:20]:
    print(f"  {u}")

# Parse items
for item in items:
    pos = item.get('position')
    p = item.get('item', {})
    name = p.get('name', '')
    price = p.get('offers', {}).get('price', 0)
    images = p.get('image', [])
    # Get UUID from image URL
    img_uuid = ''
    if images:
        m = re.search(r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', images[0])
        if m: img_uuid = m.group(1)
    print(f"\n  #{pos}: {name} | {price}€ | img_uuid={img_uuid}")