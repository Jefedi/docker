import re, json, html

# Parse Citya - has JSON prices
s = open('/tmp/src_7d2dca6d.html').read()
print(f"=== Citya ({len(s)} bytes) ===")
# Citya has price in JSON: "price":772 etc.
# Find listing blocks with price, surface, title
# Citya URLs: /annonces/location/appartement/le-havre-76351/...
# Let's find all listing links
links = re.findall(r'href="(/annonces/location/appartement/[^"]+)"', s)
# Also look for detail links
detail_links = re.findall(r'href="(/annonce/[^"]+)"', s)
print(f"Links: {len(links)}, Detail: {len(detail_links)}")
for l in links[:10]: print(f"  {l}")
for l in detail_links[:10]: print(f"  D: {l}")

# Citya uses GES IDs - find all GES references
ges_ids = re.findall(r'GES\d+-\d+', s)
print(f"GES IDs: {len(ges_ids)} -> {ges_ids[:10]}")

# Find all prices with context
prices = re.findall(r'"price":\s*(\d+)', s)
print(f"JSON prices: {prices}")

# Let's look for the listing cards structure
# Citya typically has each listing in a div with data attributes
# Look for GES references in href
ges_links = re.findall(r'href="([^"]*GES\d+[^"]*)"', s)
print(f"GES links: {ges_links[:10]}")

# Find surface and pieces data
surfaces = re.findall(r'(\d+(?:\.\d+)?)\s*m²', s)
print(f"Surfaces: {surfaces[:20]}")

# Let's look at the HTML structure around a GES reference
idx = s.find('GES')
if idx >= 0:
    block = s[max(0, idx-500):idx+500]
    print(f"\nContext around GES:\n{block[:800]}")