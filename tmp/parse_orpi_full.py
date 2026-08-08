#!/usr/bin/env python3
"""Parse Orpi individual listing pages - get full description."""
import re, html as h

files = [
    ('/tmp/scrape/orpi_715edead.html', '715edead-87f4-4060-a5e2-a9225c2cdecb', 'T2'),
    ('/tmp/scrape/orpi_9f40f407.html', '9f40f407-1705-445e-873c-6a50ed3c636b', 'T2'),
]

for fpath, uid, t in files:
    print(f"\n=== {uid} ===")
    raw = open(fpath, 'r', errors='replace').read()
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find the title
    title_match = re.search(r'Location appartement[^|]+Le Havre[^|]*(\d[\d,\.]*)\s*m[²2]', text[:500])
    if title_match:
        print(f"  Title: {text[:200]}")
    
    # Find description - look for "Description" or after the title
    # Orpi usually has a description block with the listing details
    desc_start = text.find('Description')
    if desc_start < 0:
        # Try to find the main listing text
        desc_start = text.find('Appartement')
    if desc_start >= 0:
        print(f"  Desc: {text[desc_start:desc_start+800]}")
    
    # Find price, surface, etc from structured data
    price_match = re.search(r'local_totalvalue:\s*[\'"](\d+)[\'"]', raw)
    if price_match:
        print(f"  Price from data: {price_match.group(1)}euro")
    
    # Find surface from the page
    surface_matches = re.findall(r'(\d[\d,\.]*)\s*m[²2]', text[:3000])
    print(f"  All surfaces: {surface_matches[:10]}")
    
    # Find quartier from text
    quartier_match = re.search(r'(?:quartier|secteur|rue|avenue|boulevard|place|impasse|allee)\s+([^\d,]+?)(?:\d|,|étage|etage|$)', text[:5000], re.I)
    
    # Find the listing description block - look for the main content
    # Orpi has "Appartement ... à louer" or similar
    content_match = re.search(r'(Appartement[^|]+?(?:louer|Le Havre)[^|]+?)(?=\d+\s*€|$)', text[:5000], re.I)
    if content_match:
        print(f"  Content: {content_match.group(1)[:500]}")