import re, html, json

# Check C21 more thoroughly - look for all listing data
s = open('/tmp/c21_full.html').read()
# Look for all refs and surfaces
refs = re.findall(r'Ref\s*:\s*(\d+)', s)
surfaces = re.findall(r'([\d,.]+)\s*m2', s)
pieces = re.findall(r'(\d+)\s*pi[èc]', s)
print(f"Refs: {refs}")
print(f"Surfaces: {surfaces}")
print(f"Pieces: {pieces}")

# Find all listing blocks
# Look for the pattern: surface + pieces + ref
blocks = re.findall(r'([\d,.]+)\s*m2,\s*(\d+)\s*pi[èc]\w*\s*(?:Ref\s*:\s*(\d+))?', s)
print(f"\nListing blocks: {len(blocks)}")
for surf, pc, ref in blocks:
    print(f"  {pc}p | {surf}m² | ref={ref}")

# Also look for price data
prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
print(f"\nAll prices: {prices[:20]}")

# Look for links to individual listings
links = re.findall(r'href="(/annonces/location[^"]*)"', s)
print(f"\nLinks: {links[:10]}")

# Look for JSON-LD
ld = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.DOTALL)
for b in ld:
    try:
        data = json.loads(b)
        print(f"\nJSON-LD: {json.dumps(data)[:300]}")
    except:
        pass

# Now let's also try HEUZE and Saint Roch with different approach
# Look for API endpoints or data scripts
for name, fname in [('heuze', '/tmp/heuze_loc.html'), ('stroch', '/tmp/stroch_loc.html')]:
    s = open(fname).read()
    # Look for script tags with listing data
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
    for sc in scripts:
        if ('price' in sc.lower() or 'loyer' in sc.lower() or 'bien' in sc.lower()) and len(sc) > 200:
            print(f"\n{name} script ({len(sc)} chars): {sc[:200]}")