import re, html as htmllib, json

# Parse LH Immo
raw = open('/opt/data/tmp/veille/lhimmo_home.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*(?:location|annonce|appartement|a-louer)[^"]*)"', page, re.IGNORECASE)
print(f"LH Immo links: {len(links)}")
for l in list(set(links))[:30]:
    print(f"  {l}")

# Look for listing titles
titles = re.findall(r'(?:T[23]|F[23]|appartement|studio)[^<]{0,100}', page, re.IGNORECASE)
print(f"\nTitles: {len(titles)}")
for t in titles[:15]:
    print(f"  {t.strip()[:100]}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Look for JSON-LD
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"\nJSON-LD scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    try:
        data = json.loads(s.strip())
        print(f"  Script {i}: type={data.get('@type','')}")
    except:
        print(f"  Script {i}: parse failed")