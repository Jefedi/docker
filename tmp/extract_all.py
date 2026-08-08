import re, json

def extract_sqhab():
    html = open('/opt/data/tmp/sqhab.html').read()
    listings = []
    # Find listing blocks with link, title, price, surface
    # Pattern: each listing has a link like /square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/UUID
    link_pattern = r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/[a-f0-9-]+)"'
    links = re.findall(link_pattern, html)
    
    # Find prices and surfaces near each link
    # The HTML structure has card divs with price and details
    # Let's find all "card" blocks
    
    # Extract all data-attributes or text blocks
    # Find all unique listing IDs
    seen = set()
    for l in links:
        uuid = l.split('/')[-1]
        if uuid not in seen:
            seen.add(uuid)
            listings.append({
                'id': f'sqhab-{uuid}',
                'url': f'https://www.squarehabitat.fr{l}',
                'source': 'sqhab'
            })
    
    # Now try to extract prices and surfaces from the page
    # SquareHabitat uses data in the card structure
    # Let's find the card containing each link and extract price/surface
    for uuid in seen:
        # Find the block around this UUID
        pattern = rf'(href="[^"]*{uuid}[^"]*"[^>]*>.*?)(?=<article|<div class="[^"]*(?:card|item|annonce))'
    
    # Alternative: parse the whole page text for price/surface patterns
    # Remove HTML tags and get text
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Find patterns like "XXX €" near "m²" 
    # Let's just extract all price+surface pairs
    blocks = re.split(r'(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/[a-f0-9-]+)', text)
    
    return listings, text

def extract_citya():
    html = open('/opt/data/tmp/citya.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Find listing IDs
    # Citya URLs: /annonces/location/appartement/le-havre-76351/...
    # Or data-bien-id
    ids = re.findall(r'GES\d+-\d+', html)
    urls = re.findall(r'href="(/annonces/location/appartement/[^"]+)"', html)
    
    # Also look for JSON data
    json_match = re.findall(r'data-bien[^=]*="([^"]+)"', html)
    
    return list(set(ids)), urls, text

def extract_orpi():
    html = open('/opt/data/tmp/orpi.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Orpi uses listing cards with data attributes
    # Find listing IDs
    ids = re.findall(r'data-id="([^"]+)"', html)
    if not ids:
        ids = re.findall(r'/location-immobiliere[^"]*?/([a-f0-9-]{36})', html)
    
    # Find all links to individual listings
    listing_urls = re.findall(r'href="(/location-immobiliere[^"]*?(?!louer-appartement)[^"]*)"', html)
    
    return ids, listing_urls, text

def extract_ja():
    html = open('/opt/data/tmp/ja.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Jullien-Allix listing URLs
    urls = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce/a-louer-[^"]+)"', html)
    if not urls:
        urls = re.findall(r'href="(/annonce/a-louer-[^"]+)"', html)
    
    # Also try to find listing titles/slugs
    slugs = re.findall(r'a-louer-[a-z0-9-]+', html)
    
    return urls, slugs, text

def extract_c21():
    html = open('/opt/data/tmp/c21.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Century 21 uses listing IDs
    ids = re.findall(r'data-id="([^"]+)"', html)
    urls = re.findall(r'href="(/louer/[^"]+)"', html)
    
    return ids, urls, text

def extract_lhimmo():
    html = open('/opt/data/tmp/lhimmo.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Find listing links
    urls = re.findall(r'href="([^"]*appartement[^"]*)"', html, re.IGNORECASE)
    slugs = re.findall(r'(?:appartement|maison|local)[a-z0-9-]+', html, re.IGNORECASE)
    
    return urls, slugs, text

def extract_heuze():
    html = open('/opt/data/tmp/heuze.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # HEUZE listing links
    urls = re.findall(r'href="(/location/[^"]*)"', html)
    ids = re.findall(r'(?:VA|LA|LS)\d+', html)
    
    return urls, ids, text

def extract_stroch():
    html = open('/opt/data/tmp/stroch.html').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    
    # Saint Roch listing links
    urls = re.findall(r'href="(/location/[^"]*)"', html)
    ids = re.findall(r'LA\d+', html)
    
    return urls, ids, text

# Run all extractors
print("=== SquareHabitat ===")
sq_listings, sq_text = extract_sqhab()
print(f"Listings: {len(sq_listings)}")
for l in sq_listings[:5]:
    print(f"  {l['id']} | {l['url'][:80]}")

print("\n=== Citya ===")
citya_ids, citya_urls, citya_text = extract_citya()
print(f"IDs: {len(citya_ids)}, URLs: {len(citya_urls)}")
print(f"Sample IDs: {list(set(citya_ids))[:10]}")
for u in citya_urls[:5]:
    print(f"  URL: {u[:80]}")

print("\n=== Orpi ===")
orpi_ids, orpi_urls, orpi_text = extract_orpi()
print(f"IDs: {len(orpi_ids)}, URLs: {len(orpi_urls)}")
for i in orpi_ids[:5]:
    print(f"  ID: {i}")
for u in orpi_urls[:5]:
    print(f"  URL: {u[:80]}")

print("\n=== Jullien-Allix ===")
ja_urls, ja_slugs, ja_text = extract_ja()
print(f"URLs: {len(ja_urls)}, Slugs: {len(set(ja_slugs))}")
for s in list(set(ja_slugs))[:10]:
    print(f"  slug: {s}")

print("\n=== Century 21 ===")
c21_ids, c21_urls, c21_text = extract_c21()
print(f"IDs: {len(c21_ids)}, URLs: {len(c21_urls)}")
for u in c21_urls[:10]:
    print(f"  URL: {u[:80]}")

print("\n=== LH Immo ===")
lhimmo_urls, lhimmo_slugs, lhimmo_text = extract_lhimmo()
print(f"URLs: {len(lhimmo_urls)}, Slugs: {len(set(lhimmo_slugs))}")
for s in list(set(lhimmo_slugs))[:10]:
    print(f"  slug: {s}")

print("\n=== HEUZE ===")
heuze_urls, heuze_ids, heuze_text = extract_heuze()
print(f"URLs: {len(heuze_urls)}, IDs: {len(set(heuze_ids))}")
for i in list(set(heuze_ids))[:10]:
    print(f"  ID: {i}")

print("\n=== Saint Roch ===")
stroch_urls, stroch_ids, stroch_text = extract_stroch()
print(f"URLs: {len(stroch_urls)}, IDs: {len(set(stroch_ids))}")
for i in list(set(stroch_ids))[:10]:
    print(f"  ID: {i}")