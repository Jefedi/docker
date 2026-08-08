import re, html as htmlmod, json

all_listings = []

for page in range(1, 7):
    fname = f'/tmp/lp{page}.html'
    try:
        content = open(fname).read()
    except:
        continue
    
    # Split by h2 tags that start listing titles
    sections = re.split(r'<h2[^>]*>', content)
    for sec in sections[1:]:
        # Get title text (up to </h2>)
        title_end = sec.find('</h2>')
        if title_end == -1:
            continue
        title_raw = sec[:title_end]
        title = re.sub(r'<[^>]+>', ' ', title_raw)
        title = htmlmod.unescape(title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Get block content (larger chunk for description)
        block = sec[:5000]
        
        # Clean text
        text = re.sub(r'<[^>]+>', ' ', block)
        text = htmlmod.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Extract link
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', block)
        link = link_match.group(1) if link_match else None
        
        # Extract pieces and surface from title
        pieces_match = re.search(r'(\d)\s*pi[eè]ce', title)
        surface_match = re.search(r'(\d+)\s*m[²2]', title)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Extract listing ID from link
        listing_id = None
        if link:
            id_match = re.search(r'/(\d+)$', link)
            if id_match:
                listing_id = id_match.group(1)
        
        # Extract price from text - look for "Loyer" or "€/mois" or "€ mensuel"
        price = None
        # Pattern: "XXX € / mois" or "XXX euros" or "Loyer: XXX"
        price_patterns = [
            r'Loyer\s*:?\s*(\d[\d\s]*)\s*(?:€|euros?)',
            r'(\d[\d\s]*)\s*€\s*/?\s*mois',
            r'proposé à\s*(\d[\d\s]*)\s*€',
            r'(\d[\d\s]*)\s*€\s*mensuel',
            r'(\d[\d\s]*)\s*€\s*par mois',
            r'Loyer charges comprises\s*:?\s*(\d[\d\s]*)',
        ]
        for pat in price_patterns:
            m = re.search(pat, text, re.I)
            if m:
                p = m.group(1).replace('\xa0', '').replace(' ', '').replace('\u202f', '')
                try:
                    price = int(p)
                    if price > 50:  # reasonable rent
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

# Filter: T2+ (2+ pieces), surface >= 28, price <= 500
candidates = []
for l in all_listings:
    if l['pieces'] and l['pieces'] >= 2 and l['surface'] and l['surface'] >= 28:
        # Check price - if price found and <= 500, or if price not found (need to check)
        if l['price'] is None or l['price'] <= 500:
            candidates.append(l)

print(f"Total listings across all pages: {len(all_listings)}")
print(f"T2+ candidates with surface >= 28: {len(candidates)}")
print()
for c in candidates:
    print(f"Page {c['page']} | T{c['pieces']} {c['surface']}m² | {c['price']}€ | ID: {c['id']}")
    print(f"  Link: https://www.le-partenaire.fr{c['link']}")
    print(f"  Text: {c['text'][:400]}")
    print()