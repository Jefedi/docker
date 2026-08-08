import json
import re

with open('/tmp/hermes-results/call_kx8lrzhr.txt') as f:
    data = json.load(f)

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

lbc_content = data['results'][0]['content']

# Extract ALL ad URLs from the leboncoin page
all_ad_ids = re.findall(r'leboncoin\.fr/ad/locations/(\d+)', lbc_content)
unique_ad_ids = list(dict.fromkeys(all_ad_ids))  # preserve order, unique
print(f"=== Total unique LBC ad IDs on page: {len(unique_ad_ids)}")
print()

# Check which are new
new_lbc_ids = [aid for aid in unique_ad_ids if aid not in seen_ids and f"lbc-{aid}" not in seen_ids]
print(f"=== NEW LBC IDs (not seen): {len(new_lbc_ids)}")
if new_lbc_ids:
    print("New IDs:", new_lbc_ids)
print()

# Now parse SeLoger results (results 1, 2, 3 = centre-ville, sanvic, blevelle)
seloger_listings = []
for idx, quartier_name in [(1, 'Centre-ville'), (2, 'Sanvic'), (3, 'Bléville')]:
    sl_content = data['results'][idx]['content']
    
    # SeLoger listing URLs pattern: /annonces/locations/appartement/le-havre-76/<quartier>/<ID>.htm
    # Extract listing links and details
    sl_links = re.findall(r'https://www\.seloger\.com/annonces/locations/appartement/le-havre-76/\S+?/(\w+)\.htm', sl_content)
    unique_sl_ids = list(dict.fromkeys(sl_links))
    
    # Also extract listing details from the content
    # Pattern: Title link contains price, pieces, surface
    # e.g., "Appartement à louer - Le Havre - 420 € - 2 pièces, 1 chambre, 22 m², RDC/2"
    listing_matches = re.findall(
        r'\[([^\]]+?)\s*-\s*(\d+)\s*€\s*-\s*(\d+)\s*pi[èe]ce[s]?,\s*(?:\d+\s*chambre[s]?,\s*)?([\d,]+)\s*m[²2],\s*(\S+)\]',
        sl_content
    )
    
    # Extract all listing IDs from links
    all_sl_ids = re.findall(r'seloger\.com/annonces/locations/appartement/le-havre-76/\S+?/(\w+)\.htm', sl_content)
    unique_sl_ids_all = list(dict.fromkeys(all_sl_ids))
    
    new_sl_ids = [sid for sid in unique_sl_ids_all if sid not in seen_ids and f"seloger-{sid}" not in seen_ids]
    
    print(f"=== SeLoger {quartier_name}: {len(unique_sl_ids_all)} IDs found, {len(new_sl_ids)} NEW")
    if new_sl_ids:
        print(f"  New SeLoger IDs: {new_sl_ids}")
    print()
    
    # Parse listing details
    # Split content by listing title pattern
    listing_blocks = re.split(r'\[([^\]]+?\s*-\s*\d+\s*€\s*-\s*\d+\s*pi[èe]ce[s]?,', sl_content)
    
    # Reconstruct
    for i in range(1, len(listing_blocks), 2):
        title_part = listing_blocks[i]
        content_part = listing_blocks[i+1] if i+1 < len(listing_blocks) else ""
        
        # Parse: "Title - Price € - X pièces, [Y chambres,] Surface m², Etage"
        full_title = title_part
        rest = content_part
        
        # Extract price
        price_match = re.search(r'(\d+)\s*€', title_part + rest)
        price = int(price_match.group(1)) if price_match else None
        
        # Extract pieces
        pieces_match = re.search(r'(\d+)\s*pi[èe]ce', title_part + rest)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        
        # Extract surface
        surface_match = re.search(r'([\d,]+)\s*m[²2]', rest[:200])
        surface_str = surface_match.group(1).replace(',', '.') if surface_match else None
        surface = float(surface_str) if surface_str else None
        
        # Extract etage
        etage_match = re.search(r'[ÉE]tage\s*(\S+)', rest[:200])
        etage = etage_match.group(1) if etage_match else '?'
        
        # Extract listing ID from URL
        id_match = re.search(r'/(\w+)\.htm', rest[:500])
        sl_id = id_match.group(1) if id_match else None
        
        # Extract DPE
        dpe_match = re.search(r'\b([A-G])\b\s*\n\s*\n\s*\n?\s*\d+\s*€/mois', rest[:2000])
        dpe = dpe_match.group(1) if dpe_match else '?'
        
        # Extract description text (look for meaningful content)
        desc_text = rest[:2000]
        
        is_seen = sl_id in seen_ids if sl_id else True
        if sl_id and f"seloger-{sl_id}" in seen_ids:
            is_seen = True
        
        seloger_listings.append({
            'id': sl_id,
            'source': 'seloger',
            'quartier': quartier_name,
            'title': full_title[:100],
            'price': price,
            'pieces': pieces,
            'surface': surface,
            'etage': etage,
            'dpe': dpe,
            'desc_preview': desc_text[:500],
            'seen': is_seen
        })

print(f"=== Total SeLoger listings parsed: {len(seloger_listings)}")
for sl in seloger_listings:
    status = "SEEN" if sl['seen'] else "NEW"
    print(f"  [{status}] ID={sl['id']} | {sl['quartier']} | {sl['price']}€ | {sl['pieces']}p | {sl['surface']}m² | DPE:{sl['dpe']} | {sl['title'][:60]}")
print()

# Now combine: check for any NEW qualifying listings from either source
# LBC: all 21 IDs are already seen (new_lbc_ids = 0)
# SeLoger: need to check

new_qualifying = []

# From SeLoger, filter for our criteria
print("=== SeLoger NEW listings (detailed):")
for sl in seloger_listings:
    if sl['seen']:
        continue
    # Check criteria
    if sl['price'] is None or sl['price'] > 500:
        continue
    if sl['pieces'] is not None and sl['pieces'] < 2:
        continue
    if sl['surface'] is not None and sl['surface'] < 28:
        continue
    # Quartier is already filtered by the search URL
    
    new_qualifying.append(sl)
    print(f"  NEW QUALIFYING: ID={sl['id']} | {sl['quartier']} | {sl['price']}€ | {sl['pieces']}p | {sl['surface']}m²")
    print(f"    Title: {sl['title']}")
    print(f"    Desc: {sl['desc_preview'][:300]}")
    print()

print(f"=== TOTAL NEW QUALIFYING listings: {len(new_qualifying)}")

# Summary
total_new = len(new_lbc_ids) + sum(1 for sl in seloger_listings if not sl['seen'] 
                                     and (sl['price'] or 0) <= 500 
                                     and (sl['pieces'] or 0) >= 2 
                                     and (sl['surface'] or 0) >= 28)
print(f"\n=== FINAL: {total_new} new qualifying listings found")