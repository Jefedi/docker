import re, json
# Orpi has JSON-LD ItemList - let's extract it fully
for fname, label in [('/tmp/src_a559eead.html', 'Orpi p1'), ('/tmp/orpi2.html', 'Orpi p2')]:
    s = open(fname).read()
    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.DOTALL)
    for b in ld:
        try:
            data = json.loads(b)
            if 'itemListElement' in data:
                print(f"\n=== {label}: {len(data['itemListElement'])} items ===")
                for item in data['itemListElement']:
                    url = item.get('url', '')
                    print(url)
        except:
            pass

# Also look for listing card data - Orpi typically has the listing info in the HTML cards
# Let's search for the pattern around each price
print("\n=== Orpi p1 card data ===")
s = open('/tmp/src_a559eead.html').read()
# Find all prices with context
for m in re.finditer(r'"price":(\d+)', s):
    start = max(0, m.start()-200)
    end = min(len(s), m.end()+200)
    ctx = s[start:end]
    # Find URL nearby
    url_m = re.search(r'href="([^"]+)"', ctx)
    url = url_m.group(1) if url_m else ''
    print(f"Price: {m.group(1)} | URL: {url}")