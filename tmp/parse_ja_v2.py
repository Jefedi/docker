#!/usr/bin/env python3
"""Parse JA individual listing pages - simplified."""
import re, html as h, hashlib

ja_slugs = [
    "a-louer-appartement-de-type-f2-residence-les-jardins-dostara-le-havre-quartier-saint-nicolas",
    "a-louer-appartement-de-type-f2-entierement-renove-le-havre-marechal-joffre",
    "a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre",
    "a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux",
    "a-louer-appartement-de-type-f2-le-havre-quartier-demidoff",
    "a-louer-appartement-de-type-f2-le-havre-secteur-docks-vauban",
    "a-louer-appartement-de-type-f2-le-havre-proximite-pasino",
    "a-louer-appartement-de-type-f2-le-havre-centre-ville",
]

for slug in ja_slugs:
    fname = hashlib.md5(slug.encode()).hexdigest()
    fpath = f'/tmp/scrape/ja_{fname}.html'
    try:
        with open(fpath, 'r', errors='replace') as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"File not found: {fpath}")
        continue
    
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find all € amounts
    euros = re.findall(r'(\d[\d\s\xa0]*)\s*€', text[:5000])
    
    # Find surface
    surfaces = re.findall(r'(\d[\d,\.]*)\s*m[²2]', text[:5000])
    
    # Find loyer
    loyer_match = re.search(r'Loyer\s*(?:HC|hors charges)?\s*[:\s]*(\d[\d\s\xa0]*)\s*€', text, re.I)
    
    # Check cuisine
    cuisine_sep = 'CUISINE SÉPARÉE' in text.upper() or 'CUISINE SÉPARATE' in text.upper() or 'cuisine indépendante' in text.lower() or 'cuisine séparée' in text.lower() or 'cuisine fermée' in text.lower()
    cuisine_ouverte = 'cuisine ouverte' in text.lower() or 'cuisine américaine' in text.lower() or 'kitchenette' in text.lower() or 'coin cuisine' in text.lower()
    
    print(f"=== {slug} ===")
    print(f"  Euros found: {euros[:5]}")
    print(f"  Surfaces: {surfaces[:5]}")
    print(f"  Loyer: {loyer_match.group(1) if loyer_match else 'N/A'}")
    print(f"  Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte}")
    # Show a relevant excerpt
    loyer_pos = text.find('oyer')
    if loyer_pos >= 0:
        print(f"  Context: {text[max(0,loyer_pos-50):loyer_pos+200]}")
    print()