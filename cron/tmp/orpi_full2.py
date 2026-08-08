import re, json, html

# Orpi pages - let's look at the raw HTML around the JSON-LD URLs
s = open('/tmp/src_a559eead.html').read()
# Find the JSON-LD block and extract full data
ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.DOTALL)
if ld:
    data = json.loads(ld.group(1))
    if 'itemListElement' in data:
        for item in data['itemListElement']:
            url = item.get('url', '')
            # Now find this URL in the HTML and get surrounding context
            idx = s.find(url)
            if idx >= 0:
                # Get a larger block around the URL
                block = s[max(0, idx-2000):idx+2000]
                # Look for price, surface, pieces in the block
                price_m = re.search(r'(\d{3,4})\s*€', block)
                surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
                # Look for h2/h3 heading
                title_m = re.search(r'<h[23456][^>]*>(.*?)</h[23456]>', block, re.DOTALL)
                title = html.unescape(re.sub('<[^>]+>','', title_m.group(1))).strip() if title_m else ''
                price = price_m.group(1) if price_m else ''
                surface = surf_m.group(1).replace(',','.') if surf_m else ''
                # Type from URL
                type_m = re.search(r'appartement-(t\d)-', url)
                prop_type = type_m.group(1) if type_m else ''
                # ID from URL
                id_m = re.search(r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
                if not id_m:
                    id_m = re.search(r'-(\d+-\d+)', url)
                listing_id = id_m.group(1) if id_m else ''
                print(f"{prop_type} | {price}€ | {surface}m² | id={listing_id}")
                print(f"  {url}")
                if title: print(f"  Title: {title[:100]}")
                print()
    else:
        print("No itemListElement")
else:
    print("No JSON-LD found")