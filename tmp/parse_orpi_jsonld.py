#!/usr/bin/env python3
"""Parse Orpi page 2 using JSON-LD structured data."""
import re, html as h, json

raw = open('/tmp/scrape/orpi2.html','r',errors='replace').read()

# Find JSON-LD data blocks
json_ld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S)
print(f"JSON-LD blocks: {len(json_ld_blocks)}")

for i, block in enumerate(json_ld_blocks):
    try:
        data = json.loads(block.strip())
        if isinstance(data, dict) and '@type' in data:
            if data['@type'] == 'ItemList':
                items = data.get('itemListElement', [])
                print(f"\nItemList with {len(items)} items:")
                for item in items:
                    listing = item.get('item', item)
                    name = listing.get('name', 'N/A')
                    url = listing.get('url', 'N/A')
                    offers = listing.get('offers', {})
                    price = offers.get('price', 'N/A')
                    print(f"  {name} | {price}euro | {url}")
            elif 'name' in data and 'offers' in data:
                name = data.get('name', 'N/A')
                price = data.get('offers', {}).get('price', 'N/A')
                url = data.get('url', 'N/A')
                print(f"  {name} | {price}euro | {url}")
    except json.JSONDecodeError:
        pass

# Also look for the structured data in the raw HTML (not JSON-LD)
# Orpi may use data-product or similar attributes
product_data = re.findall(r'data-(?:product|listing|bien)="([^"]+)"', raw)
print(f"\nProduct data attrs: {len(product_data)}")

# Find all JSON objects in script tags that might contain listing data
script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.S)
for block in script_blocks:
    if 'price' in block.lower() and 'location' in block.lower():
        # Try to find price+surface+pieces patterns
        prices = re.findall(r'"price"\s*:\s*"?(\d+)"?', block)
        surfaces = re.findall(r'"surface[^"]*"\s*:\s*"?(\d[\d,\.]*)"?', block, re.I)
        pieces = re.findall(r'"nbPieces"\s*:\s*"?(\d+)"?', block)
        if prices:
            print(f"\n  Script block with prices: {prices[:20]}")
            if surfaces:
                print(f"  Surfaces: {surfaces[:20]}")
            if pieces:
                print(f"  Pieces: {pieces[:20]}")