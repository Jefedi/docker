import re, html as htmllib, json

# Parse Orpi
raw = open('/opt/data/tmp/veille/orpi.html').read()
page = htmllib.unescape(raw)

# Look for JSON-LD
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"Orpi JSON-LD: {len(scripts)}")
for i, s in enumerate(scripts):
    try:
        data = json.loads(s.strip())
        print(f"  Script {i}: type={data.get('@type','')}")
        if 'itemListElement' in data:
            items = data['itemListElement']
            print(f"    Items: {len(items)}")
            for item in items[:5]:
                p = item.get('item', item)
                name = p.get('name', '')
                price = p.get('offers', {}).get('price', '') if isinstance(p.get('offers'), dict) else ''
                print(f"    {name[:60]} | {price}€")
    except Exception as e:
        print(f"  Script {i}: parse error {e}")

# Look for listing data in any script
all_scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
for i, s in enumerate(all_scripts):
    if ('price' in s.lower() and 'le-havre' in s.lower()) or 'itemListElement' in s:
        if len(s) > 500:
            print(f"\nScript {i} has relevant data, len={len(s)}")
            try:
                data = json.loads(s.strip())
                if 'itemListElement' in data:
                    items = data['itemListElement']
                    print(f"  Items: {len(items)}")
                    for item in items[:10]:
                        p = item.get('item', item)
                        name = p.get('name', '')
                        price = p.get('offers', {}).get('price', '') if isinstance(p.get('offers'), dict) else ''
                        url = p.get('url', '')
                        print(f"    {name[:60]} | {price}€ | {url[:80]}")
            except:
                pass

# Look for listing URLs
links = re.findall(r'href="(/annonce/[^"]+)"', page)
print(f"\nOrpi links: {len(links)}")
for l in list(set(links))[:20]:
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")