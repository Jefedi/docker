import re, json, html

# Parse LH Immo annonces page - look for location listings
s = open('/tmp/lhimmo_ann.html').read()
print(f"=== LH Immo ({len(s)} bytes) ===")
# Find listing links
links = re.findall(r'href="(/annonce/[^"]+)"', s)
print(f"Links: {len(links)}")
for l in set(links): print(f"  {l}")

# Find listing blocks with headings
h2s = re.findall(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL)
for h in h2s:
    t = html.unescape(re.sub('<[^>]+>','',h)).strip()
    if t and ('appartement' in t.lower() or 'maison' in t.lower() or 'T2' in t or 'T3' in t or 'T4' in t or 'colocation' in t.lower()):
        print(f"  H: {t[:120]}")

# Find prices
prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
print(f"\nPrices: {prices[:20]}")

# Now parse actual listing data - look for each listing link and its context
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

print("\n=== LH Immo candidates ===")
for link in set(links):
    idx = s.find(link)
    if idx < 0: continue
    block = s[max(0,idx-1000):idx+1000]
    h_m = re.search(r'<h[23456][^>]*>(.*?)</h[23456]>', block, re.DOTALL)
    title = html.unescape(re.sub('<[^>]+>','',h_m.group(1))).strip() if h_m else ''
    price_m = re.search(r'(\d{3,4})\s*€', block)
    price = int(price_m.group(1)) if price_m else 0
    # Check if it's location (not vente)
    # ID from URL
    id_m = re.search(r'/annonce/([^/]+)/?', link)
    lid = id_m.group(1) if id_m else link
    seen_id = f"lhimmo-{lid}"
    status = "NEW" if seen_id not in seen else "SEEN"
    # Filter T2+ from title
    tmatch = re.search(r'T(\d)', title)
    tnum = int(tmatch.group(1)) if tmatch else 0
    if 'maison' in title.lower() and 'jardin' in title.lower():
        continue  # Skip houses
    if tnum >= 2 and price <= 500 and price > 100:
        print(f"  {status}: {seen_id} | T{tnum} | {price}€ | {title[:60]}")
    elif price <= 500 and price > 100 and ('T2' in title or 'T3' in title or 'T4' in title):
        print(f"  {status}: {seen_id} | {price}€ | {title[:60]}")