import re, html as h
import sys, json

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Criteria
# T2+ (2 pièces min), loyer <= 500, surface >= 28m²
# Quartiers: Centre-ville (Coty, Massillon, Eure, Félix Faure, Perret, Docks, Rond-point Observatoire, Saint-François, Danton), Sanvic, Bléville
# Cuisine séparée (PAS cuisine ouverte/américaine/kitchenette)
# Chambre fermée (pas coin nuit/canapé-lit)

ACCEPTED_QUARTIERS = ['centre-ville', 'centre ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure', 
                       'perret', 'docks', 'rond-point', 'rond point', 'observatoire', 'saint-françois', 'saint francois',
                       'danton', 'sanvic', 'bléville', 'dollemard', 'gravière', 'les neiges']

def is_accepted_quartier(desc):
    desc_lower = desc.lower()
    for q in ACCEPTED_QUARTIERS:
        if q in desc_lower:
            return True, q
    return False, None

def has_separate_kitchen(desc):
    desc_lower = desc.lower()
    # Check for separate kitchen indicators
    if any(k in desc_lower for k in ['cuisine indépendante', 'cuisine séparée', 'cuisine séparée', 'cuisine fermée']):
        return True
    if any(k in desc_lower for k in ['cuisine ouverte', 'cuisine américaine', 'kitchenette', 'cuisine ouverte sur séjour', 'coin cuisine']):
        return False
    # If no mention, uncertain
    return None  # Unknown

def has_closed_bedroom(desc):
    desc_lower = desc.lower()
    if any(k in desc_lower for k in ['coin nuit', 'canapé-lit', 'canapé lit', 'canapé convertible', 'séjour/chambre', 'séjour chambre', 'studio']):
        return False
    if any(k in desc_lower for k in ['chambre', 'chambres']):
        return True
    return None

def extract_price(desc):
    # Try various price patterns
    # "Loyer: 480 Euros" or "loyer de 500 €" or "520 €" or "Loyer charges comprises : 520 euros"
    patterns = [
        r'[Ll]oyer[:\s]*(?:charges\s+comprises[:\s]*)?[:\s]*(\d+)\s*(?:€|euros|Euros|EUR)',
        r'(\d+)\s*€\s*(?:/mois|par mois|mensuel|cc|charges comprises)',
        r'proposé à (\d+)\s*€',
        r'loyer de (\d+)\s*€',
        r'(\d+)\s*€\s*mois',
    ]
    for p in patterns:
        m = re.search(p, desc)
        if m:
            return int(m.group(1))
    # Try the card-level price (first € amount in card)
    m = re.search(r'(\d[\d\s\xa0]*\d)\s*€', desc[:500])
    if m:
        price_str = m.group(1).replace('\xa0','').replace(' ','')
        try:
            # Take first number, might be loyer + something
            val = int(price_str)
            if val > 50 and val < 5000:
                return val
        except:
            pass
    return None

def extract_surface(title, desc):
    m = re.search(r'(\d+)\s*m²', title)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s*m²', desc[:500])
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)[,.]?\d*\s*m2', desc[:500])
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

print(f'Total LP listings: {len(all_listings)}')
print()

# Filter
for l in all_listings:
    l['accepted'], l['quartier'] = is_accepted_quartier(l['desc'])
    l['kitchen'] = has_separate_kitchen(l['desc'])
    l['bedroom'] = has_closed_bedroom(l['desc'])
    l['seen'] = l['id'] in seen_ids

# Show T2+ listings (2 pieces or more)
t2_plus = [l for l in all_listings if l['rooms'] and l['rooms'] >= 2]
print(f'T2+ listings: {len(t2_plus)}')
for l in t2_plus:
    print(f'  ID={l["id"]} | {l["title"]} | price={l["price"]} | surface={l["surface"]} | rooms={l["rooms"]} | quartier={l["quartier"]} | kitchen={l["kitchen"]} | bedroom={l["bedroom"]} | seen={l["seen"]}')
    print(f'    URL: {l["url"]}')
    print(f'    DESC: {l["desc"][:300]}')
    print()