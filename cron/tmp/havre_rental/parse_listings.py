#!/usr/bin/env python3
"""Parse rental listing HTML files from multiple French real estate sources."""
import re
import json
import os
from html import unescape

BASE_DIR = "/opt/data/cron/tmp/havre_rental"

def strip_tags(html_str):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

def extract_price(text):
    """Extract price in euros from text."""
    m = re.search(r'(\d[\d\s]*)\s*€', text)
    if m:
        return int(m.group(1).replace(' ', '').replace('\xa0', ''))
    return None

def extract_surface(text):
    """Extract surface in m² from text."""
    m = re.search(r'(\d+)\s*m[²2]', text)
    if m:
        return int(m.group(1))
    return None

def extract_rooms(text):
    """Extract number of rooms/pieces."""
    m = re.search(r'(\d+)\s*(?:pi[eè]ce|p\b|T(\d+)|F(\d+))', text, re.I)
    if m:
        if m.group(2):
            return int(m.group(2))
        if m.group(3):
            return int(m.group(3))
        return int(m.group(1))
    return None

def parse_le_partenaire(filepath):
    """Parse Le-Partenaire location listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Find h2 headings (listing titles) and "Voir l'annonce" links in DOM order
    h2_pattern = r'<h2[^>]*>(.*?)</h2>'
    h2_matches = [(m.start(), strip_tags(m.group(1))) for m in re.finditer(h2_pattern, html, re.DOTALL)]
    
    # Find all links that go to listing pages
    link_pattern = r'href="(/immobilier/location/appartement/[^"]+)"[^>]*>(.*?)</a>'
    link_matches = [(m.start(), m.group(1), strip_tags(m.group(2))) for m in re.finditer(link_pattern, html, re.DOTALL)]
    
    # Find "Voir l'annonce" links specifically
    voir_links = []
    for pos, href, text in link_matches:
        if 'voir' in text.lower() or 'annonce' in text.lower():
            full_url = f"https://www.le-partenaire.fr{href}" if href.startswith('/') else href
            voir_links.append((pos, full_url))
    
    # Also try finding listing IDs from URLs
    listing_urls = set()
    for pos, href, text in link_matches:
        # Extract the listing ID (numeric part at end of URL)
        id_match = re.search(r'/(\d+)$', href)
        if id_match:
            listing_urls.add((pos, f"https://www.le-partenaire.fr{href}" if href.startswith('/') else href, id_match.group(1)))
    
    # Match h2 headings with their nearest following listing link
    for i, (h2_pos, title) in enumerate(h2_matches):
        if not title or len(title) < 3:
            continue
        # Find the nearest "Voir" link after this h2
        matching_url = None
        matching_id = None
        for lpos, url in voir_links:
            if lpos > h2_pos:
                matching_url = url
                id_match = re.search(r'/(\d+)$', url)
                if id_match:
                    matching_id = id_match.group(1)
                break
        if not matching_url:
            for lpos, url, lid in listing_urls:
                if lpos > h2_pos:
                    matching_url = url
                    matching_id = lid
                    break
        
        # Extract info from title
        price = extract_price(title)
        surface = extract_surface(title)
        rooms = extract_rooms(title)
        
        # Get surrounding text for more details
        context_start = max(0, h2_pos - 500)
        context_end = min(len(html), h2_pos + 2000)
        context = strip_tags(html[context_start:context_end])
        
        if price is None:
            price = extract_price(context)
        if surface is None:
            surface = extract_surface(context)
        
        if matching_id:
            listings.append({
                'source': 'lp',
                'id': f"lp-{matching_id}",
                'title': title,
                'price': price,
                'surface': surface,
                'rooms': rooms,
                'url': matching_url,
                'context': context[:500]
            })
    
    return listings

def parse_citya(filepath):
    """Parse Citya Immobilier listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Find listing links with IDs
    link_pattern = r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/(GES[\w-]+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        url = m.group(1)
        citya_id = m.group(2)
        listing_id = f"citya-{citya_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        
        # Get context around this link
        context_start = max(0, m.start() - 500)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'citya',
            'id': listing_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
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
        context_start = max(0, m.start() - 1000)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'sqhab',
            'id': listing_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
        })
    
    return listings

def parse_orpi(filepath):
    """Parse Orpi listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Orpi uses UUID-based listing IDs in data attributes or URLs
    # Find listing articles/cards
    link_pattern = r'href="(https://www\.orpi\.com/[^\"]*(?:location|louer)[^\"]*(?:appartement|bien)[^\"]*)"'
    # Also try data-id pattern
    id_pattern = r'data-id="([a-f0-9-]+)"'
    
    seen_ids = set()
    
    # Try finding listing cards with data attributes
    card_pattern = r'data-id="([a-f0-9-]+)"[^>]*>(.*?)</(?:article|div|li)>'
    for m in re.finditer(card_pattern, html, re.DOTALL):
        orpi_id = m.group(1)
        listing_id = f"orpi-{orpi_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        context = strip_tags(m.group(2))
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        # Find URL
        url_match = re.search(r'href="(https://www\.orpi\.com/[^"]*' + orpi_id + '[^"]*)"', html)
        url = url_match.group(1) if url_match else f"https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/"
        
        listings.append({
            'source': 'orpi',
            'id': listing_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
        })
    
    # Also try finding hrefs with Orpi listing IDs
    href_pattern = r'href="https://www\.orpi\.com/[^\"]*-([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"'
    for m in re.finditer(href_pattern, html):
        orpi_id = m.group(1)
        listing_id = f"orpi-{orpi_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = m.group(0).replace('href="', '').rstrip('"')
        
        context_start = max(0, m.start() - 1000)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'orpi',
            'id': listing_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
        })
    
    return listings

def parse_century21(filepath):
    """Parse Century 21 listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # C21 uses numeric listing IDs
    link_pattern = r'href="(https://www\.century21\.fr/annonces/location-appartement/[^"]+/(\d+))"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html):
        c21_id = m.group(2)
        listing_id = f"c21-{c21_id}"
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)
        url = m.group(1)
        
        context_start = max(0, m.start() - 500)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'c21',
            'id': listing_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
        })
    
    return listings

def parse_jullien_allix(filepath):
    """Parse Jullien & Allix listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # JA uses slug-based URLs
    link_pattern = r'href="(https://www\.jullien-allix\.fr/annonce/a-louer-[^"]+)"'
    # Also relative
    link_pattern2 = r'href="(/annonce/a-louer-[^"]+)"'
    
    seen_ids = set()
    for pattern in [link_pattern, link_pattern2]:
        for m in re.finditer(pattern, html):
            url = m.group(1)
            if url.startswith('/'):
                url = f"https://www.jullien-allix.fr{url}"
            slug = url.split('/annonce/')[-1]
            listing_id = f"ja-{slug}"
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)
            
            context_start = max(0, m.start() - 500)
            context_end = min(len(html), m.start() + 2000)
            context = strip_tags(html[context_start:context_end])
            
            price = extract_price(context)
            surface = extract_surface(context)
            rooms = extract_rooms(context)
            
            listings.append({
                'source': 'ja',
                'id': listing_id,
                'title': context[:200],
                'price': price,
                'surface': surface,
                'rooms': rooms,
                'url': url,
                'context': context[:500]
            })
    
    return listings

def parse_saintroch(filepath):
    """Parse Saint Roch Immobilier listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # Saint Roch uses LA + numeric IDs
    link_pattern = r'href="([^"]*(?:LA|VA|LS)\d+[^"]*)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.saintrochimmo.com{url}"
        # Extract ID
        id_match = re.search(r'(?:LA|VA|LS)(\d+)', url, re.I)
        if not id_match:
            continue
        stroch_id = f"stroch-LA{id_match.group(1)}"
        if stroch_id in seen_ids:
            continue
        # Filter for location-related URLs only
        if 'vente' in url.lower() or 'acheter' in url.lower():
            continue
        seen_ids.add(stroch_id)
        
        context_start = max(0, m.start() - 500)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'stroch',
            'id': stroch_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
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
    link_pattern = r'href="([^"]*(?:LA|VA|LS)\d+[^"]*)"'
    seen_ids = set()
    for m in re.finditer(link_pattern, html, re.I):
        url = m.group(1)
        if url.startswith('/'):
            url = f"https://www.heuze-immo.fr{url}"
        id_match = re.search(r'(LA|VA|LS)(\d+)', url, re.I)
        if not id_match:
            continue
        prefix = id_match.group(1).upper()
        heuze_id = f"heuze-{prefix}{id_match.group(2)}"
        if heuze_id in seen_ids:
            continue
        # Skip vente-related
        if 'vente' in url.lower() or 'acheter' in url.lower() or 'vendre' in url.lower():
            continue
        seen_ids.add(heuze_id)
        
        context_start = max(0, m.start() - 500)
        context_end = min(len(html), m.start() + 2000)
        context = strip_tags(html[context_start:context_end])
        
        price = extract_price(context)
        surface = extract_surface(context)
        rooms = extract_rooms(context)
        
        listings.append({
            'source': 'heuze',
            'id': heuze_id,
            'title': context[:200],
            'price': price,
            'surface': surface,
            'rooms': rooms,
            'url': url,
            'context': context[:500]
        })
    
    return listings

def parse_lhimmo(filepath):
    """Parse LH Immo listings."""
    listings = []
    if not os.path.exists(filepath):
        return listings
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    # LH Immo uses slug-based URLs
    link_pattern = r'href="(https://www\.lhimmo\.com/(?:annonces|appartement|maison)[^"]*)"'
    link_pattern2 = r'href="(/(?:annonces|appartement|maison)[^"]*)"'
    
    seen_ids = set()
    for pattern in [link_pattern, link_pattern2]:
        for m in re.finditer(pattern, html):
            url = m.group(1)
            if url.startswith('/'):
                url = f"https://www.lhimmo.com{url}"
            # Create ID from URL slug
            slug = url.rstrip('/').split('/')[-1]
            if not slug or len(slug) < 3:
                continue
            listing_id = f"lhimmo-{slug}"
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)
            
            context_start = max(0, m.start() - 500)
            context_end = min(len(html), m.start() + 2000)
            context = strip_tags(html[context_start:context_end])
            
            price = extract_price(context)
            surface = extract_surface(context)
            rooms = extract_rooms(context)
            
            listings.append({
                'source': 'lhimmo',
                'id': listing_id,
                'title': context[:200],
                'price': price,
                'surface': surface,
                'rooms': rooms,
                'url': url,
                'context': context[:500]
            })
    
    return listings

# Parse all sources
all_listings = []

# Le-Partenaire
lp_listings = parse_le_partenaire(os.path.join(BASE_DIR, "lp_page1.html"))
all_listings.extend(lp_listings)
print(f"Le-Partenaire: {len(lp_listings)} listings")

# Citya
citya_listings = parse_citya(os.path.join(BASE_DIR, "citya_page.html"))
all_listings.extend(citya_listings)
print(f"Citya: {len(citya_listings)} listings")

# SquareHabitat
sqhab_listings = parse_squarehabitat(os.path.join(BASE_DIR, "sqhab_page.html"))
all_listings.extend(sqhab_listings)
print(f"SquareHabitat: {len(sqhab_listings)} listings")

# Orpi
orpi_listings = parse_orpi(os.path.join(BASE_DIR, "orpi_page.html"))
all_listings.extend(orpi_listings)
print(f"Orpi: {len(orpi_listings)} listings")

# Century 21
c21_listings = parse_century21(os.path.join(BASE_DIR, "c21_page.html"))
all_listings.extend(c21_listings)
print(f"Century21: {len(c21_listings)} listings")

# Jullien & Allix
ja_listings = parse_jullien_allix(os.path.join(BASE_DIR, "ja_page.html"))
all_listings.extend(ja_listings)
print(f"Jullien-Allix: {len(ja_listings)} listings")

# Saint Roch
stroch_listings = parse_saintroch(os.path.join(BASE_DIR, "stroch_page.html"))
all_listings.extend(stroch_listings)
print(f"SaintRoch: {len(stroch_listings)} listings")

# HEUZE
heuze_listings = parse_heuze(os.path.join(BASE_DIR, "heuze_page.html"))
all_listings.extend(heuze_listings)
print(f"HEUZE: {len(heuze_listings)} listings")

# LH Immo
lhimmo_listings = parse_lhimmo(os.path.join(BASE_DIR, "lhimmo_page.html"))
all_listings.extend(lhimmo_listings)
print(f"LH Immo: {len(lhimmo_listings)} listings")

print(f"\n=== TOTAL: {len(all_listings)} listings parsed ===")

# Print details for debugging
for l in all_listings:
    print(f"\n--- {l['id']} ---")
    print(f"  Source: {l['source']}")
    print(f"  Price: {l['price']}€")
    print(f"  Surface: {l['surface']}m²")
    print(f"  Rooms: {l['rooms']}")
    print(f"  URL: {l['url']}")
    print(f"  Context: {l['context'][:300]}")

# Save all listings to JSON
output_path = os.path.join(BASE_DIR, "all_listings.json")
with open(output_path, 'w') as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {output_path}")