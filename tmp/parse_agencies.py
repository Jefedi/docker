import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

def check_seen(seen_id):
    return seen_id in seen_ids

def extract_listings_generic(html, source_prefix, source_name):
    """Generic extraction: look for price patterns, room counts, surfaces"""
    body_start = html.find('<body')
    body = html[body_start:].replace('&nbsp;', ' ').replace('&apos;', "'")
    
    # Try to find listing cards/articles
    listings = []
    
    # Common patterns in French real estate sites
    # Look for "T2", "T3", "2 pièces", "F2" etc with surface
    room_patterns = [
        r'(\d+)\s*(?:pièces|piece|pieces|p)\s*[-:|·]\s*(\d+(?:[.,]\d+)?)\s*m²',
        r'T(\d+)\s*[-:|·]?\s*(\d+(?:[.,]\d+)?)\s*m²',
        r'F(\d+)\s*[-:|·]?\s*(\d+(?:[.,]\d+)?)\s*m²',
    ]
    
    # Price patterns
    price_patterns = [
        r'(\d[\d\s.,]*)\s*€\s*/?\s*mois',
        r'(\d[\d\s.,]*)\s*€\s*CC',
        r'(\d[\d\s.,]*)\s*€\s*charges comprises',
        r'Loyer\s*:?\s*(\d[\d\s.,]*)\s*€',
    ]
    
    # Try JSON-LD
    jsonld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', body, re.DOTALL)
    for j in jsonld_matches:
        try:
            data = json.loads(j)
            if isinstance(data, dict) and data.get("@type") in ["Apartment", "Residence", "Product"]:
                listings.append({"source": source_name, "jsonld": data})
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") in ["Apartment", "Residence"]:
                        listings.append({"source": source_name, "jsonld": item})
        except:
            pass
    
    # Find listing IDs/links
    link_patterns = [
        r'href="(/[^"]*(?:location|louer|annonce|annonce/location)[^"]*)"',
        r'href="(https?://[^"]*(?:location|louer|annonce)[^"]*)"',
    ]
    
    all_links = set()
    for pattern in link_patterns:
        matches = re.findall(pattern, body)
        for m in matches:
            all_links.add(m)
    
    # Print summary
    print(f"\n=== {source_name} ({source_prefix}) ===")
    print(f"  Body size: {len(body)} chars")
    print(f"  JSON-LD listings: {len([l for l in listings if 'jsonld' in l])}")
    print(f"  Links found: {len(all_links)}")
    
    # Extract prices
    all_prices = []
    for p in price_patterns:
        matches = re.findall(p, body, re.IGNORECASE)
        all_prices.extend(matches)
    
    # Extract room/surface
    all_rooms_surface = []
    for p in room_patterns:
        matches = re.findall(p, body)
        all_rooms_surface.extend(matches)
    
    print(f"  Prices found: {len(all_prices)}")
    print(f"  Room/surface found: {len(all_rooms_surface)}")
    
    # Try to identify individual listings
    # Many sites use data attributes or specific class names
    # Let's look for article tags or listing cards
    article_count = len(re.findall(r'<article', body, re.IGNORECASE))
    card_count = len(re.findall(r'class="[^"]*card[^"]*"', body, re.IGNORECASE))
    annonce_count = len(re.findall(r'class="[^"]*annonce[^"]*"', body, re.IGNORECASE))
    print(f"  Articles: {article_count}, Cards: {card_count}, Annonce divs: {annonce_count}")
    
    # Show some prices
    for p in all_prices[:10]:
        clean = re.sub(r'\s','',p).strip()
        try:
            val = int(clean)
            if 200 <= val <= 500:
                print(f"  Price in range: {val}€")
        except:
            pass
    
    return listings, all_links

# Parse each site
sites = [
    ('sqhab', 'SquareHabitat', '/opt/data/tmp/sqhab.html'),
    ('citya', 'Citya', '/opt/data/tmp/citya.html'),
    ('lhimmo', 'LH Immo', '/opt/data/tmp/lhimmo.html'),
    ('c21', 'Century21', '/opt/data/tmp/c21.html'),
    ('orpi', 'Orpi', '/opt/data/tmp/orpi.html'),
    ('heuze', 'HEUZE', '/opt/data/tmp/heuze.html'),
    ('ja', 'Jullien-Allix', '/opt/data/tmp/ja.html'),
    ('stroch', 'Saint Roch', '/opt/data/tmp/stroch.html'),
]

for prefix, name, path in sites:
    try:
        with open(path) as f:
            html = f.read()
        extract_listings_generic(html, prefix, name)
    except Exception as e:
        print(f"\n=== {name} ({prefix}) === ERROR: {e}")