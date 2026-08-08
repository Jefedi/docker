#!/usr/bin/env python3
"""Parse rental listing HTML files - v3 with fixed URL patterns for all sources."""
import re
import json
import os
from html import unescape

BASE_DIR = "/opt/data/cron/tmp/havre_rental"

def strip_tags(html_str):
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

def parse_le_partenaire(filepath):
    """Parse Le-Partenaire location listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    h2_iter = [(m.start(), m.group(1)) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)]
    
    for h2_pos, h2_content in h2_iter:
        title_text = strip_tags(h2_content)
        block_end = min(len(html), h2_pos + 3000)
        block = html[h2_pos:block_end]
        block_clean = re.sub(r'<[^>]+>', '\n', block)
        block_clean = block_clean.replace('&nbsp;', ' ')
        block_clean = unescape(block_clean)
        
        price_match = re.search(r'(\d[\d ]*)\s*€\s*(?:/|\\)?\s*mois', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+)\s*m[²2]', title_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ce', title_text)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        desc_block = re.sub(r'\n+', '\n', block_clean)
        desc_lines = [l.strip() for l in desc_block.split('\n') if l.strip()]
        desc_text = ' '.join(desc_lines[:20])
        desc_text = re.sub(r'\s+', ' ', desc_text)
        
        # Find the matching "Voir l'annonce" link
        all_links = re.finditer(r'href="(/immobilier/location/appartement/[^"]*?/(\d+))"', html[h2_pos:h2_pos+5000])
        listing_id = None
        listing_url = None
        for m in all_links:
            listing_id = m.group(2)
            listing_url = f"https://www.le-partenaire.fr{m.group(1)}"
            break
        
        if not listing_id:
            continue
        
        listings.append({
            'source': 'lp',
            'id': f"lp-{listing_id}",
            'title': title_text,
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': listing_url or '',
            'description': desc_text[:600]
        })
    
    return listings

def parse_citya(filepath):
    """Parse Citya listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    link_pattern = r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/(GES[\w-]+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        url = m.group(1)
        citya_id = m.group(2)
        listing_id = f"citya-{citya_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        start = max(0, m.start() - 200)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        title_match = re.search(r'Appartement\s+(\d+)\s*pi[eè]ces?\s+([\d.]+)\s*m[²2]', block_clean)
        rooms = int(title_match.group(1)) if title_match else None
        surface = float(title_match.group(2)) if title_match else None
        
        features = []
        for feat in ['Parking', 'Balcon', 'Meublé', 'Terrasse', 'Jardin', 'Ascenseur']:
            if feat in block_clean:
                features.append(feat)
        
        price_match = re.search(r'(\d{3,4})\s*€', block_clean)
        price = int(price_match.group(1)) if price_match else None
        
        cp_match = re.search(r'Le Havre\s*\((\d+)\)', block_clean)
        cp = cp_match.group(1) if cp_match else ''
        
        listings.append({
            'source': 'citya',
            'id': listing_id,
            'title': f"Appartement {rooms or '?'}p {surface or '?'}m²" + (f" ({', '.join(features)})" if features else ''),
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'features': features,
            'cp': cp,
            'description': block_clean[:500]
        })
    
    return listings

def parse_squarehabitat(filepath):
    """Parse SquareHabitat listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    link_pattern = r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([a-f0-9-]+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        uuid = m.group(2)
        listing_id = f"sqhab-{uuid}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = f"https://www.squarehabitat.fr{m.group(1)}"
        
        start = max(0, m.start() - 200)
        end = min(len(html), m.start() + 5000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        type_match = re.search(r'(Appartement|Studio)\s+à\s+louer\s*-\s*LE\s+HAVRE(?:,\s*(\d+)\s*pi[eè]ces)?', block_clean)
        rooms = None
        is_studio = False
        if type_match:
            if type_match.group(1) == 'Studio':
                rooms = 1
                is_studio = True
            elif type_match.group(2):
                rooms = int(type_match.group(2))
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        features = []
        for feat in ['Parking', 'Balcon', 'Meublé', 'Terrasse', 'Jardin', 'Ascenseur', 'Duplex']:
            if feat in block_clean:
                features.append(feat)
        
        listings.append({
            'source': 'sqhab',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'features': features,
            'description': block_clean[:500],
            'is_studio': is_studio
        })
    
    return listings

def parse_orpi(filepath):
    """Parse Orpi listings - URL pattern: /annonce-location-appartement-tX-le-havre-76600-UUID/"""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # URL pattern: /annonce-location-appartement-t1-le-havre-76600-a0204614-bd36-4d32-be2d-597c18e3927c/
    link_pattern = r'href="(/annonce-location-appartement-t(\d+)-le-havre-76600-([a-f0-9-]+))/"'
    # Also numeric IDs: /annonce-location-appartement-t2-le-havre-76600-1673-051096-170/
    link_pattern2 = r'href="(/annonce-location-appartement-t(\d+)-le-havre-76600-(\d+-\d+-\d+))/"'
    # Also other cities nearby
    link_pattern3 = r'href="(/annonce-location-appartement-t(\d+)-(?:montivilliers|harfleur)-[^"]+-([a-f0-9-]+))/"'
    
    seen_ids = set()
    
    for pattern in [link_pattern, link_pattern2, link_pattern3]:
        for m in re.finditer(pattern, html):
            url_path = m.group(1)
            t_type = int(m.group(2))
            id_part = m.group(3)
            listing_id = f"orpi-{id_part}"
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)
            url = f"https://www.orpi.com{url_path}/"
            
            start = max(0, m.start() - 500)
            end = min(len(html), m.start() + 3000)
            block = html[start:end]
            block_clean = strip_tags(block)
            
            price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            
            surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
            surface = float(surface_match.group(1)) if surface_match else None
            
            features = []
            for feat in ['Parking', 'Balcon', 'Meublé', 'Terrasse', 'Jardin', 'Ascenseur', 'Duplex']:
                if feat in block_clean:
                    features.append(feat)
            
            # Extract quartier from description
            quartier_match = re.search(r'(quartier|secteur|centre-ville|Sanvic|Bléville|Dollemard|Caucriauville|Graville|Aplemont|Rouelles|Saint-Vincent|Danton|Massillon|Coty|Eure|Perret|Docks|Félix Faure|Ormeaux|Saint-Nicolas)', block_clean, re.I)
            quartier = quartier_match.group(1) if quartier_match else ''
            
            listings.append({
                'source': 'orpi',
                'id': listing_id,
                'title': block_clean[:200],
                'price': price,
                'surface': int(surface) if surface else None,
                'rooms': t_type,
                'url': url,
                'features': features,
                'quartier': quartier,
                'description': block_clean[:600]
            })
    
    return listings

def parse_century21(filepath):
    """Parse Century 21 listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # C21 seems to load listings via JS, but let's try to find listing data in the HTML
    # Look for JSON data blocks with listing info
    json_pattern = r'"id"\s*:\s*(\d+).*?"libelle"\s*:\s*"([^"]*)".*?"prix"\s*:\s*(\d+).*?"surface"\s*:\s*"?([\d.]+)"?.*?"nbPieces"\s*:\s*(\d+)'
    
    for m in re.finditer(json_pattern, html, re.DOTALL):
        c21_id = m.group(1)
        title = m.group(2)
        price = int(m.group(3))
        surface = float(m.group(4))
        rooms = int(m.group(5))
        listing_id = f"c21-{c21_id}"
        url = f"https://www.century21.fr/annonces/location-appartement/v-le+havre/{c21_id}"
        
        listings.append({
            'source': 'c21',
            'id': listing_id,
            'title': title,
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': title
        })
    
    # If JSON approach didn't work, try finding listing cards
    if not listings:
        # Look for property data in data attributes or script tags
        script_data = re.findall(r'data-(?:property|bien|listing)-id="(\d+)"', html)
        if script_data:
            for pid in script_data:
                listing_id = f"c21-{pid}"
                url = f"https://www.century21.fr/annonces/location-appartement/v-le+havre/{pid}"
                
                # Find context
                idx = html.find(f'data-property-id="{pid}"')
                if idx == -1:
                    idx = html.find(f'data-bien-id="{pid}"')
                if idx >= 0:
                    block = html[max(0,idx-200):idx+2000]
                    block_clean = strip_tags(block)
                    price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
                    price = int(price_match.group(1).replace(' ', '')) if price_match else None
                    surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
                    surface = float(surface_match.group(1)) if surface_match else None
                    rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
                    rooms = int(rooms_match.group(1)) if rooms_match else None
                    
                    listings.append({
                        'source': 'c21',
                        'id': listing_id,
                        'title': block_clean[:200],
                        'price': price,
                        'surface': int(surface) if surface else None,
                        'rooms': rooms,
                        'url': url,
                        'description': block_clean[:500]
                    })
    
    # Also try image-based listing IDs (from earlier analysis we saw c21_202_2922_7371)
    img_pattern = r'c21_(\d+)_(\d+)_(\d+)'
    seen = set(l['id'] for l in listings)
    for m in re.finditer(img_pattern, html):
        agency = m.group(1)
        mandat = m.group(2)
        c21_id = m.group(3)
        listing_id = f"c21-{c21_id}"
        if listing_id in seen:
            continue
        seen.add(listing_id)
        
        # Find context around this image
        idx = m.start()
        block = html[max(0,idx-1000):idx+2000]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        url = f"https://www.century21.fr/annonces/location-appartement/v-le+havre/{c21_id}"
        
        listings.append({
            'source': 'c21',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:500]
        })
    
    return listings

def parse_jullien_allix(filepath):
    """Parse Jullien & Allix listings - URL: /annonce-immobiliere/a-louer-XXX.html"""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # URL pattern: /annonce-immobiliere/a-louer-appartement-de-type-f2-le-havre-XXX.html
    link_pattern = r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/(a-louer-[^"]+)\.html)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        url = m.group(1)
        slug = m.group(2)
        listing_id = f"ja-{slug}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        # Get context around the link
        start = max(0, m.start() - 200)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        # Extract price
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        # Extract surface
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        # Extract type F
        f_match = re.search(r'(?:type\s+)?F(\d+)', slug, re.I)
        rooms = int(f_match.group(1)) if f_match else None
        
        # Also try T pattern
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        # Extract quartier from slug
        quartier = ''
        for q in ['centre-ville', 'sanvic', 'bleville', 'danton', 'massillon', 'cote-ouest', 'ormeaux', 
                   'docks', 'vauban', 'demidoff', 'marechal-joffre', 'saint-nicolas', 'mazeline',
                   'anatole-france', 'proximite-plage', 'harfleur', 'universite']:
            if q in slug.lower():
                quartier = q
                break
        
        listings.append({
            'source': 'ja',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'quartier': quartier,
            'description': block_clean[:600]
        })
    
    return listings

def parse_saintroch(filepath):
    """Parse Saint Roch Immobilier - uses netty.immo platform."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # SaintRoch uses netty.immo platform. Look for listing data in JSON/script blocks
    # The site likely loads listings via JavaScript from an API
    
    # Try to find listing IDs and data in the HTML
    # Look for JSON-like data structures with listing info
    json_blocks = re.findall(r'\{[^{}]*(?:"id"|"ref")[^{}]*\}', html)
    
    # Try finding listing data in script tags
    script_pattern = r'<script[^>]*>(.*?)</script>', re.DOTALL
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    
    for script in scripts:
        # Look for listing data patterns
        listing_data = re.findall(r'"(?:id|reference)"\s*:\s*"?(\w+)?".*?"(?:titre|title|libelle)"\s*:\s*"([^"]*)"', script)
        if listing_data:
            for lid, title in listing_data:
                listings.append({
                    'source': 'stroch',
                    'id': f"stroch-{lid}",
                    'title': title,
                    'price': None,
                    'surface': None,
                    'rooms': None,
                    'url': f"https://www.saintrochimmo.com/location/appartement/le-havre/76600",
                    'description': ''
                })
    
    # If no listings found from scripts, try looking for listing cards in HTML
    if not listings:
        # Look for listing card patterns common in netty.immo sites
        # Cards might have data attributes or specific class names
        card_pattern = r'data-(?:id|ref)="([^"]+)"[^>]*>(.*?)</(?:div|article|li)'
        for m in re.finditer(card_pattern, html, re.DOTALL):
            card_id = m.group(1)
            card_content = strip_tags(m.group(2))
            
            if 'location' not in card_content.lower() and 'louer' not in card_content.lower():
                continue
            
            price_match = re.search(r'(\d[\d ]*)\s*€', card_content)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', card_content)
            surface = float(surface_match.group(1)) if surface_match else None
            rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', card_content)
            rooms = int(rooms_match.group(1)) if rooms_match else None
            
            id_match = re.search(r'LA(\d+)', card_id)
            stroch_id = f"stroch-LA{id_match.group(1)}" if id_match else f"stroch-{card_id}"
            
            listings.append({
                'source': 'stroch',
                'id': stroch_id,
                'title': card_content[:200],
                'price': price,
                'surface': int(surface) if surface else None,
                'rooms': rooms,
                'url': f"https://www.saintrochimmo.com/location/appartement/le-havre/76600",
                'description': card_content[:500]
            })
    
    # Also try finding "172 annonces" pattern and extract from HTML structure
    # The page says "172 annonces" so there should be listing data somewhere
    if not listings:
        # Try finding listing references in the HTML that might be loaded via JS
        # Look for patterns like /location/appartement/le-havre/76600/LA-XXXX or similar
        ref_pattern = r'/(?:location|annonces)/[^"]*?([A-Z]{2}\d{3,})[^"]*'
        for m in re.finditer(ref_pattern, html):
            ref = m.group(1)
            listing_id = f"stroch-{ref}"
            if any(l['id'] == listing_id for l in listings):
                continue
            
            # Find context
            idx = m.start()
            block = html[max(0,idx-500):idx+2000]
            block_clean = strip_tags(block)
            
            price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
            surface = float(surface_match.group(1)) if surface_match else None
            rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
            rooms = int(rooms_match.group(1)) if rooms_match else None
            
            listings.append({
                'source': 'stroch',
                'id': listing_id,
                'title': block_clean[:200],
                'price': price,
                'surface': int(surface) if surface else None,
                'rooms': rooms,
                'url': f"https://www.saintrochimmo.com{m.group(0)}" if m.group(0).startswith('/') else m.group(0),
                'description': block_clean[:500]
            })
    
    return listings

def parse_heuze(filepath):
    """Parse HEUZE Immobilier - uses netty.immo platform, similar to SaintRoch."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Similar approach to SaintRoch - the site uses netty.immo
    # Look for listing data in script tags or JSON data
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    
    for script in scripts:
        listing_data = re.findall(r'"(?:id|reference)"\s*:\s*"?(\w+)?"[^}]*?"(?:titre|title|libelle)"\s*:\s*"([^"]*)"', script)
        if listing_data:
            for lid, title in listing_data:
                listings.append({
                    'source': 'heuze',
                    'id': f"heuze-{lid}",
                    'title': title,
                    'price': None,
                    'surface': None,
                    'rooms': None,
                    'url': f"https://www.heuze-immo.fr/location/appartement/le-havre/76600",
                    'description': ''
                })
    
    # If no listings found from scripts, try card patterns
    if not listings:
        card_pattern = r'data-(?:id|ref)="([^"]+)"[^>]*>(.*?)</(?:div|article|li)'
        for m in re.finditer(card_pattern, html, re.DOTALL):
            card_id = m.group(1)
            card_content = strip_tags(m.group(2))
            
            price_match = re.search(r'(\d[\d ]*)\s*€', card_content)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', card_content)
            surface = float(surface_match.group(1)) if surface_match else None
            rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', card_content)
            rooms = int(rooms_match.group(1)) if rooms_match else None
            
            id_match = re.search(r'(LA|VA|LS)(\d+)', card_id, re.I)
            heuze_id = f"heuze-{id_match.group(1).upper()}{id_match.group(2)}" if id_match else f"heuze-{card_id}"
            
            listings.append({
                'source': 'heuze',
                'id': heuze_id,
                'title': card_content[:200],
                'price': price,
                'surface': int(surface) if surface else None,
                'rooms': rooms,
                'url': f"https://www.heuze-immo.fr/location/appartement/le-havre/76600",
                'description': card_content[:500]
            })
    
    # Try finding listing references
    if not listings:
        ref_pattern = r'/(?:location|annonces)/[^"]*?([A-Z]{2}\d{3,})[^"]*'
        seen = set()
        for m in re.finditer(ref_pattern, html):
            ref = m.group(1)
            listing_id = f"heuze-{ref}"
            if listing_id in seen:
                continue
            seen.add(listing_id)
            
            idx = m.start()
            block = html[max(0,idx-500):idx+2000]
            block_clean = strip_tags(block)
            
            price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
            surface = float(surface_match.group(1)) if surface_match else None
            rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
            rooms = int(rooms_match.group(1)) if rooms_match else None
            
            listings.append({
                'source': 'heuze',
                'id': listing_id,
                'title': block_clean[:200],
                'price': price,
                'surface': int(surface) if surface else None,
                'rooms': rooms,
                'url': f"https://www.heuze-immo.fr{m.group(0)}" if m.group(0).startswith('/') else m.group(0),
                'description': block_clean[:500]
            })
    
    return listings

def parse_lhimmo(filepath):
    """Parse LH Immo listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # LH Immo shows featured properties on homepage - look for property cards
    # The earlier output showed surface/rooms/title in the HTML
    # Find property blocks with pattern: surface, rooms, title
    
    # Find blocks containing "Appartement" or "Maison" with nearby surface info
    block_pattern = r'((?:\d+)m[²2]|surface[^<]*\d+).*?((?:\d+)).*?(Maison|Appartement)\s+([^<–\-]+)'
    
    # Alternative: find all links to individual property pages
    link_pattern = r'href="(https://www\.lhimmo\.com/(?!annonces/$|category|tag|page|author|wp-|contact|mentions|estimation|gestion|agence|quartiers|prix-m2)([^"]+))"'
    # Also try relative links
    link_pattern2 = r'href="(/(?!annonces/$|category|tag|page|author|wp-|contact|mentions|estimation|gestion|agence|quartiers|prix-m2)([a-z][^"]+))"'
    
    seen_ids = set()
    for pattern in [link_pattern, link_pattern2]:
        for m in re.finditer(pattern, html):
            url = m.group(1)
            if url.startswith('/'):
                url = f"https://www.lhimmo.com{url}"
            slug = m.group(2)
            listing_id = f"lhimmo-{slug}"
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)
            
            start = max(0, m.start() - 500)
            end = min(len(html), m.start() + 3000)
            block = html[start:end]
            block_clean = strip_tags(block)
            
            price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
            price = int(price_match.group(1).replace(' ', '')) if price_match else None
            surface_match = re.search(r'(\d+)\s*m[²2]', block_clean)
            surface = int(surface_match.group(1)) if surface_match else None
            rooms_match = re.search(r'T(\d+)', block_clean)
            rooms = int(rooms_match.group(1)) if rooms_match else None
            
            # Skip if this is clearly a category/page link
            if slug in ['annonces', 'contact', 'agence', 'quartiers', 'gestion', 'estimation']:
                continue
            
            listings.append({
                'source': 'lhimmo',
                'id': listing_id,
                'title': block_clean[:200],
                'price': price,
                'surface': surface,
                'rooms': rooms,
                'url': url,
                'description': block_clean[:500]
            })
    
    return listings

# Parse all sources
all_listings = []

sources = [
    ('Le-Partenaire', parse_le_partenaire, 'lp_page1.html'),
    ('Citya', parse_citya, 'citya_page.html'),
    ('SquareHabitat', parse_squarehabitat, 'sqhab_page.html'),
    ('Orpi', parse_orpi, 'orpi_page.html'),
    ('Century21', parse_century21, 'c21_page.html'),
    ('Jullien-Allix', parse_jullien_allix, 'ja_page.html'),
    ('SaintRoch', parse_saintroch, 'stroch_page.html'),
    ('HEUZE', parse_heuze, 'heuze_page.html'),
    ('LH Immo', parse_lhimmo, 'lhimmo_page.html'),
]

for name, parser, filename in sources:
    listings = parser(os.path.join(BASE_DIR, filename))
    all_listings.extend(listings)
    print(f"{name}: {len(listings)} listings")

print(f"\n=== TOTAL: {len(all_listings)} listings parsed ===")

# Print detailed results
for l in all_listings:
    print(f"\n--- {l['id']} ---")
    print(f"  Source: {l['source']}")
    print(f"  Price: {l['price']}€ | Surface: {l['surface']}m² | Rooms: {l['rooms']}")
    print(f"  URL: {l['url']}")
    desc = l.get('description', '')
    print(f"  Desc: {desc[:300]}")

# Save
output_path = os.path.join(BASE_DIR, "all_listings_v3.json")
with open(output_path, 'w') as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {output_path}")