import re, html as htmllib, json

# Parse HEUZE location page
raw = open('/opt/data/tmp/veille/heuze_loc.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*/location/appartement/le-havre/76600/[^"]+)"', page)
print(f"HEUZE listing links: {len(links)}")
for l in list(set(links))[:30]:
    print(f"  {l}")

# Also look for listing URLs
links2 = re.findall(r'href="(/location/appartement/le-havre/76600[^"]*)"', page)
print(f"\nAll HEUZE links: {len(links2)}")
for l in list(set(links2))[:30]:
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Look for surfaces
surfaces = re.findall(r'(\d+[,.]?\d*)\s*m²', page)
print(f"\nSurfaces: {len(surfaces)}")
for s in surfaces[:15]:
    print(f"  {s}")

# Look for JSON-LD with listings
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"\nJSON-LD: {len(scripts)}")
for i, s in enumerate(scripts):
    try:
        data = json.loads(s.strip())
        if 'itemListElement' in data or 'offers' in str(data):
            print(f"  Script {i}: has listings data")
            if 'itemListElement' in data:
                items = data['itemListElement']
                print(f"    Items: {len(items)}")
                for item in items[:5]:
                    p = item.get('item', item)
                    print(f"    {p.get('name','')[:60]} | {p.get('offers',{}).get('price','') if isinstance(p.get('offers'), dict) else ''}")
    except:
        pass

# Look for card data
cards = re.findall(r'class="[^"]*card[^"]*"', raw[:50000])
print(f"\nCards: {len(cards)}")

# Look for "T2" or "2 pièces" text
t2s = re.findall(r'(?:T[234]|F[234]|2\s*pièces|3\s*pièces|4\s*pièces)[^<]{0,60}', page)
print(f"\nT2-T4 mentions: {len(t2s)}")
for t in t2s[:15]:
    t_clean = t.strip()[:100]
    if not any(x in t_clean.lower() for x in ['font', 'format', 'base64', 'data:', 'var ', 'function']):
        print(f"  {t_clean}")