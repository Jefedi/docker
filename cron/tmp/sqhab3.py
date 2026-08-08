import re, json, html

# Parse SquareHabitat by matching JSON-LD prices (in order) with listing UUIDs+surfaces (in order)
s = open('/tmp/src_a8dd5e22.html').read()
prices = re.findall(r'"price":\s*(\d+)', s)
print(f"Prices: {prices}")

# Find the 18 listings that have surface info - they appear at the bottom of the page
# The pattern is: UUID followed by surface in the heading text
# Let's find the listing cards with surface data
# Pattern: data-itemId or UUID near a heading with "pièce" and "m²"
listing_pattern = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).*?(\d+)\s*pi[èc].*?(\d+(?:[.,]\d+)?)\s*m²', s, re.DOTALL)

# Better approach: find the h2 headings with surface info, in order
h2_blocks = re.findall(r'<h[234][^>]*>(.*?)</h[234]>', s, re.DOTALL)
listing_h2s = []
for h in h2_blocks:
    t = html.unescape(re.sub('<[^>]+>','',h)).strip()
    if 'pièce' in t.lower() or 'studio' in t.lower():
        # Extract pieces and surface
        pm = re.search(r'(\d+)\s*pi[èc]', t)
        sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', t)
        # Also check for UUID nearby
        listing_h2s.append({
            'title': t,
            'pieces': int(pm.group(1)) if pm else (0 if 'studio' in t.lower() else 0),
            'surface': float(sm.group(1).replace(',','.')) if sm else 0,
        })

print(f"\nListing headings: {len(listing_h2s)}")
for i, l in enumerate(listing_h2s):
    price = prices[i] if i < len(prices) else '?'
    print(f"  {i}: {l['pieces']}p | {l['surface']}m² | {price}€ | {l['title'][:60]}")

# Now find UUIDs for these listings
# The visible listings are at the end of the file - find UUIDs near h2 headings
uuids_near_h2 = []
for m in re.finditer(r'<h[234][^>]*>.*?(?:pièce|studio)', s, re.DOTALL):
    pos = m.start()
    # Look backwards for UUID
    block = s[max(0,pos-500):pos]
    uuid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', block)
    uuids_near_h2.append(uuid_m.group(1) if uuid_m else '')

print(f"\nUUIDs near h2: {len(uuids_near_h2)}")
# Filter T2+, <=500€, >=28m²
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

print("\n=== SquareHabitat candidates ===")
for i, l in enumerate(listing_h2s):
    price = int(prices[i]) if i < len(prices) else 9999
    if l['pieces'] >= 2 and price <= 500 and l['surface'] >= 28:
        uuid = uuids_near_h2[i] if i < len(uuids_near_h2) else ''
        seen_id = f"sqhab-{uuid}"
        status = "NEW" if seen_id not in seen else "SEEN"
        print(f"  {status}: {seen_id} | {l['pieces']}p | {l['surface']}m² | {price}€ | {l['title'][:60]}")