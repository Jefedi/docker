import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

lbc = data['results'][0]['content']
lines = lbc.split('\n')

# Extract ad URLs with line positions
ad_urls = []
for i, line in enumerate(lines):
    m = re.search(r'Voir l.annonce\]\((https://www\.leboncoin\.fr/ad/locations/\d+)\)', line)
    if m:
        ad_urls.append((i, m.group(1)))

# For each ad, extract the block between previous ad URL line and this one
listings = []
for idx, (line_num, url) in enumerate(ad_urls):
    start = ad_urls[idx-1][0]+1 if idx > 0 else 0
    end = line_num+1
    block = '\n'.join(lines[start:end])
    
    # Extract price
    price_m = re.search(r'(\d+)\s*€', block)
    price = price_m.group(1) if price_m else '?'
    
    # Extract type/surface/rooms
    # Pattern: "Appartement · 2 pièces · 33m² · Étage 2"
    type_m = re.search(r'(Appartement|Maison)\s*·\s*(\d+)\s*pi[èe]ces?\s*·\s*(\d+)m[²2]', block)
    if type_m:
        rooms = int(type_m.group(2))
        surface = int(type_m.group(3))
    else:
        rooms = 0
        surface = 0
    
    # Extract quartier/location
    loc_m = re.search(r'Le Havre\s*\d+\s+(.+?)(?:\n|$)', block)
    location = loc_m.group(1).strip() if loc_m else '?'
    
    # Extract features (Meublé, Dernier étage, Parking, etc.)
    features = []
    if 'Meublé' in block:
        features.append('Meublé')
    if 'Dernier étage' in block:
        features.append('Dernier étage')
    if 'Parking' in block:
        features.append('Parking')
    if 'Balcon' in block or 'balcon' in block:
        features.append('Balcon')
    
    # Extract ad ID
    ad_id = url.split('/')[-1]
    
    # Get description text — look for text blocks that seem like descriptions
    # Filter out image lines, empty lines, and navigation
    desc_lines = []
    for bl in block.split('\n'):
        bl = bl.strip()
        if not bl:
            continue
        if bl.startswith('![') or bl.startswith('https://') or bl.startswith('- [Voir'):
            continue
        if bl in ['Pro', 'Vendeur professionnel.', 'Sponsorisé', 'Afficher la carte']:
            continue
        if 'Date de dépôt' in bl or 'Logo du professionnel' in bl:
            continue
        if bl.startswith('Prix:'):
            continue
        if bl.startswith('Située à'):
            continue
        if 'Annonce possédant' in bl:
            continue
        desc_lines.append(bl)
    
    # Join first ~15 non-trivial lines as description
    desc = ' '.join(desc_lines[:20])
    
    listings.append({
        'idx': idx,
        'ad_id': ad_id,
        'url': url,
        'price': price,
        'rooms': rooms,
        'surface': surface,
        'location': location,
        'features': features,
        'desc_excerpt': desc[:500],
        'block_lines': end - start,
    })

for l in listings:
    print(f"\n--- Listing #{l['idx']} ---")
    print(f"  ID: {l['ad_id']}")
    print(f"  URL: {l['url']}")
    print(f"  Price: {l['price']}€")
    print(f"  Rooms: {l['rooms']}p | Surface: {l['surface']}m²")
    print(f"  Location: {l['location']}")
    print(f"  Features: {', '.join(l['features']) if l['features'] else 'none'}")
    print(f"  Desc: {l['desc_excerpt'][:300]}")