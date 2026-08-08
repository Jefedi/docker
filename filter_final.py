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
        
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Comprehensive price extraction
        price = None
        desc_lower = desc_text.lower()
        
        # Pattern 1: "XXX € mensuel charges comprises"
        m = re.search(r'(\d{3,4})\s*€\s*mensuel', desc_text, re.IGNORECASE)
        if m: price = int(m.group(1))
        if not price:
            m = re.search(r'[Ll]oyer\s*charges\s*comprises\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'pour un loyer de\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'proposé à\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'Location de particulier\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'[Ll]oyer\s*:?\s*(\d{3,4})\s*[e€E]', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'(\d{3,4})\s*[e€E]+\s*par\s*mois', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            # "Loyer charges incluses XXX €"
            m = re.search(r'loyer\s*charges\s*incluses?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            # "XXX euros HC" + "YYY euros de charges" 
            m_hc = re.search(r'(\d{3,4})\s*[e€E]+\s*HC', desc_text, re.IGNORECASE)
            m_ch = re.search(r'(\d{2,3})\s*[e€E]+\s*de\s*charges', desc_text, re.IGNORECASE)
            if m_hc:
                hc = int(m_hc.group(1))
                ch = int(m_ch.group(1)) if m_ch else 0
                price = hc + ch
        
        # Detect colocation
        is_colocation = any(kw in desc_lower for kw in ['colocation', 'colocataire', 'coloc ', 'chambre accès privée', 'par chambre', 'chacun pourra', 'chambre à louer', 'colocation possible', 'colocation accept'])
        
        # Detect cuisine ouverte
        cuisine_ouverte = any(kw in desc_lower for kw in ['cuisine ouverte', 'cuisine américaine', 'cuisine aménagée et équipée ouverte', 'cuisine aménagée ouverte', 'séjour/cuisine', 'séjour / cuisine', 'séjour avec cuisine'])
        
        # Detect cuisine séparée
        cuisine_sep = any(kw in desc_lower for kw in ['cuisine indépendante', 'cuisine séparée', 'cuisine indépendant', 'cuisine séparé'])
        # "grande cuisine / salle à manger indépendante" = cuisine séparée
        if 'cuisine' in desc_lower and 'indépendante' in desc_lower:
            cuisine_sep = True
            cuisine_ouverte = False
        
        # Detect chambre fermée (not studio, not coin nuit in living room)
        has_chambre_sep = bool(re.search(r'chambre\b', desc_lower))
        
        # Detect lumineux
        lumineux = any(kw in desc_lower for kw in ['lumineux', 'lumineuse', 'luminosité', 'dernier étage', 'belle luminosité'])
        
        # Detect quartier
        quartier = None
        if any(kw in desc_lower for kw in ['centre-ville', 'centre ville', 'plein centre', 'coeur du centre', 'coty', 'massillon', 'rue franklin', 'rue lesueur', 'aristide briand', 'rue d\'ingouville', 'jean-jacques rousseau', 'notre dame', 'saint-françois', 'saint-nicolas', 'docks', 'gare', 'trigauville', 'perret', 'bastion', 'saint-vincent', 'sainte-anne', 'anatole france', 'boieldieu', 'guillemard', 'rue de paris', 'sarrail', 'grand hameau', 'cathédrale', 'salvador allende', 'bléville', 'bleville', 'sanvic', 'rue du général', 'rue de belfort']):
            # These are all in Centre-ville or adjacent
            if 'bleville' in desc_lower:
                quartier = 'Bléville'
            elif 'sanvic' in desc_lower:
                quartier = 'Sanvic'
            else:
                quartier = 'Centre-ville'
        
        listings.append({
            'id': lid, 'pieces': pieces, 'surface': surface, 'price': price,
            'link': f"https://www.le-partenaire.fr{link}" if link else '',
            'desc': desc_text[:1500],
            'is_colocation': is_colocation,
            'cuisine_sep': cuisine_sep,
            'cuisine_ouverte': cuisine_ouverte,
            'has_chambre_sep': has_chambre_sep,
            'quartier': quartier,
            'lumineux': lumineux,
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

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_set = set(seen_data.get('seen_ids', []))

# Filter strictly:
# T2+, price <= 500, surface >= 28, not colocation, not cuisine ouverte, has chambre
# Quartier: Centre-ville, Bléville, Sanvic only
candidates = []
for l in unique:
    if not l['pieces'] or l['pieces'] < 2:
        continue
    if not l['price'] or l['price'] > 500:
        continue
    if l['surface'] and l['surface'] < 28:
        continue
    if l['is_colocation']:
        continue
    if l['cuisine_ouverte'] and not l['cuisine_sep']:
        continue
    if not l['has_chambre_sep']:
        continue
    # Quartier filter: only Centre-ville, Bléville, Sanvic
    # If quartier is None, we can't confirm - skip it (strict filter)
    # But many good listings don't mention quartier explicitly
    # Let's be strict: require quartier match or at least not in a known non-matching quartier
    if l['quartier'] and l['quartier'] not in ['Centre-ville', 'Bléville', 'Sanvic']:
        continue
    # If quartier is None, check if description mentions a known non-matching area
    desc_lower = l['desc'].lower()
    non_matching_areas = ['bléville', 'bleville', 'sanvic', 'caucriauville', 'ormes', 'rouelles', 'dollemard', 'bapeaume', 'mare-rouge', 'mares rouges', 'acacias', 'arbres', 'vallée', 'bois', 'deculseux', 'fontaine', 'graville', 'malraux']
    in_wrong_area = False
    for area in non_matching_areas:
        if area in desc_lower:
            in_wrong_area = True
            break
    if in_wrong_area:
        continue
    
    lp_id = f"lp-{l['id']}"
    is_new = lp_id not in seen_set
    
    candidates.append({**l, 'is_new': is_new, 'lp_id': lp_id})

candidates.sort(key=lambda x: x['price'])

# Separate new vs seen
new_candidates = [c for c in candidates if c['is_new']]
seen_candidates = [c for c in candidates if not c['is_new']]

print(f"=== TOTAL CANDIDATES: {len(candidates)} ({len(new_candidates)} NEW, {len(seen_candidates)} SEEN) ===\n")

for c in candidates:
    status = "🆕 NEW" if c['is_new'] else "✅ SEEN"
    print(f"{status} | ID: {c['lp_id']} | T{c['pieces']} | {c['surface']}m² | {c['price']}€")
    print(f"  Quartier: {c['quartier']}")
    print(f"  Cuisine sep: {c['cuisine_sep']} | Cuisine ouverte: {c['cuisine_ouverte']}")
    print(f"  Colocation: {c['is_colocation']} | Chambre: {c['has_chambre_sep']} | Lumineux: {c['lumineux']}")
    print(f"  Link: {c['link']}")
    print(f"  Desc: {c['desc'][:500]}")
    print()

# Output new candidate IDs
if new_candidates:
    print(f"\n=== {len(new_candidates)} NEW CANDIDATES ===")
    for c in new_candidates:
        print(f"  {c['lp_id']}: T{c['pieces']} {c['surface']}m² {c['price']}€ - {c['link']}")