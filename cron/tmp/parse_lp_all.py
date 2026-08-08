#!/usr/bin/env python3
"""Parse all Le-Partenaire pages."""
import re, json, glob

all_listings = []

for fpath in sorted(glob.glob('/tmp/lp_havre*.html')):
    with open(fpath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find listing blocks
    block_starts = [m.start() for m in re.finditer(r'<div class="col-12 col-md-6">\s*<div class="card w-100 mb-5 item-annonce">', html)]
    
    for i, start in enumerate(block_starts):
        end = block_starts[i+1] if i+1 < len(block_starts) else len(html)
        block = html[start:end]
        
        h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        h2_text = ''
        if h2_match:
            h2_text = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
            h2_text = re.sub(r'\s+', ' ', h2_text).replace('&nbsp;', ' ')
        
        price_match = re.search(r'<span class="prix">\s*([\d\s&nbsp;]+)\s*€\s*</span>', block)
        price = 0
        if price_match:
            price_str = price_match.group(1).replace('&nbsp;', '').replace(' ', '').strip()
            try: price = int(price_str)
            except: pass
        
        if price == 0:
            loyer_match = re.search(r'Loyer\s*(?:HC|TCC)?\s*:\s*([\d,]+)\s*€', block)
            if loyer_match:
                try: price = int(float(loyer_match.group(1).replace(',', '.')))
                except: pass
        
        pieces_match = re.search(r'(\d+)\s*pi[èe]ces', h2_text)
        surface_match = re.search(r'(\d+)\s*m[²2]', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else 0
        surface = int(surface_match.group(1)) if surface_match else 0
        
        url_match = re.search(r'href="(/immobilier/location/appartement/(?:le-)?havre/76600/\d+pieces/(\d+))"', block)
        url = f"https://www.le-partenaire.fr{url_match.group(1)}" if url_match else ''
        listing_id = url_match.group(2) if url_match else ''
        
        desc_match = re.search(r'<p class="card-text[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        desc = ''
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
            desc = re.sub(r'\s+', ' ', desc).replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
        
        all_listings.append({
            'id': listing_id, 'pieces': pieces, 'surface': surface,
            'price': price, 'h2': h2_text, 'desc': desc[:400], 'url': url,
            'source': fpath
        })

# Deduplicate by ID
seen_ids = set()
unique = []
for l in all_listings:
    if l['id'] not in seen_ids:
        seen_ids.add(l['id'])
        unique.append(l)

print(f"Total unique listings across all pages: {len(unique)}")

# Filter: T2+, ≤500€, ≥28m²
print(f"\n=== FILTERED: T2+, ≤500€, ≥28m² ===")
for l in unique:
    if l['pieces'] >= 2 and l['surface'] >= 28 and 0 < l['price'] <= 500:
        print(f"  ID={l['id']} | {l['pieces']}p | {l['surface']}m² | {l['price']}€/mois")
        print(f"    Desc: {l['desc'][:250]}")
        print(f"    URL: {l['url']}")
        print()