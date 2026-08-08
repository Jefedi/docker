import re, json

# ============= ORPI - extract proper JSON-LD with price mapping =============
print("=== ORPI (proper JSON-LD) ===")
with open('/tmp/havre/orpi.html') as f:
    html = f.read()

# Find JSON-LD script blocks
ld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.+?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")

for i, block in enumerate(ld_blocks):
    try:
        data = json.loads(block)
        if isinstance(data, dict):
            if '@graph' in data:
                for item in data['@graph']:
                    if item.get('@type') in ['Offer', 'RentOffer', 'Apartment']:
                        print(f"  Block {i}: {str(item)[:300]}")
            elif 'offers' in data:
                offers = data.get('offers', [])
                print(f"  Block {i}: {len(offers)} offers")
                for o in offers[:5]:
                    print(f"    {o}")
            elif data.get('@type') in ['Apartment', 'Residence', 'Offer']:
                print(f"  Block {i}: {str(data)[:300]}")
        elif isinstance(data, list):
            print(f"  Block {i}: list of {len(data)}")
            for item in data[:5]:
                print(f"    {str(item)[:300]}")
    except Exception as e:
        # Maybe partial JSON
        if len(block) > 100:
            # Try to extract individual offers
            offers = re.findall(r'\{"@type":"Offer"[^}]+\}', block)
            if offers:
                print(f"  Block {i}: {len(offers)} offers (regex)")
                for o in offers[:5]:
                    print(f"    {o[:200]}")

# Also try a broader approach - look for price near each listing URL
print("\n=== ORPI (price near each T2+ URL) ===")
for m in re.finditer(r'href="(/annonce-location-appartement-t[2-9][^"]*?)"', html):
    u = m.group(1)
    if '?contact=true' in u:
        continue
    # Get price from nearby context - look within 1000 chars before
    start = max(0, m.start() - 1500)
    context = html[start:m.start()]
    # Price patterns
    prices = re.findall(r'(\d{3,4})\s*(?:€|&euro;|EUR)', context)
    price = prices[-1] if prices else '?'
    # Also try data-price
    dp = re.search(r'data-price="(\d+)"', context)
    if dp:
        price = dp.group(1)
    # Surface
    surf_m = re.search(r'([\d.]+)\s*m²', context)
    if not surf_m:
        surf_m = re.search(r'Surface\s*:?\s*([\d.]+)', context, re.I)
    surf = surf_m.group(1) if surf_m else '?'
    # City
    city_m = re.search(r'(le-havre|harfleur|montivilliers)', u, re.I)
    city = city_m.group(1) if city_m else '?'
    type_m = re.search(r'(t[2-9])', u, re.I)
    typ = type_m.group(1) if type_m else '?'
    print(f"  {typ} | {price}EUR | {surf}m2 | {city} | {u}")