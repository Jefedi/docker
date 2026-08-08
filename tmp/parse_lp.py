import re, json

all_listings = []

for p in range(1,7):
    try:
        html = open(f'/opt/data/tmp/lp_page{p}.html').read()
    except:
        continue
    
    # Find all article blocks with listing data
    # The h2 pattern: "Location Appartement à Le Havre X pièces | Y m²"
    h2_pattern = r'<h2[^>]*>(.*?)</h2>'
    h2s = re.findall(h2_pattern, html, re.DOTALL)
    
    # Clean h2s
    clean_h2s = []
    for h in h2s:
        h = re.sub(r'<[^>]+>', '', h)
        h = h.replace('&nbsp;', ' ').strip()
        h = ' '.join(h.split())
        if 'pièce' in h:
            clean_h2s.append(h)
    
    # Find URLs - listing detail pages
    url_pattern = r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"'
    urls = re.findall(url_pattern, html)
    
    # Find prices - the rent is usually near the listing
    # Pattern: "XXX €" near "Loyer" or in price section
    # Let's find blocks with both price and the h2
    
    # Find all listing blocks - look for divs containing both h2 and price
    # Split by article or listing div
    blocks = re.split(r'(?=<article|class="[^"]*item[^"]*")', html)
    
    # Alternative: find all price patterns
    # Prices in Le-Partenaire are like "470 €" or "470,00 €"
    
    # Let's try a different approach - find the card containers
    # Each card has: h2 (title), price, DPE, charges, link
    
    # Find all "Voir l'annonce" links with their associated data
    card_pattern = r'<article[^>]*>(.*?)</article>'
    cards = re.findall(card_pattern, html, re.DOTALL)
    
    if not cards:
        # Try div-based cards
        card_pattern = r'<div[^>]*class="[^"]*(?:card|item|annonce|listing)[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>'
        cards = re.findall(card_pattern, html, re.DOTALL)
    
    print(f"Page {p}: {len(clean_h2s)} h2s, {len(urls)} urls, {len(cards)} cards")
    
    # Match h2s with URLs by order
    for i, h2 in enumerate(clean_h2s):
        url = urls[i] if i < len(urls) else 'N/A'
        # Extract rooms and surface from h2
        rooms_match = re.search(r'(\d+)\s*pièce', h2)
        surf_match = re.search(r'(\d+)\s*m', h2)
        rooms = int(rooms_match.group(1)) if rooms_match else 0
        surface = int(surf_match.group(1)) if surf_match else 0
        
        # Extract listing ID from URL
        id_match = re.search(r'/(\d+)$', url)
        list_id = id_match.group(1) if id_match else 'N/A'
        
        all_listings.append({
            'page': p,
            'idx': i,
            'id': list_id,
            'url': f'https://www.le-partenaire.fr{url}' if url != 'N/A' else '',
            'rooms': rooms,
            'surface': surface,
            'title': h2
        })

# Filter for T2+ and surface >= 28
filtered = [l for l in all_listings if l['rooms'] >= 2 and l['surface'] >= 28]
print(f"\n=== ALL listings: {len(all_listings)} ===")
print(f"=== T2+ >= 28m²: {len(filtered)} ===")
for l in filtered:
    print(f"  lp-{l['id']} | T{l['rooms']} | {l['surface']}m² | {l['url']}")

# Save all for later price extraction
with open('/opt/data/tmp/lp_listings.json','w') as f:
    json.dump(all_listings, f)