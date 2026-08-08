#!/usr/bin/env python3
"""Parse Orpi individual listing pages - extract full description from HTML."""
import re, html as h

files = [
    ('/tmp/scrape/orpi_715edead.html', '715edead-87f4-4060-a5e2-a9225c2cdecb'),
    ('/tmp/scrape/orpi_9f40f407.html', '9f40f407-1705-445e-873c-6a50ed3c636b'),
]

for fpath, uid in files:
    print(f"\n=== {uid} ===")
    raw = open(fpath, 'r', errors='replace').read()
    
    # Extract the JSON data block from the page
    # Orpi stores listing data in a dataLayer object
    data_match = re.search(r"local_id:\s*'([^']+)'.*?local_totalvalue:\s*'(\d+)'.*?quartier:\s*\"([^\"]*)\"", raw, re.S)
    if data_match:
        print(f"  ID: {data_match.group(1)}")
        print(f"  Price: {data_match.group(2)}euro")
        print(f"  Quartier: {data_match.group(3)}")
    
    # Find the description - look for the listing description div/section
    # Orpi usually has a description in a specific section
    desc_match = re.search(r'(?:Description|description)["\']?\s*[:\s]*(.*?)(?:Caractéristiques|DPE|Diagnostic|Voir|$)', raw, re.S)
    
    # Try finding the description in a specific div
    # Look for <p> or <div> with the actual listing text
    # Orpi stores description in a specific class
    desc_div = re.search(r'class="[^"]*description[^"]*"[^>]*>(.*?)</div>', raw, re.S | re.I)
    if desc_div:
        desc_text = re.sub(r'<[^>]+>', ' ', desc_div.group(1))
        desc_text = h.unescape(desc_text)
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        print(f"  Description: {desc_text[:500]}")
    
    # Also look for the listing text in a broader area
    # Find all text between the title and the footer
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find the main listing content - between the title and contact form
    content_start = text.find('T-2 à Le Havre')
    if content_start >= 0:
        content = text[content_start:content_start+2000]
        # Find the useful part - after the page title
        # Look for the description text
        desc_start = content.find('cuisine')
        if desc_start < 0:
            desc_start = content.find('Appartement')
        if desc_start >= 0:
            print(f"  Content excerpt: {content[desc_start:desc_start+500]}")
    
    # Find surface from the page title or content
    surface_match = re.search(r'(\d[\d,\.]*)\s*m[²2]', text[:5000])
    if surface_match:
        print(f"  Surface: {surface_match.group(1)}m2")
    
    # Check cuisine/chambre
    cuisine_sep = bool(re.search(r'cuisine\s*(?:s[ée]par[ée]e|ind[ée]pendante|ferm[ée]e)', text[:5000], re.I))
    cuisine_ouv = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette', text[:5000], re.I))
    print(f"  Cuisine sep: {cuisine_sep} | Cuisine ouverte: {cuisine_ouv}")