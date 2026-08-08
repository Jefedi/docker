import re, html as htmllib, json

# Parse Jullien-Allix
raw = open('/opt/data/tmp/veille/ja.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*a-louer[^"]*)"', page, re.IGNORECASE)
print(f"JA links: {len(links)}")
for l in list(set(links)):
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

# Look for T2/T3/T4
t2s = re.findall(r'(?:T[234]|F[234]|type\s+f?[234])[^<]{0,80}', page, re.IGNORECASE)
print(f"\nT2-T4: {len(t2s)}")
for t in t2s[:15]:
    t_clean = t.strip()[:100]
    if not any(x in t_clean.lower() for x in ['font', 'format', 'base64', 'data:']):
        print(f"  {t_clean}")

# Look for "appartement"
apps = re.findall(r'appartement[^<]{0,80}', page, re.IGNORECASE)
print(f"\nAppartement mentions: {len(apps)}")
for a in apps[:10]:
    a_clean = a.strip()[:100]
    if not any(x in a_clean.lower() for x in ['font', 'format', 'base64', 'data:']):
        print(f"  {a_clean}")