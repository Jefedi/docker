import re, html as htmllib

# Parse Saint Roch
raw = open('/opt/data/tmp/veille/stroch_home.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*(?:location|a-louer|annonce|appartement|bien)[^"]*)"', page, re.IGNORECASE)
print(f"Saint Roch links: {len(links)}")
for l in list(set(links))[:30]:
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

# Look for T2/T3
t2s = re.findall(r'(?:T[234]|F[234]|2\s*pièces|3\s*pièces|type\s+2|type\s+3)[^<]{0,80}', page, re.IGNORECASE)
print(f"\nT2-T4: {len(t2s)}")
for t in t2s[:15]:
    t_clean = t.strip()[:100]
    if not any(x in t_clean.lower() for x in ['font', 'format', 'base64', 'data:']):
        print(f"  {t_clean}")

# Look for "cuisine" and "chambre"
cuisines = re.findall(r'cuisine[^<.]{0,60}', page, re.IGNORECASE)
print(f"\nCuisine: {len(cuisines)}")
for c in cuisines[:5]:
    print(f"  {c.strip()[:80]}")