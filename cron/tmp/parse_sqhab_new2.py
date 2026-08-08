#!/usr/bin/env python3
"""Extract details from SquareHabitat listing f76a1651."""
import re, json

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
    s = s.replace('&eacute;', 'é').replace('&egrave;', 'è').replace('&agrave;', 'à').replace('&ccedil;', 'ç')
    s = s.replace('&ecirc;', 'ê').replace('&rsquo;', "'")
    return re.sub(r'\s+', ' ', s).strip()

with open('/tmp/sqhab_new2.html', 'r', errors='replace') as f:
    html = f.read()

# JSON-LD RentAction
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
for b in ld_blocks:
    if 'RentAction' in b or 'price' in b.lower():
        try:
            data = json.loads(b)
            if data.get('@type') == 'RentAction':
                price = data.get('price', '?')
                obj = data.get('object', {})
                name = obj.get('name', '?') if isinstance(obj, dict) else '?'
                num_rooms = obj.get('numberOfRooms', '?') if isinstance(obj, dict) else '?'
                floor_size = obj.get('floorSize', {}).get('value', '?') if isinstance(obj, dict) else '?'
                address = obj.get('address', {}).get('streetAddress', '?') if isinstance(obj, dict) and isinstance(obj.get('address'), dict) else '?'
                print(f"Price: {price} EUR")
                print(f"Name: {name}")
                print(f"Rooms: {num_rooms}")
                print(f"Surface: {floor_size} m2")
                print(f"Address: {address}")
        except:
            pass

# Full text search for keywords
full_text = clean(html)
print(f"\nTitle: {clean(re.search(r'<title>(.*?)</title>', html).group(1))}")

for kw in ['loyer', 'charges', 'cuisine', 'chambre', 'étage', 'balcon', 'terrasse', 'traversant', 'lumineux', 'exposition', 'DPE', 'meublé', 'quartier', 'surface']:
    idx = full_text.lower().find(kw.lower())
    if idx != -1:
        snippet = full_text[max(0,idx-40):idx+120]
        print(f"\n'{kw}': ...{snippet}...")