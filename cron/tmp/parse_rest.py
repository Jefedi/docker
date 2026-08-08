#!/usr/bin/env python3
"""Parse Jullien-Allix, HEUZE, Saint Roch location pages, Century21, PAP."""
import re, json

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
    s = s.replace('&eacute;', 'é').replace('&egrave;', 'è').replace('&agrave;', 'à').replace('&ccedil;', 'ç')
    s = s.replace('&ecirc;', 'ê').replace('&rsquo;', "'").replace('&#8217;', "'")
    return re.sub(r'\s+', ' ', s).strip()

# --- Jullien-Allix ---
print("=== JULLIEN-ALLIX ===")
with open('/tmp/ja_havre.html', 'r', errors='replace') as f:
    html = f.read()

full_text = clean(html)
# Look for listing blocks
listing_links = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce/location/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Location listing links: {len(unique_links)}")
for l in unique_links:
    print(f"  {l}")

# Get prices and details near each link
for link in unique_links:
    pos = html.find(link)
    start = max(0, pos - 3000)
    end = min(len(html), pos + 3000)
    block = clean(html[start:end])
    
    price_match = re.search(r'(\d[\d\s]*)\s*€\s*/?\s*mois', block, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r'(\d[\d\s]*)\s*€', block)
    price = price_match.group(1).strip() if price_match else '?'
    
    surface_match = re.search(r'(\d+)\s*m[²2]', block)
    surface = surface_match.group(1) if surface_match else '?'
    
    title_from_url = link.split('/location/')[-1] if '/location/' in link else link
    
    print(f"\n  {title_from_url[:60]}")
    print(f"    Price: {price}€ | Surface: {surface}m²")
    
    # Check for keywords
    for kw in ['cuisine', 'chambre', 'étage', 'quartier', 'loyer', 'charges']:
        idx = block.lower().find(kw.lower())
        if idx != -1:
            print(f"    '{kw}': {block[max(0,idx-20):idx+80]}")

# --- HEUZE location ---
print("\n\n=== HEUZE LOCATION ===")
with open('/tmp/heuze_loc.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
# Look for listing links
listing_links = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:15]:
    print(f"  https://www.heuze-immo.fr{l}")

# Look for prices and surfaces
prices = re.findall(r'(\d[\d\s]*)\s*€\s*/?\s*mois', full_text, re.IGNORECASE)
print(f"Prices: {prices[:15]}")
surfaces = re.findall(r'(\d+)\s*m[²2]', full_text)
print(f"Surfaces: {surfaces[:15]}")

# Find JSON-LD
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")
for b in ld_blocks[:3]:
    print(f"  {b[:300]}")

# --- Saint Roch location ---
print("\n\n=== SAINT ROCH LOCATION ===")
with open('/tmp/stroch_loc.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
# Look for listing links
listing_links = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:15]:
    print(f"  https://www.saintrochimmo.com{l}")

# Look for prices
prices = re.findall(r'(\d[\d\s]*)\s*€\s*/?\s*mois', full_text, re.IGNORECASE)
print(f"Prices: {prices[:15]}")
surfaces = re.findall(r'(\d+)\s*m[²2]', full_text)
print(f"Surfaces: {surfaces[:15]}")

# JSON-LD
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")
for b in ld_blocks[:3]:
    print(f"  {b[:400]}")

# --- Century21 ---
print("\n\n=== CENTURY21 ===")
with open('/tmp/c21_havre.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
prices = re.findall(r'(\d[\d\s]*)\s*€\s*/?\s*mois', full_text, re.IGNORECASE)
print(f"Prices: {prices[:15]}")
surfaces = re.findall(r'(\d+)\s*m[²2]', full_text)
print(f"Surfaces: {surfaces[:15]}")
# JSON-LD
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")
for b in ld_blocks[:3]:
    print(f"  {b[:400]}")

# --- PAP ---
print("\n\n=== PAP ===")
with open('/tmp/pap_havre.html', 'r', errors='replace') as f:
    html = f.read()
full_text = clean(html)
print(f"File size: {len(html)}")
print(f"Text: {full_text[:500]}")
prices = re.findall(r'(\d[\d\s]*)\s*€', full_text)
print(f"Prices: {prices[:15]}")