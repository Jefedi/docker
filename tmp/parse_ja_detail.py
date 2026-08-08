#!/usr/bin/env python3
"""Parse JA individual listing pages for price, surface, description."""
import re, html as h, json, os, hashlib

ja_urls = [
    ("a-louer-appartement-de-type-f2-residence-les-jardins-dostara-le-havre-quartier-saint-nicolas", "F2 Résidence Les Jardins d'Ostara - Quartier Saint-Nicolas"),
    ("a-louer-appartement-de-type-f2-entierement-renove-le-havre-marechal-joffre", "F2 Rénové - Maréchal Joffre"),
    ("a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre", "F2 Meublé - Maréchal Joffre"),
    ("a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux", "F2 Côte Ouest Les Ormeaux"),
    ("a-louer-appartement-de-type-f2-le-havre-quartier-demidoff", "F2 Quartier Demidoff"),
    ("a-louer-appartement-de-type-f2-le-havre-secteur-docks-vauban", "F2 Secteur Docks Vauban"),
    ("a-louer-appartement-de-type-f2-le-havre-proximite-pasino", "F2 Proximité Pasino"),
    ("a-louer-appartement-de-type-f2-le-havre-centre-ville", "F2 Centre-ville"),
]

for slug, title in ja_urls:
    fname = hashlib.md5(slug.encode()).hexdigest()
    fpath = f'/tmp/scrape/ja_{fname}.html'
    try:
        raw = open(fpath, 'r', errors='replace').read()
    except:
        continue
    
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find price
    price_match = re.search(r'(?:Loyer|loyer|Prix|prix|€/mois|€ mois)\s*[:\s]*(\d[\d\s\xa0]*)\s*€', text)
    price = 0
    if price_match:
        price_str = re.sub(r'[\s\xa0]', '', price_match.group(1))
        try:
            price = int(price_str)
        except:
            pass
    # Also try generic pattern
    if price == 0:
        price_match2 = re.search(r'(\d[\d\s\xa0]*)\s*€\s*(?:/mois|/ mois|par mois|mois)', text)
        if price_match2:
            price_str = re.sub(r'[\s\xa0]', '', price_match2.group(1))
            try:
                price = int(price_str)
            except:
                pass
    
    # Find surface
    surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text)
    surface = 0
    if surface_match:
        try:
            surface = int(float(surface_match.group(1).replace(',', '.')))
        except:
            pass
    
    # Find description excerpt
    desc_start = text.find('Description')
    if desc_start < 0:
        desc_start = text.find('description')
    desc = text[desc_start:desc_start+500] if desc_start >= 0 else text[:500]
    
    # Check for cuisine séparée/indépendante
    cuisine_sep = bool(re.search(r'cuisine\s*(?:s[ée]par[ée]e|ind[ée]pendante|ferm[ée]e)', text, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine| kitchenette|coin cuisine)', text, re.I))
    # Check for chambre fermée
    chambre = bool(re.search(r'chambre\s*(?:s[ée]par[ée]e|ferm[ée]e|avec porte)', text, re.I)) or bool(re.search(r'\d+\s*chambre', text, re.I))
    
    print(f"\n=== {title} ===")
    print(f"  URL: https://www.jullien-allix.fr/annonce-immobiliere/{slug}.html")
    print(f"  Price: {price}€ | Surface: {surface}m²")
    print(f"  Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte} | Chambre: {chambre}")
    print(f"  Desc: {desc[:300]}")