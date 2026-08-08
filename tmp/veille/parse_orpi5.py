import re, html as htmllib, json

# Parse Orpi - simpler approach: dedupe links, match by position with JSON-LD
raw = open('/opt/data/tmp/veille/orpi.html').read()
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
data = json.loads(scripts[0].strip())
items = data['itemListElement']
prices = [item.get('item', {}).get('offers', {}).get('price', 0) for item in items]

# Get unique listing links (remove ?contact=true duplicates)
all_links = re.findall(r'href="(/annonce-location-appartement-t\d-le-havre-76600-[^"]+)"', raw)
seen = set()
unique_links = []
for l in all_links:
    clean = l.split('?')[0]
    if clean not in seen:
        seen.add(clean)
        unique_links.append(clean)

print(f"Unique Le Havre links: {len(unique_links)}")
print(f"JSON-LD items: {len(items)}")

listings = []
for i, link in enumerate(unique_links):
    # Extract type from URL
    tm = re.search(r'appartement-(t\d)-le-havre', link)
    pieces = int(tm.group(1)[1]) if tm else 0
    
    # Extract ID from URL
    id_m = re.search(r'le-havre-76600-([0-9a-f-]+)', link)
    uid = id_m.group(1) if id_m else ''
    
    # Match price by position
    price = prices[i] if i < len(prices) else 0
    
    url = 'https://www.orpi.com' + link
    
    listings.append({
        'source': 'orpi',
        'id': f"orpi-{uid}",
        'url': url,
        'pieces': pieces,
        'price': price,
        'surface': 0,
    })

print(f"\nOrpi listings (Le Havre only): {len(listings)}")
for l in listings:
    flag = " ***" if (l['pieces'] >= 2 and 0 < l['price'] <= 500) else ""
    print(f"  {l['id']} | T{l['pieces']} | {l['price']}€{flag}")

matches = [l for l in listings if l['pieces'] >= 2 and 0 < l['price'] <= 500]
print(f"\nT2+ ≤500€: {len(matches)}")
for m in matches:
    print(f"  {m['id']} | T{m['pieces']} | {m['price']}€ | {m['url']}")

with open('/opt/data/tmp/veille/orpi_listings.json', 'w') as f:
    json.dump(matches, f, indent=2)