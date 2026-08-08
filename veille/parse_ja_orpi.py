import re, html, json

def clean_text(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# ===== JULLIEN & ALLIX =====
with open('/tmp/veille/ja.html', encoding='utf-8', errors='replace') as f:
    raw = f.read()

# Extract all listing URLs
ja_urls = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/a-louer-[^"]+\.html)"', raw)
ja_urls = list(dict.fromkeys(ja_urls))

# Parse text
text = clean_text('/tmp/veille/ja.html')
listings_start = text.find('33 Biens')
if listings_start > 0:
    listings_text = text[listings_start:]
else:
    listings_text = text[text.find('Location'):]

# Parse JA listings with full info
ja_pattern = re.compile(
    r'(F[2346]|T[2346])\s*[–-]\s*([^|]{0,200}?)\s*(\d+\s*rue\s+[^,]+,?\s*\d+\s*Le\s*[Hh]avre(?:\s*\d+)?|[^|]{0,100}?\d+\s*rue\s+[^,]+)?\s*Appartement\s+(\d+)\s*Chambre\s+(\d+)\s*Salle\s*de\s*bains\s+(\d+\.?\d*)\s*m[²2]?\s*(\d+\s*Garage)?\s*Location\s*(Visite\s*Virtuelle)?\s*(\d[\d\s]*)\s*€\s*/par\s*mois\s*CC\s*A\s*Louer'
)
ja_matches = ja_pattern.findall(listings_text)

print(f"JA URLs: {len(ja_urls)}")
print(f"JA parsed: {len(ja_matches)}")

# The listing titles in text should correspond to the URL slugs
# Let's extract listing title from URL and match
for i, m in enumerate(ja_matches):
    typ = m[0]
    title = m[1].strip()
    address = m[2].strip() if m[2] else ''
    bedrooms = int(m[3])
    surface = float(m[5])
    price = int(m[8].replace(' ', ''))
    
    # Generate slug from title for matching
    title_lower = title.lower().strip()
    
    # Find matching URL
    matching_url = None
    for u in ja_urls:
        # Extract slug from URL
        slug = u.split('/')[-1].replace('.html', '').replace('a-louer-', '')
        # Normalize
        slug_norm = re.sub(r'[^a-z0-9]', '', slug)
        title_norm = re.sub(r'[^a-z0-9]', '', title_lower)
        if title_norm in slug_norm or slug_norm in title_norm:
            matching_url = u
            break
    
    # Also try to match by position
    if not matching_url and i < len(ja_urls):
        matching_url = ja_urls[i]
    
    # Generate listing ID
    listing_id = None
    if matching_url:
        slug = matching_url.split('/')[-1].replace('.html', '')
        listing_id = f"ja-{slug}"
    
    is_new = listing_id not in seen_ids if listing_id else True
    
    # Check if qualifying
    qualifies = surface >= 28 and price <= 500 and bedrooms >= 1
    quartier = 'unknown'
    # Try to extract quartier from title
    if 'centre' in title_lower or 'coty' in title_lower:
        quartier = 'Centre-ville'
    elif 'sanvic' in title_lower:
        quartier = 'Sanvic'
    elif 'bleville' in title_lower:
        quartier = 'Bléville'
    elif 'docks' in title_lower:
        quartier = 'Centre-ville (Docks)'
    elif 'ormeaux' in title_lower:
        quartier = 'Cote Ouest (Ormeaux)'
    elif 'mazeline' in title_lower:
        quartier = 'Mazeline'
    elif 'demidoff' in title_lower:
        quartier = 'Demidoff'
    elif 'joffre' in title_lower:
        quartier = 'Maréchal Joffre'
    elif 'danton' in title_lower:
        quartier = 'Danton'
    elif 'harfleur' in title_lower:
        quartier = 'Harfleur (NOT Le Havre)'
    elif 'saint-nicolas' in title_lower or 'ostara' in title_lower:
        quartier = 'Saint-Nicolas'
    
    if qualifies:
        print(f"\n  *** QUALIFYING: {typ} | {price}€ | {surface}m² | {bedrooms}ch | {title}")
        print(f"    Quartier: {quartier}")
        print(f"    URL: {matching_url}")
        print(f"    ID: {listing_id}")
        print(f"    NEW: {is_new}")
    elif price <= 600 and surface >= 28:
        print(f"\n  * NEAR: {typ} | {price}€ | {surface}m² | {bedrooms}ch | {title}")
        print(f"    URL: {matching_url}")
        print(f"    ID: {listing_id}")
        print(f"    NEW: {is_new}")

# Also check all JA URLs for new ones we haven't seen
print("\n\n=== ALL JA URL CHECK ===")
for u in ja_urls:
    slug = u.split('/')[-1].replace('.html', '')
    listing_id = f"ja-{slug}"
    is_new = listing_id not in seen_ids
    if is_new:
        print(f"  NEW: {listing_id} -> {u}")

# ===== ORPI =====
print("\n\n=== ORPI CHECK ===")
# Parse all Orpi pages and check for new listings
orpi_all_matches = []
for name, fn in [('main', '/tmp/veille/orpi.html'), ('cv', '/tmp/veille/orpi_cv.html'),
                  ('coty', '/tmp/veille/orpi_coty.html'), ('mass', '/tmp/veille/orpi_mass.html'),
                  ('ff', '/tmp/veille/orpi_ff.html'), ('eure', '/tmp/veille/orpi_eure.html'),
                  ('sf', '/tmp/veille/orpi_sf.html'), ('p2', '/tmp/veille/orpi_p2.html')]:
    text = clean_text(fn)
    with open(fn, encoding='utf-8', errors='replace') as f:
        raw = f.read()
    
    # Orpi listing URLs - look for individual listing pages
    orpi_listing_urls = re.findall(r'href="(/location-immobiliere-le-havre[^"]*louer-appartement/[^"]+)"', raw)
    # Filter to actual listings (with a slug after the quartier)
    listing_urls = [u for u in list(dict.fromkeys(orpi_listing_urls)) if u.count('/') > 5]
    
    # Parse listings from text
    orpi_matches = re.findall(
        r'(\d[\d\s]*)\s*€\s*par\s*mois\s*(?:prix\s*en\s*hausse|prix\s*en\s*baisse)?\s*Location\s*Location\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m\s*2\s*Le\s*Havre\s*[-–]\s*([^|]+?)(?:\s+Favoris|\s+Exclusivité|\s+Loué|\s+Page|\s+Nos|\s+Vos|$)',
        text
    )
    
    # Also look for "Loué" (rented) listings
    orpi_loue = re.findall(
        r'Exclusivité\s+Loué\s+Location\s*Location\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m\s*2\s*Le\s*Havre\s*[-–]\s*([^|]+?)(?:\s+Favoris|\s+Exclusivité|\s+Page|\s+Nos|\s+Vos|$)',
        text
    )
    
    for m in orpi_matches:
        price = int(m[0].replace(' ', ''))
        pieces = int(m[1])
        surface = float(m[2])
        quartier = m[3].strip()[:80]
        orpi_all_matches.append({
            'price': price,
            'pieces': pieces,
            'surface': surface,
            'quartier': quartier,
            'source_page': name,
            'rented': False
        })
    
    for m in orpi_loue:
        pieces = int(m[0])
        surface = float(m[1])
        quartier = m[2].strip()[:80]
        orpi_all_matches.append({
            'price': None,
            'pieces': pieces,
            'surface': surface,
            'quartier': quartier,
            'source_page': name,
            'rented': True
        })
    
    # Also find listing IDs from raw HTML
    orpi_ids = re.findall(r'data-(?:id|ref)="([^"]+)"', raw)
    orpi_uuids = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', raw)
    
    # Check listing URLs
    if listing_urls:
        print(f"Orpi {name} listing URLs: {len(listing_urls)}")
        for u in listing_urls[:10]:
            print(f"  {u}")

# Check Orpi UUIDs for new ones
orpi_all_uuids = set()
for fn in ['/tmp/veille/orpi.html', '/tmp/veille/orpi_cv.html', '/tmp/veille/orpi_coty.html',
           '/tmp/veille/orpi_mass.html', '/tmp/veille/orpi_ff.html', '/tmp/veille/orpi_eure.html',
           '/tmp/veille/orpi_sf.html', '/tmp/veille/orpi_p2.html']:
    with open(fn, encoding='utf-8', errors='replace') as f:
        raw = f.read()
    uuids = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', raw)
    for u in uuids:
        orpi_all_uuids.add(f"orpi-{u}")

new_orpi = [u for u in orpi_all_uuids if u not in seen_ids]
print(f"\nOrpi total UUIDs: {len(orpi_all_uuids)}, NEW: {len(new_orpi)}")

# Print Orpi qualifying listings
print(f"\nOrpi total matches: {len(orpi_all_matches)}")
for o in orpi_all_matches:
    if not o['rented'] and o['pieces'] >= 2 and o['price'] and o['price'] <= 500 and o['surface'] >= 28:
        print(f"  *** QUALIFYING: {o['price']}€ | {o['pieces']}p | {o['surface']}m² | {o['quartier']} | page={o['source_page']}")
    elif not o['rented'] and o['pieces'] >= 2 and o['price'] and o['price'] <= 600:
        print(f"  * NEAR: {o['price']}€ | {o['pieces']}p | {o['surface']}m² | {o['quartier']} | page={o['source_page']}")