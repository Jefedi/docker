import json, re

for page_num, fname in [(1, '/tmp/lp_snapshot.json'), (2, '/tmp/lp_snapshot2.json'), (3, '/tmp/lp_snapshot3.json')]:
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
            if "Voir l'annonce" in line or "Voir l\u2019annonce" in line:
                m = re.search(r'/url: (/immobilier/location/appartement/havre/76600/\d+pieces/\d+)', line)
                if m:
                    current['url'] = m.group(1)
            if 'paragraph:' in line and '€ / mois' in line:
                m = re.search(r'([\d\s]+)\s*\xe2\x82\xac\s*/\s*mois', line)
                if m:
                    current['price'] = m.group(1).strip()
            if 'paragraph:' in line:
                # Look for description hints
                pass
    if current:
        listings.append(current)
    
    for l in listings:
        h = l.get('heading', '')
        if any(x in h for x in ['2 pi', '3 pi', '4 pi', '5 pi', '6 pi']):
            price = l.get('price', '?')
            url = l.get('url', 'NONE')
            print(f"Page {l.get('page')}: {h}")
            print(f"  Price: {price} | URL: {url}")
            print()