import re, html

# LH Immo: the listing links are probably JavaScript-based. Let's look at the HTML structure more carefully
s = open('/tmp/lhimmo_ann.html').read()
# Find all href links
all_links = re.findall(r'href="([^"]+)"', s)
# Filter for annonce-related
annonce_links = [l for l in all_links if 'annonce' in l.lower() and not l.startswith('#') and 'lhimmo' not in l.lower()]
print(f"Annonce links: {annonce_links[:20]}")

# Find the listing cards - look for div/article with class containing 'bien' or 'annonce' or 'property'
# Let's look at the HTML around each heading
h2s = list(re.finditer(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL))
for m in h2s:
    t = html.unescape(re.sub('<[^>]+>','',m.group(1))).strip()
    if t and ('appartement' in t.lower() or 'maison' in t.lower() or 'colocation' in t.lower()):
        pos = m.start()
        block = s[max(0,pos-500):pos+2000]
        # Find link in block
        link_m = re.search(r'href="([^"]*(?:annonce|bien|property)[^"]*)"', block, re.I)
        link = link_m.group(1) if link_m else 'NO LINK'
        # Find price
        price_m = re.search(r'(\d[\d\s]{2,5})\s*€', block)
        price = price_m.group(1).strip() if price_m else '?'
        # Find surface
        surf_m = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
        surf = surf_m.group(1) if surf_m else '?'
        # Find "location" or "vente" context
        is_location = 'location' in block.lower() or 'louer' in block.lower() or 'loyer' in block.lower()
        # Find full description
        desc_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        desc = html.unescape(re.sub('<[^>]+>','',desc_m.group(1))).strip()[:200] if desc_m else ''
        print(f"\n  Title: {t}")
        print(f"  Price: {price}€ | Surface: {surf}m² | Location: {is_location}")
        print(f"  Link: {link}")
        print(f"  Desc: {desc[:150]}")