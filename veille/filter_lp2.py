import re, html as h
import sys, json

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

ACCEPTED_QUARTIERS = ['centre-ville', 'centre ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure', 
                       'perret', 'docks', 'rond-point', 'rond point', 'observatoire', 'saint-françois', 'saint francois',
                       'danton', 'sanvic', 'bléville', 'bleville', 'dollemard', 'gravière', 'les neiges',
                       'saint-nicolas', 'saint nicolas', 'aristide briand', 'rue de paris', 'franklin',
                       'ingouville', 'lesueur', 'trigauville', 'sarrail', 'bastion', 'anatole france',
                       'sainte-anne', 'sainte anne', 'salvador allende', 'belvédère', 'belvedere',
                       'notre dame', 'saint jacques', 'lemaistre', 'clemenceau', 'grand hameau']

def is_accepted_quartier(desc):
    desc_lower = desc.lower()
    for q in ACCEPTED_QUARTIERS:
        if q in desc_lower:
            return True, q
    # Also check if it mentions generic centre-ville
    if 'centre-ville' in desc_lower or 'centre ville' in desc_lower or 'hyper-centre' in desc_lower:
        return True, 'centre-ville'
    return False, None

def has_separate_kitchen(desc):
    desc_lower = desc.lower()
    if any(k in desc_lower for k in ['cuisine indépendante', 'cuisine séparée', 'cuisine fermée']):
        return True
    if any(k in desc_lower for k in ['cuisine ouverte', 'cuisine américaine', 'kitchenette', 'cuisine ouverte sur', 'coin cuisine']):
        return False
    return None

def has_closed_bedroom(desc):
    desc_lower = desc.lower()
    # Studio = no separate bedroom
    if 'studio' in desc_lower:
        return False
    if any(k in desc_lower for k in ['coin nuit', 'canapé-lit', 'canapé lit', 'canapé convertible', 'séjour/chambre', 'séjour chambre']):
        return False
    if any(k in desc_lower for k in ['chambre', 'chambres']):
        return True
    return None

def extract_price(desc):
    # Try specific patterns first
    patterns = [
        r'[Ll]oyer[:\s]*(?:charges\s+comprises[:\s]*)?[:\s]*(\d+)\s*(?:€|euros|Euros|EUR)',
        r'(?:proposé à|pour un loyer de)\s*(\d+)\s*€',
        r'(\d+)\s*€\s*(?:par mois|/mois|mensuel|cc|charges comprises)',
        r'loyer de (\d+)\s*€',
    ]
    for p in patterns:
        m = re.search(p, desc)
        if m:
            val = int(m.group(1))
            if 100 <= val <= 5000:
                return val
    return None

def extract_surface(title, desc):
    m = re.search(r'(\d+)\s*m²', title)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)[,.]?\d*\s*m2\b', desc[:1000])
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)[,.]?\d*\s*m²', desc[:1000])
    if m:
        return int(m.group(1))
    return None

def extract_rooms(title, desc):
    m = re.search(r'(\d+)\s*pièce', title)
    if m:
        return int(m.group(1))
    m = re.search(r'[TtFf](\d+)\b', title)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s*pièce', desc[:500])
    if m:
        return int(m.group(1))
    return None

def parse_lp_full(fname):
    html_content = open(fname).read()
    h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', html_content)]
    valid_positions = []
    for pos in h2_positions:
        end = html_content.find('</h2>', pos)
        if end > 0:
            h2_text = html_content[pos:end+5]
            if 'Location Appartement' in h2_text:
                valid_positions.append(pos)
    
    listings = []
    for i, pos in enumerate(valid_positions):
        end_pos = valid_positions[i+1] if i+1 < len(valid_positions) else len(html_content)
        b = html_content[pos:end_pos]
        
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', b, re.DOTALL)
        title = re.sub(r'<[^>]+>', ' ', h2.group(1)).strip() if h2 else ''
        title = h.unescape(re.sub(r'\s+', ' ', title))
        
        link_m = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', b)
        link = 'https://www.le-partenaire.fr' + link_m.group(1) if link_m else ''
        lid = 'lp-' + link_m.group(1).split('/')[-1] if link_m else ''
        
        text = re.sub(r'<[^>]+>', ' ', b[:8000])
        text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
        
        rooms = extract_rooms(title, text)
        surface = extract_surface(title, text)
        price = extract_price(text)
        
        listings.append({
            'id': lid,
            'title': title,
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'desc': text,
            'url': link,
            'source': 'le-partenaire'
        })
    return listings

# Parse all Le-Partenaire pages
all_listings = []
for p in [1,2,3,4,5,6]:
    fname = f'/tmp/veille/lp{p}.html'
    try:
        all_listings.extend(parse_lp_full(fname))
    except Exception as e:
        print(f'Error parsing lp{p}: {e}', file=sys.stderr)

# Deduplicate by ID
seen_ids_local = set()
unique_listings = []
for l in all_listings:
    if l['id'] not in seen_ids_local:
        seen_ids_local.add(l['id'])
        unique_listings.append(l)

print(f'Total unique LP listings: {len(unique_listings)}')

# Filter: T2+ (2 pieces min), loyer <= 500, surface >= 28m²
# Note: some prices show 0 due to regex matching issue, need to re-check
candidates = []
for l in unique_listings:
    rooms = l['rooms']
    surface = l['surface']
    price = l['price']
    
    # Must be T2+ (2 pièces minimum)
    if not rooms or rooms < 2:
        continue
    
    # Must have surface >= 28m²
    if not surface or surface < 28:
        continue
    
    # Check quartier
    accepted, quartier = is_accepted_quartier(l['desc'])
    
    # Check cuisine and chambre
    kitchen = has_separate_kitchen(l['desc'])
    bedroom = has_closed_bedroom(l['desc'])
    
    # Skip if clearly has open kitchen (cuisine ouverte = reject)
    if kitchen is False:
        continue
    
    # Skip if clearly no closed bedroom (studio/coin nuit/canapé-lit)
    if bedroom is False:
        continue
    
    # Price check - must be <= 500
    # Some prices are None because regex failed. Let's try harder.
    if price is None or price == 0 or price > 5000:
        # Try to find the price in the description more aggressively
        desc = l['desc']
        # Look for "Loyer: XXX euros" or "XXX € par mois" or "proposé à XXX €"
        for p in [r'(\d+)\s*€\s*(?:par mois|/mois|mensuel|cc|charges comprises)',
                  r'loyer[:\s]*(\d+)\s*(?:€|euros|EUR)',
                  r'proposé à (\d+)\s*€',
                  r'pour un loyer de (\d+)\s*€',
                  r'(\d+)\s*€\s*mois']:
            m = re.search(p, desc, re.IGNORECASE)
            if m:
                price = int(m.group(1))
                break
    
    # If price still unknown or > 500, skip
    if price is None or price > 500:
        # But if price is unknown and we can't determine, we should still note it
        # For now skip if clearly > 500
        if price and price > 500:
            continue
        # If price unknown, mark as uncertain but include if other criteria match
        # Actually, let's be more lenient - if we can't find price, include it as uncertain
    
    candidates.append({
        **l,
        'price': price,
        'quartier': quartier,
        'kitchen': kitchen,
        'bedroom': bedroom,
        'already_seen': l['id'] in seen_ids
    })

print(f'\nCandidates after filter (T2+, >=28m², quartier accepted or unknown, cuisine OK, chambre OK):')
print(f'Total: {len(candidates)}')
print()

new_candidates = [c for c in candidates if not c['already_seen']]
seen_candidates = [c for c in candidates if c['already_seen']]

print(f'Already seen: {len(seen_candidates)}')
print(f'NEW: {len(new_candidates)}')
print()

for c in new_candidates:
    print(f'NEW: ID={c["id"]} | {c["title"]} | price={c["price"]} | surface={c["surface"]} | rooms={c["rooms"]} | quartier={c["quartier"]} | kitchen={c["kitchen"]} | bedroom={c["bedroom"]}')
    print(f'  URL: {c["url"]}')
    print(f'  DESC: {c["desc"][:400]}')
    print()

# Also show seen candidates that match (for verification)
print('\n--- SEEN candidates (for reference) ---')
for c in seen_candidates:
    print(f'SEEN: ID={c["id"]} | price={c["price"]} | surface={c["surface"]} | quartier={c["quartier"]} | kitchen={c["kitchen"]} | bedroom={c["bedroom"]}')