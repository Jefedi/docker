#!/usr/bin/env python3
"""Final parser: extract all Le Havre rental listings, filter by criteria, dedup, report new ones."""
import re, json, os
from html import unescape

HAVRE_DIR = "/opt/data/tmp/havre"

with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))
print(f"Loaded {len(seen_ids)} seen IDs\n")

def read_file(name):
    path = os.path.join(HAVRE_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

def clean(text):
    text = unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

# Quartiers acceptés et leurs alias
ACCEPTED_QUARTIERS = [
    'centre-ville', 'centre ville', 'coty', 'massillon', 'eure', 'felix faure',
    'fél ix faure', 'perret', 'docks', 'rond-point', 'rond point', 'observatoire',
    'saint-françois', 'saint françois', 'danton', 'sanvic', 'bleville', 'bléville',
    'saint-vincent', 'saint vincent', 'dollemard', 'universite', 'université',
    'graville', ' saint-nicolas', 'arceaux', 'brindeau'
]

all_listings = []

# ============================================
# 1. LE-PARTENAIRE (pages 1 and 2)
# ============================================
def parse_le_partenaire(filename, page_num):
    content = read_file(filename)
    listings = []
    h2_pattern = list(re.finditer(r'<h2[^>]*class="card-title[^"]*"[^>]*>(.*?)</h2>', content, re.DOTALL))
    
    for i, h2_match in enumerate(h2_pattern):
        h2_text = clean(h2_match.group(1))
        pieces_m = re.search(r'(\d+)\s*pi[èc]ce', h2_text)
        surface_m = re.search(r'(\d+)\s*m²', h2_text)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        surface = int(surface_m.group(1)) if surface_m else 0
        
        h2_pos = h2_match.start()
        block = content[h2_pos:h2_pos+5000]
        
        # Price: <span class="prix">XXX&nbsp;€</span>
        price_m = re.search(r'<span class="prix">(\d+)\s*&?nbsp;\s*€</span>', block)
        if not price_m:
            price_m = re.search(r'Loyer:\s*(\d+)\s*Euros', block)
        price = int(price_m.group(1)) if price_m else 0
        
        # href
        href_m = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', block)
        href = href_m.group(1) if href_m else ""
        
        # ID
        id_m = re.search(r'/(\d+)$', href)
        list_id = f"lp-{id_m.group(1)}" if id_m else ""
        
        # Description
        desc_m = re.search(r'<p class="card-text crop-text-4"[^>]*>(.*?)</p>', block, re.DOTALL)
        desc = clean(desc_m.group(1)) if desc_m else ""
        
        if list_id:
            listings.append({
                'id': list_id,
                'pieces': pieces,
                'surface': surface,
                'price': price,
                'href': f"https://www.le-partenaire.fr{href}" if href else "",
                'desc': desc,
                'source': 'le-partenaire'
            })
    return listings

# ============================================
# 2. ORPI (JSON-LD, pages 1-3)
# ============================================
def parse_orpi(filename):
    content = read_file(filename)
    listings = []
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in json_ld:
        try:
            data = json.loads(block.strip())
            if 'itemListElement' not in data:
                continue
            for item in data['itemListElement']:
                url = item.get('url', '')
                offers = item.get('item', {}).get('offers', {})
                price = offers.get('price', 0)
                name = item.get('item', {}).get('name', '')
                
                # Extract type (T1, T2, etc.) from URL
                type_m = re.search(r'appartement-(t\d+)-le-havre', url, re.I)
                pieces = 0
                if type_m:
                    pieces = int(type_m.group(1).replace('t', ''))
                
                # Extract UUID from URL (strict 8-4-4-4-12 format)
                uuid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
                if not uuid_m:
                    # Try numeric ref like 10484-051034-342 (extract the full ref)
                    ref_m = re.search(r'-(\d+-\d+-\d+-\d+)/', url)
                    if not ref_m:
                        ref_m = re.search(r'-(\d+-\d+-\d+)/', url)
                    if ref_m:
                        uuid_m = ref_m
                
                list_id = f"orpi-{uuid_m.group(1)}" if uuid_m else ""
                
                if list_id:
                    listings.append({
                        'id': list_id,
                        'pieces': pieces,
                        'surface': 0,  # Not available in JSON-LD
                        'price': int(price) if price else 0,
                        'href': url,
                        'desc': name,
                        'source': 'orpi'
                    })
        except json.JSONDecodeError:
            pass
    return listings

# ============================================
# 3. SQUAREHABITAT (JSON-LD, pages 1-2)
# ============================================
def parse_sqhab(filename):
    content = read_file(filename)
    listings = []
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in json_ld:
        try:
            data = json.loads(block.strip())
            if 'itemListElement' not in data:
                continue
            for item in data['itemListElement']:
                if not isinstance(item, dict):
                    continue
                if item.get('@type') != 'ListItem':
                    continue
                product = item.get('item', {})
                if not isinstance(product, dict) or product.get('@type') != 'Product':
                    continue
                name = product.get('name', '')
                offers = product.get('offers', {})
                price = offers.get('price', 0)
                
                # Extract pieces from name
                pieces_m = re.search(r'(\d+)\s*pi[èc]ces', name)
                pieces = int(pieces_m.group(1)) if pieces_m else (0 if 'studio' in name.lower() else 0)
                
                # Extract UUID from image URL
                images = product.get('image', [])
                uuid = ""
                if images:
                    uuid_m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', images[0])
                    if uuid_m:
                        uuid = uuid_m.group(1)
                
                list_id = f"sqhab-{uuid}" if uuid else ""
                
                if list_id:
                    listings.append({
                        'id': list_id,
                        'pieces': pieces,
                        'surface': 0,
                        'price': int(price) if price else 0,
                        'href': f"https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/{uuid}" if uuid else "",
                        'desc': name,
                        'source': 'squarehabitat'
                    })
        except json.JSONDecodeError:
            pass
    return listings

# ============================================
# 4. LH IMMO
# ============================================
def parse_lhimmo():
    content = read_file("lhimmo_annonces.html")
    listings = []
    hrefs = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', content)
    unique_hrefs = list(set(hrefs))
    for href in unique_hrefs:
        # Extract slug
        slug_m = re.search(r'/annonce/([^/]+)/?', href)
        slug = slug_m.group(1) if slug_m else ""
        list_id = f"lhimmo-{slug}" if slug else ""
        # Get context around href
        pos = content.find(href)
        block = content[max(0,pos-200):pos+2000]
        block_clean = clean(block)
        # Extract T-type
        type_m = re.search(r'[Tt](\d+)', slug)
        pieces = int(type_m.group(1)) if type_m else 0
        # Price
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        
        if list_id:
            listings.append({
                'id': list_id,
                'pieces': pieces,
                'surface': 0,
                'price': price,
                'href': href,
                'desc': block_clean[:200],
                'source': 'lhimmo'
            })
    return listings

# ============================================
# 5. CITYA
# ============================================
def parse_citya():
    content = read_file("citya.html")
    listings = []
    # Citya has GES refs and some listing data in the HTML
    # The HTML is complex JS - look for listing blocks
    # Try to find JSON data or structured listing info
    ref_pattern = re.findall(r'(GES\d+-\d+)', content)
    all_refs = set(ref_pattern)
    
    # Also try JSON-LD
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in json_ld:
        try:
            data = json.loads(block.strip())
            if 'itemListElement' in data:
                for item in data['itemListElement']:
                    url = item.get('url', '')
                    offers = item.get('item', {}).get('offers', {})
                    price = offers.get('price', 0)
                    name = item.get('item', {}).get('name', '')
                    ref_m = re.search(r'(GES\d+-\d+)', url)
                    list_id = f"citya-{ref_m.group(1)}" if ref_m else ""
                    if list_id:
                        listings.append({
                            'id': list_id,
                            'pieces': 0,
                            'surface': 0,
                            'price': int(price) if price else 0,
                            'href': url,
                            'desc': name,
                            'source': 'citya'
                        })
        except: pass
    
    # If no JSON-LD, try manual extraction from the HTML
    if not listings:
        for ref in all_refs:
            ref_pos = content.find(ref)
            if ref_pos < 0:
                continue
            block = content[max(0,ref_pos-2000):ref_pos+2000]
            block_clean = clean(block)
            
            price_m = re.search(r'(\d+)\s*€', block_clean)
            price = int(price_m.group(1)) if price_m else 0
            surface_m = re.search(r'(\d+)\s*m²', block_clean)
            surface = int(surface_m.group(1)) if surface_m else 0
            pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece|T(\d+))', block_clean)
            pieces = int(pieces_m.group(2) if pieces_m and pieces_m.group(2) else pieces_m.group(1)) if pieces_m else 0
            
            list_id = f"citya-{ref}"
            href = f"https://www.citya.com/annonce/location/appartement/le-havre-76351/{ref}"
            listings.append({
                'id': list_id,
                'pieces': pieces,
                'surface': surface,
                'price': price,
                'href': href,
                'desc': block_clean[:300],
                'source': 'citya'
            })
    
    return listings

# ============================================
# 6. JULLIEN & ALLIX
# ============================================
def parse_ja():
    content = read_file("ja.html")
    listings = []
    # JA HTML - look for listing blocks
    # Look for href patterns
    hrefs = re.findall(r'href="(/annonce/(a-louer-[^"]+))"', content)
    if not hrefs:
        # Try other patterns
        hrefs = re.findall(r'href="(/[^"]*a-louer[^"]*)"', content)
    unique_hrefs = list(set(hrefs))
    
    # Also try JSON-LD
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in json_ld:
        try:
            data = json.loads(block.strip())
            if isinstance(data, list):
                for d in data:
                    if d.get('@type') == 'Product' or 'offers' in d:
                        name = d.get('name', '')
                        url = d.get('url', '')
                        offers = d.get('offers', {})
                        price = offers.get('price', 0)
                        slug_m = re.search(r'/annonce/([^/]+)', url) if url else None
                        slug = slug_m.group(1) if slug_m else clean(name).lower().replace(' ', '-')
                        list_id = f"ja-{slug}"
                        type_m = re.search(r'[Ff](\d+)', name)
                        pieces = int(type_m.group(1)) if type_m else 0
                        listings.append({
                            'id': list_id,
                            'pieces': pieces,
                            'surface': 0,
                            'price': int(price) if price else 0,
                            'href': url if url.startswith('http') else f"https://www.jullien-allix.fr{url}",
                            'desc': name,
                            'source': 'jullien-allix'
                        })
        except: pass
    
    # Also parse from hrefs if no JSON-LD
    if not listings:
        for href_tuple in unique_hrefs:
            href = href_tuple if isinstance(href_tuple, str) else href_tuple[0]
            slug = href.split('/')[-1] if '/' in href else href
            list_id = f"ja-{slug}"
            # F-type extraction
            type_m = re.search(r'[Ff](\d+)', slug)
            pieces = int(type_m.group(1)) if type_m else 0
            
            pos = content.find(href)
            block = content[max(0,pos-500):pos+2000]
            block_clean = clean(block)
            price_m = re.search(r'(\d+)\s*€', block_clean)
            price = int(price_m.group(1)) if price_m else 0
            
            full_url = f"https://www.jullien-allix.fr{href}" if not href.startswith('http') else href
            listings.append({
                'id': list_id,
                'pieces': pieces,
                'surface': 0,
                'price': price,
                'href': full_url,
                'desc': block_clean[:200],
                'source': 'jullien-allix'
            })
    
    return listings

# Run all parsers
print("Parsing Le-Partenaire page 1...")
lp1 = parse_le_partenaire("lp.html", 1)
print(f"  Found {len(lp1)} listings")
all_listings.extend(lp1)

print("Parsing Le-Partenaire page 2...")
lp2 = parse_le_partenaire("lp2.html", 2)
print(f"  Found {len(lp2)} listings")
all_listings.extend(lp2)

print("Parsing Orpi pages 1-3...")
for fname in ["orpi.html", "orpi2.html", "orpi3.html"]:
    orpi = parse_orpi(fname)
    print(f"  {fname}: {len(orpi)} listings")
    all_listings.extend(orpi)

print("Parsing SquareHabitat pages 1-2...")
for fname in ["sqhab.html", "sqhab2.html"]:
    sqhab = parse_sqhab(fname)
    print(f"  {fname}: {len(sqhab)} listings")
    all_listings.extend(sqhab)

print("Parsing LH Immo...")
lhimmo = parse_lhimmo()
print(f"  Found {len(lhimmo)} listings")
all_listings.extend(lhimmo)

print("Parsing Citya...")
citya = parse_citya()
print(f"  Found {len(citya)} listings")
all_listings.extend(citya)

print("Parsing Jullien & Allix...")
ja = parse_ja()
print(f"  Found {len(ja)} listings")
all_listings.extend(ja)

# Deduplicate by ID
unique_listings = {}
for l in all_listings:
    if l['id'] and l['id'] not in unique_listings:
        unique_listings[l['id']] = l
    elif l['id'] in unique_listings and not unique_listings[l['id']]['price'] and l['price']:
        unique_listings[l['id']] = l

all_listings = list(unique_listings.values())
print(f"\n{'='*60}")
print(f"TOTAL UNIQUE LISTINGS: {len(all_listings)}")
print(f"{'='*60}\n")

# Now filter by criteria:
# - T2+ (2 pièces minimum)
# - Loyer ≤ 500€/mois
# - Surface ≥ 28m²
# - Quartiers acceptés (or unknown - we'll check description)
# - Cuisine séparée (PAS cuisine ouverte/américaine/kitchenette)
# - Chambre fermée (pas coin nuit/canapé-lit)

FILTERED = []
for l in all_listings:
    # Filter: 2+ pièces
    if l['pieces'] < 2:
        # If pieces is 0 (unknown), keep it and we'll check desc
        if l['pieces'] == 0 and l['source'] in ['orpi', 'squarehabitat', 'citya', 'jullien-allix']:
            pass  # Keep unknown pieces for now
        else:
            continue
    
    # Filter: price ≤ 500
    if l['price'] > 500:
        continue
    if l['price'] == 0:
        # Keep unknown prices for now
        pass
    
    # Exclude listings clearly not in Le Havre (e.g., Brionne, Harfleur)
    desc_and_href = f"{l['desc']} {l['href']}".lower()
    EXCLUDED_CITIES = ['brionne', 'harfleur', 'montivilliers', 'gonesse', 'sainte-adresse']
    if any(city in desc_and_href for city in EXCLUDED_CITIES):
        continue
    # Exclude LH Immo listings with 'brionne' in the slug
    if 'brionne' in l['id'].lower():
        continue
    
    # Filter: surface ≥ 28m² (only if surface is known)
    if l['surface'] > 0 and l['surface'] < 28:
        continue
    
    # Check description for cuisine and chambre criteria
    desc_lower = l['desc'].lower()
    
    # Cuisine check - reject if description explicitly says "cuisine ouverte", "cuisine américaine", "kitchenette"
    has_open_kitchen = any(kw in desc_lower for kw in [
        'cuisine ouverte', 'cuisine americaine', 'cuisine américaine',
        'cuisine équipée ouverte', 'kitchenette', 'coin cuisine'
    ])
    
    # Chambre check - reject if "coin nuit", "canapé-lit", "canapé lit", "studio" with no separate chambre
    has_no_closed_bedroom = any(kw in desc_lower for kw in [
        'coin nuit', 'canapé-lit', 'canapé lit', 'canapé convertible'
    ])
    
    # Check if it's a studio (1 pièce) disguised as T2
    if 'studio' in desc_lower and l['pieces'] <= 1:
        continue
    
    # Lumineux bonus
    is_lumineux = any(kw in desc_lower for kw in [
        'lumineux', 'lumineuse', 'dernier étage', 'dernier etage',
        'balcon', 'terrasse', 'traversant', 'exposition', 'ensoleillé', 'ensoleille'
    ])
    
    # Check quartier
    quartier_match = True  # Default: keep if we can't determine
    desc_for_quartier = desc_lower
    if l['href']:
        href_lower = l['href'].lower()
        desc_for_quartier = f"{desc_lower} {href_lower}"
    
    # Check if quartier is in accepted list or is unknown
    found_accepted = False
    found_rejected = False
    for q in ACCEPTED_QUARTIERS:
        if q in desc_for_quartier:
            found_accepted = True
            break
    
    # Known rejected quartiers
    REJECTED_QUARTIERS = [
        'caucriauville', 'bois de bléville', 'bléville nord', 'mare rouge',
        'grand hameel', 'brevilliers', 'sainte-adresse', 'harfleur',
        'gaillefontaine', 'montivilliers', 'gonesse', 'ormeaux', 'côte ouest',
        'cote ouest', 'saint-nicolas', 'dollemard'
    ]
    # Actually some of these might be acceptable - let's be more conservative
    # Only reject clearly out-of-area quartiers
    CLEARLY_REJECTED = ['harfleur', 'montivilliers', 'gonesse', 'gaillefontaine', 'sainte-adresse']
    for q in CLEARLY_REJECTED:
        if q in desc_for_quartier:
            found_rejected = True
            break
    
    if found_rejected:
        continue
    
    # Add luminosity and cuisine/chambre info
    l['lumineux'] = is_lumineux
    l['has_open_kitchen'] = has_open_kitchen
    l['has_no_closed_bedroom'] = has_no_closed_bedroom
    l['quartier_accepted'] = found_accepted
    
    FILTERED.append(l)

print(f"After initial filter (T2+, ≤500€, ≥28m² if known, not clearly rejected quartier):")
print(f"  {len(FILTERED)} listings\n")

# Now check which ones are NEW (not in seen_ids)
NEW = []
for l in FILTERED:
    if l['id'] not in seen_ids:
        NEW.append(l)

print(f"NEW listings (not seen before): {len(NEW)}\n")

# Print details
for l in NEW:
    print(f"  ID: {l['id']}")
    print(f"  Source: {l['source']}")
    print(f"  Pièces: {l['pieces']} | Surface: {l['surface']}m² | Prix: {l['price']}€")
    print(f"  Lumineux: {l.get('lumineux', False)} | Cuisine ouverte: {l.get('has_open_kitchen', False)} | Pas chambre fermée: {l.get('has_no_closed_bedroom', False)}")
    print(f"  URL: {l['href']}")
    print(f"  Desc: {l['desc'][:200]}...")
    print()

# Save results
with open(f"{HAVRE_DIR}/new_listings.json", "w") as f:
    json.dump(NEW, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(NEW)} new listings to {HAVRE_DIR}/new_listings.json")