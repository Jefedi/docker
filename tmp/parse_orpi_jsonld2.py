#!/usr/bin/env python3
"""Parse Orpi page 2 JSON-LD with full item details."""
import re, html as h, json

raw = open('/tmp/scrape/orpi2.html','r',errors='replace').read()

# Find JSON-LD data blocks
json_ld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S)

for block in json_ld_blocks:
    try:
        data = json.loads(block.strip())
        if isinstance(data, dict) and data.get('@type') == 'ItemList':
            items = data.get('itemListElement', [])
            print(f"ItemList with {len(items)} items:")
            for i, item in enumerate(items):
                listing = item.get('item', item)
                name = listing.get('name', 'N/A')
                url = listing.get('url', 'N/A')
                offers = listing.get('offers', {})
                price = offers.get('price', 'N/A')
                # Also get image which might have UUID
                image = listing.get('image', '')
                # Get description if available
                desc = listing.get('description', '')
                
                # Extract UUID from URL or image
                uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url + str(image))
                uuid = uuid_match.group(1) if uuid_match else 'N/A'
                
                print(f"  [{i}] {price}euro | UUID: {uuid} | URL: {url}")
                if desc:
                    print(f"    Desc: {desc[:200]}")
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")