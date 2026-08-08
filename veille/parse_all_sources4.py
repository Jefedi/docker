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

def clean_raw(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        return f.read()

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# Parse Citya: combine pages 1-3, match GES IDs with listing data
citya_data = []
for page_num, fn in [(1, '/tmp/veille/citya.html'), (2, '/tmp/veille/citya_p2.html'), (3, '/tmp/veille/citya_p3.html')]:
    try:
        text = clean_text(fn)
    except:
        continue
    
    # Parse listing data
    pattern = re.compile(r'(\d[\d\s]*)\s*€\s+Le Havre\s*\((\d+)\)\s+Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)m[²2]?\s*([^.]*?)(?=\d+\s*€\s+Le Havre|$)')
    matches = pattern.findall(text)
    
    # Get GES IDs from raw HTML
    raw = clean_raw(fn)
    ges_ids = re.findall(r'GES\d+-\d+', raw)
    ges_ids = list(dict.fromkeys(ges_ids))
    
    for i, m in enumerate(matches):
        price = int(m[0].replace(' ', ''))
        cp = m[1]
        pieces = int(m[2])
        surface = float(m[3])
        features = m[4].strip()[:200]
        ges_id = ges_ids[i] if i < len(ges_ids) else None
        listing_id = f"citya-{ges_id}" if ges_id else f"citya-unknown-{page_num}-{i}"
        url = f"https://www.citya.com/annonces/location/appartement/le-havre-76351/{ges_id}" if ges_id else None
        
        is_new = listing_id not in seen_ids
        citya_data.append({
            'price': price,
            'pieces': pieces,
            'surface': surface,
            'cp': cp,
            'features': features,
            'ges_id': ges_id,
            'listing_id': listing_id,
            'url': url,
            'is_new': is_new,
            'page': page_num
        })

print(f"=== CITYA TOTAL: {len(citya_data)} listings ===")
qualifying = []
for c in citya_data:
    if c['pieces'] >= 2 and c['price'] <= 500 and c['surface'] >= 28:
        qualifying.append(c)
        print(f"  *** QUALIFYING: {c['price']}€ | {c['pieces']}p | {c['surface']}m² | {c['cp']} | {c['features']} | NEW={c['is_new']} | {c['url']}")
    elif c['pieces'] >= 2 and c['price'] <= 550:
        print(f"  * NEAR: {c['price']}€ | {c['pieces']}p | {c['surface']}m² | {c['cp']} | {c['features']} | NEW={c['is_new']}")

print(f"\n=== CITYA QUALIFYING & NEW: {len([q for q in qualifying if q['is_new']])} ===")

# Parse SqHab: extract listing URLs from raw HTML, match with text blocks
print("\n\n=== SQUAREHABITAT ===")
for fn_label, fn in [('P1', '/tmp/veille/sqhab.html'), ('P2', '/tmp/veille/sqhab_p2.html')]:
    raw = clean_raw(fn)
    text = clean_text(fn)
    
    # SqHab listing URLs - look for specific listing paths
    sqhab_urls = re.findall(r'href="(/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/[^"]+)"', raw)
    sqhab_urls = list(dict.fromkeys(sqhab_urls))
    
    # Also try broader pattern
    all_sqhab = re.findall(r'href="(/annonces/location/bien/[^"]+)"', raw)
    listing_urls = [u for u in list(dict.fromkeys(all_sqhab)) if 'le-havre' in u and 'page' not in u and 'immobilier/normandie/seine-maritime/le-havre-76600' != u]
    
    print(f"\nSqHab {fn_label} URLs: {len(listing_urls)}")
    for u in listing_urls[:15]:
        print(f"  {u}")
    
    # Extract T2/T3 blocks with prices
    # SqHab text has: "T[23] ... m² ... [price info]"
    t_blocks = re.findall(r'(T[2346][^|]{0,800})', text)
    for b in t_blocks:
        # Look for price
        pm = re.search(r'(\d[\d\s]*)\s*€', b)
        sm = re.search(r'(\d+\.?\d*)\s*m[²2]?', b)
        # Check for key features
        bl = b.lower()
        has_cuisine_sep = 'cuisine indépendante' in bl or 'cuisine indépendante' in bl or ('cuisine' in bl and 'indépendante' in bl)
        has_cuisine_ouverte = 'cuisine ouverte' in bl or 'cuisine américaine' in bl
        has_chambre = bool(re.search(r'\d+\s*chambre', bl)) or 'une chambre' in bl or 'd\'une chambre' in bl
        has_dernier = 'dernier étage' in bl or '5ème et dernier' in bl or '4ème et dernier' in bl
        
        price = int(pm.group(1).replace(' ', '')) if pm else None
        surface = float(sm.group(1)) if sm else None
        
        if price and surface and surface >= 28 and price <= 500:
            print(f"  *** POTENTIAL: {price}€ | {surface}m² | cs={has_cuisine_sep} co={has_cuisine_ouverte} ch={has_chambre} dernier={has_dernier}")
            print(f"    {b.strip()[:400]}")
        elif price and surface and surface >= 28 and price <= 600:
            print(f"  * NEAR: {price}€ | {surface}m²")
            print(f"    {b.strip()[:300]}")

# Parse HEUZE location page - check raw HTML more carefully
print("\n\n=== HEUZE LOCATION PAGE ===")
raw = clean_raw('/tmp/veille/heuze_loc.html')
text = clean_text('/tmp/veille/heuze_loc.html')

# Look for any listing URLs
heuze_all_urls = re.findall(r'href="(/location/[^"]+)"', raw)
heuze_all_urls = list(dict.fromkeys(heuze_all_urls))
print(f"Heuze all location URLs: {len(heuze_all_urls)}")
for u in heuze_all_urls[:30]:
    print(f"  {u}")

# Look for listing data in text
heuze_prices = re.findall(r'(\d[\d\s]*)\s*€', text)
print(f"\nHeuze prices found: {heuze_prices[:40]}")

# Look for T/F patterns
heuze_t = re.findall(r'(?:T[2346]|F[2346])\s*[^|]{0,300}', text)
print(f"Heuze T/F blocks: {len(heuze_t)}")
for b in heuze_t[:20]:
    print(f"  {b.strip()[:250]}")

# Parse Saint Roch location page
print("\n\n=== SAINT ROCH LOCATION PAGE ===")
raw = clean_raw('/tmp/veille/stroch_loc.html')
text = clean_text('/tmp/veille/stroch_loc.html')
stroch_all_urls = re.findall(r'href="(/location/[^"]+)"', raw)
stroch_all_urls = list(dict.fromkeys(stroch_all_urls))
print(f"StRoch all location URLs: {len(stroch_all_urls)}")
for u in stroch_all_urls[:30]:
    print(f"  {u}")
stroch_prices = re.findall(r'(\d[\d\s]*)\s*€', text)
print(f"\nStRoch prices found: {stroch_prices[:40]}")
stroch_t = re.findall(r'(?:T[2346]|F[2346])\s*[^|]{0,300}', text)
print(f"StRoch T/F blocks: {len(stroch_t)}")
for b in stroch_t[:20]:
    print(f"  {b.strip()[:250]}")

# Parse C21 listing page more carefully
print("\n\n=== C21 LISTING PAGE ===")
raw = clean_raw('/tmp/veille/c21_list.html')
text = clean_text('/tmp/veille/c21_list.html')
# Find listing URLs
c21_listing_urls = re.findall(r'href="(/annonces/location-appartement/[^"]+)"', raw)
c21_listing_urls = [u for u in list(dict.fromkeys(c21_listing_urls)) if 'v-le' not in u and 'v-trouville' not in u and 'v-deauville' not in u and 'v-' not in u]
print(f"C21 listing URLs: {len(c21_listing_urls)}")
for u in c21_listing_urls[:20]:
    print(f"  {u}")

# Find listing descriptions
c21_desc_start = text.find('Appartement à louer')
if c21_desc_start > 0:
    print(f"\nC21 listing text: {text[c21_desc_start:c21_desc_start+2000]}")
else:
    # Find by price
    c21_prices = re.findall(r'(\d[\d\s]*)\s*€\s*(?:par\s*mois|/mois)?\s*(?:charges\s*comprises|CC)?', text)
    print(f"\nC21 prices: {c21_prices[:30]}")