import re, html as htmllib, json

# Parse LH Immo annonces page
raw = open('/opt/data/tmp/veille/lhimmo_annonces.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', page)
print(f"LH Immo links: {len(links)}")
for l in list(set(links)):
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Look for T2/T3/T4 mentions and surfaces
titles = re.findall(r'(?:T[234]|F[234])\s*[^<]{0,60}', page)
print(f"\nTitles: {len(titles)}")
for t in titles[:15]:
    print(f"  {t.strip()[:100]}")

# Look for surface
surfaces = re.findall(r'(\d+[,.]?\d*)\s*m²', page)
print(f"\nSurfaces: {len(surfaces)}")
for s in surfaces[:15]:
    print(f"  {s}")

# Look for "location" keyword
locs = re.findall(r'(location|louer|loyer)[^<]{0,60}', page, re.IGNORECASE)
print(f"\nLocation mentions: {len(locs)}")
for l in locs[:10]:
    print(f"  {l.strip()[:80]}")