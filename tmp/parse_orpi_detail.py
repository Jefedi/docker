#!/usr/bin/env python3
"""Parse Orpi individual listing pages for details."""
import re, html as h

files = [
    ('/tmp/scrape/orpi_715edead.html', '715edead', 'T2 Coty 485euro?'),
    ('/tmp/scrape/orpi_b3c18ecf.html', 'b3c18ecf', 'T2 Rond-point 490euro?'),
    ('/tmp/scrape/orpi_9f40f407.html', '9f40f407', 'T2 Sainte-Anne 430euro?'),
]

for fpath, uid, expected in files:
    print(f"\n=== {uid} ({expected}) ===")
    try:
        raw = open(fpath, 'r', errors='replace').read()
    except:
        print(f"  File not found: {fpath}")
        continue
    
    # Check if it's a real listing or 404
    if '404' in raw[:500] or 'not found' in raw[:500].lower() or len(raw) < 50000:
        print(f"  POSSIBLE 404 or redirect (size: {len(raw)})")
    
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find price
    price_match = re.search(r'(\d[\d\s]*)\s*€\s*(?:par\s*mois|/mois|cc)', text)
    price = 0
    if price_match:
        price_str = re.sub(r'\s', '', price_match.group(1))
        try:
            price = int(price_str)
        except:
            pass
    
    # Find surface
    surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text[:5000])
    surface = surface_match.group(1) if surface_match else '?'
    
    # Find pièces
    pieces_match = re.search(r'(\d+)\s*pi[èe]ces?', text[:5000])
    pieces = pieces_match.group(1) if pieces_match else '?'
    
    # Find quartier
    quartier_match = re.search(r'(?:Quartier|QUARTIER|Secteur|SECTEUR)\s*[:\s]*([^\n,]+)', text[:5000])
    quartier = quartier_match.group(1).strip() if quartier_match else '?'
    
    # Check cuisine
    cuisine_sep = bool(re.search(r'cuisine\s*(?:s[ée]par[ée]e|ind[ée]pendante|ferm[ée]e)', text, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette', text, re.I))
    
    # Check chambre
    chambre = bool(re.search(r'chambre', text[:5000], re.I))
    
    print(f"  Price: {price}euro | Surface: {surface}m2 | Pieces: {pieces}")
    print(f"  Quartier: {quartier}")
    print(f"  Cuisine sep: {cuisine_sep} | C. ouverte: {cuisine_ouverte} | Chambre: {chambre}")
    
    # Show relevant excerpt
    loyer_pos = text.find('oyer')
    if loyer_pos < 0:
        loyer_pos = text.find('Loyer')
    if loyer_pos >= 0:
        print(f"  Context: {text[max(0,loyer_pos-50):loyer_pos+300]}")
    
    # Find description
    desc_pos = text.find('Description')
    if desc_pos < 0:
        desc_pos = text.find('description')
    if desc_pos >= 0:
        print(f"  Desc: {text[desc_pos:desc_pos+400]}")
    else:
        # Just show first 500 chars of body text
        print(f"  Text excerpt: {text[:400]}")