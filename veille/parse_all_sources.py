import re, html, json, os

def clean_html(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === CITYA ===
text = clean_html('/tmp/veille/citya.html')
# Pattern: "PRICE € Le Havre (CP) Appartement N pièces SURFACEm² ..."
# e.g., "772 € Le Havre (76600) Appartement 2 pièces 53.35m² Parking Meublé"
citya_listings = re.findall(
    r'(\d[\d\s]*)\s*€\s+Le Havre \((\d+)\)\s+Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)m[²2]?\s*([^\n]*)',
    text
)
print(f"=== CITYA ({len(citya_listings)} listings) ===")
for c in citya_listings:
    price = int(c[0].replace(' ', ''))
    cp = c[1]
    pieces = int(c[2])
    surface = float(c[3])
    features = c[4].strip()[:200]
    # Extract listing ID/URL from the raw HTML
    print(f"  {price}€ | {pieces}p | {surface}m² | {cp} | {features}")
print()

# === SQUAREHABITAT ===
text = clean_html('/tmp/veille/sqhab.html')
# Look for listing pattern
# First let's find the listings section
idx = text.find('annonces')
if idx > 0:
    listings_text = text[idx:]
else:
    listings_text = text

# Try to find price + pieces + surface patterns
sqhab_listings = re.findall(
    r'(\d[\d\s]*)\s*€\s*(?:/mois)?\s*(?:Le Havre|Havre)?\s*(?:\(7\d+\))?\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m[²2]?',
    listings_text
)
print(f"=== SQUAREHABITAT ({len(sqhab_listings)} listings) ===")
for s in sqhab_listings:
    price = int(s[0].replace(' ', ''))
    pieces = int(s[1])
    surface = float(s[2])
    print(f"  {price}€ | {pieces}p | {surface}m²")
print()

# Also look for any T2/T3 references
t_refs = re.findall(r'T[23]\s*[^|]{0,100}', text)
print(f"=== SQUAREHABITAT T2/T3 refs ({len(t_refs)}) ===")
for t in t_refs[:20]:
    print(f"  {t.strip()[:150]}")
print()

# === CENTURY 21 ===
text = clean_html('/tmp/veille/c21.html')
# Find listing data
c21_idx = text.find('4 annonces')
if c21_idx > 0:
    c21_text = text[c21_idx:]
else:
    c21_text = text
c21_listings = re.findall(
    r'(\d[\d\s]*)\s*€\s*(?:/mois)?\s*(?:Le Havre)?\s*(?:\(7\d+\))?\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m[²2]?',
    c21_text
)
print(f"=== CENTURY21 ({len(c21_listings)} listings) ===")
for c in c21_listings:
    price = int(c[0].replace(' ', ''))
    pieces = int(c[1])
    surface = float(c[2])
    print(f"  {price}€ | {pieces}p | {surface}m²")
print()

# Also search for "Appartement" references
c21_refs = re.findall(r'Appartement[^\d]{0,50}(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m[²2]?\s*(\d[\d\s]*)\s*€', c21_text)
if c21_refs:
    print(f"=== CENTURY21 (alt pattern) ===")
    for c in c21_refs:
        print(f"  {c[2].strip()}€ | {c[0]}p | {c[1]}m²")
print()

# === ORPI ===
text = clean_html('/tmp/veille/orpi.html')
# Orpi pattern: price, pieces, surface
orpi_listings = re.findall(
    r'(\d[\d\s]*)\s*€\s*(?:/mois)?\s*(?:Le Havre)?\s*(?:\(7\d+\))?\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m[²2]?',
    text
)
print(f"=== ORPI ({len(orpi_listings)} listings) ===")
for o in orpi_listings:
    price = int(o[0].replace(' ', ''))
    pieces = int(o[1])
    surface = float(o[2])
    print(f"  {price}€ | {pieces}p | {surface}m²")
print()

# Also try finding T2 references in Orpi
orpi_t_refs = re.findall(r'T[234]\s*[^|]{0,200}', text)
print(f"=== ORPI T-refs ({len(orpi_t_refs)}) ===")
for t in orpi_t_refs[:30]:
    print(f"  {t.strip()[:200]}")
print()

# === LHIMMO ===
text = clean_html('/tmp/veille/lhimmo.html')
# LH Immo shows specific listings on the homepage
lhimmo_listings = re.findall(
    r'(\d+)\s*m[²2]?\s+(\d+)\s+(\d+)\s*([^\n]{0,100})\s+(\d[\d\s]*)\s*€\s*(?:/mois)?',
    text
)
print(f"=== LHIMMO ({len(lhimmo_listings)} listings) ===")
for l in lhimmo_listings:
    surface = int(l[0])
    rooms = int(l[1])
    bedrooms = int(l[2])
    title = l[3].strip()[:100]
    price = int(l[4].replace(' ', ''))
    print(f"  {price}€ | {surface}m² | {rooms}p {bedrooms}ch | {title}")
print()

# === JULLIEN-ALLIX ===
text = clean_html('/tmp/veille/ja.html')
# JA shows 33 biens
ja_idx = text.find('33 Biens')
if ja_idx < 0:
    ja_idx = text.find('Location')
ja_text = text[ja_idx:] if ja_idx > 0 else text
# Look for listing patterns
ja_listings = re.findall(
    r'(\d[\d\s]*)\s*€\s*(?:/mois)?\s*(?:Le Havre|Havre|Harfleur)?\s*(?:\(7\d+\))?\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m[²2]?',
    ja_text
)
print(f"=== JULLIEN-ALLIX ({len(ja_listings)} listings) ===")
for j in ja_listings:
    price = int(j[0].replace(' ', ''))
    pieces = int(j[1])
    surface = float(j[2])
    print(f"  {price}€ | {pieces}p | {surface}m²")
print()

# Also try broader pattern for JA
ja_refs = re.findall(r'(?:F[23]|T[23])\s*[^|]{0,200}', ja_text)
print(f"=== JA T/F-refs ({len(ja_refs)}) ===")
for t in ja_refs[:30]:
    print(f"  {t.strip()[:200]}")
print()