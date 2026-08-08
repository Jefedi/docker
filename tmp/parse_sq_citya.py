#!/usr/bin/env python3
"""Parse SquareHabitat and Citya to match listing IDs with prices."""
import re, html as h, json

# === SQUAREHABITAT ===
print("=== SQUAREHABITAT - Detailed parse ===")
raw = open('/tmp/scrape/sqhab.html','r',errors='replace').read()

# Find all listing UUIDs and their surrounding text
sq_links = re.findall(r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([a-f0-9-]+))"', raw)
unique_sq = []
for path, uuid in sq_links:
    if uuid not in [u for _, u in unique_sq]:
        unique_sq.append((path, uuid))

print(f"SquareHabitat listings: {len(unique_sq)}")

# For each UUID, find the price and details in surrounding HTML
for path, uuid in unique_sq:
    pos = raw.find(uuid)
    if pos < 0:
        continue
    # Get chunk around the UUID - look both before and after
    chunk_before = raw[max(0,pos-2000):pos]
    chunk_after = raw[pos:pos+3000]
    chunk = chunk_before + chunk_after
    
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find price
    price_match = re.search(r'(\d[\d\s]*)\s*€\s*cc', text, re.I)
    if not price_match:
        price_match = re.search(r'(\d[\d\s]*)\s*€\s*(?:par mois|/mois)', text, re.I)
    price = 0
    if price_match:
        price_str = re.sub(r'\s', '', price_match.group(1))
        try:
            price = int(price_str)
        except:
            pass
    
    # Find surface
    surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text)
    surface = 0
    if surface_match:
        try:
            surface = int(float(surface_match.group(1).replace(',', '.')))
        except:
            pass
    
    # Find pièces
    pieces_match = re.search(r'(\d+)\s*(?:pi[èe]ce|piece)', text, re.I)
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    
    # Find quartier
    quartier_match = re.search(r'(?:SECTEUR|QUARTIER|"([^"]+)")\s*[-:]\s*([A-Z][A-Z\s]+)', text)
    
    if price > 0:
        print(f"  UUID: {uuid} | Price: {price}€ | Surface: {surface}m² | Pièces: {pieces}")
        print(f"    URL: https://www.squarehabitat.fr{path}")
        # Show a context excerpt
        short = text[max(0,text.find(str(price))-100):text.find(str(price))+200]
        print(f"    Context: {short[:200]}")
        print()

# === CITYA ===
print("\n=== CITYA - Detailed parse ===")
raw = open('/tmp/scrape/citya.html','r',errors='replace').read()

# Find all Citya listing IDs
citya_links = re.findall(r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/([A-Z0-9-]+))"', raw)
unique_citya = []
for url, id_code in citya_links:
    if id_code not in [u for _, u in unique_citya]:
        unique_citya.append((url, id_code))

print(f"Citya listings: {len(unique_citya)}")

# For each listing, find price and details
for url, id_code in unique_citya:
    pos = raw.find(id_code)
    if pos < 0:
        continue
    chunk = raw[max(0,pos-1000):pos+2000]
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find price - look for pattern "XXX €" near the listing
    price_match = re.search(r'(\d[\d\s]*)\s*€', text)
    price = 0
    if price_match:
        price_str = re.sub(r'\s', '', price_match.group(1))
        try:
            price = int(price_str)
        except:
            pass
    
    # Find surface and pièces
    surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text)
    surface = 0
    if surface_match:
        try:
            surface = int(float(surface_match.group(1).replace(',', '.')))
        except:
            pass
    
    pieces_match = re.search(r'(\d+)\s*(?:pi[èe]ce|piece)', text, re.I)
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    
    if price > 0 and pieces >= 2:
        print(f"  ID: {id_code} | Price: {price}€ | Surface: {surface}m² | Pièces: {pieces}")
        print(f"    URL: {url}")
        print(f"    Context: {text[:200]}")
        print()