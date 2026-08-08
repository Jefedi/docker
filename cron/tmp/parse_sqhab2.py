import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

content = open('/tmp/sqhab.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all listings: "APPARTEMENT TX ... - ADDRESS ... LE HAVRE" + "Au prix de (par mois) XXX € cc"
# Or: pattern "XX pièces" + price
# Let's try to find all listing blocks

# Pattern: "à louer - LE HAVRE, N pièces LE HAVRE (XXXXX) Au prix de (par mois) XXX € cc"
listings = re.findall(
    r'à louer\s*-\s*LE HAVRE,?\s*(\d)\s*pièces?\s+LE HAVRE\s*\((\d+)\)\s+Au prix de\s*\(par mois\)\s*(\d+)\s*€\s*cc\s+(.*?)(?=à louer|$)',
    text
)

# Also try: "APPARTEMENT TX - ADDRESS LE HAVRE" + "Au prix de (par mois) XXX € cc"
listings2 = re.findall(
    r'APPARTEMENT\s+T(\d)\s*-\s*(.+?)\s*-\s*LE HAVRE\s+LE HAVRE\s*\(\d+\)\s+Au prix de\s*\(par mois\)\s*(\d+)\s*€\s*cc\s+(.*?)(?=APPARTEMENT\s+T|à louer|$)',
    text
)

# Also: "Studio à louer" or "appartement à louer" with price
listings3 = re.findall(
    r'(Studio|APPARTEMENT\s+T\d|appartement\s+T\d)\s+à louer\s*-\s*LE HAVRE\s+LE HAVRE\s*\((\d+)\)\s+Au prix de\s*\(par mois\)\s*(\d+)\s*€\s*cc\s+(.*?)(?=Studio|APPARTEMENT|appartement|à louer|$)',
    text
)

print(f"Listings pattern 1: {len(listings)}")
print(f"Listings pattern 2: {len(listings2)}")
print(f"Listings pattern 3: {len(listings3)}")

# Let's try a broader approach
# Find all "Au prix de (par mois) XXX € cc" and look backward
all_listings = []
price_positions = [(m.start(), int(m.group(1))) for m in re.finditer(r'Au prix de\s*\(par mois\)\s*(\d+)\s*€\s*cc', text)]
print(f"\nPrice positions: {len(price_positions)}")

for pos, price in price_positions:
    before = text[max(0, pos-400):pos]
    after = text[pos:pos+500]
    
    # Extract pieces
    pieces_match = re.search(r'(\d)\s*pièces?', before)
    if not pieces_match:
        t_match = re.search(r'T(\d)\b', before)
        if t_match:
            pieces = int(t_match.group(1))
        else:
            pieces = 0
    else:
        pieces = int(pieces_match.group(1))
    
    # Extract surface
    surface_match = re.search(r'(\d+(?:,\d+)?)\s*m[²2]', before + after)
    surface = float(surface_match.group(1).replace(',', '.')) if surface_match else None
    
    # Extract address
    addr_match = re.search(r'-\s*(.+?)\s*-\s*LE HAVRE', before)
    addr = addr_match.group(1).strip() if addr_match else ''
    
    # Extract UUID from links
    uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', before + after)
    sqhab_id = f"sqhab-{uuid_match.group(1)}" if uuid_match else None
    
    all_listings.append({
        'pieces': pieces,
        'surface': surface,
        'price': price,
        'addr': addr,
        'id': sqhab_id,
        'desc': after[:300]
    })

# Filter
for l in all_listings:
    if l['pieces'] >= 2 and l['surface'] and l['surface'] >= 28 and l['price'] <= 500:
        is_new = l['id'] not in seen_ids if l['id'] else True
        status = "NEW" if is_new else "SEEN"
        print(f"\n  [{status}] {l['id']} | T{l['pieces']} {l['surface']}m² {l['price']}€ | {l['addr']}")
        print(f"  Desc: {l['desc'][:300]}")