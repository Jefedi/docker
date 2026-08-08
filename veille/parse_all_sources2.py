import re, html, json, os

def clean_html_raw(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        return f.read()

def clean_text(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

all_new = []

# ===== CITYA =====
print("===== CITYA =====")
raw = clean_html_raw('/tmp/veille/citya.html')
text = clean_text('/tmp/veille/citya.html')
# Citya listing pattern from text: "PRICE € Le Havre (CP) Appartement N pièces SURFACEm² FEATURES"
# But we also need the listing ID. Let's look for URLs in raw HTML
citya_urls = re.findall(r'href="(/annonces/location/[^"]+)"', raw)
citya_urls = list(dict.fromkeys(citya_urls))  # dedupe preserving order
print(f"Citya URLs: {len(citya_urls)}")
for u in citya_urls[:20]:
    print(f"  {u}")

# Parse text listings
citya_pattern = re.compile(r'(\d[\d\s]*)\s*€\s+Le Havre\s*\((\d+)\)\s+Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)m[²2]?\s*([^.]*?)(?=\d+\s*€\s+Le Havre|$)')
citya_matches = citya_pattern.findall(text)
print(f"\nCitya parsed listings: {len(citya_matches)}")
for i, m in enumerate(citya_matches):
    price = int(m[0].replace(' ', ''))
    cp = m[1]
    pieces = int(m[2])
    surface = float(m[3])
    features = m[4].strip()[:200]
    url = citya_urls[i] if i < len(citya_urls) else 'NO_URL'
    # Extract ID from URL
    listing_id = None
    idm = re.search(r'-(\d+)$', url)
    if idm:
        listing_id = f"citya-{idm.group(1)}"
    elif 'GES' in features:
        # Citya uses GES IDs
        gm = re.search(r'GES\d+', features)
        if gm:
            listing_id = f"citya-{gm.group(0)}"
    
    is_new = listing_id not in seen_ids if listing_id else True
    if pieces >= 2 and price <= 500 and surface >= 28:
        print(f"  *** QUALIFYING: {price}€ | {pieces}p | {surface}m² | {cp} | {features} | NEW={is_new} | {url}")
    elif pieces >= 2 and price <= 600:
        print(f"  * NEAR: {price}€ | {pieces}p | {surface}m² | {cp} | {features} | NEW={is_new}")
print()

# ===== SQUAREHABITAT =====
print("===== SQUAREHABITAT =====")
raw = clean_html_raw('/tmp/veille/sqhab.html')
text = clean_text('/tmp/veille/sqhab.html')
# Look for listing URLs
sqhab_urls = re.findall(r'href="(/annonces/location/[^"]+)"', raw)
sqhab_urls = list(dict.fromkeys(sqhab_urls))
print(f"SqHab URLs: {len(sqhab_urls)}")
for u in sqhab_urls[:20]:
    print(f"  {u}")

# Parse from text - look for T2/T3 blocks
# Pattern: "T[23] ... m² ... EUR/mois"
sqhab_blocks = re.findall(r'(T[234][^|]{0,500})', text)
print(f"\nSqHab T-blocks: {len(sqhab_blocks)}")
for b in sqhab_blocks[:15]:
    # Try to extract price
    pm = re.search(r'(\d[\d\s]*)\s*€', b)
    sm = re.search(r'(\d+\.?\d*)\s*m[²2]?', b)
    print(f"  {b.strip()[:250]}")
    if pm and sm:
        print(f"    -> {pm.group(1).strip()}€ | {sm.group(1)}m²")
    print()

# Also try to find prices in SqHab raw HTML
sqhab_prices = re.findall(r'(\d[\d\s]*)\s*€\s*/\s*mois', text)
print(f"SqHab prices found: {sqhab_prices[:20]}")
print()

# ===== JULLIEN-ALLIX =====
print("===== JULLIEN & ALLIX =====")
raw = clean_html_raw('/tmp/veille/ja.html')
text = clean_text('/tmp/veille/ja.html')
# JA URLs
ja_urls = re.findall(r'href="(/annonce/location/[^"]+)"', raw)
ja_urls = list(dict.fromkeys(ja_urls))
print(f"JA URLs: {len(ja_urls)}")
for u in ja_urls[:30]:
    print(f"  {u}")

# Parse listings from text - JA has detailed blocks
ja_pattern = re.compile(
    r'(F[2346]|T[2346])\s*[–-]\s*([^|]{0,200}?)\s*(\d+\s*rue\s+[^,]+,?\s*\d+\s*Le\s*[Hh]avre|[^|]{0,100}?\d+\s*rue\s+[^,]+)?\s*Appartement\s+(\d+)\s*Chambre\s+(\d+)\s*Salle\s*de\s*bains\s+(\d+\.?\d*)\s*m[²2]?\s*(\d+\s*Garage)?\s*Location\s*(Visite\s*Virtuelle)?\s*(\d[\d\s]*)\s*€\s*/par\s*mois\s*CC'
)
ja_matches = ja_pattern.findall(text)
print(f"\nJA parsed listings: {len(ja_matches)}")
for i, m in enumerate(ja_matches):
    typ = m[0]
    title = m[1].strip()
    address = m[2].strip() if m[2] else ''
    bedrooms = int(m[4])
    surface = float(m[5])
    price = int(m[8].replace(' ', ''))
    url = ja_urls[i] if i < len(ja_urls) else 'NO_URL'
    listing_id = None
    # Extract slug from URL
    if url != 'NO_URL':
        slug = url.split('/')[-1]
        listing_id = f"ja-{slug}"
    
    is_new = listing_id not in seen_ids if listing_id else True
    print(f"  {typ} | {price}€ | {surface}m² | {bedrooms}ch | {title} | NEW={is_new}")
    print(f"    URL: {url}")
    print(f"    ID: {listing_id}")
print()

# ===== ORPI =====
print("===== ORPI =====")
raw = clean_html_raw('/tmp/veille/orpi.html')
text = clean_text('/tmp/veille/orpi.html')
orpi_urls = re.findall(r'href="(/location-immobiliere[^"]+)"', raw)
orpi_urls = list(dict.fromkeys(orpi_urls))
print(f"Orpi URLs: {len(orpi_urls)}")
for u in orpi_urls[:20]:
    print(f"  {u}")

# Parse Orpi listings from text
orpi_pattern = re.compile(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*(?:prix\s*en\s*hausse|prix\s*en\s*baisse)?\s*Location\s*Location\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m\s*2\s*(Le\s*Havre\s*[-–]\s*[^|]+)')
orpi_matches = orpi_pattern.findall(text)
print(f"\nOrpi parsed: {len(orpi_matches)}")
for i, m in enumerate(orpi_matches):
    price = int(m[0].replace(' ', ''))
    pieces = int(m[1])
    surface = float(m[2])
    quartier = m[3].strip()
    print(f"  {price}€ | {pieces}p | {surface}m² | {quartier}")

# Also try simpler pattern
orpi_simple = re.findall(r'(\d[\d\s]*)\s*€\s*(?:par\s*mois)?\s*.*?Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m', text)
print(f"Orpi simple: {len(orpi_simple)}")
for o in orpi_simple[:20]:
    print(f"  {o[0].strip()}€ | {o[1]}p | {o[2]}m²")
print()

# ===== CENTURY 21 =====
print("===== CENTURY 21 =====")
raw = clean_html_raw('/tmp/veille/c21.html')
text = clean_text('/tmp/veille/c21.html')
c21_urls = re.findall(r'href="(/annonces/[^"]+)"', raw)
c21_urls = list(dict.fromkeys(c21_urls))
print(f"C21 URLs: {len(c21_urls)}")
for u in c21_urls[:20]:
    print(f"  {u}")

# C21 listings
c21_text = text[text.find('4 annonces'):] if '4 annonces' in text else text
c21_pattern = re.findall(r'(\d[\d\s]*)\s*€\s*(?:/mois)?\s*.*?(\d+)\s*pi[èe]ces?\s*(\d+\.?\d*)\s*m', c21_text)
print(f"\nC21 parsed: {len(c21_pattern)}")
for c in c21_pattern[:20]:
    print(f"  {c[0].strip()}€ | {c[1]}p | {c[2]}m²")
print()

# ===== HEUZE =====
print("===== HEUZE =====")
raw = clean_html_raw('/tmp/veille/heuze.html')
text = clean_text('/tmp/veille/heuze.html')
heuze_urls = re.findall(r'href="(/[^"]*location[^"]*)"', raw, re.I)
heuze_urls = list(dict.fromkeys(heuze_urls))
print(f"Heuze URLs: {len(heuze_urls)}")
for u in heuze_urls[:20]:
    print(f"  {u}")

# Look for listing blocks
heuze_blocks = re.findall(r'(?:F[2346]|T[2346]|Appartement)\s*[–-]\s*[^|]{0,300}', text)
print(f"\nHeuze blocks: {len(heuze_blocks)}")
for b in heuze_blocks[:20]:
    print(f"  {b.strip()[:250]}")
print()

# ===== SAINT ROCH =====
print("===== SAINT ROCH =====")
raw = clean_html_raw('/tmp/veille/stroch.html')
text = clean_text('/tmp/veille/stroch.html')
stroch_urls = re.findall(r'href="(/[^"]*location[^"]*)"', raw, re.I)
stroch_urls = list(dict.fromkeys(stroch_urls))
print(f"StRoch URLs: {len(stroch_urls)}")
for u in stroch_urls[:20]:
    print(f"  {u}")
stroch_blocks = re.findall(r'(?:F[2346]|T[2346]|Appartement)\s*[–-]\s*[^|]{0,300}', text)
print(f"\nStRoch blocks: {len(stroch_blocks)}")
for b in stroch_blocks[:20]:
    print(f"  {b.strip()[:250]}")
print()