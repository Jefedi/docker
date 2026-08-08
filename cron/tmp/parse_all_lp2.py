import re, html as htmlmod, json

all_listings = []

for page in range(1, 7):
    fname = f'/tmp/lp{page}.html'
    try:
        content = open(fname).read()
    except:
        continue
    
    sections = re.split(r'<h2[^>]*>', content)
    for sec in sections[1:]:
        title_end = sec.find('</h2>')
        if title_end == -1:
            continue
        title_raw = sec[:title_end]
        title = re.sub(r'<[^>]+>', ' ', title_raw)
        title = htmlmod.unescape(title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        block = sec[:5000]
        text = re.sub(r'<[^>]+>', ' ', block)
        text = htmlmod.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', block)
        link = link_match.group(1) if link_match else None
        
        pieces_match = re.search(r'(\d)\s*pi[eè]ce', title)
        surface_match = re.search(r'(\d+)\s*m[²2]', title)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface = int(surface_match.group(1)) if surface_match else None
        
        listing_id = None
        if link:
            id_match = re.search(r'/(\d+)$', link)
            if id_match:
                listing_id = id_match.group(1)
        
        # Better price extraction
        price = None
        price_patterns = [
            r'Loyer\s*:?\s*(\d[\d\s]*)\s*(?:€|euros?)',
            r'(\d[\d\s]*)\s*€\s*/?\s*mois',
            r'proposé à\s*(\d[\d\s]*)\s*€',
            r'(\d[\d\s]*)\s*€\s*mensuel',
            r'(\d[\d\s]*)\s*€\s*par mois',
            r'Loyer charges comprises\s*:?\s*(\d[\d\s]*)',
            r'(\d{3})\s*euros?\s*par\s*mois',
        ]
        for pat in price_patterns:
            m = re.search(pat, text, re.I)
            if m:
                p = m.group(1).replace('\xa0', '').replace(' ', '').replace('\u202f', '')
                try:
                    price = int(p)
                    if price > 50:
                        break
                except:
                    pass
        
        all_listings.append({
            'page': page,
            'title': title,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'link': link,
            'id': listing_id,
            'text': text[:800]
        })

# Show ALL T2+ listings (regardless of price) to understand what we have
t2plus = [l for l in all_listings if l['pieces'] and l['pieces'] >= 2]
print(f"=== ALL T2+ listings ({len(t2plus)}) ===")
for l in t2plus:
    print(f"P{l['page']} T{l['pieces']} {l['surface']}m² | {l['price']}€ | ID: {l['id']} | link: {l['link']}")

# Now show T2+ with surface >= 28 and price <= 500 (or price None - to check)
print(f"\n=== T2+ with surface >= 28 and price <= 500 ===")
for l in t2plus:
    if l['surface'] and l['surface'] >= 28:
        if l['price'] is None or (l['price'] and l['price'] <= 500):
            print(f"  P{l['page']} T{l['pieces']} {l['surface']}m² | {l['price']}€ | ID: {l['id']}")
            print(f"  Text: {l['text'][:500]}")
            print()

# Also show listings where price is None for T2+
print(f"\n=== T2+ with price=None (need manual check) ===")
for l in t2plus:
    if l['price'] is None and l['surface'] and l['surface'] >= 28:
        print(f"  P{l['page']} T{l['pieces']} {l['surface']}m² | ID: {l['id']}")
        print(f"  Text: {l['text'][:500]}")
        print()