#!/usr/bin/env python3
"""Filter all rental listings by strict criteria and deduplicate against seen file."""
import re
import json
import os
from html import unescape

BASE_DIR = "/opt/data/cron/tmp/havre_rental"
SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

# Load seen IDs
with open(SEEN_FILE, 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))
print(f"Loaded {len(seen_ids)} seen IDs")

# Load all listings from v3 parser
with open(os.path.join(BASE_DIR, "all_listings_v3.json"), 'r') as f:
    all_listings = json.load(f)

# Also parse Le-Partenaire page 2 and add to listings
def strip_tags(html_str):
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

with open(os.path.join(BASE_DIR, 'lp_page2.html'), 'r', errors='replace') as f:
    html = f.read()

h2_iter = [(m.start(), m.group(1)) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)]
for h2_pos, h2_content in h2_iter:
    title_text = strip_tags(h2_content)
    block_end = min(len(html), h2_pos + 3000)
    block = html[h2_pos:block_end]
    block_clean = re.sub(r'<[^>]+>', '\n', block)
    block_clean = block_clean.replace('&nbsp;', ' ')
    block_clean = unescape(block_clean)
    
    price_match = re.search(r'(\d[\d ]*)\s*€\s*(?:/|\\)?\s*mois', block_clean)
    price = int(price_match.group(1).replace(' ', '')) if price_match else None
    
    surface_match = re.search(r'(\d+)\s*m[²2]', title_text)
    surface = int(surface_match.group(1)) if surface_match else None
    
    rooms_match = re.search(r'(\d+)\s*pi[eè]ce', title_text)
    rooms = int(rooms_match.group(1)) if rooms_match else None
    
    desc_lines = [l.strip() for l in block_clean.split('\n') if l.strip()]
    desc_text = ' '.join(desc_lines[:20])
    desc_text = re.sub(r'\s+', ' ', desc_text)
    
    all_links = re.finditer(r'href="(/immobilier/location/appartement/[^"]*?/(\d+))"', html[h2_pos:h2_pos+5000])
    listing_id = None
    listing_url = None
    for m in all_links:
        listing_id = m.group(2)
        listing_url = f"https://www.le-partenaire.fr{m.group(1)}"
        break
    
    if listing_id:
        all_listings.append({
            'source': 'lp',
            'id': f"lp-{listing_id}",
            'title': title_text,
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': listing_url or '',
            'description': desc_text[:600]
        })

print(f"Total listings after adding LP page 2: {len(all_listings)}")

# Accepted quartiers (Leboncoin sub-labels mapped to official names)
ACCEPTED_QUARTIERS = {
    'centre-ville', 'centre ville', 'coty', 'massillon', 'eure', 'felix faure',
    'perret', 'docks', 'rond-point', 'observatoire', 'saint-francois', 'danton',
    'sanvic', 'bleville', 'dollemard', 'ormeaux', 'cote ouest', 'saint-nicolas',
    'saint-vincent', 'demidoff', 'mazeline', 'anatole france', 'marechal joffre',
    'universite', 'docks vauban', 'graville', 'aplemont'
}

# Quartiers NOT accepted (outside the target areas)
EXCLUDED_QUARTIERS = {
    'caucriauville', 'rouelles', 'bapeaume', 'blangorval', 'la blactere',
    'harfleur', 'montivilliers', 'sainte-adresse'
}

def check_quartier(desc, title):
    """Check if the listing is in an accepted quartier."""
    text = (desc + ' ' + title).lower()
    
    # Check excluded quartiers first
    for q in EXCLUDED_QUARTIERS:
        if q in text:
            return False, q
    
    # Check accepted quartiers
    for q in ACCEPTED_QUARTIERS:
        if q in text:
            return True, q
    
    # If no quartier mentioned, accept by default (will be manually verified)
    return True, 'non-spécifié'

def check_cuisine_separee(desc):
    """Check if the listing mentions cuisine séparée (not open/américaine/kitchenette)."""
    text = desc.lower()
    
    # Explicit mentions of cuisine séparée
    if 'cuisine séparée' in text or 'cuisine separee' in text or 'cuisine indépendante' in text or 'cuisine independante' in text:
        return True, 'cuisine séparée'
    
    # Check for cuisine ouverte/américaine/kitchenette (excluded)
    if 'cuisine ouverte' in text or 'cuisine américaine' in text or 'cuisine americaine' in text:
        return False, 'cuisine ouverte/américaine'
    if 'kitchenette' in text:
        return False, 'kitchenette'
    if 'coin cuisine' in text:
        return False, 'coin cuisine'
    
    # If no mention of cuisine type, mark as unknown
    return None, 'non-spécifié'

def check_chambre_fermee(desc, rooms):
    """Check if the listing mentions chambre fermée (not coin nuit/canapé-lit)."""
    text = desc.lower()
    
    # Excluded: coin nuit, canapé-lit, chambre en colocation
    if 'coin nuit' in text or 'canapé-lit' in text or 'canape lit' in text or 'canape-lit' in text:
        return False, 'coin nuit/canapé-lit'
    if 'chambre en colocation' in text or 'colocation' in text:
        return False, 'colocation'
    
    # Check for chambre
    if 'chambre' in text:
        if 'chambre fermée' in text or 'chambre fermee' in text:
            return True, 'chambre fermée'
        if 'chambre' in text and rooms and rooms >= 2:
            # For T2+, having a "chambre" usually means a separate bedroom
            return True, 'chambre mentionnée'
    
    # For T2+ properties, it's reasonable to assume a separate bedroom exists
    if rooms and rooms >= 2:
        return True, 'implicite (T2+)'
    
    return None, 'non-spécifié'

def check_lumineux(desc):
    """Check if the listing mentions luminosity features."""
    text = desc.lower()
    features = []
    
    if 'lumineux' in text or 'lumineuse' in text:
        features.append('lumineux')
    if 'dernier étage' in text or 'dernier etage' in text:
        features.append('dernier étage')
    if 'balcon' in text:
        features.append('balcon')
    if 'terrasse' in text:
        features.append('terrasse')
    if 'traversant' in text:
        features.append('traversant')
    if 'exposition' in text:
        features.append('exposition')
    if 'vue mer' in text:
        features.append('vue mer')
    if 'ascenseur' in text:
        features.append('ascenseur')
    
    return features

# Filter listings
qualified = []
rejected_reasons = {}

for listing in all_listings:
    lid = listing['id']
    price = listing.get('price')
    surface = listing.get('surface')
    rooms = listing.get('rooms')
    desc = listing.get('description', '')
    title = listing.get('title', '')
    
    # Skip non-apartments (garages, parkings, commercial)
    desc_lower = desc.lower()
    title_lower = title.lower()
    if any(kw in desc_lower or kw in title_lower for kw in ['garage', 'parking', 'stationnement', 'local commercial', 'local professionnel', 'immobilier pro']):
        rejected_reasons[lid] = 'garage/parking/commercial'
        continue
    
    # Skip colocation/chambre
    if 'colocation' in desc_lower or 'chambre en colocation' in desc_lower:
        rejected_reasons[lid] = 'colocation'
        continue
    if 'chambre dans' in desc_lower and 'appartement' in desc_lower:
        rejected_reasons[lid] = 'chambre dans appartement'
        continue
    
    # Filter: T2+ (2 rooms minimum)
    if rooms is not None and rooms < 2:
        rejected_reasons[lid] = f'T{rooms} (studio)'
        continue
    
    # Filter: price ≤ 500€
    if price is not None and price > 500:
        rejected_reasons[lid] = f'prix {price}€ > 500€'
        continue
    
    # Filter: surface ≥ 28m²
    if surface is not None and surface < 28:
        rejected_reasons[lid] = f'surface {surface}m² < 28m²'
        continue
    
    # If we don't have rooms info, try to infer from title
    if rooms is None:
        # Try to extract from title/description
        t_match = re.search(r'T(\d+)', title + ' ' + desc)
        if t_match:
            rooms = int(t_match.group(1))
            listing['rooms'] = rooms
        f_match = re.search(r'(?:type\s+)?F(\d+)', title + ' ' + desc, re.I)
        if f_match and rooms is None:
            rooms = int(f_match.group(1))
            listing['rooms'] = rooms
        p_match = re.search(r'(\d+)\s*pi[eè]ces?', title + ' ' + desc)
        if p_match and rooms is None:
            rooms = int(p_match.group(1))
            listing['rooms'] = rooms
        
        if rooms is not None and rooms < 2:
            rejected_reasons[lid] = f'T{rooms} (inferred)'
            continue
    
    # Check quartier
    quartier_ok, quartier_name = check_quartier(desc, title)
    if not quartier_ok:
        rejected_reasons[lid] = f'quartier exclu: {quartier_name}'
        continue
    
    # Check cuisine
    cuisine_ok, cuisine_info = check_cuisine_separee(desc)
    if cuisine_ok is False:
        rejected_reasons[lid] = f'cuisine: {cuisine_info}'
        continue
    
    # Check chambre
    chambre_ok, chambre_info = check_chambre_fermee(desc, rooms)
    if chambre_ok is False:
        rejected_reasons[lid] = f'chambre: {chambre_info}'
        continue
    
    # Check luminosity
    lumineux_features = check_lumineux(desc)
    
    # For listings with missing price/surface/rooms, include them but flag
    # They may be relevant if we can verify manually
    
    listing['quartier'] = quartier_name
    listing['cuisine_info'] = cuisine_info
    listing['chambre_info'] = chambre_info
    listing['lumineux_features'] = lumineux_features
    
    # Check if already seen
    is_new = lid not in seen_ids
    listing['is_new'] = is_new
    
    qualified.append(listing)

print(f"\n=== FILTERING RESULTS ===")
print(f"Total parsed: {len(all_listings)}")
print(f"Qualified: {len(qualified)}")
print(f"Rejected: {len(rejected_reasons)}")
print(f"New (not seen): {sum(1 for q in qualified if q['is_new'])}")
print(f"Already seen: {sum(1 for q in qualified if not q['is_new'])}")

print(f"\n=== REJECTED REASONS ===")
reason_counts = {}
for lid, reason in rejected_reasons.items():
    # Simplify reason
    simple = reason.split(':')[0].split('(')[0].strip()
    reason_counts[simple] = reason_counts.get(simple, 0) + 1
for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
    print(f"  {reason}: {count}")

print(f"\n=== QUALIFIED LISTINGS ===")
for q in qualified:
    status = "🆕 NEW" if q['is_new'] else "✓ seen"
    print(f"\n  {status} {q['id']}")
    print(f"  Source: {q['source']}")
    print(f"  Price: {q.get('price')}€ | Surface: {q.get('surface')}m² | Rooms: {q.get('rooms')}")
    print(f"  Quartier: {q.get('quartier')}")
    print(f"  Cuisine: {q.get('cuisine_info')}")
    print(f"  Chambre: {q.get('chambre_info')}")
    print(f"  Lumineux: {', '.join(q.get('lumineux_features', []))}")
    print(f"  URL: {q.get('url')}")
    print(f"  Desc: {q.get('description', '')[:300]}")

# Save qualified listings
output_path = os.path.join(BASE_DIR, "qualified_listings.json")
with open(output_path, 'w') as f:
    json.dump(qualified, f, indent=2, ensure_ascii=False)
print(f"\nSaved qualified listings to {output_path}")

# Get new qualified listings for notification
new_qualified = [q for q in qualified if q['is_new']]
print(f"\n=== NEW QUALIFIED LISTINGS FOR NOTIFICATION: {len(new_qualified)} ===")
for q in new_qualified:
    print(f"  {q['id']}: {q.get('price')}€ | {q.get('surface')}m² | {q.get('rooms')}p | {q.get('quartier')}")

# Save new qualified for the notification step
new_path = os.path.join(BASE_DIR, "new_qualified.json")
with open(new_path, 'w') as f:
    json.dump(new_qualified, f, indent=2, ensure_ascii=False)