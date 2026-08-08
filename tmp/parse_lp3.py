import json, re

all_listings = []

for page_num, fname in [(1, '/tmp/lp_snapshot.json'), (2, '/tmp/lp_snapshot2.json'), (3, '/tmp/lp_snapshot3.json'), (4, '/tmp/lp_snapshot4.json')]:
    with open(fname) as f:
        d = json.load(f)
    snap = d['snapshot']
    lines = snap.split('\n')
    current = {}
    listings = []
    for line in lines:
        if 'heading' in line and 'level=2' in line and 'Location Appartement' in line:
            if current:
                listings.append(current)
            current = {'heading': line.strip(), 'page': page_num}
        if current:
            m = re.search(r'/url: (/immobilier/location/appartement/havre/76600/\d+pieces/\d+)', line)
            if m and 'url' not in current:
                current['url'] = m.group(1)
            if 'paragraph:' in line:
                m2 = re.search(r'(\d[\d\s]*)\s*\u20ac\s*/\s*mois', line)
                if m2:
                    current['price'] = m2.group(1).strip()
                # Collect description
                m3 = re.search(r'paragraph:\s*(.+)', line)
                if m3 and len(m3.group(1)) > 50:
                    current['desc'] = m3.group(1)[:500]
    if current:
        listings.append(current)
    all_listings.extend(listings)

# Now filter: T2+ (2+ pieces), price <= 500, surface >= 28
for l in all_listings:
    h = l.get('heading', '')
    if not any(x in h for x in ['2 pi', '3 pi', '4 pi', '5 pi', '6 pi']):
        continue
    price = l.get('price', '?')
    url = l.get('url', 'NONE')
    # Extract surface
    m = re.search(r'\|\s*(\d+)\s*m\u00b2', h)
    surface = m.group(1) if m else '?'
    # Extract rooms
    m2 = re.search(r'(\d+)\s*pi', h)
    rooms = m2.group(1) if m2 else '?'
    # Clean price
    price_clean = price.replace(' ', '').replace('\xa0', '') if price != '?' else '?'
    try:
        price_num = int(price_clean)
    except:
        price_num = 9999
    surface_num = int(surface) if surface != '?' else 0
    
    print(f"Page {l['page']}: {h}")
    print(f"  Rooms: {rooms} | Surface: {surface}m² | Price: {price_clean}€")
    print(f"  URL: https://www.le-partenaire.fr{url}")
    if price_num <= 500 and surface_num >= 28:
        print(f"  *** CANDIDAT (price<=500, surface>=28, T2+) ***")
        print(f"  Desc: {l.get('desc', 'N/A')[:200]}")
    print()