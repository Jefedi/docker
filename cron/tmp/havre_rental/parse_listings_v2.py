#!/usr/bin/env python3
"""Parse rental listing HTML files - improved parser with correct price extraction."""
import re
import json
import os
from html import unescape

BASE_DIR = "/opt/data/cron/tmp/havre_rental"

def strip_tags(html_str):
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

def clean_text(text):
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_le_partenaire(filepath):
    """Parse Le-Partenaire location listings with correct price extraction."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Find h2 headings and their context
    h2_iter = [(m.start(), m.group(1)) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)]
    
    # Find all "Voir l'annonce" links with their positions
    voir_pattern = r'href="(/immobilier/location/appartement/[^"]+)"[^>]*class="button-first[^"]*"[^>]*>'
    voir_links = [(m.start(), m.group(1)) for m in re.finditer(voir_pattern, html)]
    
    for i, (h2_pos, h2_content) in enumerate(h2_iter):
        title_text = strip_tags(h2_content)
        
        # Get a block of HTML after the h2 to find the price
        block_end = min(len(html), h2_pos + 3000)
        block = html[h2_pos:block_end]
        
        # Clean the block to find price
        block_clean = re.sub(r'<[^>]+>', '\n', block)
        block_clean = block_clean.replace('&nbsp;', ' ')
        block_clean = unescape(block_clean)
        block_clean = re.sub(r'\n+', '\n', block_clean)
        
        # The price pattern is: listing_number\n price € / mois
        # Look for number patterns followed by € / mois
        price_match = re.search(r'(\d[\d ]*)\s*€\s*(?:/|\\)\s*mois', block_clean)
        price = None
        if price_match:
            price = int(price_match.group(1).replace(' ', ''))
        
        # Extract surface from title
        surface_match = re.search(r'(\d+)\s*m[²2]', title_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Extract rooms from title
        rooms_match = re.search(r'(\d+)\s*pi[eè]ce', title_text)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        # Find description text
        desc_match = re.search(r'(Quartier\s+[^.]+|STUDIO\s+[^.]+|Appartement\s+T\d[^.]+|A\s+louer[^.]+|Colocation[^.]+)', block_clean)
        desc = desc_match.group(1).strip() if desc_match else ''
        
        # Get more description context
        desc_block = clean_text(block_clean[:1500])
        
        # Find the matching "Voir l'annonce" link
        listing_url = None
        listing_id = None
        for lpos, href in voir_links:
            if lpos > h2_pos:
                listing_url = f"https://www.le-partenaire.fr{href}" if href.startswith('/') else href
                id_match = re.search(r'/(\d+)$', href)
                if id_match:
                    listing_id = id_match.group(1)
                break
        
        if not listing_id:
            # Try finding any listing link after this h2
            all_links = re.finditer(r'href="(/immobilier/location/appartement/[^"]*?/(\d+))"', html[h2_pos:h2_pos+5000])
            for m in all_links:
                listing_id = m.group(2)
                listing_url = f"https://www.le-partenaire.fr{m.group(1)}" if m.group(1).startswith('/') else m.group(1)
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
            'description': desc_block[:600],
            'raw_desc': desc
        })
    
    return listings

def parse_citya(filepath):
    """Parse Citya listings - extract from JSON-like data in HTML."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Citya has listing info in the href context. Find all listing links
    link_pattern = r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/(GES[\w-]+))"'
    
    # Get the full text content around each listing
    for m in re.finditer(link_pattern, html):
        url = m.group(1)
        citya_id = m.group(2)
        listing_id = f"citya-{citya_id}"
        
        # Get a wider context around this link - look for price, surface, rooms
        start = max(0, m.start() - 200)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        # Extract surface from the title pattern "Appartement X pièces Ym²"
        title_match = re.search(r'Appartement\s+(\d+)\s*pi[eè]ces?\s+([\d.]+)\s*m[²2]', block_clean)
        rooms = None
        surface = None
        if title_match:
            rooms = int(title_match.group(1))
            surface = float(title_match.group(2))
        
        # Extract features like Parking, Balcon, Meublé, Terrasse
        features = []
        for feat in ['Parking', 'Balcon', 'Meublé', 'Terrasse', 'Jardin', 'Ascenseur']:
            if feat in block_clean:
                features.append(feat)
        
        # Extract price - look for patterns like "XXX €" or "XXX€ CC" or "XXX€ HC"
        price_match = re.search(r'(\d[\d ]*)\s*€\s*(?:CC|HC| charges)', block_clean)
        if not price_match:
            price_match = re.search(r'Loyer\s*:?\s*(\d[\d ]*)\s*€', block_clean)
        if not price_match:
            # Try to find any euro amount
            price_match = re.search(r'(\d{3,})\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        # Get postal code
        cp_match = re.search(r'Le Havre\s*\((\d+)\)', block_clean)
        cp = cp_match.group(1) if cp_match else ''
        
        # Deduplicate
        if any(l['id'] == listing_id for l in listings):
            continue
        
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
    
    # Find listing links with UUIDs
    link_pattern = r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([a-f0-9-]+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        uuid = m.group(2)
        listing_id = f"sqhab-{uuid}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = f"https://www.squarehabitat.fr{m.group(1)}"
        
        # Get context
        start = max(0, m.start() - 200)
        end = min(len(html), m.start() + 5000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        # Extract type info: "Appartement à louer - LE HAVRE, X pièces" or "Studio à louer - LE HAVRE"
        type_match = re.search(r'(Appartement|Studio)\s+à\s+louer\s*-\s*LE\s+HAVRE(?:,\s*(\d+)\s*pi[eè]ces)?', block_clean)
        rooms = None
        is_studio = False
        if type_match:
            if type_match.group(1) == 'Studio':
                rooms = 1
                is_studio = True
            elif type_match.group(2):
                rooms = int(type_match.group(2))
        
        # Extract price
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        # Extract surface
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        # Extract features
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
    """Parse Orpi listings - more robust parsing."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Orpi listing IDs are UUIDs in the URL
    link_pattern = r'href="(https://www\.orpi\.com/[^"]*?([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})[^"]*?)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        orpi_id = m.group(2)
        listing_id = f"orpi-{orpi_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = m.group(1)
        
        # Get context
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        # Extract price
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        # Extract surface
        surface_match = re.search(r'(\d+)\s*m[²2]', block_clean)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Extract rooms
        rooms_match = re.search(r'(\d+)\s*(?:pi[eè]ces?|p\b)', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        # Extract T-type
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        listings.append({
            'source': 'orpi',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:500]
        })
    
    return listings

def parse_century21(filepath):
    """Parse Century 21 listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # C21 listing links
    link_pattern = r'href="(https://www\.century21\.fr/annonces/[^"]*?/(\d+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        c21_id = m.group(2)
        listing_id = f"c21-{c21_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = m.group(1)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+)\s*m[²2]', block_clean)
        surface = int(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        listings.append({
            'source': 'c21',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:500]
        })
    
    return listings

def parse_jullien_allix(filepath):
    """Parse Jullien & Allix listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # JA uses slug-based URLs for listings
    link_pattern = r'href="(https://www\.jullien-allix\.fr/annonce/(a-louer[^"]+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        url = m.group(1)
        slug = m.group(2)
        listing_id = f"ja-{slug}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        # Extract price
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        # Extract surface
        surface_match = re.search(r'(\d+)\s*m[²2]', block_clean)
        surface = int(surface_match.group(1)) if surface_match else None
        
        # Extract type F
        f_match = re.search(r'(?:type\s+)?F(\d+)', block_clean, re.I)
        rooms = int(f_match.group(1)) if f_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        listings.append({
            'source': 'ja',
            'id': listing_id,
            'title': block_clean[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:600]
        })
    
    return listings

def parse_saintroch(filepath):
    """Parse Saint Roch Immobilier listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Look for listing cards with LA/VA/LS IDs
    # The IDs appear in href links
    link_pattern = r'href="([^"]*(?:location|louer|a-louer)[^"]*(?:LA|VA|LS)(\d+)[^"]*)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.saintrochimmo.com{url}"
        stroch_id = f"stroch-LA{m.group(2)}"
        if stroch_id in seen_ids:
            continue
        seen_ids.add(stroch_id)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        f_match = re.search(r'(?:type\s+)?F(\d+)', block_clean, re.I)
        if f_match and rooms is None:
            rooms = int(f_match.group(1))
        
        listings.append({
            'source': 'stroch',
            'id': stroch_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:600]
        })
    
    # Also try generic pattern - any link with LA/VA/LS number that's in a location context
    general_pattern = r'href="([^"]*(?:LA|VA|LS)(\d+)[^"]*)"'
    for m in re.finditer(general_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.saintrochimmo.com{url}"
        # Skip vente links
        if any(x in url.lower() for x in ['vente', 'acheter', 'vendre']):
            continue
        stroch_id = f"stroch-LA{m.group(2)}"
        if stroch_id in seen_ids:
            continue
        seen_ids.add(stroch_id)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        f_match = re.search(r'(?:type\s+)?F(\d+)', block_clean, re.I)
        if f_match and rooms is None:
            rooms = int(f_match.group(1))
        
        listings.append({
            'source': 'stroch',
            'id': stroch_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:600]
        })
    
    return listings

def parse_heuze(filepath):
    """Parse HEUZE Immobilier listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # HEUZE uses LA/VA/LS + numeric IDs
    link_pattern = r'href="([^"]*(?:location|louer|a-louer)[^"]*(?:LA|VA|LS)(\d+)[^"]*)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.heuze-immo.fr{url}"
        prefix = re.search(r'(LA|VA|LS)(\d+)', url, re.I)
        if not prefix:
            continue
        heuze_id = f"heuze-{prefix.group(1).upper()}{prefix.group(2)}"
        if heuze_id in seen_ids:
            continue
        seen_ids.add(heuze_id)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        f_match = re.search(r'(?:type\s+)?F(\d+)', block_clean, re.I)
        if f_match and rooms is None:
            rooms = int(f_match.group(1))
        
        listings.append({
            'source': 'heuze',
            'id': heuze_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:600]
        })
    
    # Also try generic pattern
    general_pattern = r'href="([^"]*(?:LA|VA|LS)(\d+)[^"]*)"'
    for m in re.finditer(general_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.heuze-immo.fr{url}"
        if any(x in url.lower() for x in ['vente', 'acheter', 'vendre']):
            continue
        prefix = re.search(r'(LA|VA|LS)(\d+)', url, re.I)
        if not prefix:
            continue
        heuze_id = f"heuze-{prefix.group(1).upper()}{prefix.group(2)}"
        if heuze_id in seen_ids:
            continue
        seen_ids.add(heuze_id)
        
        start = max(0, m.start() - 500)
        end = min(len(html), m.start() + 3000)
        block = html[start:end]
        block_clean = strip_tags(block)
        
        price_match = re.search(r'(\d[\d ]*)\s*€', block_clean)
        price = int(price_match.group(1).replace(' ', '')) if price_match else None
        
        surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', block_clean)
        surface = float(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[eè]ces?', block_clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        t_match = re.search(r'T(\d+)', block_clean)
        if t_match and rooms is None:
            rooms = int(t_match.group(1))
        
        f_match = re.search(r'(?:type\s+)?F(\d+)', block_clean, re.I)
        if f_match and rooms is None:
            rooms = int(f_match.group(1))
        
        listings.append({
            'source': 'heuze',
            'id': heuze_id,
            'title': block_clean[:200],
            'price': price,
            'surface': int(surface) if surface else None,
            'rooms': rooms,
            'url': url,
            'description': block_clean[:600]
        })
    
    return listings

def parse_lhimmo(filepath):
    """Parse LH Immo listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # LH Immo uses WordPress-style URLs with property slugs
    # Look for links to property pages
    link_patterns = [
        r'href="(https://www\.lhimmo\.com/(?!annonces/$|category|tag|page|author|wp-)[^"]+)"',
        r'href="(/(?!annonces/$|category|tag|page|author|wp-)[a-z][^"]+)"',
    ]
    
    seen_ids = set()
    # Also look for property cards with specific data
    # Find blocks with surface, rooms, price indicators
    card_pattern = r'(\d+)m[²2].*?(\d+).{0,50}?(?:Maison|Appartement|Studio)\s+([^<]+)'
    
    # Get the section with property listings
    # LH Immo shows property cards with surface, rooms, title
    blocks = re.findall(r'((?:\d+)m[²2][^<]*(?:\d+)[^<]*(?:Maison|Appartement|Studio)[^<]*)', html, re.DOTALL)
    
    for block in blocks:
        clean = strip_tags(block)
        surface_match = re.search(r'(\d+)m[²2]', clean)
        surface = int(surface_match.group(1)) if surface_match else None
        
        rooms_match = re.search(r'T(\d+)', clean)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        title_match = re.search(r'((?:Maison|Appartement|Studio)\s+[^\-]+)', clean)
        title = title_match.group(1).strip() if title_match else clean[:100]
        
        # Try to find a link
        link_match = re.search(r'href="([^"]+)"', block)
        url = link_match.group(1) if link_match else ''
        if url.startswith('/'):
            url = f"https://www.lhimmo.com{url}"
        
        slug = url.rstrip('/').split('/')[-1] if url else title.lower().replace(' ', '-')
        listing_id = f"lhimmo-{slug}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        listings.append({
            'source': 'lhimmo',
            'id': listing_id,
            'title': title,
            'price': None,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'description': clean[:500]
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
    print(f"  Price: {l['price']}€")
    print(f"  Surface: {l['surface']}m²")
    print(f"  Rooms: {l['rooms']}")
    print(f"  URL: {l['url']}")
    print(f"  Desc: {l.get('description', '')[:300]}")

# Save
output_path = os.path.join(BASE_DIR, "all_listings_v2.json")
with open(output_path, 'w') as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {output_path}")