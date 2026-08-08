#!/usr/bin/env python3
"""Extract details from individual listing pages."""
import re

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
    s = s.replace('&eacute;', 'é').replace('&egrave;', 'è').replace('&agrave;', 'à').replace('&ccedil;', 'ç')
    return re.sub(r'\s+', ' ', s).strip()

# --- SquareHabitat new listing ---
print("=== SQUAREHABITAT 8a7d0d7c ===")
with open('/tmp/sqhab_new.html', 'r', errors='replace') as f:
    html = f.read()

# Look for JSON-LD
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
for b in ld_blocks:
    if 'price' in b.lower() or 'rent' in b.lower() or 'location' in b.lower():
        print(f"  JSON-LD: {b[:500]}")

# Look for price, surface, rooms in page
full_text = clean(html)

# Find price
price_matches = re.findall(r'(\d[\d\s]*)\s*€\s*/?\s*mois', full_text, re.IGNORECASE)
print(f"  Prices /mois: {price_matches[:5]}")
price_matches2 = re.findall(r'(\d[\d\s]*)\s*€', full_text)
print(f"  All prices: {price_matches2[:10]}")

# Find surface
surface_matches = re.findall(r'(\d+)\s*m[²2]', full_text)
print(f"  Surfaces: {surface_matches[:10]}")

# Find room count
room_matches = re.findall(r'(\d+)\s*(?:pi[èe]ce|piece)', full_text, re.IGNORECASE)
print(f"  Rooms: {room_matches[:5]}")

# Find title
title_match = re.search(r'<title>(.*?)</title>', html)
print(f"  Title: {clean(title_match.group(1)) if title_match else '?'}")

# Find description area
desc_area = full_text[:3000]
print(f"  Text start: {desc_area[:500]}")

# Look for specific keywords
for kw in ['loyer', 'charges', 'cuisine', 'chambre', 'étage', 'balcon', 'terrasse', 'traversant', 'lumineux', 'exposition', 'DPE', 'classe énergétique']:
    idx = full_text.lower().find(kw.lower())
    if idx != -1:
        print(f"  '{kw}': ...{full_text[max(0,idx-30):idx+100]}...")

# --- LHImmo Danton ---
print("\n\n=== LHIMMO DANTON ===")
with open('/tmp/lhimmo_danton.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
title_match = re.search(r'<title>(.*?)</title>', html)
print(f"  Title: {clean(title_match.group(1)) if title_match else '?'}")
price_matches = re.findall(r'(\d[\d\s]*)\s*€', full_text)
print(f"  Prices: {price_matches[:10]}")
surface_matches = re.findall(r'(\d+)\s*m[²2]', full_text)
print(f"  Surfaces: {surface_matches[:10]}")
for kw in ['loyer', 'charges', 'cuisine', 'chambre', 'étage', 'location', 'vente', 'colocation', 'meublé']:
    idx = full_text.lower().find(kw.lower())
    if idx != -1:
        print(f"  '{kw}': ...{full_text[max(0,idx-30):idx+100]}...")

# --- LHImmo Université ---
print("\n\n=== LHIMMO UNIVERSITÉ ===")
with open('/tmp/lhimmo_univ.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
title_match = re.search(r'<title>(.*?)</title>', html)
print(f"  Title: {clean(title_match.group(1)) if title_match else '?'}")
price_matches = re.findall(r'(\d[\d\s]*)\s*€', full_text)
print(f"  Prices: {price_matches[:10]}")
for kw in ['loyer', 'location', 'vente', 'cuisine', 'chambre']:
    idx = full_text.lower().find(kw.lower())
    if idx != -1:
        print(f"  '{kw}': ...{full_text[max(0,idx-30):idx+100]}...")

# --- LHImmo T4 ---
print("\n\n=== LHIMMO T4 HYPER CENTRE ===")
with open('/tmp/lhimmo_t4.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
title_match = re.search(r'<title>(.*?)</title>', html)
print(f"  Title: {clean(title_match.group(1)) if title_match else '?'}")
price_matches = re.findall(r'(\d[\d\s]*)\s*€', full_text)
print(f"  Prices: {price_matches[:10]}")
for kw in ['loyer', 'location', 'vente', 'cuisine', 'chambre']:
    idx = full_text.lower().find(kw.lower())
    if idx != -1:
        print(f"  '{kw}': ...{full_text[max(0,idx-30):idx+100]}...")