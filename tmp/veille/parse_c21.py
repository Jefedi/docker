import re, html as htmllib, json

# Parse Century21
raw = open('/opt/data/tmp/veille/c21.html').read()
page = htmllib.unescape(raw)

# Look for JSON-LD
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
for i, s in enumerate(scripts):
    if 'ItemList' in s or 'RealEstateListing' in s or '"offers"' in s.lower() or 'priceSpecification' in s.lower():
        print(f"Script {i}: len={len(s)}, has listing data")
        try:
            data = json.loads(s.strip())
            if 'itemListElement' in data:
                items = data['itemListElement']
                print(f"  Items: {len(items)}")
                for item in items[:5]:
                    p = item.get('item', {})
                    print(f"    {p.get('name','')[:60]} | {p.get('offers',{}).get('price','')}")
        except:
            print(f"  parse failed: {s[:200]}")

# Look for listing links
links = re.findall(r'href="(/annonces/location[^"]*)"', page)
print(f"\nLinks: {len(links)}")
for l in list(set(links))[:20]:
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Look for T2/T3 mentions
t2s = re.findall(r'(?:T[23]|F[23]|2\s*pièces|3\s*pièces)[^<]{0,80}', page)
print(f"\nT2/T3 mentions: {len(t2s)}")
for t in t2s[:10]:
    print(f"  {t.strip()[:100]}")