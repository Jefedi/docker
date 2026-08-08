import re, json, html

# Try to find __NEXT_DATA__ or similar data structure in Orpi
s = open('/tmp/src_a559eead.html').read()

# Look for window.__NEXT_DATA__ or __INITIAL_STATE__
for pattern in [r'__NEXT_DATA__\s*=\s*({.*?})\s*;', r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;', r'data-props="([^"]*)"']:
    m = re.search(pattern, s, re.DOTALL)
    if m:
        print(f"Found {pattern[:30]}: {len(m.group(1))} chars")
        print(m.group(1)[:500])
        break

# Orpi likely uses a data attribute or inline script
# Look for script tags with listing data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
for i, sc in enumerate(scripts):
    if 'price' in sc and 'surface' in sc:
        print(f"\nScript {i} has price+surface ({len(sc)} chars):")
        print(sc[:500])
    if 'listing' in sc.lower() and 'price' in sc.lower():
        print(f"\nScript {i} has listing+price ({len(sc)} chars):")
        print(sc[:500])

# Try to find the Orpi data in data attributes on cards
# Orpi cards typically have data attributes
cards = re.findall(r'<div[^>]*class="[^"]*card[^"]*"[^>]*>(.*?)</div>', s, re.DOTALL)
print(f"\nCard divs: {len(cards)}")

# Let's look at the raw HTML around the first listing URL
url = "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-b3dd06ab-75f3-4b58-97d3-48e8bab59d48/"
idx = s.find(url)
if idx >= 0:
    print(f"\n=== Context around first T2 listing (idx {idx}) ===")
    block = s[max(0, idx-1000):idx+1000]
    print(block)