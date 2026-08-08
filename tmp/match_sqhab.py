#!/usr/bin/env python3
"""Match SquareHabitat UUIDs with listings by position."""
import re, html as h

raw = open('/tmp/scrape/sqhab.html','r',errors='replace').read()

# Find all listing entries: "N Appartement à louer - LE HAVRE ... Au prix de (par mois) XXX € cc DESCRIPTION"
# Also find all UUIDs in order
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all listing entries in text
listing_pattern = r'(\d+)\s+Appartement à louer[^|]+?Au prix de \(par mois\)\s*(\d[\d\s]*)\s*€\s*cc\s*(.+?)(?=\d+\s+Appartement à louer|$)'
listings = re.findall(listing_pattern, text, re.I)

# Find all UUIDs in the raw HTML (in order of appearance)
uuids_in_order = re.findall(r'/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([a-f0-9-]{36})', raw)
unique_uuids = []
for u in uuids_in_order:
    if u not in unique_uuids:
        unique_uuids.append(u)

print(f"Text listings: {len(listings)} | Unique UUIDs: {len(unique_uuids)}")

# Match them
for i, (num, price_str, desc) in enumerate(listings):
    price = int(re.sub(r'\s', '', price_str))
    desc_short = desc.strip()[:200]
    
    # Extract pièces
    pieces_match = re.search(r',\s*(\d+)\s*pi[èe]ces', desc[:50])
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    
    # Extract surface
    surface_match = re.search(r'(\d+[,\.]?\d*)\s*m[²2]', desc[:300])
    surface = surface_match.group(1) if surface_match else '?'
    
    # Get UUID
    uuid = unique_uuids[i] if i < len(unique_uuids) else 'N/A'
    
    # Check cuisine
    cuisine_sep = bool(re.search(r'cuisine\s*(?:ind[ée]pendante|s[ée]par[ée]e|ferm[ée]e)', desc, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette', desc, re.I))
    # Check chambre
    chambre = bool(re.search(r'chambre', desc, re.I))
    
    tag = "✅" if price <= 500 and pieces >= 2 else "❌"
    print(f"  {tag} [{uuid[:12]}] {pieces}p {surface}m² {price}€ | Cuisine sep: {cuisine_sep} | C. ouverte: {cuisine_ouverte} | Chambre: {chambre}")
    print(f"    URL: https://www.squarehabitat.fr/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/{uuid}")
    print(f"    Desc: {desc_short[:200]}")
    print()