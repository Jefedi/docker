#!/usr/bin/env python3
"""Extract SquareHabitat listings from embedded JSON data."""
import re, json

HAVRE_DIR = "/opt/data/tmp/havre"

with open(f"{HAVRE_DIR}/sqhab.html", encoding="utf-8", errors="replace") as f:
    content1 = f.read()
with open(f"{HAVRE_DIR}/sqhab2.html", encoding="utf-8", errors="replace") as f:
    content2 = f.read()

all_listings = []

for content, page_name in [(content1, "page1"), (content2, "page2")]:
    # Find all listing JSON objects. They start with {"codeRef":
    # We need to find the start of the biens array and extract each listing object
    # Pattern: {"codeRef":"UUID","isProgramme":false,...
    
    # Find all occurrences of "codeRef"
    positions = [m.start() for m in re.finditer(r'"codeRef":', content)]
    print(f"SqHab {page_name}: Found {len(positions)} codeRef entries")
    
    for pos in positions:
        # Find the enclosing { 
        brace_start = content.rfind('{', 0, pos)
        if brace_start < 0:
            continue
        
        # Try to extract the JSON object by counting braces
        depth = 0
        end = brace_start
        for i in range(brace_start, min(brace_start + 20000, len(content))):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        json_str = content[brace_start:end]
        
        try:
            listing = json.loads(json_str)
        except json.JSONDecodeError:
            continue
        
        # Extract fields
        code_ref = listing.get('codeRef', '')
        type_bien = listing.get('typeBien', '')
        ville = listing.get('ville', '')
        cp = listing.get('codePostal', '')
        nb_pieces = listing.get('nbPieces', 0)
        nb_chambres = listing.get('nbChambres', 0)
        surface = listing.get('surfaceHabitable', 0)
        prix = listing.get('prix', 0)
        
        # Get externalId from medias
        medias = listing.get('medias', [])
        external_id = ''
        if medias and isinstance(medias, list) and isinstance(medias[0], dict):
            external_id = medias[0].get('externalId', '')
        
        # Get description if available
        description = listing.get('description', '')
        
        # Get quartier if available
        quartier = listing.get('quartier', '')
        
        list_id = f"sqhab-{external_id}" if external_id else f"sqhab-{code_ref}"
        
        listing_data = {
            'id': list_id,
            'pieces': nb_pieces,
            'chambres': nb_chambres,
            'surface': surface,
            'price': prix,
            'href': f"https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/{external_id}" if external_id else "",
            'desc': description[:300] if description else f"{type_bien} à louer - {ville}, {nb_pieces} pièces",
            'source': 'squarehabitat',
            'quartier': quartier,
            'cp': cp,
            'code_ref': code_ref
        }
        all_listings.append(listing_data)

# Deduplicate
unique = {}
for l in all_listings:
    if l['id'] not in unique:
        unique[l['id']] = l
all_listings = list(unique.values())

print(f"\nTotal SqHab listings extracted: {len(all_listings)}")
print("\n=== ALL SQHAB LISTINGS ===")
for l in sorted(all_listings, key=lambda x: x['price']):
    print(f"  {l['id'][:40]} | {l['pieces']}p/{l['chambres']}ch | {l['surface']}m² | {l['price']}€ | CP={l['cp']} | {l['desc'][:60]}")

# Save
with open(f"{HAVRE_DIR}/sqhab_listings.json", "w") as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)

# Now filter for our criteria
print("\n=== FILTERED (T2+, ≤500€, ≥28m²) ===")
for l in all_listings:
    # nbPieces=0 but nbChambres>=1 could still be T2+
    effective_pieces = max(l['pieces'], l['chambres'])
    if effective_pieces < 2:
        continue
    if l['price'] > 500:
        continue
    if l['surface'] > 0 and l['surface'] < 28:
        continue
    
    print(f"  {l['id'][:40]} | {l['pieces']}p/{l['chambres']}ch | {l['surface']}m² | {l['price']}€ | CP={l['cp']}")
    print(f"    URL: {l['href']}")
    print(f"    Desc: {l['desc'][:200]}")
    print()