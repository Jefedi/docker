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
        m1 = re.search(r'(\d{3,4})\s*€\s*mensuel', desc_text, re.IGNORECASE)
        if m1:
            price = int(m1.group(1))
        else:
            m2 = re.search(r'[Ll]oyer\s*charges\s*comprises\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
            if m2:
                price = int(m2.group(1))
            else:
                m3 = re.search(r'[Ll]oyer\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
                if m3:
                    price = int(m3.group(1))
                else:
                    m4 = re.search(r'(?:proposé à|pour un loyer de)\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
                    if m4:
                        price = int(m4.group(1))
                    else:
                        m5 = re.search(r'Location de particulier\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
                        if m5:
                            price = int(m5.group(1))
                        else:
                            for m6 in re.finditer(r'(\d{2,4})\s*€\s*/?\s*mois', desc_text):
                                p = int(m6.group(1))
                                if 100 <= p <= 500:
                                    price = p
                                    break
        
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        listings.append({
            'id': lid,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'link': f"https://www.le-partenaire.fr{link}" if link else '',
            'desc': desc_text[:800]
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

# Debug: show how many pass each filter
f_pieces = [l for l in unique if l['pieces'] and l['pieces'] >= 2]
print(f"After pieces >= 2: {len(f_pieces)}")
for l in f_pieces:
    print(f"  ID={l['id']} pieces={l['pieces']} surf={l['surface']}m² price={l['price']}€")

f_price = [l for l in f_pieces if l['price'] is not None and l['price'] <= 500]
print(f"\nAfter price <= 500: {len(f_price)}")
for l in f_price:
    print(f"  ID={l['id']} pieces={l['pieces']} surf={l['surface']}m² price={l['price']}€")

f_surface = [l for l in f_price if l['surface'] is None or l['surface'] >= 28]
print(f"\nAfter surface >= 28: {len(f_surface)}")
for l in f_surface:
    print(f"  ID={l['id']} pieces={l['pieces']} surf={l['surface']}m² price={l['price']}€")
    print(f"    desc: {l['desc'][:400]}")
    print()