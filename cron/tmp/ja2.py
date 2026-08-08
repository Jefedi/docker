import re, json, html

# Parse JA more carefully - extract listing blocks with title + price
s = open('/tmp/src_b82d1c6c.html').read()

# Find all listing links (deduplicated, preserving order)
links = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/[^"]+\.html)"', s)
seen_urls = set()
unique_links = []
for l in links:
    if l not in seen_urls:
        seen_urls.add(l)
        unique_links.append(l)

# For each unique link, find the surrounding block and extract price
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

print(f"JA unique listings: {len(unique_links)}")
print("\n=== F2+ listings ===")
for link in unique_links:
    idx = s.find(link)
    if idx < 0: continue
    # Get a larger block around the link
    block = s[max(0,idx-2000):idx+2000]
    # Find price - look for "Loyer" or "€" pattern
    price_m = re.search(r'(?:Loyer|loyer)[:\s]*(\d+)\s*€', block)
    if not price_m:
        price_m = re.search(r'(\d{3,4})\s*€', block)
    price = int(price_m.group(1)) if price_m else 0
    # Extract type from URL (f1, f2, f3, etc.)
    type_m = re.search(r'-de-type-(f\d)|type-(f\d)|-(f\d)-', link, re.I)
    ftype = type_m.group(1).lower() if type_m and type_m.group(1) else ''
    # Check if it's a chambre/colocation (not an appartement)
    if 'chambre' in link.lower() or 'garage' in link.lower() or 'parking' in link.lower() or 'local' in link.lower() or 'emplacement' in link.lower():
        continue
    # F2+ filter
    fnum = 0
    if ftype:
        m = re.search(r'f(\d+)', ftype)
        if m: fnum = int(m.group(1))
    if fnum >= 2 and price <= 500 and price > 0:
        # ID from URL
        id_m = re.search(r'/([a-z0-9-]+)\.html', link)
        lid = id_m.group(1) if id_m else ''
        seen_id = f"ja-{lid}"
        status = "NEW" if seen_id not in seen else "SEEN"
        # Get surface from block
        surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
        surf = surf_m.group(1) if surf_m else '?'
        print(f"  {status}: {seen_id} | {ftype} | {price}€ | {surf}m² | {link}")