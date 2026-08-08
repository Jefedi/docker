import re, html, json

# Read seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# Parse all Le-Partenaire pages
all_listings = []
for p in range(1, 7):
    fname = f'/tmp/lp{p}.html' if p > 1 else '/tmp/lp1.html'
    with open(fname) as f:
        s = f.read()
    h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', s)]
    h2_positions.append(len(s))
    for i in range(len(h2_positions)-1):
        block = s[h2_positions[i]:h2_positions[i+1]]
        title_raw = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        title = html.unescape(re.sub('<[^>]+>','', title_raw.group(1))).strip() if title_raw else ''
        lnk = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', block)
        url = 'https://www.le-partenaire.fr' + lnk.group(1) if lnk else ''
        mid = ''
        if lnk:
            m = re.search(r'/(\d+)$', lnk.group(1))
            if m: mid = m.group(1)
        # price - find "XXX €" in block
        price = re.search(r'(\d[\d\s]*)\s*€', block)
        price_txt = price.group(1).replace(' ','').strip() if price else ''
        # surface
        surf = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', block)
        surf_txt = surf.group(1).replace(',','.') if surf else ''
        # pieces from URL
        pmatch = re.search(r'/(\d+)pieces/', lnk.group(1)) if lnk else None
        pieces_txt = pmatch.group(1) if pmatch else ''
        # date
        dt = re.search(r'(\d{2}/\d{2}/\d{4})', block)
        date_txt = dt.group(1) if dt else ''
        # description text
        desc = re.search(r'<p[^>]*class="[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        desc_txt = html.unescape(re.sub('<[^>]+>','', desc.group(1))).strip()[:500] if desc else ''
        all_listings.append({'id': mid, 'pieces': pieces_txt, 'surface': surf_txt, 'price': price_txt, 'url': url, 'date': date_txt, 'title': title, 'desc': desc_txt})

# Filter: T2+ (>=2 pieces), <=500 eur, >=28m2
cands = []
for l in all_listings:
    try: pr = int(l['price']) if l['price'] else 9999
    except: pr = 9999
    try: sf = float(l['surface']) if l['surface'] else 0
    except: sf = 0
    try: pc = int(l['pieces']) if l['pieces'] else 0
    except: pc = 0
    if pc >= 2 and pr <= 500 and sf >= 28:
        cands.append(l)

# Dedupe
unique = {}
for c in cands:
    unique[c['id']] = c
cands = list(unique.values())

print(f"Total LP listings: {len(all_listings)}, candidates: {len(cands)}")
for l in cands:
    seen_id = f"lp-{l['id']}"
    is_new = seen_id not in seen
    l['is_new'] = is_new
    print(json.dumps(l, ensure_ascii=False))