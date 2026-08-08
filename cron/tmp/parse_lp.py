import re, html, json

with open('/tmp/lp1.html') as f:
    s = f.read()

# Extract listing blocks by splitting on h2
h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', s)]
h2_positions.append(len(s))

listings = []
for i in range(len(h2_positions)-1):
    block = s[h2_positions[i]:h2_positions[i+1]]
    title_raw = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
    title = html.unescape(re.sub('<[^>]+>','', title_raw.group(1))).strip() if title_raw else ''
    lnk = re.search(r'href="(/immobilier/location/appartement/[^"]+)"', block)
    url = 'https://www.le-partenaire.fr' + lnk.group(1) if lnk else ''
    # ID from URL
    mid = ''
    if lnk:
        m = re.search(r'/(\d+)$', lnk.group(1))
        if m: mid = m.group(1)
    # price
    price = re.search(r'(\d[\d\s]*)\s*€', block)
    price_txt = price.group(1).replace(' ','').strip() if price else ''
    # surface
    surf = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
    surf_txt = surf.group(1).replace(',','.') if surf else ''
    # pieces from title
    p = re.search(r'(\d+)\s*p\b', title)
    pieces_txt = p.group(1) if p else ''
    # date
    dt = re.search(r'(\d{2}/\d{2}/\d{4})', block)
    date_txt = dt.group(1) if dt else ''
    # description snippet
    desc = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
    desc_txt = html.unescape(re.sub('<[^>]+>','', desc.group(1))).strip()[:300] if desc else ''
    listings.append({'id': mid, 'pieces': pieces_txt, 'surface': surf_txt, 'price': price_txt, 'url': url, 'date': date_txt, 'title': title, 'desc_preview': desc_txt})

print(f"Total LP listings: {len(listings)}")
# Filter: T2+ (>=2 pieces), <=500 eur, >=28m2
cands = []
for l in listings:
    try:
        pr = int(l['price']) if l['price'] else 0
    except:
        pr = 0
    try:
        sf = float(l['surface']) if l['surface'] else 0
    except:
        sf = 0
    try:
        pc = int(l['pieces']) if l['pieces'] else 0
    except:
        pc = 0
    if pc >= 2 and pr <= 500 and sf >= 28:
        cands.append(l)
print(f"Candidates: {len(cands)}")
for l in cands:
    print(json.dumps(l, ensure_ascii=False))