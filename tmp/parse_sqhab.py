import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Parse SquareHabitat JSON-LD
with open('/opt/data/tmp/sqhab.html') as f:
    html = f.read()
body_start = html.find('<body')
body = html[body_start:].replace('&nbsp;', ' ')

jsonld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', body, re.DOTALL)
print(f"Found {len(jsonld_matches)} JSON-LD blocks")

for i, j in enumerate(jsonld_matches):
    try:
        data = json.loads(j)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    print(f"\n--- Item {i} ---")
                    print(f"  @type: {item.get('@type','')}")
                    print(f"  name: {item.get('name','')}")
                    print(f"  url: {item.get('url','')}")
                    print(f"  description: {str(item.get('description',''))[:200]}")
                    
                    # Check for rental data
                    if 'offers' in item:
                        offers = item['offers']
                        if isinstance(offers, dict):
                            print(f"  price: {offers.get('price','')} {offers.get('priceCurrency','')}")
                    if 'numberOfRooms' in item:
                        print(f"  numberOfRooms: {item['numberOfRooms']}")
                    if 'floorSize' in item or 'area' in item:
                        print(f"  surface: {item.get('floorSize','') or item.get('area','')}")
        elif isinstance(data, dict):
            print(f"\n--- Block {i} (dict) ---")
            print(f"  @type: {data.get('@type','')}")
            print(f"  name: {data.get('name','')}")
            if 'offers' in data:
                offers = data['offers']
                if isinstance(offers, list):
                    for o in offers:
                        print(f"  offer: {o.get('price','')} {o.get('priceCurrency','')}")
                elif isinstance(offers, dict):
                    print(f"  offer: {offers.get('price','')} {offers.get('priceCurrency','')}")
    except Exception as e:
        print(f"\n--- Block {i}: parse error: {e}")
        print(f"  First 200 chars: {j[:200]}")