#!/usr/bin/env python3
"""Parse SquareHabitat using text content approach."""
import re, html as h, json

raw = open('/tmp/scrape/sqhab.html','r',errors='replace').read()

# Extract all text content
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all listing-like patterns: "X Appartement à louer - LE HAVRE, Y pièces LE HAVRE (NNNNN) Au prix de (par mois) XXX € cc DESCRIPTION"
listings_text = re.findall(r'(\d+\s+Appartement à louer[^|]+?Au prix de \(par mois\)\s*(\d[\d\s]*)\s*€\s*cc\s*([^|]+?)(?=\d+\s+Appartement à louer|$))', text)
print(f"SquareHabitat listings found: {len(listings_text)}")
for lt in listings_text:
    full = lt[0].strip()
    price = lt[1].strip()
    desc = lt[2].strip()[:200]
    # Extract pièces and surface
    pieces_match = re.search(r'(\d+)\s*pi[èe]ces?', full)
    surface_match = re.search(r'(\d+[,\.]?\d*)\s*m[²2]', desc)
    pieces = pieces_match.group(1) if pieces_match else '?'
    surface = surface_match.group(1) if surface_match else '?'
    price_clean = re.sub(r'\s', '', price)
    print(f"  {pieces}p {surface}m² {price_clean}€ — {desc[:150]}")

# Also try a different pattern - SquareHabitat may use JSON-LD or data attributes
# Let's look for script type="application/ld+json"
json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S)
print(f"\nJSON-LD blocks: {len(json_ld)}")
for j in json_ld[:3]:
    print(f"  {j[:300]}")

# Let's also look for data attributes
# SquareHabitat listing cards have data-id or similar
data_attrs = re.findall(r'data-(?:id|uuid|bien|annonce)="([^"]+)"', raw)
print(f"\nData IDs: {data_attrs[:10]}")