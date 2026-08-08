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
        
        # Try ALL price patterns
        price = None
        # Pattern: "XXX € mensuel charges comprises"
        m = re.search(r'(\d{3,4})\s*€\s*mensuel', desc_text, re.IGNORECASE)
        if m: price = int(m.group(1))
        if not price:
            m = re.search(r'[Ll]oyer\s*charges\s*comprises\s*:?\s*(\d{3,4})\s*[e€]', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'[Ll]oyer\s*:?\s*(\d{3,4})\s*[e€E]', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'(?:proposé à|pour un loyer de)\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'Location de particulier\s*(\d{3,4})\s*€', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            m = re.search(r'(\d{3,4})\s*[e€]\s*par\s*mois', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            # Look for "Loyer: XXX Euros"
            m = re.search(r'[Ll]oyer\s*:?\s*(\d{3,4})\s*Euros', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            # Pattern: "à XXX €/mois" or "à XXX€ / mois" with reasonable range
            for m in re.finditer(r'(\d{3,4})\s*€\s*/?\s*mois', desc_text):
                p = int(m.group(1))
                if 100 <= p <= 500:
                    price = p
                    break
        if not price:
            # Pattern: "XXX € CC" or "XXX euros CC"  
            m = re.search(r'(\d{3,4})\s*[e€E]+\s*CC', desc_text, re.IGNORECASE)
            if m: price = int(m.group(1))
        if not price:
            # "XXX euros HC" + "YYY euros de charges" -> total = XXX + YYY
            m_hc = re.search(r'(\d{3,4})\s*[e€E]+\s*HC', desc_text, re.IGNORECASE)
            m_ch = re.search(r'(\d{2,3})\s*[e€E]+\s*de\s*charges', desc_text, re.IGNORECASE)
            if m_hc:
                hc = int(m_hc.group(1))
                ch = int(m_ch.group(1)) if m_ch else 0
                price = hc + ch
        
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Check colocation
        desc_lower = desc_text.lower()
        is_colocation = any(kw in desc_lower for kw in ['colocation', 'colocataire', 'chambre accès privée', 'par chambre', 'chacun pourra avoir son propre bail', 'coloc '])
        
        # Check cuisine
        cuisine_sep = any(kw in desc_lower for kw in ['cuisine indépendante', 'cuisine séparée', 'cuisine indépendant'])
        cuisine_ouverte = any(kw in desc_lower for kw in ['cuisine ouverte', 'cuisine américaine', 'cuisine équipée ouverte', 'cuisine aménagée et équipée ouverte', 'cuisine aménagée et équipée ouverte sur', 'séjour/cuisine', 'séjour / cuisine', 'cuisine / salle à manger'])
        
        # Fix: "grande cuisine / salle à manger indépendante" should be cuisine_sep, not cuisine_ouverte
        if 'cuisine' in desc_lower and 'indépendante' in desc_lower:
            cuisine_sep = True
            cuisine_ouverte = False
        
        # Check chambre
        has_chambre = bool(re.search(r'chambre', desc_lower))
        has_coin_nuit = any(kw in desc_lower for kw in ['coin nuit', 'coin bureau', 'coin chambre', 'séjour/chambre', 'pièce de vie'])
        
        # Check quartier
        quartier = None
        if any(kw in desc_lower for kw in ['centre-ville', 'centre ville', 'plein centre', 'coeur du centre', 'centre commercial coty', 'coty', 'massillon', 'rue franklin', 'rue lesueur', 'aristide briand', 'rue d\'ingouville', 'jean-jacques rousseau', 'notre dame', 'saint-françois', 'saint-nicolas', 'docks', 'gare', 'trigauville', 'perret', 'bastion', 'saint-vincent', 'sainte-anne', 'anatole france', 'boieldieu', 'guillemard']):
            quartier = 'Centre-ville'
        if 'bleville' in desc_lower:
            quartier = 'Bléville'
        if 'sanvic' in desc_lower:
            quartier = 'Sanvic'
        
        # Check lumineux
        lumineux = any(kw in desc_lower for kw in ['lumineux', 'lumineuse', 'luminosité', 'dernier étage', 'belle luminosité'])
        
        listings.append({
            'id': lid, 'pieces': pieces, 'surface': surface, 'price': price,
            'link': f"https://www.le-partenaire.fr{link}" if link else '',
            'desc': desc_text[:1500],
            'is_colocation': is_colocation,
            'cuisine_sep': cuisine_sep,
            'cuisine_ouverte': cuisine_ouverte,
            'has_chambre': has_chambre,
            'has_coin_nuit': has_coin_nuit,
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

# Filter: T2+, price <= 500, surface >= 28 (or None), not colocation, not cuisine ouverte
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
    # Must have chambre mention (separate bedroom)
    if not l['has_chambre']:
        continue
    candidates.append(l)

candidates.sort(key=lambda x: x['price'])

print(f"=== {len(candidates)} CANDIDATES after strict filter ===\n")

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_set = set(seen_data.get('seen_ids', []))

new_candidates = []
for c in candidates:
    lp_id = f"lp-{c['id']}"
    is_new = lp_id not in seen_set
    status = "🆕 NEW" if is_new else "✅ SEEN"
    print(f"{status} | ID: {c['id']} | T{c['pieces']} | {c['surface']}m² | {c['price']}€")
    print(f"  Quartier: {c['quartier']}")
    print(f"  Cuisine sep: {c['cuisine_sep']} | Cuisine ouverte: {c['cuisine_ouverte']}")
    print(f"  Colocation: {c['is_colocation']} | Chambre: {c['has_chambre']} | Lumineux: {c['lumineux']}")
    print(f"  Link: {c['link']}")
    print(f"  Desc: {c['desc'][:600]}")
    print()
    if is_new:
        new_candidates.append(c)

print(f"\n=== {len(new_candidates)} NEW candidates ===")
for c in new_candidates:
    print(f"  lp-{c['id']}: T{c['pieces']} {c['surface']}m² {c['price']}€")