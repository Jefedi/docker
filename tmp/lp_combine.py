import json, re

# Load URL mapping
url_map = json.load(open('/opt/data/tmp/lp_url_map.json'))

# Load body text listings with prices
body_chunks = []
with open('/opt/data/tmp/lp_full_body.txt') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            data = json.loads(line)
            if 'result' in data: body_chunks.append(data['result'])
        except: pass
full_body = ''.join(body_chunks).replace('\xa0', ' ')

# Parse body listings with prices
listing_pattern = r'Location Appartement\s+à Le Havre\s+(\d+)\s+pi[èe]ces?\s*\|\s*(\d+)\s*m[²2]'
matches = list(re.finditer(listing_pattern, full_body))

body_listings = []
for i, m in enumerate(matches):
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else min(len(full_body), start + 3000)
    block = full_body[start:end]
    
    rooms = int(m.group(1))
    surface = int(m.group(2))
    
    # Price
    price_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*€\s*/\s*mois', block)
    price = 0
    if price_match:
        price_str = price_match.group(1).replace(' ', '').strip()
        try:
            price = int(price_str)
        except:
            pass
    
    body_listings.append({
        'idx': i,
        'rooms': rooms,
        'surface': surface,
        'price': price,
        'block': block
    })

# Match body listings with URL mapping by index
# They should be in the same order (page by page, 20 per page)
combined = []
for i, bl in enumerate(body_listings):
    if i < len(url_map):
        url_entry = url_map[i]
        combined.append({
            'id': url_entry['id'],
            'url': url_entry['url'],
            'rooms': bl['rooms'],
            'surface': bl['surface'],
            'price': bl['price'],
            'block': bl['block'][:500],
            'url_rooms': url_entry['rooms'],
            'url_surface': url_entry['surface']
        })

# Filter: T2+, surface >= 28, price <= 500
qualifying = [c for c in combined if c['rooms'] >= 2 and c['surface'] >= 28 and 0 < c['price'] <= 500]
print(f"=== LP qualifying (T2+ >= 28m² <= 500€): {len(qualifying)} ===")
for c in qualifying:
    # Check cuisine
    cuisine_sep = bool(re.search(r'cuisine\s+(ind[ée]pendante|s[ée]par)', c['block'], re.IGNORECASE))
    cuisine_ouverte = bool(re.search(r'cuisine\s+(ouverte|am[ée]ricaine)', c['block'], re.IGNORECASE))
    # Check colocation
    colocation = bool(re.search(r'colocation|coloc', c['block'], re.IGNORECASE))
    # Check chambre
    chambre = bool(re.search(r'\d+\s*chambre', c['block'], re.IGNORECASE))
    # Quartier
    quartier = ""
    loc_match = re.search(r'(Quartier [^,.\n]+|centre[- ]ville|sanvic|bl[èe]ville|Docks|Coty|Massillon|Danton|Saint-Vincent|Saint-Nicolas|Graville|Universit)', c['block'], re.IGNORECASE)
    if loc_match:
        quartier = loc_match.group(0)
    
    cuisine_status = "séparée" if cuisine_sep else ("ouverte" if cuisine_ouverte else "non vérifié")
    print(f"  lp-{c['id']} | T{c['rooms']} | {c['surface']}m² | {c['price']}€ | cuisine:{cuisine_status} | coloc:{colocation} | chambre:{chambre} | {quartier[:30]}")
    print(f"    URL: {c['url']}")
    print(f"    Block: {c['block'][:200]}")

with open('/opt/data/tmp/lp_combined.json', 'w') as f:
    json.dump(qualifying, f)