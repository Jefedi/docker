import re, json

# Parse Orpi JSON-LD to get full listing data with price, surface, title
for fname, label in [('/tmp/src_a559eead.html', 'Orpi p1'), ('/tmp/orpi2.html', 'Orpi p2')]:
    s = open(fname).read()
    # Find listing cards - Orpi embeds each card with price, title, surface
    # The JSON-LD only has URLs. Let's parse the HTML cards.
    # Each listing card has a link to the annonce, and nearby text with price, surface, pieces

    # Find all annonce-location links
    annonce_links = re.findall(r'href="(https://www\.orpi\.com/annonce-location-appartement-[^"]+)"', s)
    # Deduplicate preserving order
    seen = set()
    unique_links = []
    for l in annonce_links:
        if l not in seen:
            seen.add(l)
            unique_links.append(l)

    print(f"\n=== {label}: {len(unique_links)} unique listings ===")
    # For each link, find the surrounding block to extract price/surface
    for url in unique_links:
        idx = s.find(url)
        if idx < 0: continue
        block = s[max(0, idx-500):idx+500]
        # Extract type from URL (t1, t2, t3, t4)
        type_m = re.search(r'appartement-(t\d)-', url)
        prop_type = type_m.group(1) if type_m else ''
        # Find price in block
        price_m = re.search(r'(\d[\d\s]*)\s*€', block)
        price = price_m.group(1).replace(' ','').strip() if price_m else ''
        # Find surface
        surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
        surface = surf_m.group(1).replace(',','.') if surf_m else ''
        # Find title/description
        title_m = re.search(r'<h[23456][^>]*>(.*?)</h[23456]>', block, re.DOTALL)
        import html as h
        title = h.unescape(re.sub('<[^>]+>','', title_m.group(1))).strip() if title_m else ''
        # Extract ID from URL
        id_m = re.search(r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
        if not id_m:
            id_m = re.search(r'-(\d+-\d+)', url)
        listing_id = id_m.group(1) if id_m else ''
        print(f"  {prop_type} | {price}€ | {surface}m² | id={listing_id} | {url}")
        if title: print(f"    Title: {title[:100]}")