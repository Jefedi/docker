#!/usr/bin/env python3
"""Match Orpi qualifying listings with their UUIDs by looking at raw HTML."""
import re, html as h

raw = open('/tmp/scrape/orpi2.html','r',errors='replace').read()

# Find all UUIDs in order
uuids = re.findall(r'/annonce-location-appartement-t(\d)-le-havre-76600-([a-f0-9-]+)', raw)
# Deduplicate
unique_uuids = []
for t, uid in uuids:
    if uid not in [u for _, u in unique_uuids]:
        unique_uuids.append((t, uid))

# Find all prices in order
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# The Orpi listing structure: each listing has a URL followed by price info
# Let's find each listing block by looking at the raw HTML structure

# Find all listing entries with their position in the raw HTML
listing_positions = []
for m in re.finditer(r'/annonce-location-appartement-t(\d)-le-havre-76600-([a-f0-9-]+)', raw):
    listing_positions.append((m.start(), m.group(1), m.group(2)))

# Deduplicate by UUID (keep first occurrence)
seen = set()
unique_positions = []
for pos, t, uid in listing_positions:
    if uid not in seen:
        seen.add(uid)
        unique_positions.append((pos, t, uid))

print(f"Unique listings on page 2: {len(unique_positions)}")

# For each listing, find the price in the text after its URL
for i, (pos, t, uid) in enumerate(unique_positions):
    # Get the chunk from this listing to the next one
    next_pos = unique_positions[i+1][0] if i+1 < len(unique_positions) else len(raw)
    chunk = raw[pos:next_pos]
    chunk_text = re.sub(r'<[^>]+>', ' ', chunk)
    chunk_text = h.unescape(chunk_text)
    chunk_text = re.sub(r'\s+', ' ', chunk_text).strip()
    
    # Find price
    price_match = re.search(r'(\d[\d\s]*)\s*€\s*par\s*mois', chunk_text)
    price = 0
    if price_match:
        price_str = re.sub(r'\s', '', price_match.group(1))
        try:
            price = int(price_str)
        except:
            pass
    
    # Find surface
    surface_match = re.search(r'(\d[\d,\.]*)\s*m\s*²', chunk_text)
    surface = 0
    if surface_match:
        try:
            surface = float(surface_match.group(1).replace(',', '.'))
        except:
            pass
    
    # Find pièces
    pieces_match = re.search(r'(\d+)\s*pi[èe]ces?', chunk_text)
    pieces = int(pieces_match.group(1)) if pieces_match else int(t)
    
    # Find quartier
    quartier_match = re.search(r'Le Havre\s*-\s*([^-]+?)(?:\s+Favoris|\s+Message)', chunk_text)
    quartier = quartier_match.group(1).strip() if quartier_match else '?'
    
    # Check cuisine
    cuisine_sep = bool(re.search(r'cuisine\s*(?:s[ée]par[ée]e|ind[ée]pendante|ferm[ée]e)', chunk_text, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette', chunk_text, re.I))
    
    if price > 0:
        tag = "OK" if price <= 500 and pieces >= 2 and surface >= 28 else "NO"
        print(f"  [{tag}] T{t} UUID:{uid} {pieces}p {surface}m2 {price}euro | Quartier: {quartier} | C.sep: {cuisine_sep} C.ouv: {cuisine_ouverte}")
        if tag == "OK":
            print(f"    URL: https://www.orpi.com/annonce-location-appartement-t{t}-le-havre-76600-{uid}/")
            print(f"    Desc: {chunk_text[:200]}")