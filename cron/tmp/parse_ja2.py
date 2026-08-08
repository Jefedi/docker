import re, html as htmlmod, json

content = open('/tmp/ja.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Parse all listings from Jullien & Allix
# Pattern: "A Louer Appartement De Type FX ... ADDRESS ... Appartement N Chambres ... XX m² ... Location ... XXX€ /par mois"
listings = []
# Find all blocks that start with "A Louer" or "A louer"
pattern = r'A [Ll]ouer\s+(.+?)(?=A [Ll]ouer|$)'
blocks = re.split(r'(?=A [Ll]ouer)', text)
for block in blocks:
    if 'Appartement' not in block and 'appartement' not in block:
        continue
    if 'F1' in block and 'F2' not in block and 'F3' not in block and 'F4' not in block and 'F6' not in block:
        continue  # Skip F1
    if 'garage' in block.lower() or 'parking' in block.lower() or 'local commercial' in block.lower() or 'emplacement' in block.lower():
        continue
    
    # Extract type
    type_match = re.search(r'(?:Type\s+)?F(\d)', block)
    if not type_match:
        continue
    pieces = int(type_match.group(1))
    if pieces < 2:
        continue
    
    # Extract surface
    surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m²', block)
    surface = float(surface_match.group(1)) if surface_match else None
    
    # Extract price
    price_match = re.search(r'(\d{3,4})\s*€\s*/?par\s*mois', block)
    price = int(price_match.group(1)) if price_match else None
    
    # Extract address/quartier
    addr_match = re.search(r'(LE HAVRE|HARFLEUR|Sainte-Adresse)[–\-\s]*(.+?)(?:\d+\s+rue|\d+\s+place|rue\s+\w+|place\s+\w+|Appartement)', block)
    
    # Extract slug from link
    slug_match = re.search(r'href="(/annonce-immobiliere/a-louer-[^"]+)"', content)
    
    # Find the link for this listing
    # Look for the title in the block and match to a link
    title_match = re.search(r'A [Ll]ouer\s+(.+?)(?:\d+\s+(?:place|rue|rue\s))', block)
    title = title_match.group(1).strip() if title_match else ''
    
    # Extract address
    addr_line_match = re.search(r'(\d+\s+(?:place|rue|boulevard|avenue)\s+[\w\s]+)\s+\d{5}', block)
    addr = addr_line_match.group(1).strip() if addr_line_match else ''
    
    if surface and surface >= 28 and price and price <= 500:
        listings.append({
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'title': title[:120],
            'addr': addr,
            'block': block[:500]
        })

# Also find all links
all_links = re.findall(r'href="(/annonce-immobiliere/a-louer-[^"]+)"', content)
unique_links = list(dict.fromkeys(all_links))

# Match links to listings
for l in listings:
    # Find matching link by title keywords
    title_words = re.findall(r'\w+', l['title'].lower())
    for link in unique_links:
        link_lower = link.lower()
        if all(w in link_lower for w in title_words[:3]):
            l['link'] = f"https://www.jullien-allix.fr{link}"
            break

print(f"JA T2+ listings with surface >= 28 and price <= 500: {len(listings)}")
for l in listings:
    print(f"\n  F{l['pieces']} {l['surface']}m² | {l['price']}€/mois")
    print(f"  Title: {l['title']}")
    print(f"  Addr: {l['addr']}")
    print(f"  Link: {l.get('link', 'NOT FOUND')}")
    print(f"  Block: {l['block'][:300]}")