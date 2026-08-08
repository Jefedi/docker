import re, html, json

# Parse Orpi - has JSON data embedded
print("=== ORPI page 1 ===")
s = open('/tmp/src_a559eead.html').read()
# Orpi embeds listing data in JSON. Look for patterns with price, surface, pieces
# Try to find listing objects
# Look for data-price or JSON blocks
listings_raw = re.findall(r'\{[^{}]*"price"\s*:\s*\d+[^{}]*\}', s)
print(f"JSON listing objects: {len(listings_raw)}")
for l in listings_raw[:5]:
    print(l[:300])
    print()

# Also try to find individual listing URLs with IDs
orpi_urls = re.findall(r'href="(/location-immobiliere-le-havre/louer-appartement/[^"]+)"', s)
print(f"Listing URLs: {orpi_urls[:20]}")

# Let's look for the __NEXT_DATA__ json
nxt = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', s, re.DOTALL)
if nxt:
    print(f"\n__NEXT_DATA__ found: {len(nxt.group(1))} chars")
    try:
        data = json.loads(nxt.group(1))
        print(json.dumps(data, indent=2)[:2000])
    except:
        print(nxt.group(1)[:1000])