import re
with open('/tmp/rental/lhimmo_loc.html', 'r') as f:
    content = f.read()
listings = re.findall(r'<a href="(https://www\.lhimmo\.com/annonce/[^"]+)"', content)
print(f'LH Immo total: {len(listings)}')
for url in listings:
    idx = content.find(url)
    if idx >= 0:
        block = content[max(0, idx-200):idx+500]
        price_match = re.search(r'iwp__price">(\d[\d\s]*)\s*€</span>', block)
        surface_match = re.search(r'(\d+)m²</span>', block)
        title_match = re.search(r'<h3[^>]*>([^<]+)</h3>', block)
        price = int(re.sub(r'\s', '', price_match.group(1))) if price_match else 0
        surface = int(surface_match.group(1)) if surface_match else 0
        title = title_match.group(1) if title_match else ''
        listing_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        print(f'  {listing_id}: {title} {surface}m² {price}€')