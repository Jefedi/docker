import re, html, json, os

def clean_text(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_raw(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        return f.read()

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# ===== HEUZE LOCATION PAGE =====
print("===== HEUZE LOCATION =====")
raw = clean_raw('/tmp/veille/heuze_loc.html')
text = clean_text('/tmp/veille/heuze_loc.html')
# Find listing URLs
heuze_urls = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', raw)
heuze_urls = list(dict.fromkeys(heuze_urls))
print(f"Heuze listing URLs: {len(heuze_urls)}")
for u in heuze_urls[:30]:
    print(f"  {u}")

# Find listing blocks in text
heuze_blocks = re.findall(r'(?:Appartement|F[2346]|T[2346])\s*[–-]\s*[^|]{0,500}', text)
print(f"\nHeuze text blocks: {len(heuze_blocks)}")
for b in heuze_blocks[:20]:
    print(f"  {b.strip()[:300]}")
    print()

# Look for price + surface patterns
heuze_prices = re.findall(r'(\d[\d ]*)\s*€\s*(?:/mois|CC|par mois|€/mois)', text, re.I)
print(f"Heuze prices: {heuze_prices[:30]}")

# ===== SAINT ROCH LOCATION PAGE =====
print("\n===== SAINT ROCH LOCATION =====")
raw = clean_raw('/tmp/veille/stroch_loc.html')
text = clean_text('/tmp/veille/stroch_loc.html')
stroch_urls = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', raw)
stroch_urls = list(dict.fromkeys(stroch_urls))
print(f"StRoch listing URLs: {len(stroch_urls)}")
for u in stroch_urls[:30]:
    print(f"  {u}")

stroch_blocks = re.findall(r'(?:Appartement|F[2346]|T[2346])\s*[–-]\s*[^|]{0,500}', text)
print(f"\nStRoch text blocks: {len(stroch_blocks)}")
for b in stroch_blocks[:20]:
    print(f"  {b.strip()[:300]}")
    print()

# ===== LHIMMO ANNONCES =====
print("\n===== LHIMMO ANNONCES =====")
raw = clean_raw('/tmp/veille/lhimmo_annonces.html')
text = clean_text('/tmp/veille/lhimmo_annonces.html')
lhimmo_urls = re.findall(r'href="([^"]*annonces?[^"]*)"', raw)
lhimmo_urls = [u for u in list(dict.fromkeys(lhimmo_urls)) if 'location' in u.lower() or 'appartement' in u.lower()]
print(f"LHimmo URLs: {len(lhimmo_urls)}")
for u in lhimmo_urls[:30]:
    print(f"  {u}")

# Look for listing blocks
lhimmo_blocks = re.findall(r'(?:Appartement|T[2346])\s*[–-]\s*[^|]{0,500}', text)
print(f"\nLHimmo blocks: {len(lhimmo_blocks)}")
for b in lhimmo_blocks[:20]:
    print(f"  {b.strip()[:300]}")
    print()

# ===== ORPI quartier pages =====
for name, fn in [('orpi_cv', '/tmp/veille/orpi_cv.html'), ('orpi_coty', '/tmp/veille/orpi_coty.html'), 
                  ('orpi_mass', '/tmp/veille/orpi_mass.html'), ('orpi_ff', '/tmp/veille/orpi_ff.html'),
                  ('orpi_eure', '/tmp/veille/orpi_eure.html'), ('orpi_sf', '/tmp/veille/orpi_sf.html'),
                  ('orpi_p2', '/tmp/veille/orpi_p2.html')]:
    print(f"\n===== ORPI {name} =====")
    raw = clean_raw(fn)
    text = clean_text(fn)
    
    # Find listing URLs with full path
    orpi_urls = re.findall(r'href="(/location-immobiliere-le-havre[^"]*louer-appartement/[^"]+)"', raw)
    # Filter out the quartier-level pages (they don't have a specific listing slug)
    orpi_listing_urls = [u for u in list(dict.fromkeys(orpi_urls)) if u.count('/') > 4]
    print(f"Orpi {name} listing URLs: {len(orpi_listing_urls)}")
    for u in orpi_listing_urls[:15]:
        print(f"  {u}")
    
    # Find listings with price + pieces + surface
    orpi_matches = re.findall(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*(?:prix\s*en\s*hausse|prix\s*en\s*baisse)?\s*Location\s*Location\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m\s*2\s*Le\s*Havre\s*[-–]\s*([^|]+)', text)
    print(f"Orpi {name} parsed: {len(orpi_matches)}")
    for m in orpi_matches:
        price = int(m[0].replace(' ', ''))
        pieces = int(m[1])
        surface = float(m[2])
        quartier = m[3].strip()[:80]
        print(f"  {price}€ | {pieces}p | {surface}m² | {quartier}")

# ===== SQUAREHABITAT page 2 =====
print("\n===== SQUAREHABITAT PAGE 2 =====")
raw = clean_raw('/tmp/veille/sqhab_p2.html')
text = clean_text('/tmp/veille/sqhab_p2.html')
sqhab_urls = re.findall(r'href="(/annonces/location/bien/appartement/[^"]+)"', raw)
sqhab_listing_urls = [u for u in list(dict.fromkeys(sqhab_urls)) if 'le-havre' in u and 'page' not in u and 'normandie/seine-maritime' not in u]
print(f"SqHab P2 listing URLs: {len(sqhab_listing_urls)}")
for u in sqhab_listing_urls[:20]:
    print(f"  {u}")

sqhab_blocks = re.findall(r'(T[2346][^|]{0,500})', text)
print(f"\nSqHab P2 blocks: {len(sqhab_blocks)}")
for b in sqhab_blocks[:15]:
    print(f"  {b.strip()[:300]}")
    print()

# ===== CITYA page 2 =====
print("\n===== CITYA PAGE 2 =====")
raw = clean_raw('/tmp/veille/citya_p2.html')
text = clean_text('/tmp/veille/citya_p2.html')
citya_p2 = re.findall(r'(\d[\d\s]*)\s*€\s+Le Havre\s*\((\d+)\)\s+Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)m[²2]?\s*([^.]*?)(?=\d+\s*€\s+Le Havre|$)', text)
print(f"Citya P2 parsed: {len(citya_p2)}")
for m in citya_p2:
    price = int(m[0].replace(' ', ''))
    cp = m[1]
    pieces = int(m[2])
    surface = float(m[3])
    features = m[4].strip()[:200]
    print(f"  {price}€ | {pieces}p | {surface}m² | {cp} | {features}")

# ===== C21 listing page =====
print("\n===== C21 LISTING =====")
raw = clean_raw('/tmp/veille/c21_list.html')
text = clean_text('/tmp/veille/c21_list.html')
c21_urls = re.findall(r'href="(/annonces/location[^"]*)"', raw)
c21_urls = list(dict.fromkeys(c21_urls))
print(f"C21 URLs: {len(c21_urls)}")
for u in c21_urls[:20]:
    print(f"  {u}")

c21_blocks = re.findall(r'(Appartement\s+[^|]{0,500})', text)
print(f"\nC21 blocks: {len(c21_blocks)}")
for b in c21_blocks[:10]:
    print(f"  {b.strip()[:300]}")
    print()