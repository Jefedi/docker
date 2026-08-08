#!/usr/bin/env python3
"""Parse all additional pages - SquareHabitat p3, Orpi p2-5, Citya p2, Century21 p2."""
import re, html as h

def clean_text(raw):
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === SQUAREHABITAT PAGE 3 ===
print("=== SQUAREHABITAT PAGE 3 ===")
raw = open('/tmp/scrape/sqhab3.html','r',errors='replace').read()
text = clean_text(raw)
listings = re.findall(r'(\d+)\s+(?:Appartement|Studio|Maison)\s+à louer.+?Au prix de \(par mois\)\s*(\d[\d\s]*)\s*€\s*cc\s*(.+?)(?=\d+\s+(?:Appartement|Studio|Maison)\s+à louer|$)', text, re.I)
print(f"Page 3 listings: {len(listings)}")
for num, price_str, desc in listings:
    price = int(re.sub(r'\s', '', price_str))
    pieces_match = re.search(r',\s*(\d+)\s*pi[èe]ces', text[max(0,text.find(price_str)-200):text.find(price_str)+100])
    pieces = int(pieces_match.group(1)) if pieces_match else 0
    surface_match = re.search(r'(\d+[,\.]?\d*)\s*m[²2]', desc[:300])
    surface = surface_match.group(1) if surface_match else '?'
    cuisine_sep = bool(re.search(r'cuisine\s*(?:ind[ée]pendante|s[ée]par[ée]e|ferm[ée]e)', desc, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette', desc, re.I))
    tag = "OK" if price <= 500 and pieces >= 2 and not cuisine_ouverte else "NO"
    print(f"  [{tag}] {pieces}p {surface}m2 {price}euro | C.sep: {cuisine_sep} C.ouv: {cuisine_ouverte} | {desc[:150]}")

# === ORPI PAGES 2-5 ===
for page in range(2, 6):
    print(f"\n=== ORPI PAGE {page} ===")
    raw = open(f'/tmp/scrape/orpi{page}.html','r',errors='replace').read()
    text = clean_text(raw)
    orpi_listings = re.findall(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*Location\s*Location\s*Appartement\s*(\d+)\s*pi[èe]ces?\s*(\d[\d,\.]*)\s*m\s*²?\s*([^€]+?)(?=\d+[\d\s]*€\s*par\s*mois|$)', text)
    for price_str, pieces, surface, location in orpi_listings:
        price = int(re.sub(r'\s', '', price_str))
        pieces = int(pieces)
        loc = location.strip()[:120]
        tag = "OK" if price <= 500 and pieces >= 2 else "NO"
        print(f"  [{tag}] {pieces}p {surface}m2 {price}euro -- {loc}")

# === CITYA PAGE 2 ===
print("\n=== CITYA PAGE 2 ===")
raw = open('/tmp/scrape/citya2.html','r',errors='replace').read()
text = clean_text(raw)
citya_listings = re.findall(r'Appartement\s+(\d+)\s*pi[èe]ces?\s+(\d[\d,\.]*)\s*m[²2]?\s*([^€]+?)\s*(\d[\d\s]*)\s*€', text)
for pieces, surface, features, price_str in citya_listings:
    price = int(re.sub(r'\s', '', price_str))
    pieces = int(pieces)
    feat = features.strip()[:80]
    tag = "OK" if price <= 500 and pieces >= 2 else "NO"
    print(f"  [{tag}] {pieces}p {surface}m2 {price}euro -- {feat}")

# === CENTURY21 PAGE 2 ===
print("\n=== CENTURY21 PAGE 2 ===")
raw = open('/tmp/scrape/c212.html','r',errors='replace').read()
text = clean_text(raw)
c21_listings = re.findall(r'HAVRE\s*76\s+([\d,\.]+)\s*m\s*2\s*,\s*(\d+)\s*pi[èe]ces?\s+Ref\s*:\s*(\d+)\s+([^€]+?)(\d[\d\s]*)\s*€\s*par\s*mois', text)
for surface, pieces, ref, desc, price_str in c21_listings:
    price = int(re.sub(r'\s', '', price_str))
    pieces = int(pieces)
    tag = "OK" if price <= 500 and pieces >= 2 else "NO"
    print(f"  [{tag}] {pieces}p {surface}m2 {price}euro ref:{ref} -- {desc.strip()[:100]}")