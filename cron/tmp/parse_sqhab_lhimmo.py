#!/usr/bin/env python3
"""Parse SquareHabitat and LHImmo for detailed listing info."""
import re, json

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
    s = s.replace('&eacute;', 'é').replace('&egrave;', 'è').replace('&agrave;', 'à')
    return re.sub(r'\s+', ' ', s).strip()

# --- SquareHabitat ---
print("=== SQUAREHABITAT ===")
with open('/tmp/sqhab_havre.html', 'r', errors='replace') as f:
    html = f.read()

# Find data-context="annonce" blocks
annonce_blocks = re.split(r'data-context="annonce"', html)
print(f"Annonce blocks: {len(annonce_blocks)-1}")

for i, block in enumerate(annonce_blocks[1:], 1):
    snippet = block[:3000]
    # Get URL
    url_match = re.search(r'href="(/annonces/location/bien/appartement/[^"]+)"', snippet)
    url = url_match.group(1) if url_match else ''
    
    # Get price
    price_match = re.search(r'(\d[\d\s]*)\s*€', clean(snippet[:1000]))
    price = price_match.group(1).strip() if price_match else '?'
    
    # Get title
    title_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', snippet, re.DOTALL)
    title = clean(title_match.group(1)) if title_match else ''
    
    # Get surface
    surface_match = re.search(r'(\d+)\s*m[²2]', snippet)
    surface = surface_match.group(1) if surface_match else '?'
    
    # Get rooms/pieces
    rooms_match = re.search(r'(\d+)\s*(?:pi[èe]ce|piece|p\b)', snippet, re.IGNORECASE)
    rooms = rooms_match.group(1) if rooms_match else '?'
    
    # Get description
    desc_text = clean(snippet[:2000])
    
    print(f"\n  #{i}: {title[:80]}")
    print(f"     Price: {price}€ | Surface: {surface}m² | Rooms: {rooms}")
    print(f"     URL: https://www.squarehabitat.fr{url}" if url else "     URL: N/A")
    print(f"     Desc: {desc_text[:200]}")

# --- LHImmo ---
print("\n\n=== LH IMMO ===")
with open('/tmp/lhimmo_annonces.html', 'r', errors='replace') as f:
    html = f.read()

# Find listing blocks - LHImmo uses article or div blocks
listing_links = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Unique listing links: {len(unique_links)}")

for link in unique_links:
    # Find the block around this link
    pos = html.find(link)
    start = max(0, pos - 2000)
    end = min(len(html), pos + 2000)
    block = html[start:end]
    
    clean_block = clean(block)
    
    # Extract price
    price_match = re.search(r'(\d[\d\s]*)\s*€', clean_block)
    price = price_match.group(1).strip() if price_match else '?'
    
    # Extract surface
    surface_match = re.search(r'(\d+)\s*m[²2]', clean_block)
    surface = surface_match.group(1) if surface_match else '?'
    
    # Title from URL
    title = link.split('/annonce/')[-1].replace('-', ' ')
    
    print(f"\n  {title[:60]}")
    print(f"     Price: {price}€ | Surface: {surface}m²")
    print(f"     URL: {link}")
    print(f"     Context: {clean_block[:200]}")