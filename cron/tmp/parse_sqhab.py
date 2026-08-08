#!/usr/bin/env python3
"""Parse SquareHabitat snapshot for all listings."""
import json, re

with open('/opt/data/cron/tmp/sqhab_snapshot.txt', 'w') as f:
    pass  # just create

import subprocess
tab_id = "41c46838-108d-4fd5-aa28-f27e490b615c"

result = subprocess.run(
    ['curl', '-s', f'http://127.0.0.1:9377/tabs/{tab_id}/snapshot?userId=hermes-veille'],
    capture_output=True, text=True, timeout=30
)
data = json.loads(result.stdout)
snap = data.get('snapshot', '')

with open('/opt/data/cron/tmp/sqhab_snapshot.txt', 'w') as f:
    f.write(snap)

# Extract all listings: heading "Appartement à louer - LE HAVRE, X pièces" + link URL + price
entries = re.findall(
    r'heading "Appartement à louer - LE HAVRE, (\d+) pièces".*?/url: /square-habitat.*?/annonces/biens/location/appartement/le-havre/([a-f0-9-]+).*?paragraph: (\d+) €.*?(\d+)[,.]?(\d+)?\s*m',
    snap, re.DOTALL
)

# Also try simpler approach: find all listing URLs and prices
urls = re.findall(r'/url: /square-habitat.*?/annonces/biens/location/appartement/le-havre/([a-f0-9-]+)', snap)
prices = re.findall(r'paragraph: (\d+)\s*€', snap)
# Find pieces from headings
pieces_list = re.findall(r'Appartement à louer - LE HAVRE, (\d+) pièces', snap)
# Find surfaces from alt text
surfaces = re.findall(r'(\d+(?:[.,]\d+)?)\s*m²', snap)

print(f"URLs: {len(urls)}")
print(f"Prices: {len(prices)}")
print(f"Pieces: {len(pieces_list)}")
print(f"Surfaces: {len(surfaces)}")

# Better: parse article by article
# Split by "heading \"Appartement à louer"
articles = snap.split('heading "Appartement à louer')
print(f"\nArticles split: {len(articles)}")

listings = []
for i, art in enumerate(articles[1:], 1):
    # Find pieces
    pm = re.search(r'LE HAVRE, (\d+) pièces', art)
    # Find URL
    um = re.search(r'/annonces/biens/location/appartement/le-havre/([a-f0-9-]+)', art)
    # Find price
    prm = re.search(r'(\d+)\s*€', art)
    # Find surface from alt text or text
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', art)
    
    pieces = int(pm.group(1)) if pm else 0
    id_ = um.group(1) if um else ''
    prix = int(prm.group(1)) if prm else 0
    surf_str = sm.group(1).replace(',', '.') if sm else '0'
    surf = int(float(surf_str))
    
    if id_:
        listing = {
            'id': f"sqhab-{id_}",
            'pieces': pieces,
            'prix': prix,
            'surf': surf,
            'url': f"https://www.squarehabitat.fr/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/{id_}"
        }
        listings.append(listing)
        print(f"  {listing['id']} | {prix}€ | {pieces}p | {surf}m²")

print(f"\nTotal SQHAB: {len(listings)}")

# Filter
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

new = [l for l in listings if l['id'] not in seen_ids and l['prix'] <= 500 and l['pieces'] >= 2 and l['surf'] >= 28]
seen = [l for l in listings if l['id'] in seen_ids]
rejected = [l for l in listings if l['id'] not in seen_ids and not (l['prix'] <= 500 and l['pieces'] >= 2 and l['surf'] >= 28)]

print(f"\nSEEN: {len(seen)} | REJECTED: {len(rejected)} | NEW: {len(new)}")
for l in new:
    print(f"  NEW: {l['id']} | {l['prix']}€ | {l['pieces']}p | {l['surf']}m²")
    print(f"    URL: {l['url']}")
for l in rejected:
    print(f"  REJECTED: {l['id']} | {l['prix']}€ | {l['pieces']}p | {l['surf']}m²")