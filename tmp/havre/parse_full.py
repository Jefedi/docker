#!/usr/bin/env python3
"""Comprehensive parser for Le Havre rental listings from all sources."""
import re, json, os
from html import unescape

HAVRE_DIR = "/opt/data/tmp/havre"
BASE_LP = "https://www.le-partenaire.fr"

with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))
print(f"Loaded {len(seen_ids)} seen IDs\n")

def read_file(name):
    path = os.path.join(HAVRE_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

def clean_text(text):
    text = unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === LE-PARTENAIRE ===
def parse_le_partenaire():
    content = read_file("lp.html")
    listings = []
    h2_pattern = re.findall(r'<h2[^>]*class="card-title[^"]*"[^>]*>(.*?)</h2>', content, re.DOTALL)
    print(f"=== LE-PARTENAIRE ({len(h2_pattern)} listings) ===")
    
    for i, h2_raw in enumerate(h2_pattern):
        h2_text = clean_text(h2_raw)
        # Extract pieces and surface
        pieces_m = re.search(r'(\d+)\s*pi[èc]ce', h2_text)
        surface_m = re.search(r'(\d+)\s*m²', h2_text)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        surface = int(surface_m.group(1)) if surface_m else 0
        
        # Find the block after this h2
        h2_pos = content.find(h2_raw)
        block = content[h2_pos:h2_pos+4000]
        
        # Extract price: look for <span class="prix">XXX&nbsp;€</span>
        price_m = re.search(r'<span class="prix">(\d+)\s*&?nbsp;\s*€</span>', block)
        if not price_m:
            price_m = re.search(r'Loyer:\s*(\d+)\s*Euros', block)
        price = int(price_m.group(1)) if price_m else 0
        
        # Extract href
        href_m = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', block)
        href = href_m.group(1) if href_m else ""
        
        # Extract description
        desc_m = re.search(r'<p class="card-text crop-text-4"[^>]*>(.*?)</p>', block, re.DOTALL)
        desc = clean_text(desc_m.group(1)) if desc_m else ""
        
        # Extract listing ID
        id_m = re.search(r'/(\d+)"', href)
        list_id = f"lp-{id_m.group(1)}" if id_m else ""
        
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': f"{BASE_LP}{href}" if href else "",
            'desc': desc,
            'source': 'le-partenaire'
        })
        print(f"  [{i}] ID={list_id} | {pieces}p {surface}m² | {price}€ | seen={list_id in seen_ids}")
        if desc:
            print(f"       desc: {desc[:150]}...")
    return listings

# === ORPI ===
def parse_orpi():
    content = read_file("orpi.html")
    listings = []
    print(f"\n=== ORPI ===")
    # Orpi uses a JSON-like structure or data attributes
    # Look for listing blocks with UUID
    # Orpi typically has <a href="/location-immobiliere-le-havre/louer-appartement/UUID">
    href_pattern = re.findall(r'href="/location-immobiliere-le-havre/louer-appartement/([0-9a-f-]{36})"', content)
    # Also try with other URL patterns
    href_pattern2 = re.findall(r'href="/location-immobiliere[^"]*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', content)
    all_uuids = set(href_pattern + href_pattern2)
    print(f"  Found {len(all_uuids)} unique UUIDs")
    
    # Try to find listing data blocks
    # Orpi HTML often has data in specific div structures
    # Look for price, surface, rooms near each UUID
    for uuid in list(all_uuids):
        uuid_pos = content.find(uuid)
        if uuid_pos < 0:
            continue
        block = content[max(0,uuid_pos-200):uuid_pos+2000]
        block_clean = clean_text(block)
        
        # Extract price
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        
        # Extract surface
        surface_m = re.search(r'(\d+)\s*m²', block_clean)
        surface = int(surface_m.group(1)) if surface_m else 0
        
        # Extract rooms/pièces
        pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece|p\b)', block_clean)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        list_id = f"orpi-{uuid}"
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': f"https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/{uuid}",
            'desc': block_clean[:300],
            'source': 'orpi'
        })
        print(f"  {list_id} | {pieces}p {surface}m² | {price}€ | seen={list_id in seen_ids}")
    
    return listings

# === SQUAREHABITAT ===
def parse_sqhab():
    content = read_file("sqhab.html")
    listings = []
    print(f"\n=== SQUAREHABITAT ===")
    # SquareHabitat uses UUID-based URLs
    href_pattern = re.findall(r'href="/annonces/location/bien/[^"]*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', content)
    all_uuids = set(href_pattern)
    print(f"  Found {len(all_uuids)} unique UUIDs")
    
    for uuid in list(all_uuids):
        uuid_pos = content.find(uuid)
        if uuid_pos < 0:
            continue
        block = content[max(0,uuid_pos-500):uuid_pos+3000]
        block_clean = clean_text(block)
        
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        surface_m = re.search(r'(\d+)\s*m²', block_clean)
        surface = int(surface_m.group(1)) if surface_m else 0
        pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece)', block_clean)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        list_id = f"sqhab-{uuid}"
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': f"https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/{uuid}",
            'desc': block_clean[:300],
            'source': 'squarehabitat'
        })
        print(f"  {list_id} | {pieces}p {surface}m² | {price}€ | seen={list_id in seen_ids}")
    
    return listings

# === CENTURY21 ===
def parse_c21():
    content = read_file("c21.html")
    listings = []
    print(f"\n=== CENTURY21 ===")
    # C21 uses numeric IDs in URLs
    href_pattern = re.findall(r'href="/annonces/location-appartement/[^"]*-(\d+)"', content)
    # Also try to find listing blocks
    all_ids = set(href_pattern)
    print(f"  Found {len(all_ids)} unique IDs")
    
    for list_id_num in list(all_ids):
        id_pos = content.find(list_id_num)
        if id_pos < 0:
            continue
        block = content[max(0,id_pos-1000):id_pos+2000]
        block_clean = clean_text(block)
        
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        surface_m = re.search(r'(\d+)\s*m²', block_clean)
        surface = int(surface_m.group(1)) if surface_m else 0
        pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece)', block_clean)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        list_id = f"c21-{list_id_num}"
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': f"https://www.century21.fr/annonces/location-appartement/v-le+havre/{list_id_num}",
            'desc': block_clean[:300],
            'source': 'century21'
        })
        print(f"  {list_id} | {pieces}p {surface}m² | {price}€ | seen={list_id in seen_ids}")
    
    return listings

# === JULLIEN & ALLIX ===
def parse_ja():
    content = read_file("ja.html")
    listings = []
    print(f"\n=== JULLIEN & ALLIX ===")
    # JA uses slug-based URLs
    href_pattern = re.findall(r'href="/annonce/(a-louer-[^"]+)"', content)
    all_slugs = set(href_pattern)
    print(f"  Found {len(all_slugs)} unique slugs")
    
    for slug in list(all_slugs):
        slug_clean = slug.split('"')[0]
        slug_pos = content.find(slug_clean)
        if slug_pos < 0:
            continue
        block = content[max(0,slug_pos-1000):slug_pos+3000]
        block_clean = clean_text(block)
        
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        surface_m = re.search(r'(\d+)\s*m²', block_clean)
        surface = int(surface_m.group(1)) if surface_m else 0
        # JA uses F2, F3, etc. for room count
        pieces_m = re.search(r'[Ff](\d+)', block_clean)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        # Also try pièces
        if not pieces:
            pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece)', block_clean)
            pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        list_id = f"ja-{slug_clean}"
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': f"https://www.jullien-allix.fr/annonce/{slug_clean}",
            'desc': block_clean[:300],
            'source': 'jullien-allix'
        })
        print(f"  {list_id[:60]} | F{pieces} {surface}m² | {price}€ | seen={list_id in seen_ids}")
    
    return listings

# === HEUZE ===
def parse_heuze():
    content = read_file("heuze_home.html")
    listings = []
    print(f"\n=== HEUZE ===")
    # HEUZE has a /location page - let's fetch that
    # First check what we have on the home page
    # Found /location/appartement/le-havre/76600
    return listings

# === CITYA ===
def parse_citya():
    content = read_file("citya.html")
    listings = []
    print(f"\n=== CITYA ===")
    # Citya uses GES reference numbers
    ref_pattern = re.findall(r'(GES\d+-\d+)', content)
    all_refs = set(ref_pattern)
    print(f"  Found {len(all_refs)} unique GES refs")
    
    for ref in list(all_refs)[:30]:
        ref_pos = content.find(ref)
        if ref_pos < 0:
            continue
        block = content[max(0,ref_pos-2000):ref_pos+2000]
        block_clean = clean_text(block)
        
        price_m = re.search(r'(\d+)\s*€', block_clean)
        price = int(price_m.group(1)) if price_m else 0
        surface_m = re.search(r'(\d+)\s*m²', block_clean)
        surface = int(surface_m.group(1)) if surface_m else 0
        pieces_m = re.search(r'(\d+)\s*(?:pi[èc]ce|piece)', block_clean)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        
        list_id = f"citya-{ref}"
        # Construct URL
        href = f"https://www.citya.com/annonce/location/appartement/le-havre-76351/{ref}"
        listings.append({
            'id': list_id,
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': href,
            'desc': block_clean[:300],
            'source': 'citya'
        })
        print(f"  {list_id} | {pieces}p {surface}m² | {price}€ | seen={list_id in seen_ids}")
    
    return listings

# Run all parsers
all_listings = []
all_listings.extend(parse_le_partenaire())
all_listings.extend(parse_orpi())
all_listings.extend(parse_sqhab())
all_listings.extend(parse_c21())
all_listings.extend(parse_ja())
all_listings.extend(parse_heuze())
all_listings.extend(parse_citya())

print(f"\n{'='*60}")
print(f"TOTAL LISTINGS PARSED: {len(all_listings)}")
print(f"{'='*60}")

# Save for next step
with open(f"{HAVRE_DIR}/all_listings.json", "w") as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)
print(f"Saved to {HAVRE_DIR}/all_listings.json")