import re, html, json, os

def parse_page(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    h2_positions = [(m.start(), m.end()) for m in re.finditer(r'<h2[^>]*>.*?</h2>', content, re.DOTALL)]
    listings = []
    for i, (start, end) in enumerate(h2_positions):
        block_start = start
        block_end = h2_positions[i+1][0] if i+1 < len(h2_positions) else len(content)
        block = content[block_start:block_end]
        h2_text = re.sub(r'<[^>]+>', '', content[start:end]).strip()
        h2_text = html.unescape(h2_text)
        h2_text = re.sub(r'\s+', ' ', h2_text)
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/\d+pieces/\d+)"', block)
        link = link_match.group(1) if link_match else ''
        lid = link.split('/')[-1] if link else ''
        desc_text = re.sub(r'<[^>]+>', ' ', block)
        desc_text = html.unescape(desc_text)
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        
        price = None
        for pattern in [
            r'(\d{3,4})\s*€\s*mensuel',
            r'[Ll]oyer\s*charges\s*comprises\s*:?\s*(\d{3,4})\s*[e€]',
            r'[Ll]oyer\s*:?\s*(\d{3,4})\s*[e€]',
            r'(?:proposé à|pour un loyer de)\s*(\d{3,4})\s*€',
            r'Location de particulier\s*(\d{3,4})\s*€',
        ]:
            m = re.search(pattern, desc_text, re.IGNORECASE)
            if m:
                price = int(m.group(1))
                break
        if not price:
            for m in re.finditer(r'(\d{2,4})\s*€\s*/?\s*mois', desc_text):
                p = int(m.group(1))
                if 100 <= p <= 500:
                    price = p
                    break
        
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        listings.append({
            'id': lid, 'pieces': pieces, 'surface': surface, 'price': price,
            'link': f"https://www.le-partenaire.fr{link}" if link else '',
            'desc': desc_text[:1200]  # longer desc
        })
    return listings

all_listings = []
for p in ['', '_p2', '_p3', '_p4', '_p5', '_p6']:
    filepath = f'/tmp/lp_rent{p}.html'
    if os.path.exists(filepath):
        all_listings.extend(parse_page(filepath))

seen_ids = set()
unique = []
for l in all_listings:
    if l['id'] and l['id'] not in seen_ids:
        seen_ids.add(l['id'])
        unique.append(l)

# Filter: T2+, price <= 500, surface >= 28 (or None)
candidates = [l for l in unique 
    if l['pieces'] and l['pieces'] >= 2 
    and l['price'] and l['price'] <= 500
    and (l['surface'] is None or l['surface'] >= 28)]

candidates.sort(key=lambda x: x['price'])

# Print full descriptions for manual analysis
for c in candidates:
    print(f"{'='*80}")
    print(f"ID: {c['id']} | T{c['pieces']} | {c['surface']}m² | {c['price']}€")
    print(f"Link: {c['link']}")
    print(f"Desc: {c['desc']}")
    print()