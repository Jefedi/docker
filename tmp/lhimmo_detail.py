import re
with open('/tmp/rental/lhimmo_loc.html', 'r') as f:
    content = f.read()
# Find all listing blocks with their price, surface, title, and URL
blocks = re.split(r'<div class="iwp__item">', content)
for block in blocks[1:]:
    url_match = re.search(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', block)
    title_match = re.search(r'<h3>(.*?)</h3>', block)
    price_match = re.search(r'iwp__price">([^<]+)</span>', block)
    surface_match = re.search(r'<span>(\d+)m²</span>', block)
    loc_match = re.search(r'class="localisation">\s*<span>([^<]+)</span>', block)
    
    url = url_match.group(1) if url_match else ''
    title = title_match.group(1) if title_match else ''
    price = price_match.group(1) if price_match else ''
    surface = surface_match.group(1) if surface_match else ''
    loc = loc_match.group(1) if loc_match else ''
    
    listing_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
    print(f'{listing_id}: {title} | {surface}m² | {price} | {loc}')