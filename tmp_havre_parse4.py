import re, base64, json

# ============= HEUZE - SPA with base64 data =============
print("=== HEUZE ===")
with open('/tmp/havre/heuze_loc.html') as f:
    html = f.read()

# Find base64 encoded data
b64_match = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', html)
if b64_match:
    b64_data = b64_match.group(1)
    try:
        decoded = base64.b64decode(b64_data).decode('utf-8')
        data = json.loads(decoded)
        # Look for listings
        if 'products' in data:
            products = data['products']
            print(f"  Products: {len(products)}")
            for p in products[:20]:
                print(f"    {p}")
        elif isinstance(data, dict):
            # Print keys
            print(f"  Keys: {list(data.keys())[:20]}")
            # Try to find listings
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0:
                    print(f"  {k}: {len(v)} items, first: {str(v[0])[:200]}")
    except Exception as e:
        print(f"  Decode error: {e}")
        print(f"  B64 length: {len(b64_data)}")
else:
    print("  No base64 data found")
    # Try other patterns
    data_match = re.search(r'window\.__SSR_TEMPLATE_DATA__\s*=\s*({.+?});', html, re.DOTALL)
    if data_match:
        print(f"  Found SSR data (JSON): {len(data_match.group(1))} chars")
    data_match2 = re.search(r'window\.__INITIAL_DATA__\s*=\s*(.+?);', html, re.DOTALL)
    if data_match2:
        print(f"  Found initial data: {len(data_match2.group(1))} chars")

# ============= SAINT ROCH - SPA with base64 data =============
print("\n=== SAINT ROCH ===")
with open('/tmp/havre/stroch_loc.html') as f:
    html = f.read()

b64_match = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', html)
if b64_match:
    b64_data = b64_match.group(1)
    try:
        decoded = base64.b64decode(b64_data).decode('utf-8')
        data = json.loads(decoded)
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:20]}")
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    print(f"  {k}: {len(v)} items")
                    if len(v) <= 20:
                        for item in v[:15]:
                            # Try to get listing info
                            if isinstance(item, dict):
                                title = item.get('title', item.get('name', ''))
                                price = item.get('price', item.get('loyer', ''))
                                surf = item.get('surface', item.get('area', ''))
                                rooms = item.get('rooms', item.get('pieces', item.get('nb_pieces', '')))
                                ref = item.get('reference', item.get('id', item.get('ref', '')))
                                if title or price:
                                    print(f"    ref={ref} | {title} | {price}EUR | {surf}m2 | {rooms}p")
    except Exception as e:
        print(f"  Decode error: {e}")
else:
    print("  No base64 data found")
    # Look for other data patterns
    for pattern in [r'window\.__SSR[A-Z_]*\s*=\s*(.+?);\s*<', r'window\.__INITIAL[A-Z_]*\s*=\s*(.+?);\s*<', r'"products":\s*(\[.+?\])', r'"listings":\s*(\[.+?\])']:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            print(f"  Found: {pattern[:40]}... len={len(m.group(1))}")
            break