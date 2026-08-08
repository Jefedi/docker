import re, json

sources = {
    'sqhab': '/opt/data/tmp/sqhab.html',
    'citya': '/opt/data/tmp/citya.html',
    'orpi': '/opt/data/tmp/orpi.html',
    'ja': '/opt/data/tmp/ja.html',
    'c21': '/opt/data/tmp/c21.html',
    'lhimmo': '/opt/data/tmp/lhimmo.html',
    'heuze': '/opt/data/tmp/heuze.html',
    'stroch': '/opt/data/tmp/stroch.html',
}

for src_name, path in sources.items():
    try:
        html = open(path).read()
    except:
        print(f"\n=== {src_name}: FILE NOT FOUND ===")
        continue
    
    # Look for rental listing patterns
    # Common patterns: price (€), surface (m²), rooms (pièce/T2/F2)
    
    # Find all links that look like listing detail pages
    all_links = re.findall(r'href="([^"]*(?:location|louer|annonce|bien|property)[^"]*)"', html, re.IGNORECASE)
    
    # Find prices
    prices = re.findall(r'(\d[\d\s]*\d)\s*€', html)
    
    # Find surfaces
    surfaces = re.findall(r'(\d+(?:[.,]\d+)?)\s*m[²2]', html)
    
    # Find room patterns
    rooms = re.findall(r'(?:T|F|Type\s*)(\d+)\s*pi[èe]ce', html, re.IGNORECASE)
    
    # Find "Le Havre" mentions
    havre_count = len(re.findall(r'[Hh]avre', html))
    
    print(f"\n=== {src_name}: {len(html)} bytes, {havre_count} Havre mentions ===")
    print(f"  Links: {len(all_links)}, Prices: {len(prices)}, Surfaces: {len(surfaces)}, Rooms: {len(rooms)}")
    
    # Show sample links
    rental_links = [l for l in all_links if any(k in l.lower() for k in ['location','louer','rent','lease'])]
    print(f"  Rental links: {len(rental_links)}")
    for l in rental_links[:5]:
        print(f"    {l}")