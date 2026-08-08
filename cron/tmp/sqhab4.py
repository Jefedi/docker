import re, json, html

# SquareHabitat: the surface data is in a different part of the HTML. Let's look at the JSON-LD blocks properly
s = open('/tmp/src_a8dd5e22.html').read()
# Find all JSON-LD blocks
ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")
for i, b in enumerate(ld_blocks):
    try:
        data = json.loads(b)
        print(f"\nBlock {i}: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"\nBlock {i} (raw): {b[:300]}")

# Also look for data in data attributes on the card elements
# Find the property card containers
# Look for the div that contains both the UUID and the price
# The JSON-LD prices are in order: 600, 629, 322, 670, 475, 870, 730, 393, 395, 725, 770, 300, 480, 530, 520, 575, 395, 350
# Let's find the full JSON-LD with surface info
for b in ld_blocks:
    try:
        data = json.loads(b)
        if isinstance(data, list):
            for item in data:
                if 'surface' in str(item).lower() or 'floorArea' in str(item).lower():
                    print(f"\nFound surface data: {json.dumps(item)[:500]}")
        elif isinstance(data, dict):
            s_str = json.dumps(data)
            if 'surface' in s_str.lower() or 'floorArea' in s_str.lower():
                print(f"\nFound surface data: {s_str[:500]}")
    except:
        pass

# Let's also look for individual listing links - /annonces/location/bien/appartement/...
links = re.findall(r'href="(/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600/[^"]+)"', s)
print(f"\nLe Havre listing links: {len(links)}")
for l in links: print(f"  {l}")