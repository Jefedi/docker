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
        
        # Title from h2
        h2_text = re.sub(r'<[^>]+>', '', content[start:end]).strip()
        h2_text = html.unescape(h2_text)
        h2_text = re.sub(r'\s+', ' ', h2_text)
        
        # Extract listing link
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/\d+pieces/\d+)"', block)
        link = link_match.group(1) if link_match else ''
        lid = link.split('/')[-1] if link else ''
        
        # Extract description text (all text in block)
        desc_text = re.sub(r'<[^>]+>', ' ', block)
        desc_text = html.unescape(desc_text)
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        
        # Extract price - try multiple patterns
        price = None
        # Pattern 1: "XXX € mensuel charges comprises"
        m1 = re.search(r'(\d{3,4})\s*€\s*mensuel', desc_text, re.IGNORECASE)
        if m1:
            price = int(m1.group(1))
        else:
            # Pattern 2: "Loyer charges comprises : XXX euros"
            m2 = re.search(r'[Ll]oyer\s*charges\s*comprises\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
            if m2:
                price = int(m2.group(1))
            else:
                # Pattern 3: "Loyer : XXX Euros" or "Loyer: XXX Euros"
                m3 = re.search(r'[Ll]oyer\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
                if m3:
                    price = int(m3.group(1))
                else:
                    # Pattern 4: "proposé à XXX €" or "pour un loyer de XXX €"
                    m4 = re.search(r'(?:proposé à|pour un loyer de)\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
                    if m4:
                        price = int(m4.group(1))
                    else:
                        # Pattern 5: "Location de particulier XXX €"
                        m5 = re.search(r'Location de particulier\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
                        if m5:
                            price = int(m5.group(1))
                        else:
                            # Pattern 6: "XXX € / mois" where XXX is 100-500 (reasonable rent)
                            for m6 in re.finditer(r'(\d{2,4})\s*€\s*/?\s*mois', desc_text):
                                p = int(m6.group(1))
                                if 100 <= p <= 500:
                                    price = p
                                    break
        
        # Extract pieces from title
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        
        # Extract surface from title
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Determine quartier from description
        quartier = None
        # Known quartiers: Centre-ville, Bléville, Sanvic, etc.
        desc_lower = desc_text.lower()
        if any(kw in desc_lower for kw in ['centre-ville', 'centre ville', 'plein centre', 'coeur du centre', 'coty', 'massillon']):
            quartier = 'Centre-ville'
        elif 'bleville' in desc_lower:
            quartier = 'Bléville'
        elif 'sanvic' in desc_lower:
            quartier = 'Sanvic'
        else:
            # Try to extract from "Quartier XXX"
            q_match = re.search(r'[Qq]uartier\s+(?:de\s+|d[ues]\s+)?([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\-\s]+)', desc_text)
            if q_match:
                q_raw = q_match.group(1).strip()
                # Map known sub-quartiers
                if any(kw in q_raw.lower() for kw in ['danton', 'coty', 'massillon', 'eure', 'saint-françois', 'saint vincent', 'aristide briand', 'franklin', 'lesueur', 'jean-jacques', 'docks', 'gare', 'notre dame', 'saint-nicolas', 'sainte-anne', 'trigauville', 'perret']):
                    quartier = 'Centre-ville'  # Most of these are in or adjacent to centre-ville
                else:
                    quartier = q_raw
        
        # Check for cuisine info
        cuisine_sep = any(kw in desc_lower for kw in ['cuisine indépendante', 'cuisine séparée', 'cuisine indépendant', 'cuisine séparé'])
        cuisine_ouverte = any(kw in desc_lower for kw in ['cuisine ouverte', 'cuisine américaine', 'cuisine équipée ouverte', 'cuisine ouverte sur', 'cuisine aménagée et équipée ouverte', 'pièce de vie ouverte', 'open space', 'loft', 'séjour/cuisine', 'séjour / cuisine', 'cuisine équipée (tv', 'kitchenette'])
        
        # Check for chambre séparée
        chambre_sep = any(kw in desc_lower for kw in ['chambre', 'deux chambres', '2 chambres', 'chambre avec', 'chambre de', 'chambre et', 'chambre,'])
        studio = any(kw in desc_lower for kw in ['studio', 't1 ', 'f1 ', 'f2 meuble', 'pièce de vie', 'séjour/chambre', 'séjour et chambre'])
        
        # Check for luminosity
        lumineux = any(kw in desc_lower for kw in ['lumineux', 'lumineuse', 'luminosité', 'dernier étage', 'belle luminosité', 'très lumineux', 'lumineux et'])
        
        listings.append({
            'id': lid,
            'title': h2_text,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'quartier': quartier,
            'link': f"https://www.le-partenaire.fr{link}" if link else '',
            'cuisine_sep': cuisine_sep,
            'cuisine_ouverte': cuisine_ouverte,
            'chambre_sep': chambre_sep,
            'studio': studio,
            'lumineux': lumineux,
            'desc': desc_text[:800]
        })
    
    return listings

all_listings = []
for p in ['', '_p2', '_p3', '_p4', '_p5', '_p6']:
    filepath = f'/tmp/lp_rent{p}.html'
    if os.path.exists(filepath):
        listings = parse_page(filepath)
        all_listings.extend(listings)

# Deduplicate by ID
seen_ids = set()
unique = []
for l in all_listings:
    if l['id'] and l['id'] not in seen_ids:
        seen_ids.add(l['id'])
        unique.append(l)

print(f"Total unique listings: {len(unique)}")
print()

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_set = set(seen_data.get('seen_ids', []))

# Filter according to criteria:
# 1. T2 minimum (2 pieces+)
# 2. Budget <= 500€
# 3. Quartier: Centre-ville, Bléville, Sanvic only
# 4. Chambre séparée et fermée
# 5. Cuisine séparée
# 6. Surface >= 28m² (realistic minimum)
# 7. Not in seen list

candidates = []
for l in unique:
    # Must have 2+ pieces
    if l['pieces'] is None or l['pieces'] < 2:
        continue
    # Must have a price
    if l['price'] is None or l['price'] > 500:
        continue
    # Must have surface >= 28
    if l['surface'] is not None and l['surface'] < 28:
        continue
    # Must NOT have cuisine ouverte
    if l['cuisine_ouverte'] and not l['cuisine_sep']:
        continue
    # Must have chambre séparée (not a studio)
    if l['studio'] and not l['chambre_sep']:
        continue
    
    # Quartier filter
    q = l['quartier']
    if q and q not in ['Centre-ville', 'Bléville', 'Sanvic']:
        continue
    # If quartier is None, we can't confirm it's in the right area
    # But let's keep them and flag as "quartier non identifié"
    
    # Check if already seen
    lp_id = f"lp-{l['id']}"
    if lp_id in seen_set:
        continue
    
    candidates.append(l)

# Sort by price ascending
candidates.sort(key=lambda x: x['price'] or 999)

print(f"=== {len(candidates)} CANDIDATES (after filtering) ===")
print()

for c in candidates:
    print(f"--- ID: lp-{c['id']} ---")
    print(f"  Title: {c['title']}")
    print(f"  Pieces: {c['pieces']} | Surface: {c['surface']}m² | Price: {c['price']} EUR")
    print(f"  Quartier: {c['quartier']}")
    print(f"  Cuisine séparée: {c['cuisine_sep']} | Cuisine ouverte: {c['cuisine_ouverte']}")
    print(f"  Chambre séparée: {c['chambre_sep']} | Studio: {c['studio']}")
    print(f"  Lumineux: {c['lumineux']}")
    print(f"  Link: {c['link']}")
    print(f"  Desc: {c['desc'][:600]}")
    print()

# Output candidate IDs as JSON for the next step
output = {
    'candidates': [{'id': c['id'], 'lp_id': f"lp-{c['id']}", 'price': c['price'], 'pieces': c['pieces'], 'surface': c['surface'], 'quartier': c['quartier'], 'link': c['link'], 'desc': c['desc']} for c in candidates]
}
with open('/opt/data/cron/output/candidates.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nWrote {len(candidates)} candidates to /opt/data/cron/output/candidates.json")