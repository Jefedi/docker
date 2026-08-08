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
        
        # Fixed price extraction: pattern is "{photo_count} {price} € / mois"
        price = None
        # Pattern: "N XXX € / mois" where N is 1 digit (photos) and XXX is the price
        m = re.search(r'\d\s+(\d{2,4})\s*€\s*/?\s*mois', text)
        if m:
            price = int(m.group(1))
        else:
            # Try other patterns
            for pat in [r'Loyer\s*:?\s*(\d{3,4})\s*(?:€|euros?)',
                        r'proposé à\s*(\d{3,4})\s*€',
                        r'(\d{3,4})\s*€\s*mensuel',
                        r'(\d{3,4})\s*€\s*par mois',
                        r'Loyer charges comprises\s*:?\s*(\d{3,4})']:
                m = re.search(pat, text, re.I)
                if m:
                    price = int(m.group(1))
                    break
        
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

# Filter: T2+, surface >= 28, price <= 500
candidates = [l for l in all_listings if l['pieces'] and l['pieces'] >= 2 
             and l['surface'] and l['surface'] >= 28
             and l['price'] and l['price'] <= 500]

print(f"Total listings: {len(all_listings)}")
print(f"T2+ with surface >= 28 and price <= 500: {len(candidates)}")
print()
for c in candidates:
    print(f"P{c['page']} T{c['pieces']} {c['surface']}m² | {c['price']}€/mois | ID: {c['id']}")
    print(f"  Link: https://www.le-partenaire.fr{c['link']}")
    print(f"  Text: {c['text'][:600]}")
    print()