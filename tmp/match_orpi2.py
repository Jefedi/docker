#!/usr/bin/env python3
"""Match Orpi page 2 - improved approach using text blocks."""
import re, html as h

raw = open('/tmp/scrape/orpi2.html','r',errors='replace').read()
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all UUIDs with their position in the text
uuid_positions = []
for m in re.finditer(r'/annonce-location-appartement-t(\d)-le-havre-76600-([a-f0-9-]+)', raw):
    uuid_positions.append((m.start(), m.group(1), m.group(2)))

# Deduplicate
seen = set()
unique_uuids = []
for pos, t, uid in uuid_positions:
    if uid not in seen:
        seen.add(uid)
        unique_uuids.append((pos, t, uid))

# The issue is that the raw HTML has the UUID links but the prices are in different parts
# Let me try a text-based approach instead
# Find all "€ par mois Location Location Appartement N pièces" patterns

# Find all price+listing blocks in text
price_blocks = list(re.finditer(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*Location\s*Location\s*Appartement\s*(\d+)\s*pi[èe]ces?\s*(\d[\d,\.]*)\s*m\s*²?\s*([^€]+?)(?=\d+[\d\s]*€\s*par\s*mois|Exclusivité 290|Location Immobilière|$)', text))
print(f"Price blocks found: {len(price_blocks)}")

# For each block, find the nearest UUID before it in the text
for i, m in enumerate(price_blocks):
    price_str = m.group(1)
    pieces = int(m.group(2))
    surface = m.group(3)
    location = m.group(4).strip()[:150]
    price = int(re.sub(r'\s', '', price_str))
    surface_num = float(surface.replace(',', '.'))
    
    # Find the text position
    text_pos = m.start()
    
    # Convert text position to raw HTML position (approximate)
    # Find the UUID that appears just before this text in the raw HTML
    nearest_uuid = None
    nearest_t = None
    for pos, t, uid in unique_uuids:
        if pos < text_pos + 5000:  # Allow some flexibility
            nearest_uuid = uid
            nearest_t = t
    
    tag = "OK" if price <= 500 and pieces >= 2 and surface_num >= 28 else "NO"
    print(f"  [{tag}] T{nearest_t} UUID:{nearest_uuid} {pieces}p {surface}m2 {price}euro -- {location[:120]}")
    if tag == "OK":
        print(f"    URL: https://www.orpi.com/annonce-location-appartement-t{nearest_t}-le-havre-76600-{nearest_uuid}/")