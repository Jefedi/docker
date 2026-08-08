import re, html, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

for fn_label, fn in [('main', '/tmp/veille/orpi.html'), ('cv', '/tmp/veille/orpi_cv.html'), ('coty', '/tmp/veille/orpi_coty.html'),
                      ('mass', '/tmp/veille/orpi_mass.html'), ('ff', '/tmp/veille/orpi_ff.html'), ('eure', '/tmp/veille/orpi_eure.html'),
                      ('sf', '/tmp/veille/orpi_sf.html'), ('p2', '/tmp/veille/orpi_p2.html')]:
    with open(fn, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    all_listings = re.findall(
        r'(?:(\d[\d\s]*)\s*€\s*par\s*mois\s*(?:prix\s*en\s*hausse|prix\s*en\s*baisse)?)?\s*(?:Exclusivité\s+)?(Loué\s+)?Location\s*Location\s*Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d+\.?\d*)\s*m\s*2\s*Le\s*Havre\s*[-–]\s*([^|]+?)(?:\s+Favoris|\s+Exclusivité|\s+Page|\s+Nos|\s+Vos|$)',
        text
    )
    
    listing_urls = re.findall(r'href="(/location-immobiliere-le-havre[^/]+/louer-appartement/[^"]+)"', content)
    actual_listings = [u for u in list(dict.fromkeys(listing_urls)) if u.count('/') > 5]
    
    print(f'Orpi {fn_label}: {len(all_listings)} text listings, {len(actual_listings)} listing URLs')
    
    for i, m in enumerate(all_listings):
        price_str = m[0].strip() if m[0] else ''
        rented = bool(m[1])
        pieces = int(m[2])
        surface = float(m[3])
        quartier = m[4].strip()[:80]
        price = int(price_str.replace(' ', '')) if price_str else None
        
        url = actual_listings[i] if i < len(actual_listings) else None
        listing_id = None
        if url:
            slug = url.split('/')[-1]
            listing_id = f'orpi-{slug}'
        
        is_new = listing_id not in seen_ids if listing_id else True
        
        if not rented and pieces >= 2 and price and price <= 500 and surface >= 28:
            print(f'  *** QUAL: {price}€ | {pieces}p | {surface}m² | {quartier} | NEW={is_new} | {url}')
        elif not rented and pieces >= 2 and price and price <= 600:
            print(f'  * NEAR: {price}€ | {pieces}p | {surface}m² | {quartier} | NEW={is_new} | {url}')
        elif rented and pieces >= 2:
            print(f'  RENTED: {pieces}p | {surface}m² | {quartier}')
    print()