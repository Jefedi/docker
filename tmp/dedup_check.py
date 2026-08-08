import json, re

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# All listing IDs from this scrape (from the parse output)
# Let me re-parse all files
import html as html_module

all_ids = []
all_listings_details = []

for page in range(1, 7):
    if page == 1:
        fname = '/tmp/lp_havre.html'
    else:
        fname = f'/tmp/lp_havre_p{page}.html'
    
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cards = content.split('item-annonce')
    
    for i in range(1, len(cards)):
        card = cards[i][:6000]
        
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/(\d+)pieces/(\d+))"', card)
        if not link_match:
            continue
        pieces = int(link_match.group(2))
        listing_id = link_match.group(3)
        
        h2_match = re.search(r'(\d+)\s*&nbsp;\s*m', card)
        surface = int(h2_match.group(1)) if h2_match else None
        
        price_match = re.search(r'<span class="prix">(.*?)</span>', card, re.DOTALL)
        price = None
        if price_match:
            price_str = re.sub(r'<[^>]+>', '', price_match.group(1)).strip()
            price_str = html_module.unescape(price_str)
            price_str = re.sub(r'[^\d]', '', price_str)
            try:
                price = int(price_str) if price_str else None
            except:
                price = None
        
        full_text = re.sub(r'<[^>]+>', ' ', card)
        full_text = html_module.unescape(full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        # Check features
        ft = full_text.lower()
        has_cuisine_ouverte = bool(re.search(r'cuisine (ouverte|américaine)|kitchenette|cusine ouverte', ft))
        has_cuisine_separee = bool(re.search(r'cuisine (séparée|indépendante|fermée|séparé)', ft))
        has_open_space = bool(re.search(r'open space|loft|pièce de vie ouverte', ft))
        
        # Check for colocation
        is_colocation = bool(re.search(r'colocation|chambre à louer|chambre meublée|colocataire', ft))
        
        # Check for studio/T1
        is_studio = bool(re.search(r'studio|t1\b|t1 bis|f1\b', ft)) and pieces <= 2
        
        all_ids.append(f'lp-{listing_id}')
        all_listings_details.append({
            'id': f'lp-{listing_id}',
            'raw_id': listing_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'has_cuisine_ouverte': has_cuisine_ouverte,
            'has_cuisine_separee': has_cuisine_separee,
            'has_open_space': has_open_space,
            'is_colocation': is_colocation,
            'is_studio': is_studio,
            'full_text': full_text[:400],
        })

# Find NEW IDs (not in seen file)
new_ids = [id for id in all_ids if id not in seen_ids]
print(f"Total listings scraped: {len(all_ids)}")
print(f"Already seen: {len(all_ids) - len(new_ids)}")
print(f"NEW IDs: {len(new_ids)}")
print()

if new_ids:
    print("=== NEW LISTINGS ===")
    for l in all_listings_details:
        if l['id'] in new_ids:
            print(f"  {l['id']} | {l['pieces']}p | {l['surface']}m² | {l['price']}€")
            print(f"    Colocation: {l['is_colocation']} | Studio: {l['is_studio']}")
            print(f"    Cuisine ouv: {l['has_cuisine_ouverte']} | Cuisine sep: {l['has_cuisine_separee']} | Open space: {l['has_open_space']}")
            print(f"    Text: {l['full_text'][:300]}")
            print()
    
    # Now apply strict filters to NEW listings only
    print("\n=== NEW listings passing strict filter ===")
    print("Filter: 2p+, >=28m², <=500€, NOT colocation, NOT studio, NO cuisine ouverte")
    
    candidates = []
    for l in all_listings_details:
        if l['id'] not in new_ids:
            continue
        if l['pieces'] < 2:
            continue
        if l['surface'] and l['surface'] < 28:
            continue
        if l['price'] and l['price'] > 500:
            continue
        if l['is_colocation']:
            continue
        if l['is_studio']:
            continue
        if l['has_cuisine_ouverte'] and not l['has_cuisine_separee']:
            continue
        if l['has_open_space']:
            continue
        
        candidates.append(l)
        print(f"  ✅ {l['id']} | {l['pieces']}p | {l['surface']}m² | {l['price']}€")
        print(f"     Cuisine sep: {l['has_cuisine_separee']} | Cuisine ouv: {l['has_cuisine_ouverte']}")
        print(f"     Text: {l['full_text'][:400]}")
        print()
    
    if not candidates:
        print("  Aucune nouvelle annonce ne passe les filtres stricts.")
else:
    print("AUCUNE nouvelle annonce trouvée. Tous les IDs étaient déjà vus.")