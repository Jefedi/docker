#!/usr/bin/env python3
"""Extract Citya and Orpi listings, filter, dedup against seen."""
import re, json

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# --- CITYA ---
print("=== CITYA ===")
with open('/tmp/citya_havre.html', 'r', errors='replace') as f:
    html = f.read()

ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_blocks:
    try:
        data = json.loads(ld_blocks[0])
        offers = data.get('offers', [])
        citya_listings = []
        for o in offers:
            price = o.get('price', 0)
            url = o.get('url', '')
            ref_match = re.search(r'GES(\d+-\d+)', url)
            ref = ref_match.group(1) if ref_match else ''
            
            item = o.get('itemOffered', {})
            name = item.get('name', '') if isinstance(item, dict) else ''
            
            # Extract pieces and surface from name
            pieces_match = re.search(r'(\d+)\s*pi[èe]ce', name)
            surface_match = re.search(r'(\d+\.?\d*)\s*m[²2]', name)
            pieces = int(pieces_match.group(1)) if pieces_match else 0
            surface = float(surface_match.group(1)) if surface_match else 0
            
            citya_id = f"citya-GES{ref}"
            already_seen = citya_id in seen_ids
            
            citya_listings.append({
                'id': citya_id, 'raw_id': ref, 'price': price, 'pieces': pieces,
                'surface': surface, 'name': name, 'url': url, 'seen': already_seen
            })
        
        # Filter: T2+, ≤500€, ≥28m²
        print("All Citya listings:")
        for l in citya_listings:
            mark = "✓ NEW" if not l['seen'] else "  SEEN"
            if l['pieces'] >= 2 and l['surface'] >= 28 and l['price'] <= 500:
                print(f"  *** MATCH {mark} | {l['price']}€ | {l['pieces']}p | {l['surface']}m² | {l['name'][:60]}")
                print(f"      URL: {l['url']}")
            elif l['pieces'] >= 2:
                print(f"  T2+ {mark} | {l['price']}€ | {l['pieces']}p | {l['surface']}m² | {l['name'][:60]}")
    except Exception as e:
        print(f"Error: {e}")

# --- ORPI ---
print("\n=== ORPI ===")
with open('/tmp/orpi_havre.html', 'r', errors='replace') as f:
    html = f.read()

ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_blocks:
    try:
        data = json.loads(ld_blocks[0])
        items = data.get('itemListElement', [])
        orpi_listings = []
        for item in items:
            url = item.get('url', '')
            # Extract type (T1, T2, T3, T4) from URL
            type_match = re.search(r't(\d)-le-havre', url, re.IGNORECASE)
            pieces = int(type_match.group(1)) if type_match else 0
            
            # Extract ID from URL
            id_match = re.search(r'le-havre-76600-([^/]+)/', url)
            orpi_raw_id = id_match.group(1) if id_match else ''
            orpi_id = f"orpi-{orpi_raw_id}"
            
            already_seen = orpi_id in seen_ids
            
            orpi_listings.append({
                'id': orpi_id, 'pieces': pieces, 'url': url, 'seen': already_seen
            })
        
        print(f"Orpi listings: {len(orpi_listings)}")
        for l in orpi_listings:
            mark = "✓ NEW" if not l['seen'] else "  SEEN"
            if l['pieces'] >= 2:
                print(f"  T{l['pieces']}+ {mark} | {l['url']}")
    except Exception as e:
        print(f"Error: {e}")