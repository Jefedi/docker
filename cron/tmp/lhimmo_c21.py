import re, html, json

# LH Immo page 2 - look for T2 location listings
s = open('/tmp/lhimmo_p2.html').read()
h2s = list(re.finditer(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL))
print("=== LH Immo page 2 ===")
for m in h2s:
    t = html.unescape(re.sub('<[^>]+>','',m.group(1))).strip()
    if t and ('appartement' in t.lower() or 'T2' in t or 'T3' in t or 'T4' in t or 'studio' in t.lower()):
        pos = m.start()
        block = s[max(0,pos-500):pos+2000]
        link_m = re.search(r'href="([^"]*(?:annonce|bien)[^"]*)"', block, re.I)
        link = link_m.group(1) if link_m else 'NO LINK'
        price_m = re.search(r'(\d[\d\s]{2,5})\s*€', block)
        price = price_m.group(1).strip() if price_m else '?'
        surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
        surf = surf_m.group(1) if surf_m else '?'
        is_location = 'location' in block.lower() or 'louer' in block.lower() or 'loyer' in block.lower()
        print(f"  {t[:60]} | {price}€ | {surf}m² | loc={is_location} | {link}")

# Parse C21 - look for listing data
s = open('/tmp/c21_full.html').read()
print(f"\n=== Century 21 ({len(s)} bytes) ===")
# C21 has listing headings with surface info
h2s = list(re.finditer(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL))
for m in h2s:
    t = html.unescape(re.sub('<[^>]+>','',m.group(1))).strip()
    if t and ('m2' in t or 'm²' in t or 'pièce' in t.lower()):
        pos = m.start()
        block = s[max(0,pos-1000):pos+2000]
        price_m = re.search(r'(\d[\d\s]{2,5})\s*€', block)
        price = price_m.group(1).strip() if price_m else '?'
        # Find ref
        ref_m = re.search(r'Ref\s*:\s*(\d+)', block)
        ref = ref_m.group(1) if ref_m else ''
        # Find link
        link_m = re.search(r'href="(/annonces/[^"]+)"', block)
        link = link_m.group(1) if link_m else ''
        # Surface and pieces
        surf_m = re.search(r'([\d,.]+)\s*m2', t)
        pieces_m = re.search(r'(\d+)\s*pi[èc]', t)
        surf = surf_m.group(1) if surf_m else '?'
        pc = pieces_m.group(1) if pieces_m else '?'
        print(f"  {pc}p | {surf}m² | {price}€ | ref={ref} | {link} | {t[:60]}")