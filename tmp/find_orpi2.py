#!/usr/bin/env python3
"""Find Orpi listing URLs for qualifying T2+ under 500€."""
import re, html as h

accepted_quartiers = ['centre-ville', 'coty', 'massillon', 'eure', 'felix faure', 'perret',
                      'docks', 'rond-point', 'observatoire', 'saint-francois', 'danton',
                      'sanvic', 'bleville', 'saint-nicolas', 'docks vauban', 'halles',
                      'aristide briand', 'demidoff']

for page in range(1, 6):
    fname = '/tmp/scrape/orpi.html' if page == 1 else f'/tmp/scrape/orpi{page}.html'
    try:
        raw = open(fname, 'r', errors='replace').read()
    except:
        continue
    
    # Find all Le Havre listing URLs with T2+
    havre_urls = re.findall(r'href="(/annonce-location-appartement-t(\d)-le-havre-76600-([a-f0-9-]+)/?)"', raw)
    unique_urls = []
    for path, t, uid in havre_urls:
        if int(t) >= 2 and uid not in [u for _, _, u in unique_urls]:
            unique_urls.append((path, t, uid))
    
    if unique_urls:
        print(f"\n=== Orpi page {page} - Le Havre T2+ URLs ===")
        for path, t, uid in unique_urls:
            print(f"  T{t} UUID:{uid} -> https://www.orpi.com{path}")
    
    # Also parse text for qualifying listings
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    orpi_listings = re.findall(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*Location\s*Location\s*Appartement\s*(\d+)\s*pi[èe]ces?\s*(\d[\d,\.]*)\s*m\s*²?\s*([^€]+?)(?=\d+[\d\s]*€\s*par\s*mois|$)', text)
    
    for price_str, pieces_str, surface, location in orpi_listings:
        price = int(re.sub(r'\s', '', price_str))
        pieces = int(pieces_str)
        surface_num = float(surface.replace(',', '.'))
        loc = location.strip()
        loc_lower = loc.lower()
        
        if price <= 500 and pieces >= 2 and surface_num >= 28:
            quartier_ok = any(q in loc_lower for q in accepted_quartiers)
            is_havre = 'le havre' in loc_lower
            is_montiv = 'montivilliers' in loc_lower
            
            if quartier_ok and is_havre and not is_montiv:
                print(f"  [QUALIFIES] Page {page}: {pieces}p {surface}m2 {price}euro -- {loc[:150]}")