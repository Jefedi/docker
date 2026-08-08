import re, html as htmllib, json

# Parse HEUZE
raw = open('/opt/data/tmp/veille/heuze_home.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*(?:annonce|location|bien|a-louer|appartement)[^"]*)"', page, re.IGNORECASE)
print(f"HEUZE links: {len(links)}")
for l in list(set(links))[:30]:
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Look for T2/T3
t2s = re.findall(r'(?:T[234]|F[234])\s*[^<]{0,60}', page)
print(f"\nT2-T4: {len(t2s)}")
for t in t2s[:15]:
    t_clean = t.strip()[:100]
    if 'font' not in t_clean.lower() and 'format' not in t_clean.lower():
        print(f"  {t_clean}")

# Look for JSON-LD
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"\nJSON-LD: {len(scripts)}")
for i, s in enumerate(scripts):
    try:
        data = json.loads(s.strip())
        print(f"  {i}: type={data.get('@type','')}")
        if 'itemListElement' in data:
            items = data['itemListElement']
            print(f"    Items: {len(items)}")
    except:
        print(f"  {i}: parse failed, {s[:100]}")