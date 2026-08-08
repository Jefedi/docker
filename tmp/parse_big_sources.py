#!/usr/bin/env python3
"""Parse SquareHabitat, Citya, Century21, Orpi for T2+ listings under 500€."""
import re, html as h, json

def clean_text(raw):
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === SQUAREHABITAT ===
print("=== SQUAREHABITAT ===")
raw = open('/tmp/scrape/sqhab.html','r',errors='replace').read()
text = clean_text(raw)
# Find listing blocks with prices
# SquareHabitat typically has listing cards with title + price
# Look for patterns like "T2", "F2", "2 pièces" near prices
sq_listings = re.findall(r'((?:T2|T3|F2|F3|2 pièces|2pièces|3 pièces|3pièces|appartement)\s*(?:de\s*)?(\d+)[,\.]?\d*\s*m[²2]?[^\.]{0,300}?(\d[\d\s]*€)[^\.]{0,100})', text, re.I)
for s in sq_listings[:10]:
    print(f"  {s[0][:200]}")

# Also find all prices near "Le Havre"
havre_prices = re.findall(r'(Le Havre[^\.]{0,200}?(\d[\d\s\xa0]*\s*€)[^\.]{0,100})', text, re.I)
for p in havre_prices[:10]:
    print(f"  Price: {p[1]} — {p[0][:200]}")

# Find listing URLs
sq_links = re.findall(r'href="([^"]*(?:annonce|bien|location)[^"]*le-havre[^"]*)"', raw, re.I)
unique_sq = list(set(sq_links))
print(f"\n  Listing links: {len(unique_sq)}")
for l in unique_sq[:15]:
    if len(l) > 20:
        print(f"    {l}")

print()

# === CITYA ===
print("=== CITYA ===")
raw = open('/tmp/scrape/citya.html','r',errors='replace').read()
text = clean_text(raw)
# Find T2/F2 listings with prices
citya_listings = re.findall(r'((?:T2|F2|2 pièces|T3|F3)\s*(?:de\s*)?(\d+)[,\.]?\d*\s*m[²2]?[^\.]{0,300}?(\d[\d\s]*€)[^\.]{0,100})', text, re.I)
for c in citya_listings[:10]:
    print(f"  {c[0][:200]}")

# Find all € amounts with context
citya_prices = re.findall(r'((?:Le Havre|Havre)[^\.]{0,200}?(\d[\d\s\xa0]*\s*€)[^\.]{0,100})', text, re.I)
for p in citya_prices[:10]:
    print(f"  Price: {p[1]} — {p[0][:200]}")

# Find listing URLs
citya_links = re.findall(r'href="([^"]*(?:annonce|location|bien)[^"]*)"', raw, re.I)
unique_citya = list(set(citya_links))
print(f"\n  Listing links: {len(unique_citya)}")
for l in unique_citya[:15]:
    if 'le-havre' in l.lower() or 'havre' in l.lower():
        print(f"    {l}")

print()

# === CENTURY 21 ===
print("=== CENTURY 21 ===")
raw = open('/tmp/scrape/c21.html','r',errors='replace').read()
text = clean_text(raw)
c21_listings = re.findall(r'((?:T2|F2|2 pièces|T3|F3)\s*(?:de\s*)?(\d+)[,\.]?\d*\s*m[²2]?[^\.]{0,300}?(\d[\d\s]*€)[^\.]{0,100})', text, re.I)
for c in c21_listings[:10]:
    print(f"  {c[0][:200]}")

c21_prices = re.findall(r'((?:Havre|Location|appartement)[^\.]{0,200}?(\d[\d\s\xa0]*\s*€)[^\.]{0,100})', text, re.I)
for p in c21_prices[:10]:
    print(f"  Price: {p[1]} — {p[0][:200]}")

c21_links = re.findall(r'href="([^"]*(?:annonce|location|bien|listing)[^"]*)"', raw, re.I)
unique_c21 = list(set(c21_links))
print(f"\n  Listing links: {len(unique_c21)}")
for l in unique_c21[:15]:
    if len(l) > 20 and ('havre' in l.lower() or 'annonce' in l.lower()):
        print(f"    {l}")

print()

# === ORPI ===
print("=== ORPI ===")
raw = open('/tmp/scrape/orpi.html','r',errors='replace').read()
text = clean_text(raw)
orpi_listings = re.findall(r'((?:T2|F2|2 pièces|T3|F3)\s*(?:de\s*)?(\d+)[,\.]?\d*\s*m[²2]?[^\.]{0,300}?(\d[\d\s]*€)[^\.]{0,100})', text, re.I)
for o in orpi_listings[:10]:
    print(f"  {o[0][:200]}")

orpi_prices = re.findall(r'((?:Havre|Location|appartement)[^\.]{0,200}?(\d[\d\s\xa0]*\s*€)[^\.]{0,100})', text, re.I)
for p in orpi_prices[:10]:
    print(f"  Price: {p[1]} — {p[0][:200]}")

orpi_links = re.findall(r'href="([^"]*(?:annonce|location|bien|listing)[^"]*)"', raw, re.I)
unique_orpi = list(set(orpi_links))
print(f"\n  Listing links: {len(unique_orpi)}")
for l in unique_orpi[:15]:
    if len(l) > 20 and ('havre' in l.lower() or 'annonce' in l.lower()):
        print(f"    {l}")