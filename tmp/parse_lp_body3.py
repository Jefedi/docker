import json, re

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

listing_pattern = r'Location Appartement\s+à Le Havre\s+(\d+)\s+pi[èe]ces?\s*\|\s*(\d+)\s*m[²2]'
matches = list(re.finditer(listing_pattern, full_body))

listings = []
for i, m in enumerate(matches):
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else min(len(full_body), start + 3000)
    block = full_body[start:end]
    
    rooms = int(m.group(1))
    surface = int(m.group(2))
    
    # Fix price extraction: the pattern is "NUMBER\n\nPRICE € / mois"
    # The number before is a photo count. Look for "€ / mois" and get the number just before €
    price_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*€\s*/\s*mois', block)
    price = 0
    if price_match:
        price_str = price_match.group(1).replace(' ', '').strip()
        try:
            price = int(price_str)
        except:
            pass
    
    # Also try a different pattern - sometimes it's "X XXX € /mois"
    if price == 0:
        price_match2 = re.search(r'(\d+)\s*€\s*/?\s*mois', block[:200])
        if price_match2:
            price = int(price_match2.group(1))
    
    # Quartier
    quartier = ""
    loc_match = re.search(r'(Quartier [^,.\n]+|centre[- ]ville|sanvic|bl[èe]ville|Docks|Coty|Massillon|Danton|Saint-Vincent|Saint-Nicolas|Graville|Universit)', block, re.IGNORECASE)
    if loc_match:
        quartier = loc_match.group(0)
    
    # Cuisine
    cuisine_sep = bool(re.search(r'cuisine\s+(ind[ée]pendante|s[ée]par)', block, re.IGNORECASE))
    cuisine_ouverte = bool(re.search(r'cuisine\s+(ouverte|am[ée]ricaine)', block, re.IGNORECASE))
    
    # Chambre
    chambre = bool(re.search(r'\d+\s*chambre', block, re.IGNORECASE))
    
    # Meublé
    meuble = bool(re.search(r'meubl', block, re.IGNORECASE))
    
    # DPE
    dpe_match = re.search(r'DPE\s+([A-G])\s', block)
    dpe = dpe_match.group(1) if dpe_match else ""
    
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
        'block_preview': block[:500]
    }
    listings.append(listing)

print(f"=== Total LP listings: {len(listings)} ===")
# Show all with prices
for l in listings:
    if l['price'] > 0:
        print(f"  {l['idx']+1}. T{l['rooms']} | {l['surface']}m² | {l['price']}€ | DPE:{l['dpe']} | {l['quartier'][:30]}")

qualifying = [l for l in listings if l['rooms'] >= 2 and l['surface'] >= 28 and 0 < l['price'] <= 500]
print(f"\n=== T2+ >= 28m² <= 500€: {len(qualifying)} ===")
for l in qualifying:
    cuisine_status = "séparée" if l['cuisine_sep'] else ("ouverte" if l['cuisine_ouverte'] else "non vérifié")
    print(f"  T{l['rooms']} | {l['surface']}m² | {l['price']}€ | DPE:{l['dpe']} | cuisine:{cuisine_status} | chambre:{l['chambre']} | meublé:{l['meuble']} | {l['quartier'][:30]}")
    print(f"    {l['block_preview'][:200]}")

with open('/opt/data/tmp/lp_qualifying.json', 'w') as f:
    json.dump(qualifying, f)