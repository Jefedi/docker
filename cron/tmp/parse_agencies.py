import re, html, json

# Parse Saint Roch location page
s = open('/tmp/stroch_loc.html').read()
print(f"=== Saint Roch location ({len(s)} bytes) ===")
# Look for listing links and data
links = re.findall(r'href="(/location/appartement/[^"]+)"', s)
print(f"Links: {links[:20]}")
# Find listing blocks - stroch uses /annonce/ or similar
links2 = re.findall(r'href="(/annonce/[^"]+)"', s)
print(f"Annonce links: {links2[:20]}")
# Prices
prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
print(f"Prices: {prices[:20]}")
# headings
h2s = re.findall(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL)
for h in h2s[:20]:
    t = html.unescape(re.sub('<[^>]+>','',h)).strip()
    if t and len(t) > 5: print(f"  H: {t[:120]}")
# JSON
for pat in [r'"price"\s*:\s*(\d+)', r'"loyer"\s*:\s*(\d+)', r'"surface"\s*:\s*"?(\d+)', r'"pieces"\s*:\s*"?(\d+)']:
    m = re.findall(pat, s)
    if m: print(f"  {pat[:25]}: {m[:15]}")

print()
# Parse Heuze location page
s = open('/tmp/heuze_loc.html').read()
print(f"=== Heuze location ({len(s)} bytes) ===")
links = re.findall(r'href="(/location/[^"]+)"', s)
print(f"Links: {links[:20]}")
links2 = re.findall(r'href="(/annonce/[^"]+)"', s)
print(f"Annonce links: {links2[:20]}")
links3 = re.findall(r'href="(/bien/[^"]+)"', s)
print(f"Bien links: {links3[:20]}")
prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
print(f"Prices: {prices[:20]}")
h2s = re.findall(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL)
for h in h2s[:20]:
    t = html.unescape(re.sub('<[^>]+>','',h)).strip()
    if t and len(t) > 5: print(f"  H: {t[:120]}")
for pat in [r'"price"\s*:\s*"?(\d+)', r'"loyer"\s*:\s*"?(\d+)', r'"surface"\s*:\s*"?(\d+)', r'"pieces"\s*:\s*"?(\d+)']:
    m = re.findall(pat, s)
    if m: print(f"  {pat[:25]}: {m[:15]}")

print()
# Parse LH Immo annonces
s = open('/tmp/lhimmo_ann.html').read()
print(f"=== LH Immo annonces ({len(s)} bytes) ===")
links = re.findall(r'href="(/annonce/[^"]+)"', s)
print(f"Links: {links[:20]}")
prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
print(f"Prices: {prices[:20]}")
h2s = re.findall(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL)
for h in h2s[:20]:
    t = html.unescape(re.sub('<[^>]+>','',h)).strip()
    if t and len(t) > 5: print(f"  H: {t[:120]}")

print()
# Parse Orpi page 2
s = open('/tmp/orpi2.html').read()
print(f"=== Orpi page 2 ({len(s)} bytes) ===")
prices = re.findall(r'"price"\s*:\s*(\d+)', s)
print(f"JSON prices: {prices[:20]}")
surfaces = re.findall(r'"surface"\s*:\s*"?(\d+)', s)
print(f"JSON surfaces: {surfaces[:20]}")
pieces = re.findall(r'"pieces"\s*:\s*"?(\d+)', s)
print(f"JSON pieces: {pieces[:20]}")
# links to individual listings
links = re.findall(r'href="(/location-immobiliere[^"]+)"', s)
print(f"Links: {links[:20]}")