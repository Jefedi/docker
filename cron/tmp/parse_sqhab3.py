import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

content = open('/tmp/sqhab.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all listing links with UUIDs
links = re.findall(r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([0-9a-f-]{36}))"', content)
unique_links = list(dict.fromkeys(links))
print(f"SquareHabitat links: {len(unique_links)}")

# Parse all listings properly
# Pattern from text: "Au prix de (par mois) XXX € cc DESCRIPTION"
# But we need to match them to links by order

# Let's find all listing blocks in order
# Each listing seems to start with a pattern and end with the next one
# Let's try to extract: price, pieces, surface, address from each block

# Find all prices with "cc" 
prices = re.finditer(r'Au prix de\s*\(par mois\)\s*(\d+)\s*€\s*cc', text)
price_list = [(m.start(), m.end(), int(m.group(1))) for m in prices]

listings = []
for i, (start, end, price) in enumerate(price_list):
    # Get context after price
    after_end = price_list[i+1][0] if i+1 < len(price_list) else len(text)
    after_text = text[end:after_end]
    
    # Get context before price
    before_start = price_list[i-1][2] if i > 0 else 0
    before_text = text[max(0, start-500):start]
    
    # Extract pieces from before
    pieces_match = re.search(r'(\d)\s*pièces?', before_text)
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    
    # Extract surface from after
    surface_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', after_text)
    surface = float(surface_match.group(1).replace(',', '.')) if surface_match else None
    
    # Extract address from after
    addr_match = re.search(r'(?:SECTEUR|QUARTIER)\s+[""\']?([^"-]+?)(?:\s*-\s*\d+\s*RUE|\s*-\s*\d+\s+(?:RUE|AVENUE|BOULEVARD|IMPASSE|PLACE))', after_text)
    if not addr_match:
        addr_match = re.search(r'-\s*(\d+\s+RUE\s+[\w\s]+)', after_text)
    addr = addr_match.group(1).strip() if addr_match else ''
    
    # Get UUID from links - match by order
    uuid = unique_links[i][1] if i < len(unique_links) else None
    sqhab_id = f"sqhab-{uuid}" if uuid else None
    
    # Full description
    desc = after_text[:400]
    
    listings.append({
        'pieces': pieces,
        'surface': surface,
        'price': price,
        'addr': addr,
        'id': sqhab_id,
        'desc': desc,
        'link': f"https://www.squarehabitat.fr{unique_links[i][0]}" if i < len(unique_links) else None
    })

print(f"\nAll listings: {len(listings)}")
print(f"\nT2+ with surface >= 28 and price <= 500:")
for l in listings:
    if l['pieces'] >= 2 and l['surface'] and l['surface'] >= 28 and l['price'] <= 500:
        is_new = l['id'] not in seen_ids if l['id'] else True
        status = "NEW" if is_new else "SEEN"
        print(f"\n  [{status}] {l['id']}")
        print(f"  T{l['pieces']} {l['surface']}m² {l['price']}€/mois | {l['addr']}")
        print(f"  Link: {l['link']}")
        print(f"  Desc: {l['desc'][:300]}")