import re, json, os

# === Parse Leboncoin ===
with open('/opt/data/cache/web/lbc_source_0.txt') as f:
    content = f.read()

links = re.findall(r'leboncoin\.fr/ad/locations/(\d+)', content)
parts = re.split(r'leboncoin\.fr/ad/locations/\d+\)', content)

listings = []
for i in range(len(links)):
    if i + 1 >= len(parts):
        break
    section = parts[i + 1]
    
    price_match = re.search(r'(\d+)\s*€', section)
    type_match = re.search(r'Appartement\s*·\s*(\d+)\s*pièces?\s*·\s*(\d+)m²', section)
    loc_match = re.search(r'Le Havre 76600\s+([^\n]+)', section)
    
    price = int(price_match.group(1)) if price_match else 0
    pieces = int(type_match.group(1)) if type_match else 0
    surface = int(type_match.group(2)) if type_match else 0
    loc = loc_match.group(1).strip() if loc_match else "?"
    
    flags = []
    if "Meublé" in section: flags.append("meublé")
    if "Dernier étage" in section: flags.append("dernier étage")
    if "Balcon" in section: flags.append("balcon")
    if "Terrasse" in section: flags.append("terrasse")
    if "Parking" in section: flags.append("parking")
    if "Baisse de prix" in section: flags.append("baisse prix")
    if "Sponsorisé" in section: flags.append("sponsorisé")
    
    listings.append({
        'id': links[i],
        'price': price,
        'pieces': pieces,
        'surface': surface,
        'loc': loc,
        'flags': flags,
        'url': f"https://www.leboncoin.fr/ad/locations/{links[i]}"
    })
    
    print(f"LBC #{i+1} ID:{links[i]} | {price}€ | {pieces}p | {surface}m² | {loc} | {', '.join(flags)}")

# === Apply Leboncoin filters ===
print("\n\n=== LBC AFTER FILTERS ===")
accepted_quartiers_map = {
    'coty': 'Centre-ville',
    'massillon': 'Centre-ville', 
    'eure': 'Centre-ville',
    'centre-ville': 'Centre-ville',
    'sanvic': 'Sanvic',
    'bléville': 'Bléville',
    'bleville': 'Bléville',
}

lbc_candidates = []
for l in listings:
    loc_lower = l['loc'].lower().strip()
    quartier = None
    for key, val in accepted_quartiers_map.items():
        if key in loc_lower:
            quartier = val
            break
    
    if quartier is None:
        continue
    if l['pieces'] < 2:
        continue
    if l['surface'] < 28:
        continue
    if l['price'] > 500:
        continue
    
    l['quartier'] = quartier
    lbc_candidates.append(l)
    print(f"  ✅ {l['price']}€ | {l['pieces']}p | {l['surface']}m² | {quartier} | {l['loc']} | {', '.join(l['flags'])} | {l['url']}")

# === Parse SeLoger from cache files ===
print("\n\n=== SeLoger PARSED (relevant only) ===")

# Read centre-ville cache
with open('/opt/data/cache/web/www.seloger.com-c92e44cada.md') as f:
    cv_content = f.read()
with open('/opt/data/cache/web/www.seloger.com-52bf488734.md') as f:
    sanvic_content = f.read()
with open('/opt/data/cache/web/www.seloger.com-719c0c3822.md') as f:
    bleville_content = f.read()

# Key candidate: 114 Cours de la République - appears in both Sanvic "plus d'annonces" and Bléville
# T2, 31.6m², 476€ CC, cuisine indépendante, 1 chambre, DPE D
# Also: Sanvic 420€ T2 22m² (too small)
# Also: SeLoger Centre-ville has many but most >500€ or studios

# Parse SeLoger listings properly
seloger_listings = []

for source_name, content in [("Centre-ville", cv_content), ("Sanvic", sanvic_content), ("Bléville", bleville_content)]:
    # Find all listing blocks
    # Pattern: [Title](url) ... DPE letter ... price ... details ... * * * ... description ... agency
    pattern = r'\[(Appartement|Studio|Colocation)\s+à louer[^\]]*\]\((https://www\.seloger\.com/annonces/locations/appartement/[^\)]+?)\)'
    
    for match in re.finditer(pattern, content):
        title = match.group(0).split(']')[0][1:]
        url = match.group(2).split('?')[0]  # clean URL
        
        # Extract from title
        price_m = re.search(r'(\d+)\s*€', title)
        pieces_m = re.search(r'(\d+)\s*pièce', title)
        surface_m = re.search(r'([\d,]+)\s*m²', title)
        chambres_m = re.search(r'(\d+)\s*chambre', title)
        
        price = int(price_m.group(1)) if price_m else 0
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        surface_str = surface_m.group(1).replace(',', '.') if surface_m else "0"
        surface = float(surface_str)
        chambres = int(chambres_m.group(1)) if chambres_m else 0
        
        colocation = 'colocation' in title.lower()
        studio = 'studio' in title.lower()
        logement_etudiant = 'logement étudiant' in title.lower()
        
        # Get section after URL
        start = match.end()
        next_match = re.search(r'\[(Appartement|Studio|Colocation)\s+à louer', content[start:])
        if next_match:
            end = start + next_match.start()
        else:
            end = min(start + 5000, len(content))
        
        section = content[start:end]
        
        # DPE letter (appears as single line before price)
        dpe_m = re.search(r'^([A-G])$', section.strip(), re.MULTILINE)
        if not dpe_m:
            # Try finding it in first few lines
            lines = section.strip().split('\n')
            for line in lines[:10]:
                if line.strip() in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
                    dpe_m = type('obj', (object,), {'group': lambda self, x=0: line.strip()})()
                    break
        dpe = dpe_m.group(1) if dpe_m else "?"
        
        # Extract description between * * *
        desc_m = re.search(r'\* \* \*\s*\n*(.*?)(?:\n*(?:\* \* \*|Exclusivité|AGENCE|SAINT|PAILLETTE|LHL|JULLIEN|Foncia|123 LOGER|Cabinet|SQUARE|ORPI|L ADRESSE|IMMOBILIERE|LE LAB|MANDA|Diffuze|ALBERT|Seine|Particulier|STUDAPART|Laforêt|Agence du Palais|Immo de France|Sponsorisé|SeLoger logo|Accélérez|Plus d))', section, re.DOTALL)
        desc = desc_m.group(1).strip() if desc_m else ""
        
        # Check cuisine
        desc_lower = desc.lower()
        cuisine_ouverte = any(x in desc_lower for x in ['cuisine ouverte', 'cuisine américaine', 'kitchenette', 'coin cuisine', 'cuisine aménagée et équipée ouverte', 'cuisine aménagée ouverte', 'cusine ouverte'])
        cuisine_separee = any(x in desc_lower for x in ['cuisine indépendante', 'cuisine séparée', 'entrée, salon, cuisine indépendante', 'cuisine, salle', 'une cuisine, un séjour', 'séjour avec cuisine, 2 chambres' , 'entrée, un séjour, une cuisine'])
        # Also "une cuisine" without "ouverte" implies separate
        if not cuisine_ouverte and not cuisine_separee:
            if re.search(r'une cuisine\b(?!.*ouverte)', desc_lower):
                cuisine_separee = True
        
        lumineux = any(x in desc_lower for x in ['lumineux', 'lumineuse', 'baigné de lumière', 'baigne de lumière', 'excellente exposition', 'belle luminosité', 'très lumineux', 'bien éclairé'])
        
        # Filter: price ≤ 500, pieces ≥ 2, surface ≥ 28, not colocation, not studio, not logement étudiant
        if price > 500 or pieces < 2 or surface < 28:
            continue
        if colocation or studio or logement_etudiant:
            continue
        
        seloger_listings.append({
            'source': source_name,
            'price': price,
            'pieces': pieces,
            'chambres': chambres,
            'surface': surface,
            'dpe': dpe,
            'cuisine_ouverte': cuisine_ouverte,
            'cuisine_separee': cuisine_separee,
            'lumineux': lumineux,
            'url': url,
            'desc': desc[:400],
            'title': title
        })
        
        print(f"\n  📋 SeLoger {source_name}: {price}€ | T{pieces} {chambres}ch | {surface}m² | DPE:{dpe}")
        print(f"     Cuisine: {'ouverte ❌' if cuisine_ouverte else 'séparée ✅' if cuisine_separee else 'incertain ❓'}")
        print(f"     Lumineux: {'oui ✅' if lumineux else 'incertain ❓'}")
        print(f"     URL: {url}")
        print(f"     Desc: {desc[:200]}")

# === Dedup against seen file ===
print("\n\n=== DEDUP ===")
seen_file = '/opt/data/cron/output/havre-rental-seen.json'
seen_ids = set()
if os.path.exists(seen_file):
    with open(seen_file) as f:
        seen_data = json.load(f)
        seen_ids = set(seen_data.get('seen_ids', []))
    print(f"Seen file exists with {len(seen_ids)} IDs: {seen_ids}")
else:
    print("No seen file exists yet")

# Collect all new candidate IDs
all_new = []

# From LBC
for l in lbc_candidates:
    if l['id'] not in seen_ids:
        all_new.append({
            'source': 'Leboncoin',
            'id': l['id'],
            'price': l['price'],
            'pieces': l['pieces'],
            'surface': l['surface'],
            'quartier': l['quartier'],
            'loc': l['loc'],
            'flags': l['flags'],
            'url': l['url']
        })
        print(f"  NEW LBC: {l['id']} | {l['price']}€ | {l['pieces']}p | {l['surface']}m² | {l['quartier']} | {l['loc']}")

# From SeLoger - need ID extraction
for s in seloger_listings:
    # Extract ID from URL
    id_m = re.search(r'/(\d+)\.htm', s['url'])
    sid = id_m.group(1) if id_m else s['url']
    if sid not in seen_ids:
        all_new.append({
            'source': 'SeLoger',
            'id': sid,
            'price': s['price'],
            'pieces': s['pieces'],
            'surface': s['surface'],
            'quartier': s['source'],
            'dpe': s['dpe'],
            'cuisine_separee': s['cuisine_separee'],
            'cuisine_ouverte': s['cuisine_ouverte'],
            'lumineux': s['lumineux'],
            'url': s['url'],
            'desc': s['desc'][:200]
        })
        print(f"  NEW SeLoger: {sid} | {s['price']}€ | T{s['pieces']} | {s['surface']}m² | DPE:{s['dpe']} | cuisine:{'séparée' if s['cuisine_separee'] else 'ouverte' if s['cuisine_ouverte'] else 'incertain'}")

print(f"\n\nTotal NEW: {len(all_new)}")

# Save for next step
with open('/opt/data/cache/web/new_candidates.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False, indent=2)