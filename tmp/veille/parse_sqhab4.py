import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/sqhab.html').read()
page = htmllib.unescape(raw)

# Look for listing card links - they might use a different pattern
# The page seems SPA. Let me look for data attributes or links with UUIDs
links = re.findall(r'href="([^"]*(?:le-havre|le\+havre)[^"]*)"', page, re.IGNORECASE)
print(f"Le Havre links: {len(links)}")
for l in set(links):
    print(f"  {l}")

# Look for "card" or "item" patterns with UUIDs
# Try finding anchors near image UUIDs
uuid_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

# Find all href containing UUIDs
uuid_links = re.findall(r'href="([^"]*?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[^"]*)"', raw)
print(f"\nUUID links: {len(uuid_links)}")
for l in uuid_links[:20]:
    print(f"  {l}")

# Also try to find surface info in the page
surfaces = re.findall(r'(\d+[,.]?\d*)\s*m²', page)
print(f"\nSurfaces found: {len(surfaces)}")
for s in surfaces[:20]:
    print(f"  {s}")