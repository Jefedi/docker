import re, html as htmllib, json

# Parse Citya
raw = open('/opt/data/tmp/veille/citya.html').read()
page = htmllib.unescape(raw)

# Citya uses data attributes and links to /annonces/location/...
# Find listing blocks
links = re.findall(r'href="(/annonces/location/[^"]+)"', page)
print(f"Citya links: {len(links)}")
for l in links[:20]:
    print(f"  {l}")

# Also look for price/pieces patterns
# Citya typically has cards with title, price, surface
titles = re.findall(r'class="[^"]*title[^"]*"[^>]*>(.*?)</(?:a|div|span|p|h)', page, re.DOTALL)
print(f"\nCitya titles: {len(titles)}")
for t in titles[:10]:
    print(f"  {re.sub(r'<[^>]+>', '', t).strip()[:80]}")

# Look for JSON data
json_m = re.search(r'window\.__NUXT__\s*=\s*(.+?);?\s*</script>', page, re.DOTALL)
print(f"\nNUXT data: {'YES' if json_m else 'NO'}")

# Try to find listing data in any JSON blob
jsons = re.findall(r'\{[^{}]*"price"[^{}]*\}', page)
print(f"JSON with price: {len(jsons)}")
for j in jsons[:5]:
    print(f"  {j[:200]}")