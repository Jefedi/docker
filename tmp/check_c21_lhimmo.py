#!/usr/bin/env python3
import re, json

seen_file = '/opt/data/cron/output/havre-rental-seen.json'
with open(seen_file, 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# Century21
with open('/tmp/rental/c21.html', 'r') as f:
    content = f.read()
listings = re.findall(r'(\d+,\d+|\d+)\s*m<sup>2</sup>,\s*(\d+)\s*pièce', content)
print('Century21 Le Havre listings:')
for surface_str, pieces in listings:
    surface = float(surface_str.replace(',', '.'))
    pieces = int(pieces)
    idx = content.find(f'{surface_str} m<sup>2</sup>, {pieces} pièce')
    if idx >= 0:
        block = content[max(0, idx-1000):idx+500]
        price_match = re.search(r'(\d[\d\s]*)\s*€', block)
        price = int(re.sub(r'\s', '', price_match.group(1))) if price_match else 0
        desc_match = re.search(r'tw-text-c21-gold-darker.*?>(.*?)</div>', block, re.DOTALL)
        desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()[:200] if desc_match else ''
        url_match = re.search(r'href="(/annonces/[^"]+)"', block)
        url = url_match.group(1) if url_match else ''
        
        if pieces >= 2 and price <= 500 and surface >= 28:
            listing_id = url.split('/')[-1] if url else f'c21-{surface}'
            sid = f'c21-{listing_id}'
            is_new = sid not in seen_ids
            print(f'  T{pieces} {surface}m² {price}€ — {sid} NEW={is_new}')
            print(f'    Desc: {desc[:200]}')
        else:
            print(f'  (filtered) T{pieces} {surface}m² {price}€')

print()

# LH Immo
with open('/tmp/rental/lhimmo_loc.html', 'r') as f:
    content = f.read()
listings = re.findall(r'<a href="(https://www\.lhimmo\.com/annonce/[^"]+)"', content)
print(f'LH Immo listings: {len(listings)}')
for url in listings:
    idx = content.find(url)
    if idx >= 0:
        block = content[max(0, idx-200):idx+500]
        price_match = re.search(r'iwp__price">(\d+)\s*€</span>', block)
        surface_match = re.search(r'(\d+)m²</span>', block)
        title_match = re.search(r'<h3[^>]*>([^<]+)</h3>', block)
        price = int(price_match.group(1)) if price_match else 0
        surface = int(surface_match.group(1)) if surface_match else 0
        title = title_match.group(1) if title_match else ''
        
        if 'T2' in title or 'F2' in title: pieces = 2
        elif 'T3' in title or 'F3' in title: pieces = 3
        elif 'T4' in title or 'F4' in title: pieces = 4
        elif 'colocation' in title.lower() or 'chambre' in title.lower(): pieces = 1
        else: pieces = 0
        
        if pieces >= 2 and price <= 500:
            listing_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            sid = f'lhimmo-{listing_id}'
            is_new = sid not in seen_ids
            print(f'  T{pieces} {surface}m² {price}€ — {sid} NEW={is_new}')
            print(f'    Title: {title}')
            print(f'    URL: {url}')