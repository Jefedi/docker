import re, json, html

# SquareHabitat: look at the actual listing card structure more carefully
s = open('/tmp/src_a8dd5e22.html').read()
# Find the 18th listing (index 17, 2 pièces, 395€) - the last one with surface data in our initial scan
# Look for "395" in the page
positions = [m.start() for m in re.finditer(r'395', s)]
for pos in positions:
    block = s[max(0,pos-500):pos+500]
    if 'pièce' in block or 'm²' in block:
        print(f"=== Context at {pos} ===")
        # Clean up for display
        clean = re.sub(r'<[^>]+>', ' ', block)
        clean = html.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(clean[:300])
        print()