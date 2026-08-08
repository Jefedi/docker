import re

with open('/opt/data/cache/web/www.leboncoin.fr-6dab532d68.md') as f:
    content = f.read()

lines = content.split('\n')

# Extract ALL ad URLs with line positions from the full cached file
ad_urls = []
for i, line in enumerate(lines):
    m = re.search(r'Voir l.annonce\]\((https://www\.leboncoin\.fr/ad/locations/\d+)\)', line)
    if m:
        ad_urls.append((i, m.group(1)))

print(f"Total ad URLs found in full cached file: {len(ad_urls)}")

# For each ad, extract info from the block
listings = []
for idx, (line_num, url) in enumerate(ad_urls):
    start = ad_urls[idx-1][0]+1 if idx > 0 else 0
    end = line_num+1
    block = '\n'.join(lines[start:end])
    
    # Extract price
    price_m = re.search(r'(\d+)\s*€', block)
    price = int(price_m.group(1)) if price_m else 0
    
    # Extract type/surface/rooms
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
    # Clean location
    if 'Située à' in location:
        location = '?'
    
    # Extract features
    features = []
    if 'Meublé' in block:
        features.append('Meublé')
    if 'Dernier étage' in block:
        features.append('Dernier étage')
    if 'Parking' in block:
        features.append('Parking')
    if 'Balcon' in block or 'balcon' in block:
        features.append('Balcon')
    if 'Terrasse' in block or 'terrasse' in block:
        features.append('Terrasse')
    if 'Cave' in block:
        features.append('Cave')
    
    # Check for "Baisse de prix"
    if 'Baisse de prix' in block:
        features.append('Baisse de prix')
    
    ad_id = url.split('/')[-1]
    
    listings.append({
        'idx': idx,
        'ad_id': ad_id,
        'url': url,
        'price': price,
        'rooms': rooms,
        'surface': surface,
        'location': location,
        'features': features,
    })

# Print all listings sorted by price
listings.sort(key=lambda x: x['price'])

print(f"\n{'='*80}")
print(f"ALL LEBONCOIN LISTINGS (sorted by price):")
print(f"{'='*80}")
for l in listings:
    print(f"  #{l['idx']:2d} | {l['price']}€ | {l['rooms']}p {l['surface']}m² | {l['location'][:40]:40s} | ID:{l['ad_id']} | {', '.join(l['features'])}")