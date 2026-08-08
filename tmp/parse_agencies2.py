#!/usr/bin/env python3
"""Parse agency listing pages - extract T2+ rentals with prices."""
import re, html as h, json

def clean_text(html_str):
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === LH IMMO ===
print("=== LH IMMO LISTINGS ===")
raw = open('/tmp/scrape/lhimmo_listings.html','r',errors='replace').read()
# Find listing links and titles
listing_links = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', raw)
unique_links = []
for l in listing_links:
    if l not in unique_links:
        unique_links.append(l)
print(f"Unique listing links: {len(unique_links)}")
for l in unique_links:
    print(f"  {l}")

# Also extract any text with prices
text = clean_text(raw)
# Find price patterns near "T2" or "F2" or "appartement"
price_context = re.findall(r'((?:T2|T3|F2|F3|appartement)[^\.]{0,300}?(\d[\d\s]*\s*€)[^\.]{0,100})', text, re.I)
for ctx in price_context[:10]:
    print(f"  Price context: {ctx[0][:200]}")

print()

# === HEUZE ===
print("=== HEUZE LISTINGS ===")
raw = open('/tmp/scrape/heuze_listings.html','r',errors='replace').read()
# Find listing links
listing_links = re.findall(r'href="(/location/appartement/le-havre/[^"]+)"', raw)
unique_links = []
for l in listing_links:
    if l not in unique_links and 'le-havre' in l:
        unique_links.append(l)
print(f"Unique listing links: {len(unique_links)}")
for l in unique_links[:30]:
    print(f"  https://www.heuze-immo.fr{l}")

# Extract text content around listings
text = clean_text(raw)
# Find patterns like "T2 45m² 450€" or similar
listings_text = re.findall(r'((?:T2|F2|2 pièces|T3|F3)[^\.]{0,500})', text, re.I)
for lt in listings_text[:10]:
    print(f"  Text: {lt[:200]}")

print()

# === SAINT ROCH ===
print("=== SAINT ROCH LISTINGS ===")
raw = open('/tmp/scrape/stroch_listings.html','r',errors='replace').read()
listing_links = re.findall(r'href="(/location/appartement/le-havre/[^"]+)"', raw)
unique_links = []
for l in listing_links:
    if l not in unique_links and 'le-havre' in l and len(l) > 30:
        unique_links.append(l)
print(f"Unique listing links: {len(unique_links)}")
for l in unique_links[:30]:
    print(f"  https://www.saintrochimmo.com{l}")

text = clean_text(raw)
listings_text = re.findall(r'((?:T2|F2|2 pièces|T3|F3|appartement)[^\.]{0,300})', text, re.I)
for lt in listings_text[:5]:
    print(f"  Text: {lt[:200]}")

print()

# === JULLIEN & ALLIX ===
print("=== JULLIEN & ALLIX LISTINGS ===")
raw = open('/tmp/scrape/ja_listings.html','r',errors='replace').read()
listing_links = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/[^"]+)"', raw)
unique_links = []
for l in listing_links:
    if l not in unique_links and 'a-louer' in l:
        unique_links.append(l)
print(f"Unique listing links: {len(unique_links)}")
for l in unique_links[:30]:
    print(f"  {l}")

text = clean_text(raw)
# Find listing titles with prices
listings_text = re.findall(r'((?:F2|F3|T2|T3|appartement)[^\.]{0,500})', text, re.I)
for lt in listings_text[:10]:
    if 'louer' in lt.lower() or '€' in lt:
        print(f"  Text: {lt[:250]}")