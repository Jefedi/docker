#!/usr/bin/env python3
"""Extract listings from netty.immo-based sites (SaintRoch, HEUZE) and Le-Partenaire page 2."""
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

# Check SaintRoch location page for listing data
for name, filepath in [
    ('SaintRoch /location', os.path.join(BASE_DIR, 'stroch_location.html')),
    ('HEUZE /location', os.path.join(BASE_DIR, 'heuze_location.html')),
]:
    if not os.path.exists(filepath):
        print(f"{name}: file not found")
        continue
    with open(filepath, 'r', errors='replace') as f:
        html = f.read()
    
    print(f"\n=== {name} ({len(html)} bytes) ===")
    
    # Look for JSON data in script tags - netty.immo likely embeds listing data in a JSON script
    # Common patterns: window.__INITIAL_STATE__ or window.__APOLLO_STATE__ or data-react-helmet
    for pattern_name, pattern in [
        ('window.__INITIAL_STATE__', r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>'),
        ('window.__DATA__', r'window\.__DATA__\s*=\s*(\{.*?\});?\s*</script>'),
        ('window.__APOLLO_STATE__', r'window\.__APOLLO_STATE__\s*=\s*(\{.*?\});?\s*</script>'),
        ('window.NETTY', r'window\.NETTY[^=]*=\s*(\{.*?\});?\s*</script>'),
        ('application/json', r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'),
        ('application/ld+json', r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'),
        ('data-react-helmet', r'data-react-helmet[^>]*>(.*?)</script>'),
    ]:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"  Found {pattern_name}: {len(matches)} blocks")
            for m in matches[:2]:
                print(f"    {m[:300]}")
    
    # Try to find listing data in any script tag
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, script in enumerate(scripts):
        # Look for listing-related data
        if any(kw in script for kw in ['"annonces"', '"liste"', '"location"', '"bien"', '"Loyer"', '"loyer"', '"prix"']):
            if len(script) > 100:
                print(f"  Script {i} contains listing keywords ({len(script)} chars)")
                # Find the relevant data
                if 'annonces' in script:
                    idx = script.find('annonces')
                    print(f"    Context: ...{script[max(0,idx-50):idx+200]}...")
    
    # Look for listing cards in HTML - maybe the SSR includes them
    # Look for common patterns: data attributes with listing IDs
    data_attrs = re.findall(r'data-(?:annonce|bien|listing|ref|id)[^=]*="([^"]+)"', html, re.I)
    if data_attrs:
        print(f"  Data attrs: {data_attrs[:20]}")
    
    # Look for listing titles/links
    listing_links = re.findall(r'href="(/location/[^"]+)"', html)
    if listing_links:
        print(f"  Location links: {listing_links[:10]}")
    
    # Look for price patterns
    prices = re.findall(r'(\d[\d ]*)\s*€', html[:50000])
    if prices:
        print(f"  Prices found: {prices[:20]}")
    
    # Look for listing references like LA-XXXX or reference patterns
    refs = re.findall(r'(?:ref|reference|LA|VA|LS)\s*[:#]\s*(\w+)', html, re.I)
    if refs:
        print(f"  References: {refs[:20]}")
    
    # Search for common netty data structure
    netty_data = re.findall(r'"annonces?"\s*:\s*\[(.*?)\]', html, re.DOTALL)
    if netty_data:
        print(f"  Netty annonces array: {len(netty_data)} matches")
        for d in netty_data[:1]:
            print(f"    {d[:500]}")

# Parse Le-Partenaire page 2
print("\n=== Le-Partenaire page 2 ===")
lp2_path = os.path.join(BASE_DIR, 'lp_page2.html')
if os.path.exists(lp2_path):
    with open(lp2_path, 'r', errors='replace') as f:
        html = f.read()
    
    h2_iter = [(m.start(), m.group(1)) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)]
    print(f"H2 headings: {len(h2_iter)}")
    
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
        
        all_links = re.finditer(r'href="(/immobilier/location/appartement/[^"]*?/(\d+))"', html[h2_pos:h2_pos+5000])
        listing_id = None
        listing_url = None
        for m in all_links:
            listing_id = m.group(2)
            listing_url = f"https://www.le-partenaire.fr{m.group(1)}"
            break
        
        if listing_id:
            print(f"  lp-{listing_id}: {price}€ | {surface}m² | {rooms}p | {title_text[:80]}")