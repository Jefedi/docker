import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

# Parse SeLoger results (indices 1, 2, 3 in results array)
seloger_sources = [
    ('Centre-ville', data['results'][1]),
    ('Sanvic', data['results'][2]),
    ('Bléville', data['results'][3]),
]

for quartier_name, result in seloger_sources:
    content = result['content']
    print(f"\n{'='*80}")
    print(f"SELOGER — {quartier_name}")
    print(f"URL: {result['url']}")
    print(f"Content length: {len(content)}")
    print(f"{'='*80}")
    
    # Extract listing links and their text
    # SeLoger format: [Title](url) followed by description
    # Pattern: [Appartement à louer - Le Havre - PRICE - ROOMS, SURFACE, ...](url)
    
    listings = re.findall(r'\[([^\]]+à louer[^\]]*)\]\((https://www\.seloger\.com/annonces/locations/[^\)]+)\)', content)
    print(f"\nFound {len(listings)} listings:")
    
    for idx, (title, url) in enumerate(listings):
        # Extract info from title
        price_m = re.search(r'(\d+)\s*€', title)
        price = int(price_m.group(1)) if price_m else 0
        
        pieces_m = re.search(r'(\d+)\s*pi[èe]ce', title)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        surface_m = re.search(r'([\d,]+)\s*m[²2]', title)
        surface_str = surface_m.group(1).replace(',', '.') if surface_m else '0'
        surface = float(surface_str)
        
        chambre_m = re.search(r'(\d+)\s*chambre', title)
        chambres = int(chambre_m.group(1)) if chambre_m else 0
        
        print(f"\n  [{idx}] {title[:100]}")
        print(f"       Price: {price}€ | Pieces: {pieces} | Surface: {surface}m² | Chambres: {chambres}")
        print(f"       URL: {url}")