import re, json, sys

files = {
    'orpi': '/tmp/havre/orpi.html',
    'c21': '/tmp/havre/c21.html',
    'sqhab': '/tmp/havre/sqhab.html',
    'lhimmo': '/tmp/havre/lhimmo_home.html',
    'ja': '/tmp/havre/ja.html',
}

for label, fn in files.items():
    try:
        with open(fn) as f:
            html = f.read()
    except:
        print(f"=== {label}: FILE NOT FOUND ===")
        continue
    
    print(f"\n=== {label} ({len(html)} chars) ===")
    
    # Extract JSON-LD offers
    m = re.search(r'"offers":\[(.+?)\]\}\s*\n', html, re.DOTALL)
    if not m:
        m = re.search(r'"offers":\[(.+?)\]\}', html, re.DOTALL)
    if m:
        try:
            offers_str = m.group(1).replace('\\/', '/').replace('\\u00b2', '\u00b2').replace('\\u00e8', '\u00e8').replace('\\u00e9', '\u00e9')
            offers = json.loads('[' + offers_str + ']')
            print(f"  JSON-LD offers: {len(offers)}")
            for o in offers:
                price = o.get('price', 0)
                url = o.get('url', '')
                item = o.get('itemOffered', {})
                name = item.get('name', '')
                addr = item.get('address', {})
                cp = addr.get('postalCode', '')
                pieces_m = re.search(r'(\d+)\s*pi[èe]ces?', name)
                surf_m = re.search(r'([\d.]+)\s*m', name)
                pieces = int(pieces_m.group(1)) if pieces_m else 0
                surface = float(surf_m.group(1)) if surf_m else 0
                if pieces >= 2 and price <= 500 and surface >= 28:
                    print(f"  PASS: {url} | {pieces}p | {surface}m2 | {price}EUR | {cp}")
                elif pieces >= 2:
                    print(f"  skip(price): {url} | {pieces}p | {surface}m2 | {price}EUR | {cp}")
        except Exception as e:
            print(f"  JSON parse error: {e}")
    else:
        print("  No JSON-LD offers found")
    
    # Extract annonce URLs with T2+
    t2plus = re.findall(r'href="([^"]*(?:t2|t3|t4|t5|t6|f2|f3|f4|2-pieces|3-pieces|4-pieces)[^"]*)"', html, re.I)
    if t2plus:
        print(f"  T2+ URLs found: {len(t2plus)}")
        for u in sorted(set(t2plus))[:20]:
            print(f"    {u}")