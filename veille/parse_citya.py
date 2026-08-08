import re, html as h
import json, sys

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
    if 'studio' in desc_lower:
        return False
    if any(k in desc_lower for k in ['coin nuit', 'canapé-lit', 'canapé lit', 'canapé convertible', 'séjour/chambre', 'séjour chambre']):
        return False
    if any(k in desc_lower for k in ['chambre', 'chambres']):
        return True
    return None

def parse_citya(fname):
    html_content = open(fname).read()
    cards = re.split(r'class="property-card', html_content)
    listings = []
    for c in cards[1:]:
        # data-itemId, data-itemName, data-price
        id_m = re.search(r'data-itemId="([^"]+)"', c)
        name_m = re.search(r'data-itemName="([^"]+)"', c)
        price_m = re.search(r'data-price="([^"]+)"', c)
        
        item_id = id_m.group(1) if id_m else ''
        name = name_m.group(1) if name_m else ''
        price = int(price_m.group(1)) if price_m else None
        
        # Extract text from the card
        text = re.sub(r'<[^>]+>', ' ', c[:4000])
        text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
        
        # Extract rooms and surface from name: "Appartement 2 pièces 53.35m²"
        rooms_m = re.search(r'(\d+)\s*pièce', name)
        rooms = int(rooms_m.group(1)) if rooms_m else None
        surface_m = re.search(r'([\d.]+)m', name)
        surface = int(float(surface_m.group(1))) if surface_m else None
        
        # Find link
        link_m = re.search(r'href="(https://www\.citya\.com/annonces/location/[^"]+)"', c)
        if not link_m:
            link_m = re.search(r'href="(/annonces/location/[^"]+)"', c)
        link = link_m.group(1) if link_m else ''
        if link and not link.startswith('http'):
            link = 'https://www.citya.com' + link
        
        lid = 'citya-' + item_id if item_id else ''
        
        listings.append({
            'id': lid,
            'title': name,
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'desc': text,
            'url': link,
            'source': 'citya'
        })
    return listings

all_citya = []
for f in ['citya.html', 'citya2.html', 'citya3.html']:
    try:
        all_citya.extend(parse_citya(f'/tmp/veille/{f}'))
    except Exception as e:
        print(f'Error {f}: {e}', file=sys.stderr)

# Deduplicate
seen_local = set()
unique = []
for l in all_citya:
    if l['id'] not in seen_local:
        seen_local.add(l['id'])
        unique.append(l)

print(f'Citya total unique: {len(unique)}')

# Filter: T2+, <=500€, >=28m²
for l in unique:
    rooms = l['rooms']
    surface = l['surface']
    price = l['price']
    
    if not rooms or rooms < 2:
        continue
    if not surface or surface < 28:
        continue
    if not price or price > 500:
        continue
    
    accepted, quartier = is_accepted_quartier(l['desc'])
    kitchen = has_separate_kitchen(l['desc'])
    bedroom = has_closed_bedroom(l['desc'])
    
    if kitchen is False:
        continue
    if bedroom is False:
        continue
    
    already_seen = l['id'] in seen_ids
    status = 'SEEN' if already_seen else 'NEW'
    
    print(f'{status}: ID={l["id"]} | {l["title"]} | price={price}€ | surface={surface}m² | rooms={rooms} | quartier={quartier} | kitchen={kitchen} | bedroom={bedroom}')
    print(f'  URL: {l["url"]}')
    print(f'  DESC: {l["desc"][:300]}')
    print()