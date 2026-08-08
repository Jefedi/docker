import re, html as h
import json

html = open('/tmp/veille/lhimmo_annonces.html').read()
cards = re.split(r'(?=href="https://www\.lhimmo\.com/annonce/)', html)
listings = []
for c in cards[1:]:
    link_m = re.search(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', c)
    link = link_m.group(1) if link_m else ''
    
    text = re.sub(r'<[^>]+>', ' ', c[:3000])
    text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
    
    if '/mois' not in text and 'mois' not in text:
        continue
    
    price_m = re.search(r'(\d[\d\s]*)\s*€\s*/mois', text)
    if not price_m:
        price_m = re.search(r'(\d[\d\s]*)\s*€\s*mois', text)
    price = int(price_m.group(1).replace(' ','')) if price_m else None
    
    surface_m = re.search(r'(\d+)\s*m[²2]', text)
    surface = int(surface_m.group(1)) if surface_m else None
    
    slug = link.split('/')[-2] if link.endswith('/') else link.split('/')[-1]
    lid = f'lhimmo-{slug}'
    
    listings.append({
        'id': lid,
        'url': link,
        'price': price,
        'surface': surface,
        'text': text[:500],
        'slug': slug
    })

print(f'LH Immo rental listings: {len(listings)}')
for l in listings:
    print(f'  ID={l["id"]} | price={l["price"]} | surface={l["surface"]} | slug={l["slug"]}')
    print(f'  URL: {l["url"]}')
    print(f'  TEXT: {l["text"][:300]}')
    print()