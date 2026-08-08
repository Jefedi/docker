import re, html as htmllib, json, glob

# Parse SquareHabitat page 2
raw = open('/opt/data/tmp/veille/sqhab_p2.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
for s in scripts:
    if 'ItemList' in s and len(s) > 500:
        try:
            data = json.loads(s.strip())
            items = data.get('itemListElement', [])
            print(f"SqHab p2 items: {len(items)}")
            for item in items:
                p = item.get('item', {})
                name = p.get('name', '')
                price = p.get('offers', {}).get('price', 0)
                print(f"  {name} | {price}€")
        except:
            pass

# Parse Orpi page 2
raw2 = open('/opt/data/tmp/veille/orpi_p2.html').read()
scripts2 = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw2, re.DOTALL)
for s in scripts2:
    try:
        data = json.loads(s.strip())
        if 'itemListElement' in data:
            items = data['itemListElement']
            print(f"\nOrpi p2 items: {len(items)}")
            for item in items:
                p = item.get('item', {})
                price = p.get('offers', {}).get('price', 0)
                print(f"  {price}€")
            
            # Get links
            links = re.findall(r'href="(/annonce-location-appartement-t\d-le-havre-76600-[^"]+)"', raw2)
            seen = set()
            unique_links = []
            for l in links:
                clean = l.split('?')[0]
                if clean not in seen:
                    seen.add(clean)
                    unique_links.append(clean)
            
            print(f"\nOrpi p2 links: {len(unique_links)}")
            for i, link in enumerate(unique_links):
                tm = re.search(r'appartement-(t\d)-le-havre', link)
                pieces = int(tm.group(1)[1]) if tm else 0
                id_m = re.search(r'le-havre-76600-([0-9a-f-]+)', link)
                uid = id_m.group(1) if id_m else ''
                price = 0
                if i < len(items):
                    price = items[i].get('item', {}).get('offers', {}).get('price', 0)
                flag = " ***" if (pieces >= 2 and 0 < price <= 500) else ""
                print(f"  orpi-{uid} | T{pieces} | {price}€{flag}")
    except:
        pass

# Parse Citya page 2
raw3 = open('/opt/data/tmp/veille/citya_p2.html').read()
scripts3 = re.findall(r'<script[^>]*>(.*?)</script>', raw3, re.DOTALL)
for s in scripts3:
    if 'OfferCatalog' in s or 'RealEstateListing' in s:
        try:
            data = json.loads(s.strip())
            offers = data.get('offers', [])
            print(f"\nCitya p2 offers: {len(offers)}")
            for o in offers:
                price = o.get('price', '')
                url = o.get('url', '')
                print(f"  {price}€ | {url[:80]}")
        except:
            pass