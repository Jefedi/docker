#!/usr/bin/env python3
"""Scrape Le-Partenaire all pages for locations."""
import json, subprocess, time, re

def get_snapshot(tab_id):
    result = subprocess.run(
        ['curl', '-s', f'http://127.0.0.1:9377/tabs/{tab_id}/snapshot?userId=hermes-veille'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        return {}

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

tab_id = "41c46838-108d-4fd5-aa28-f27e490b615c"

all_listings = []

for page in range(1, 14):
    url = f"https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2&page={page}"
    if page == 1:
        url = "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2"
    print(f"\n--- Page {page} ---")
    navigate(tab_id, url)
    time.sleep(4)
    snap = get_snapshot(tab_id)
    snapshot_text = snap.get('snapshot', '')
    
    # Extract listings: heading + price + Voir l'annonce link
    # Pattern: heading "Location Appartement à Le Havre X pièces | XX m²" ... paragraph: XXX € / mois ... link "Voir l'annonce" ... /url: /immobilier/location/appartement/havre/76600/Npieces/ID
    entries = re.findall(
        r'heading "Location Appartement à Le Havre (\d+) pièces \| (\d+) m²".*?paragraph: (\d+) € / mois.*?/url: /immobilier/location/appartement/havre/76600/\d+pieces/(\d+)',
        snapshot_text, re.DOTALL
    )
    
    if not entries:
        print(f"  No listings found on page {page}")
        break
    
    for e in entries:
        pieces, surf, prix, id_ = e
        listing = {
            'id': f"lp-{id_}",
            'pieces': int(pieces),
            'surf': int(surf),
            'prix': int(prix),
            'url': f"https://www.le-partenaire.fr/immobilier/location/appartement/havre/76600/{pieces}pieces/{id_}"
        }
        all_listings.append(listing)
        print(f"  {listing['id']} | {prix}€ | {pieces}p | {surf}m²")

print(f"\n=== Total LP listings: {len(all_listings)} ===")

# Save
with open('/opt/data/cron/tmp/lp_listings.json', 'w') as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)