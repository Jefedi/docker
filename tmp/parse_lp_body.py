import json, re

# Parse Le-Partenaire body text to extract listings with prices
# Read the raw JSON chunks from the body text file
body_chunks = []
with open('/opt/data/tmp/lp_full_body.txt') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if 'result' in data:
                body_chunks.append(data['result'])
        except:
            pass

full_body = ''.join(body_chunks)

# Split into listings by the pattern "Location Appartement à Le Havre"
# Each listing starts with this title
listing_pattern = r'Location Appartement\s+à Le Havre\s+(\d+)\s*pi[èe]ces?\s*\|\s*(\d+)\s*m[²2]'
matches = list(re.finditer(listing_pattern, full_body))

listings = []
for i, m in enumerate(matches):
    start = m.start()
    # Get the text until the next listing or end
    end = matches[i+1].start() if i+1 < len(matches) else len(full_body)
    block = full_body[start:end]
    
    rooms = int(m.group(1))
    surface = int(m.group(2))
    
    # Extract price - look for "XXX €/mois" or "XXX € / mois"
    price_match = re.search(r'(\d[\d\s]*)\s*€\s*/?\s*mois', block)
    price = 0
    if price_match:
        price_str = price_match.group(1).replace(' ', '').replace('\xa0', '')
        try:
            price = int(price_str)
        except:
            pass
    
    # Extract quartier/location info
    quartier = ""
    loc_match = re.search(r'(Quartier [^,.\n]+|centre[- ]ville|sanvic|bl[èe]ville|Docks|Coty|Massillon|Danton)', block, re.IGNORECASE)
    if loc_match:
        quartier = loc_match.group(0)
    
    # Check for cuisine séparée
    cuisine_sep = bool(re.search(r'cuisine\s+(ind[ée]pendante|s[ée]par)', block, re.IGNORECASE))
    cuisine_ouverte = bool(re.search(r'cuisine\s+(ouverte|am[ée]ricaine|[ée]quip)', block, re.IGNORECASE))
    
    # Check for chambre fermée
    chambre = bool(re.search(r'\d+\s*chambre', block, re.IGNORECASE))
    
    # Check for vendu loué / meublé
    meuble = bool(re.search(r'meubl', block, re.IGNORECASE))
    
    # DPE
    dpe_match = re.search(r'DPE\s+([A-G])\s', block)
    dpe = dpe_match.group(1) if dpe_match else ""
    
    # Surface check >= 28, rooms >= 2, price <= 500
    listing = {
        'idx': i,
        'rooms': rooms,
        'surface': surface,
        'price': price,
        'quartier': quartier,
        'cuisine_sep': cuisine_sep,
        'cuisine_ouverte': cuisine_ouverte,
        'chambre': chambre,
        'meuble': meuble,
        'dpe': dpe,
        'block_preview': block[:300]
    }
    listings.append(listing)

# Filter: T2+, surface >= 28, price <= 500
print(f"=== Total LP listings: {len(listings)} ===")
qualifying = [l for l in listings if l['rooms'] >= 2 and l['surface'] >= 28 and 0 < l['price'] <= 500]
print(f"=== T2+ >= 28m² <= 500€: {len(qualifying)} ===")
for l in qualifying:
    cuisine_status = "séparée" if l['cuisine_sep'] else ("ouverte" if l['cuisine_ouverte'] else "non vérifié")
    print(f"  T{l['rooms']} | {l['surface']}m² | {l['price']}€ | DPE:{l['dpe']} | cuisine:{cuisine_status} | chambre:{l['chambre']} | {l['quartier'][:30]}")
    print(f"    Preview: {l['block_preview'][:200]}")

# Also show all T2+ with price > 0 but > 500
print(f"\n=== T2+ >= 28m² > 500€ (excluded): ===")
excluded = [l for l in listings if l['rooms'] >= 2 and l['surface'] >= 28 and l['price'] > 500]
for l in excluded[:10]:
    print(f"  T{l['rooms']} | {l['surface']}m² | {l['price']}€ | {l['block_preview'][:150]}")