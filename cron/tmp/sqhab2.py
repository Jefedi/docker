import re, json, html

# SquareHabitat: prices are in JSON but not near the headings. Let's find the JSON data structure
s = open('/tmp/src_a8dd5e22.html').read()
# Find JSON data with listing info
# Look for "price": and "surface": or similar
json_prices = re.findall(r'"price":\s*(\d+)', s)
print(f"JSON prices: {json_prices}")

# Look for __NEXT_DATA__ or __NUXT__
nuxt = re.search(r'window\.__NUXT__\s*=', s)
nxt = re.search(r'__NEXT_DATA__', s)
print(f"NUXT: {nuxt is not None}, NEXT_DATA: {nxt is not None}")

# Look for inline JSON with listing data
# Find script tags containing "price"
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
for i, sc in enumerate(scripts):
    if '"price"' in sc and len(sc) > 200:
        print(f"\nScript {i} ({len(sc)} chars) contains price:")
        # Try to find JSON objects
        objs = re.findall(r'\{[^{}]*"price"[^{}]*\}', sc)
        for o in objs[:5]:
            print(f"  {o[:200]}")

# Alternative: look for data in attributes near UUIDs
# Find each UUID and look for nearby price
uuids = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', s)
unique_uuids = list(dict.fromkeys(uuids))
print(f"\nUnique UUIDs: {len(unique_uuids)}")
for u in unique_uuids:
    idx = s.find(u)
    block = s[max(0, idx-200):idx+500]
    price_m = re.search(r'(\d{3,4})\s*€', block)
    surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
    pieces_m = re.search(r'(\d+)\s*pi[èc]', block)
    title_m = re.search(r'<h[234][^>]*>(.*?)</h[234]>', block, re.DOTALL)
    title = html.unescape(re.sub('<[^>]+>','', title_m.group(1))).strip() if title_m else ''
    price = price_m.group(1) if price_m else ''
    surf = surf_m.group(1) if surf_m else ''
    pc = pieces_m.group(1) if pieces_m else ''
    # Also try to find a link
    link_m = re.search(r'href="(/annonces/[^"]+)"', block)
    link = link_m.group(1) if link_m else ''
    print(f"  {u} | {price}€ | {pc}p | {surf}m² | {title[:60]}")