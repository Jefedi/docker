import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

content = open('/tmp/c21_p2.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find listings
refs = re.findall(r'Ref\s*:\s*(\w+)\s+(.{0,300})', text)
for ref, ctx in refs[:20]:
    # Find price in context
    price_match = re.search(r'(\d{3,4})\s*€\s*par\s*mois', ctx)
    if price_match:
        price = int(price_match.group(1))
        # Find surface
        surface_match = re.search(r'(\d+(?:,\d+)?)\s*m\s*2', ctx)
        surface = float(surface_match.group(1).replace(',', '.')) if surface_match else None
        # Find pieces
        pieces_match = re.search(r'(\d)\s*pièces?', ctx)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        
        c21_id = f"c21-{ref}"
        is_new = c21_id not in seen_ids
        
        if pieces and pieces >= 2 and surface and surface >= 28 and price <= 500:
            status = "NEW" if is_new else "SEEN"
            print(f"  [{status}] {c21_id} | T{pieces} {surface}m² {price}€/mois")
            print(f"  Desc: {ctx[:200]}")
            print()

# Also search for all Refs
print("\n=== All Century21 p2 refs ===")
all_refs = re.findall(r'Ref\s*:\s*(\w+)', text)
print(f"Refs: {all_refs}")

# Also check for more pages
page_refs = re.findall(r'page=(\d+)', text)
print(f"Page refs: {set(page_refs)}")