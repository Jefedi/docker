#!/usr/bin/env python3
"""Parse Citya and Orpi listings from the links we collected."""
import json, re

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# Citya listings (from the links output)
citya_listings = [
    {"id": "citya-GES85360073-78", "text": "Appartement 2 pièces 53.35m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES85360073-78"},
    {"id": "citya-GES40870029-78", "text": "Appartement 1 pièce 26.91m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES40870029-78"},
    {"id": "citya-GES60020012-78", "text": "Appartement 2 pièces 30.19m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES60020012-78"},
    {"id": "citya-GES47000001-78", "text": "Appartement 1 pièce 18.32m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES47000001-78"},
    {"id": "citya-GES00350030-78", "text": "Appartement 2 pièces 44.97m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES00350030-78"},
    {"id": "citya-GES21610004-78", "text": "Appartement 4 pièces 52.83m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES21610004-78"},
    {"id": "citya-GES31080809-78", "text": "Appartement 1 pièce 30m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES31080809-78"},
    {"id": "citya-GES80080071-78", "text": "Appartement 1 pièce 20.28m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES80080071-78"},
    {"id": "citya-GES96790016-78", "text": "Appartement 2 pièces 41.05m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES96790016-78"},
    {"id": "citya-GES05080105-90", "text": "Appartement 2 pièces 45.6m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES05080105-90"},
    {"id": "citya-GES10600173-78", "text": "Appartement 1 pièce 11.65m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES10600173-78"},
    {"id": "citya-GES35850001-78", "text": "Appartement 1 pièce 21m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES35850001-78"},
    {"id": "citya-GES92240042-78", "text": "Appartement 3 pièces 58.41m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES92240042-78"},
    {"id": "citya-GES00180028-78", "text": "Appartement 2 pièces 46.02m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES00180028-78"},
    {"id": "citya-GES90120105-78", "text": "Appartement 2 pièces 46.44m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES90120105-78"},
    {"id": "citya-GES89130015-78", "text": "Appartement 4 pièces 70.3m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES89130015-78"},
    {"id": "citya-GES90120170-78", "text": "Appartement 1 pièce 28.97m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES90120170-78"},
    {"id": "citya-GES42560005-78", "text": "Appartement 2 pièces 34.6m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES42560005-78"},
    {"id": "citya-GES40780261-78", "text": "Appartement 3 pièces 63.35m²", "url": "https://www.citya.com/annonces/location/appartement/le-havre-76351/GES40780261-78"},
]

# Orpi listings (from the links output) - need to extract ID from URL
orpi_listings_raw = [
    {"text": "Location Appartement 1 pièce 8,71 m2 Le Havre - Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t1-le-havre-76600-10484-051034"},
    {"text": "Location Appartement 3 pièces 56 m2 Le Havre - Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-fe039240-8ac"},
    {"text": "Location Appartement 1 pièce 34,18 m2 Le Havre - Sainte-Anne", "url": "https://www.orpi.com/annonce-location-appartement-t1-le-havre-76600-a0204614-bd3"},
    {"text": "Location Appartement 2 pièces 40,93 m2 Le Havre - Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-b3dd06ab-75f"},
    {"text": "Location Appartement 3 pièces 78,09 m2 Le Havre - Coty", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-5bdf2d74-8e5"},
    {"text": "Location Appartement 3 pièces 59,32 m2 Le Havre - Rond point - Observatoire", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-d94480cc-dfe"},
    {"text": "Location Appartement 4 pièces 81,29 m2 Le Havre - Les Ormeaux - Maréchal Joffre", "url": "https://www.orpi.com/annonce-location-appartement-t4-le-havre-76600-cab26761-0eb"},
    {"text": "Location Appartement 2 pièces 42,36 m2 Le Havre - Graville", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-aabc2df5-791"},
    {"text": "Location Appartement 3 pièces 58,96 m2 Le Havre - Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-4c1c8618-f31"},
    {"text": "Location Appartement 3 pièces 61,50 m2 Le Havre - Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-3ccc38ca-99e"},
    {"text": "Location Appartement 2 pièces 49,89 m2 Le Havre - Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-45580ff2-c2c"},
    {"text": "Location Appartement 1 pièce 13,32 m2 Le Havre - Coty", "url": "https://www.orpi.com/annonce-location-appartement-t1-le-havre-76600-0751930c-b7f"},
    {"text": "Location Appartement 2 pièces 29,90 m2 Le Havre - Sainte-Anne", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-094f3534-529"},
    {"text": "Location Appartement 1 pièce 17,87 m2 Le Havre - Massillon", "url": "https://www.orpi.com/annonce-location-appartement-t1-le-havre-76600-c5717b9f-6be"},
    {"text": "Location Appartement 1 pièce 22,05 m2 Le Havre - Sainte-Anne", "url": "https://www.orpi.com/annonce-location-appartement-t1-le-havre-76600-814976fa-04d"},
    {"text": "Location Appartement 2 pièces 61,96 m2 Montivilliers", "url": "https://www.orpi.com/annonce-location-appartement-t2-montivilliers-76290-280-051"},
    {"text": "Location Appartement 2 pièces 59,09 m2 Montivilliers", "url": "https://www.orpi.com/annonce-location-appartement-t2-montivilliers-76290-9ba9d07"},
    {"text": "Location Appartement 2 pièces 37 m2 Harfleur", "url": "https://www.orpi.com/annonce-location-appartement-t2-harfleur-76700-8cdff6a6-4ac"},
    {"text": "Location Appartement 2 pièces 47,80 m2 Montivilliers", "url": "https://www.orpi.com/annonce-location-appartement-t2-montivilliers-76290-77fa097"},
]

# Parse Orpi - extract ID from URL
orpi_listings = []
for l in orpi_listings_raw:
    # Extract ID: last part of URL after the last hyphen
    m = re.search(r'/annonce-location-appartement-t\d-le-havre-76600-([a-f0-9-]+(?:-\d+)?)$', l['url'])
    if not m:
        m = re.search(r'/annonce-location-appartement-t\d-le-havre-76600-(.+)$', l['url'])
    id_part = m.group(1) if m else 'unknown'
    
    # Parse pieces and surface from text
    pm = re.search(r'(\d+)\s*pi[èe]ces?\s+([\d,]+)\s*m', l['text'])
    pieces = int(pm.group(1)) if pm else 0
    surf_str = pm.group(2).replace(',', '.') if pm else '0'
    surf = int(float(surf_str))
    
    # Extract quartier
    qm = re.search(r'Le Havre\s*-\s*(.+?)(?:\n|$)', l['text'])
    quartier = qm.group(1).strip() if qm else ""
    
    orpi_listings.append({
        'id': f"orpi-{id_part}",
        'pieces': pieces,
        'surf': surf,
        'quartier': quartier,
        'url': l['url']
    })

# Parse Citya - extract pieces and surface from text
for l in citya_listings:
    pm = re.search(r'(\d+)\s*pi[èe]ce[s]?\s+([\d.]+)\s*m', l['text'])
    l['pieces'] = int(pm.group(1)) if pm else 0
    l['surf'] = int(float(pm.group(2))) if pm else 0

# Check which are new
print("=== CITYA ===")
for l in citya_listings:
    status = "SEEN" if l['id'] in seen_ids else "NEW"
    if l['pieces'] >= 2 and l['surf'] >= 28:
        print(f"  {status}: {l['id']} | {l['pieces']}p | {l['surf']}m² | {l['url'][:80]}")

print("\n=== ORPI ===")
for l in orpi_listings:
    status = "SEEN" if l['id'] in seen_ids else "NEW"
    if l['pieces'] >= 2 and l['surf'] >= 28:
        print(f"  {status}: {l['id']} | {l['pieces']}p | {l['surf']}m² | {l['quartier']} | {l['url'][:80]}")

# All new candidates
print("\n=== ALL NEW (not seen, T2+, 28m²+) ===")
for l in citya_listings:
    if l['id'] not in seen_ids and l['pieces'] >= 2 and l['surf'] >= 28:
        print(f"  CITYA NEW: {l['id']} | {l['pieces']}p | {l['surf']}m² | {l['url']}")
for l in orpi_listings:
    if l['id'] not in seen_ids and l['pieces'] >= 2 and l['surf'] >= 28:
        # Also check Le Havre only (not Montivilliers/Harfleur)
        if 'le-havre' in l['url']:
            print(f"  ORPI NEW: {l['id']} | {l['pieces']}p | {l['surf']}m² | {l['quartier']} | {l['url']}")