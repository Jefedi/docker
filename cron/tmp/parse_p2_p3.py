#!/usr/bin/env python3
"""Parse Citya p2/p3, Orpi p2, SquareHabitat p2 for new listings."""
import re, json

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

new_listings = []

# --- CITYA p2/p3 ---
for fpath, label in [('/tmp/citya_p2.html', 'Citya p2'), ('/tmp/citya_p3.html', 'Citya p3')]:
    with open(fpath, 'r', errors='replace') as f:
        html = f.read()
    ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    if ld_blocks:
        try:
            data = json.loads(ld_blocks[0])
            offers = data.get('offers', [])
            for o in offers:
                price = o.get('price', 0)
                url = o.get('url', '')
                ref_match = re.search(r'GES(\d+-\d+)', url)
                ref = ref_match.group(1) if ref_match else ''
                item = o.get('itemOffered', {})
                name = item.get('name', '') if isinstance(item, dict) else ''
                pieces_match = re.search(r'(\d+)\s*pi[èe]ce', name)
                surface_match = re.search(r'(\d+\.?\d*)\s*m[²2]', name)
                pieces = int(pieces_match.group(1)) if pieces_match else 0
                surface = float(surface_match.group(1)) if surface_match else 0
                citya_id = f"citya-GES{ref}"
                is_new = citya_id not in seen_ids

                if pieces >= 2 and surface >= 28 and price <= 500:
                    status = "NEW!" if is_new else "seen"
                    print(f"  [{label}] {status} | {price}EUR | {pieces}p | {surface}m2 | {name[:50]}")
                    print(f"    URL: {url}")
                    if is_new:
                        new_listings.append({
                            'source': 'citya', 'id': citya_id, 'price': price,
                            'pieces': pieces, 'surface': surface, 'url': url, 'name': name
                        })
        except Exception as e:
            print(f"  [{label}] Error: {e}")

# --- ORPI p2 ---
print("\n--- Orpi p2 ---")
with open('/tmp/orpi_p2.html', 'r', errors='replace') as f:
    html = f.read()
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_blocks:
    try:
        data = json.loads(ld_blocks[0])
        items = data.get('itemListElement', [])
        for item in items:
            url = item.get('url', '')
            type_match = re.search(r't(\d)-le-havre', url, re.IGNORECASE)
            pieces = int(type_match.group(1)) if type_match else 0
            id_match = re.search(r'le-havre-76600-([^/]+)/', url)
            orpi_raw_id = id_match.group(1) if id_match else ''
            orpi_id = f"orpi-{orpi_raw_id}"
            is_new = orpi_id not in seen_ids

            if pieces >= 2:
                status = "NEW!" if is_new else "seen"
                print(f"  {status} | T{pieces} | {url}")
                if is_new:
                    new_listings.append({
                        'source': 'orpi', 'id': orpi_id, 'pieces': pieces, 'url': url
                    })
    except Exception as e:
        print(f"  Error: {e}")

# --- SquareHabitat p2 ---
print("\n--- SquareHabitat p2 ---")
with open('/tmp/sqhab_p2.html', 'r', errors='replace') as f:
    html = f.read()

# Find listing blocks
listing_blocks = re.findall(r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/[^"]+)"[^>]*>\s*([^<]+)', html)
for url, title in listing_blocks:
    id_match = re.search(r'le-havre/([a-f0-9-]+)', url)
    sqhab_id = f"sqhab-{id_match.group(1)}" if id_match else ''
    is_new = sqhab_id not in seen_ids

    pieces_match = re.search(r'(\d+)\s*pi[èe]ces', title)
    pieces = int(pieces_match.group(1)) if pieces_match else 0

    if pieces >= 2:
        status = "NEW!" if is_new else "seen"
        print(f"  {status} | {title.strip()[:50]} | https://www.squarehabitat.fr{url}")
        if is_new:
            new_listings.append({
                'source': 'sqhab', 'id': sqhab_id, 'pieces': pieces,
                'url': f"https://www.squarehabitat.fr{url}", 'title': title.strip()
            })

print(f"\n\n=== TOTAL NEW LISTINGS: {len(new_listings)} ===")
for l in new_listings:
    print(f"  {l}")