#!/usr/bin/env python3
"""Parse JSON-LD from Citya and Orpi."""
import re, json

# --- Citya ---
print("=== CITYA ===")
with open('/tmp/citya_havre.html', 'r', errors='replace') as f:
    html = f.read()

ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_blocks:
    try:
        data = json.loads(ld_blocks[0])
        offers = data.get('offers', [])
        print(f"Offers: {len(offers)}")
        for o in offers:
            price = o.get('price', '?')
            url = o.get('url', '')
            # Extract ID from URL
            ref_match = re.search(r'GES(\d+-\d+)', url)
            ref = ref_match.group(1) if ref_match else ''
            
            # Get item fields
            item = o.get('itemOffered', {})
            name = item.get('name', '') if isinstance(item, dict) else ''
            surface = item.get('floorSize', {}).get('value', '?') if isinstance(item, dict) else '?'
            rooms = item.get('numberOfRooms', '?') if isinstance(item, dict) else '?'
            
            print(f"  {price}€ | {rooms}p | {surface}m² | {name[:60]} | ref={ref}")
            print(f"    URL: {url}")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Try to find offers manually
        offers = re.findall(r'"price"\s*:\s*"?(\d+)"?\s*,\s*"url"\s*:\s*"([^"]+)"', ld_blocks[0])
        print(f"Manual offers: {len(offers)}")
        for price, url in offers[:25]:
            ref_match = re.search(r'GES(\d+-\d+)', url)
            ref = ref_match.group(1) if ref_match else ''
            print(f"  {price}€ | ref={ref} | {url}")

# --- Orpi ---
print("\n=== ORPI ===")
with open('/tmp/orpi_havre.html', 'r', errors='replace') as f:
    html = f.read()

ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if ld_blocks:
    try:
        data = json.loads(ld_blocks[0])
        items = data.get('itemListElement', [])
        print(f"Items: {len(items)}")
        for item in items:
            url = item.get('url', '')
            name = item.get('name', '')
            print(f"  {name[:60]} | {url}")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Try to extract URLs from the JSON
        urls = re.findall(r'"url"\s*:\s*"([^"]+annonce-location[^"]*)"', ld_blocks[0])
        print(f"URLs found: {len(urls)}")
        for u in urls[:20]:
            print(f"  {u}")