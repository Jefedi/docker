#!/usr/bin/env python3
"""Find Orpi listing URLs for the qualifying T2+ under 500€."""
import re, html as h

# Check Orpi page 2 for qualifying listings
accepted_quartiers = ['centre-ville', 'coty', 'massillon', 'eure', 'felix faure', 'perret',
                      'docks', 'rond-point', 'observatoire', 'saint-francois', 'danton',
                      'sanvic', 'bleville', 'saint-nicolas', 'docks vauban', 'halles',
                      'aristide briand', 'demidoff']

for page in range(1, 6):
    fname = f'/tmp/scrape/orpi.html' if page == 1 else f'/tmp/scrape/orpi{page}.html'
    try:
        raw = open(fname, 'r', errors='replace').read()
    except:
        continue
    
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find all listing entries with their URLs
    # Orpi listing URLs: /annonce-location-appartement-tX-le-havre-76600-UUID/
    listing_urls = re.findall(r'href="(/annonce-location-appartement-t(\d)-le-havre-76600-([a-f0-9-]+)/?)"', raw)
    # Also try Montivilliers
    listing_urls_m = re.findall(r'href="(/annonce-location-appartement-t(\d)-montivilliers[^"]+)"', raw)
    # Also Harfleur
    listing_urls_h = re.findall(r'href="(/annonce-location-appartement-t(\d)-harfleur[^"]+)"', raw)
    
    all_urls = listing_urls + listing_urls_m + listing_urls_h
    
    # Now find all prices with quartier info
    # Pattern: "XXX € par mois Location Location Appartement N pièces XX m² Le Havre - QUARTIER ..."
    orpi_listings = re.findall(r'(\d[\d\s]*)\s*€\s*par\s*mois\s*Location\s*Location\s*Appartement\s*(\d+)\s*pi[èe]ces?\s*(\d[\d,\.]*)\s*m\s*²?\s*([^€]+?)(?=\d+[\d\s]*€\s*par\s*mois|$)', text)
    
    # Match URLs with listings by order
    # Actually, let's find each listing's URL by looking at the text around it
    for price_str, pieces, surface, location in orpi_listings:
        price = int(re.sub(r'\s', '', price_str))
        pieces = int(pieces)
        if price <= 500 and pieces >= 2:
            surface_num = float(surface.replace(',', '.'))
            if surface_num >= 28:
                loc = location.strip()
                # Check quartier
                loc_lower = loc.lower()
                quartier_ok = any(q in loc_lower for q in accepted_quartiers)
                # Also check if it's Le Havre (not Montivilliers/Harfleur)
                is_havre = 'le havre' in loc_lower or 'havre' in loc_lower
                is_montiv = 'montivilliers' in loc_lower
                is_harfleur = 'harfleur' in loc_lower
                
                if quartier_ok and is_havre and not is_montiv and not is_harfleur:
                    # Find the URL for this listing
                    # Look for the price in the raw HTML and find the nearest listing URL
                    price_pos = text.find(f'{price_str.strip()} €')
                    if price_pos < 0:
                        price_pos = text.find(f'{price} € par mois')
                    
                    # Find UUIDs near this position in the raw HTML
                    if price_pos >= 0:
                        # Search raw HTML for UUIDs near this price
                        raw_price_str = re.sub(r'\s', '', price_str)
                        raw_pos = raw.find(raw_price_str)
                        if raw_pos < 0:
                            # Try with spaces
                            raw_pos = raw.find(price_str.strip())
                    
                    # Just find all T2 URLs on this page and try to match by order
                    pass
                    
                    print(f"  Page {page}: {pieces}p {surface}m2 {price}euro -- {loc[:120]}")
    
    # Let me also directly list all Le Havre T2 URLs
    havre_t2_urls = [(path, t, uid) for path, t, uid in all_urls if 'le-havre' in path and len(uid) > 10]
    if havre_t2_urls:
        print(f"\n  All Le Havre T2+ URLs on page {page}:")
        for path, t, uid in havre_t2_urls:
            if int(t) >= 2:
                print(f"    T{t}: https://www.orpi.com{path}")