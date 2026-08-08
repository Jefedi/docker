import re, html as htmllib, json

# Parse Orpi - get URLs from HTML
raw = open('/opt/data/tmp/veille/orpi.html').read()
page = htmllib.unescape(raw)

# Find listing links
links = re.findall(r'href="([^"]*location-immobiliere-le-havre[^"]*)"', page)
print(f"Orpi Le Havre links: {len(links)}")
for l in list(set(links))[:20]:
    print(f"  {l}")

# Also try generic listing links
links2 = re.findall(r'href="(/louer[^"]*|/location[^"]*|/bien[^"]*)"', page)
print(f"\nGeneric listing links: {len(links2)}")
for l in list(set(links2))[:20]:
    print(f"  {l}")

# Orpi uses Sweepbright platform. The listing URLs might be different.
# Try finding anchor elements with listing-related hrefs
links3 = re.findall(r'href="([^"]*(?:appartement|bien|annonce)[^"]*)"', page, re.IGNORECASE)
print(f"\nAll apartment/bien/annonce links: {len(links3)}")
for l in list(set(links3))[:30]:
    if 'le-havre' in l.lower() or 'havre' in l.lower() or 'bien' in l.lower():
        print(f"  {l}")

# Get all hrefs
all_hrefs = re.findall(r'href="([^"]+)"', raw)
print(f"\nTotal hrefs: {len(all_hrefs)}")
# Filter for potential listing pages
for h in all_hrefs:
    if re.search(r'/[0-9a-f]{8}-[0-9a-f]{4}', h) or 'location' in h.lower():
        if 'css' not in h and 'js' not in h and 'img' not in h:
            print(f"  {h}")