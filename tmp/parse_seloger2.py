import json, re

with open('/tmp/seloger1_snap.json') as f:
    d = json.load(f)
snap = d.get('snapshot', '')

# Find all seloger listing URLs
urls = re.findall(r'https://www\.seloger\.com/annonces/locations/appartement/le-havre-76/[^\s"\\]+', snap)
unique_urls = list(dict.fromkeys(urls))

# Find all price mentions near listing links
lines = snap.split('\n')
for i, line in enumerate(lines):
    if 'annonces/locations/' in line and '/url:' in line:
        m = re.search(r'/url:\s*(https://[^\s]+)', line)
        url = m.group(1).rstrip('\\') if m else ''
        # Get surrounding context
        context = ' '.join(lines[max(0,i-5):i+15])
        
        # Extract listing ID
        id_m = re.search(r'/(\d+)\.htm', url)
        lid = id_m.group(1) if id_m else '?'
        
        # Find price
        price_m = re.search(r'(\d[\d\s]*)\s*\u20ac\s*/mois', context)
        price = price_m.group(1).strip() if price_m else '?'
        
        # Find surface and rooms
        surf_m = re.search(r'(\d+[,\d]*)\s*m\u00b2', context)
        surface = surf_m.group(1) if surf_m else '?'
        
        rooms_m = re.search(r'(\d+)\s*pi\u00e8ce', context)
        rooms = rooms_m.group(1) if rooms_m else '?'
        
        print(f"seloger-{lid}: {price}EUR | {rooms}p | {surface}m2")
        print(f"  URL: {url[:120]}")
        print()