import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# ============= ORPI - match data-reference with price from JSON-LD =============
print("=== ORPI (reference + price matching) ===")
with open('/tmp/havre/orpi.html') as f:
    html = f.read()

# Extract JSON-LD offers (list format)
ld_match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.+?)</script>', html, re.DOTALL)
if ld_match:
    try:
        data = json.loads(ld_match.group(1))
        if isinstance(data, list):
            print(f"  JSON-LD: {len(data)} items")
            for item in data:
                if isinstance(item, dict):
                    ref = item.get('reference', item.get('sku', ''))
                    price = item.get('price', item.get('offers', {}).get('price', 0))
                    url = item.get('url', '')
                    name = item.get('name', item.get('description', ''))
                    # Get surface and pieces
                    surf = item.get('floorSize', {}).get('value', '') if isinstance(item.get('floorSize'), dict) else ''
                    rooms = item.get('numberOfRooms', '')
                    if not surf:
                        surf_m = re.search(r'([\d.]+)\s*m', name)
                        surf = surf_m.group(1) if surf_m else '?'
                    if not rooms:
                        rooms_m = re.search(r'(\d+)\s*pi[èe]ces?', name)
                        rooms = rooms_m.group(1) if rooms_m else '?'
                    pid = f'orpi-{ref}'
                    status = 'SEEN' if pid in seen else 'NEW'
                    if price and int(price) <= 500 and int(rooms) >= 2 if str(rooms).isdigit() else False:
                        marker = 'PASS' if status == 'NEW' else 'seen-PASS'
                        print(f"  {marker}: {pid} | {rooms}p | {surf}m2 | {price}EUR | {url}")
                    elif int(rooms) >= 2 if str(rooms).isdigit() else False:
                        marker = 'skip-price' if status == 'NEW' else 'seen'
                        print(f"  {marker}: {pid} | {rooms}p | {surf}m2 | {price}EUR")
    except Exception as e:
        print(f"  JSON parse error: {e}")

# Alternative: extract reference blocks and match with prices
# Find all data-reference blocks
print("\n=== ORPI (block extraction) ===")
refs = re.findall(r'data-reference="([^"]+)"', html)
print(f"  References: {len(refs)}")

# Find price JSON array
prices_json = re.findall(r'"price":(\d+)', html)
print(f"  Prices: {prices_json}")

# Get each estate-thumb block with its reference and nearby price
thumb_blocks = re.split(r'data-component="estate-thumb"', html)
print(f"  Thumb blocks: {len(thumb_blocks)}")
for block in thumb_blocks[1:]:  # skip first (before first thumb)
    ref_m = re.search(r'data-reference="([^"]+)"', block[:500])
    # Get price from the block - look for the next 2000 chars
    block_full = block[:3000]
    price_m = re.search(r'"price":(\d+)', block_full)
    if not price_m:
        price_m = re.search(r'(\d{3,4})\s*(?:€|&euro;)', block_full)
    price = price_m.group(1) if price_m else '?'
    surf_m = re.search(r'([\d.]+)\s*m', block_full)
    surf = surf_m.group(1) if surf_m else '?'
    rooms_m = re.search(r'(\d+)\s*pi[èe]ces?', block_full)
    rooms = rooms_m.group(1) if rooms_m else '?'
    type_m = re.search(r'(t[2-9]|T[2-9])', block_full)
    typ = type_m.group(1) if type_m else '?'
    ref = ref_m.group(1) if ref_m else '?'
    pid = f'orpi-{ref}'
    status = 'SEEN' if pid in seen else 'NEW'
    if status == 'NEW':
        print(f"  NEW: {pid} | {typ} | {price}EUR | {surf}m2 | {rooms}p")