#!/usr/bin/env python3
"""Parse all downloaded HTML files for Le Havre rental listings matching criteria."""
import re, json, os, html
from html.parser import HTMLParser

HAVRE_DIR = "/opt/data/tmp/havre"

# Load seen IDs
with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))
print(f"Loaded {len(seen_ids)} seen IDs")

def read_file(name):
    path = os.path.join(HAVRE_DIR, name)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

# === LE-PARTENAIRE ===
def parse_le_partenaire():
    """Le-Partenaire: parse HTML for listing cards with price, surface, rooms, title, URL."""
    content = read_file("lp.html")
    listings = []
    # Le-Partenaire listings have links like /immobilier/location/appartement/havre/76600/Npieces/ID
    # Try to find listing cards
    # Pattern: href="/immobilier/location/appartement/..."
    href_pattern = re.findall(r'href="(/immobilier/location/appartement/[^"]+)"', content)
    print(f"LP: Found {len(href_pattern)} href links")
    for h in href_pattern[:5]:
        print(f"  {h}")
    
    # Look for listing data - typically in article/div blocks
    # Try extracting h2 headings (listing titles) and prices
    h2_pattern = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL)
    print(f"LP: Found {len(h2_pattern)} h2 headings")
    for h in h2_pattern[:5]:
        clean = re.sub(r'<[^>]+>', '', h).strip()
        print(f"  h2: {clean[:100]}")
    
    # Look for price patterns (€/mois or €)
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"LP: Found {len(price_pattern)} prices with /mois")
    for p in price_pattern[:10]:
        print(f"  price: {p}")
    
    # Look for surface patterns (XXm²)
    surface_pattern = re.findall(r'(\d+)\s*m²', content)
    print(f"LP: Found {len(surface_pattern)} surface mentions")
    
    # Extract listing blocks - look for article elements or specific class patterns
    # Le-Partenaire uses data in structured blocks
    # Try to find listing IDs from URLs
    ids = set()
    for h in href_pattern:
        m = re.search(r'/(\d+)$', h)
        if m:
            ids.add(m.group(1))
    print(f"LP: Unique listing IDs from URLs: {len(ids)}")
    for i in sorted(ids)[:10]:
        print(f"  ID: {i}")
    
    return listings

# === CITYA ===
def parse_citya():
    content = read_file("citya.html")
    listings = []
    # Citya listing URLs: /annonce/location/...
    href_pattern = re.findall(r'href="(/annonce/location/[^"]+)"', content)
    print(f"Citya: Found {len(href_pattern)} href links")
    for h in href_pattern[:5]:
        print(f"  {h}")
    
    # Citya uses data attributes or specific structures
    # Look for "GES" reference patterns
    ref_pattern = re.findall(r'GES\d+-\d+', content)
    print(f"Citya: Found {len(ref_pattern)} GES refs")
    
    # Look for price patterns
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"Citya: Found {len(price_pattern)} prices")
    
    # Try to find listing blocks with title, price, surface
    # Citya HTML structure varies - let's look for common patterns
    # Look for article tags or listing divs
    articles = re.findall(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
    print(f"Citya: Found {len(articles)} article tags")
    
    return listings

# === ORPI ===
def parse_orpi():
    content = read_file("orpi.html")
    listings = []
    href_pattern = re.findall(r'href="(/location-immobiliere-le-havre/[^"]+)"', content)
    # Also try general patterns
    href_pattern2 = re.findall(r'href="(https://www\.orpi\.com/[^"]+location[^"]+)"', content)
    print(f"Orpi: Found {len(href_pattern)} local hrefs, {len(href_pattern2)} absolute hrefs")
    for h in (href_pattern + href_pattern2)[:5]:
        print(f"  {h}")
    
    # Look for UUID patterns in Orpi URLs
    uuid_pattern = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', content)
    print(f"Orpi: Found {len(uuid_pattern)} UUIDs")
    
    # Look for price
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"Orpi: Found {len(price_pattern)} prices with /mois")
    
    # Look for surface
    surface_pattern = re.findall(r'(\d+)\s*m²', content)
    print(f"Orpi: Found {len(surface_pattern)} surface mentions")
    
    return listings

# === SQUAREHABITAT ===
def parse_sqhab():
    content = read_file("sqhab.html")
    listings = []
    href_pattern = re.findall(r'href="(/annonces/location/[^"]+)"', content)
    print(f"SqHab: Found {len(href_pattern)} href links")
    for h in href_pattern[:5]:
        print(f"  {h}")
    
    # Look for listing IDs (UUIDs)
    uuid_pattern = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', content)
    print(f"SqHab: Found {len(uuid_pattern)} UUIDs")
    
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"SqHab: Found {len(price_pattern)} prices")
    
    return listings

# === CENTURY21 ===
def parse_c21():
    content = read_file("c21.html")
    listings = []
    href_pattern = re.findall(r'href="(/annonces/location[^"]+)"', content)
    href_pattern2 = re.findall(r'href="(https://www\.century21\.fr/annonces/[^"]+)"', content)
    print(f"C21: Found {len(href_pattern)} local, {len(href_pattern2)} absolute hrefs")
    for h in (href_pattern + href_pattern2)[:5]:
        print(f"  {h}")
    
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"C21: Found {len(price_pattern)} prices")
    
    return listings

# === JULLIEN & ALLIX ===
def parse_ja():
    content = read_file("ja.html")
    listings = []
    href_pattern = re.findall(r'href="(/annonce/[^"]+)"', content)
    print(f"JA: Found {len(href_pattern)} href links")
    for h in href_pattern[:10]:
        print(f"  {h}")
    
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"JA: Found {len(price_pattern)} prices")
    
    return listings

# === HEUZE ===
def parse_heuze():
    content = read_file("heuze_home.html")
    listings = []
    href_pattern = re.findall(r'href="(/[^"]*(?:location|a-louer|annonce)[^"]*)"', content, re.I)
    print(f"HEUZE: Found {len(href_pattern)} location-related hrefs")
    for h in href_pattern[:10]:
        print(f"  {h}")
    
    price_pattern = re.findall(r'(\d{2,4})\s*€\s*/?\s*mois', content, re.IGNORECASE)
    print(f"HEUZE: Found {len(price_pattern)} prices")
    
    return listings

# === LH IMMO ===
def parse_lhimmo():
    content = read_file("lhimmo_home.html")
    listings = []
    href_pattern = re.findall(r'href="(/[^"]*(?:location|a-louer|annonce|biens)[^"]*)"', content, re.I)
    print(f"LHImmo: Found {len(href_pattern)} location-related hrefs")
    for h in href_pattern[:10]:
        print(f"  {h}")
    
    return listings

# === SAINT ROCH ===
def parse_stroch():
    content = read_file("stroch_home.html")
    listings = []
    href_pattern = re.findall(r'href="(/[^"]*(?:location|a-louer|annonce|biens)[^"]*)"', content, re.I)
    print(f"StRoch: Found {len(href_pattern)} location-related hrefs")
    for h in href_pattern[:10]:
        print(f"  {h}")
    
    return listings

# === BIEN'ICI ===
def parse_bienici():
    content = read_file("bienici.html")
    # Bien'ici is JS-heavy - check if there's any listing data
    print(f"Bienici: {len(content)} bytes")
    # Look for JSON data embedded
    json_pattern = re.findall(r'"(annonce|listing|product)Id":\s*"([^"]+)"', content)
    print(f"Bienici: Found {len(json_pattern)} listing IDs in JSON")
    
    # Check for any script data
    script_data = re.findall(r'window\.__\w+__\s*=\s*({.*?});', content, re.DOTALL)
    print(f"Bienici: Found {len(script_data)} window data blocks")
    
    return []

print("=" * 60)
print("PARSING LE-PARTENAIRE")
print("=" * 60)
parse_le_partenaire()
print()
print("=" * 60)
print("PARSING CITYA")
print("=" * 60)
parse_citya()
print()
print("=" * 60)
print("PARSING ORPI")
print("=" * 60)
parse_orpi()
print()
print("=" * 60)
print("PARSING SQUAREHABITAT")
print("=" * 60)
parse_sqhab()
print()
print("=" * 60)
print("PARSING CENTURY21")
print("=" * 60)
parse_c21()
print()
print("=" * 60)
print("PARSING JULLIEN & ALLIX")
print("=" * 60)
parse_ja()
print()
print("=" * 60)
print("PARSING HEUZE")
print("=" * 60)
parse_heuze()
print()
print("=" * 60)
print("PARSING LH IMMO")
print("=" * 60)
parse_lhimmo()
print()
print("=" * 60)
print("PARSING SAINT ROCH")
print("=" * 60)
parse_stroch()
print()
print("=" * 60)
print("PARSING BIEN'ICI")
print("=" * 60)
parse_bienici()