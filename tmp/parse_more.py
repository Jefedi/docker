#!/usr/bin/env python3
"""Parse SquareHabitat page 2 and Orpi/Citya for T2+ under 500€."""
import re, html as h

# === SQUAREHABITAT PAGE 2 ===
print("=== SQUAREHABITAT PAGE 2 ===")
raw = open('/tmp/scrape/sqhab2.html','r',errors='replace').read()
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

listings = re.findall(r'(\d+)\s+Appartement à louer[^|]+?Au prix de \(par mois\)\s*(\d[\d\s]*)\s*€\s*cc\s*(.+?)(?=\d+\s+Appartement à louer|$)', text, re.I)
print(f"Page 2 listings: {len(listings)}")
for num, price_str, desc in listings:
    price = int(re.sub(r'\s', '', price_str))
    # Extract pièces from text before the description
    full_text = f"{num} Appartement à louer ... {price_str} € cc {desc}"
    pieces_match = re.search(r',\s*(\d+)\s*pi[èe]ces', full_text[:100])
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    surface_match = re.search(r'(\d+[,\.]?\d*)\s*m[²2]', desc[:300])
    surface = surface_match.group(1) if surface_match else '?'
    cuisine_sep = bool(re.search(r'cuisine\s*(?:ind[ée]pendante|s[ée]par[ée]e|ferm[ée]e)', desc, re.I))
    
    tag = "✅" if price <= 500 and pieces >= 2 else "❌"
    print(f"  {tag} {pieces}p {surface}m² {price}€ | Cuisine sep: {cuisine_sep} | {desc[:150]}")

# === ORPI - more detailed ===
print("\n=== ORPI - T2+ under 500€ ===")
raw = open('/tmp/scrape/orpi.html','r',errors='replace').read()
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find all Orpi listings with prices
# Orpi patterns: "XXX € par mois Location Location Appartement N pièces XX m² Lieu"
orpi_listings = re.findall(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*Location\s*Location\s*Appartement\s*(\d+)\s*pi[èe]ces\s*(\d[\d,\.]*)\s*m\s*[²2]?\s*([^\d]+?)(?=\d+[\d\s]*€\s*par\s*mois|$)', text)
print(f"Orpi listings: {len(orpi_listings)}")
for price_str, pieces, surface, location in orpi_listings:
    price = int(re.sub(r'\s', '', price_str))
    pieces = int(pieces)
    surface_num = surface.strip()
    loc = location.strip()[:100]
    tag = "✅" if price <= 500 and pieces >= 2 else "❌"
    print(f"  {tag} {pieces}p {surface_num}m² {price}€ — {loc}")

# === CITYA - more detailed ===
print("\n=== CITYA - T2+ under 500€ ===")
raw = open('/tmp/scrape/citya.html','r',errors='replace').read()
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find Citya listings: "Appartement N pièces XXm² ... XXX € Le Havre"
citya_listings = re.findall(r'Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d[\d,\.]*)\s*m[²2]?\s*([^€]+?)\s*(\d[\d\s]*)\s*€\s*(?:Le Havre|Havre)', text)
print(f"Citya listings: {len(citya_listings)}")
for pieces, surface, features, price_str in citya_listings:
    price = int(re.sub(r'\s', '', price_str))
    pieces = int(pieces)
    feat = features.strip()[:100]
    tag = "✅" if price <= 500 and pieces >= 2 else "❌"
    print(f"  {tag} {pieces}p {surface}m² {price}€ — {feat}")