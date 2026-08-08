import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# ============= ORPI =============
print("=== ORPI ===")
with open('/tmp/havre/orpi.html') as f:
    html = f.read()

# Get all listing links - T2+
full_urls = re.findall(r'href="(/annonce-location-appartement-t[2-9][^"]*?)"', html, re.I)
orpi_new = []
for u in set(full_urls):
    if '?contact=true' in u:
        continue
    id_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', u)
    if id_match:
        uid = id_match.group(1)
    else:
        id_match2 = re.search(r'(\d+-\d+-\d+)$', u)
        uid = id_match2.group(1) if id_match2 else u
    pid = f'orpi-{uid}'
    status = 'SEEN' if pid in seen else 'NEW'
    # Need to get price - look in surrounding context
    idx = html.find(u)
    context = html[max(0,idx-3000):idx+500] if idx >= 0 else ''
    price_m = re.search(r'"price":(\d+)', context)
    if not price_m:
        price_m = re.search(r'(\d+)\s*(?:€|EUR|euros)', context)
    price = price_m.group(1) if price_m else '?'
    # Get city from URL
    city_m = re.search(r'(le-havre|harfleur|montivilliers|brionne)', u, re.I)
    city = city_m.group(1) if city_m else '?'
    type_m = re.search(r'(t[2-9])', u, re.I)
    typ = type_m.group(1) if type_m else '?'
    if status == 'NEW':
        orpi_new.append((pid, u, price, city, typ))
        print(f"  NEW: {pid} | {typ} | {price}EUR | {city} | {u}")
    else:
        pass  # seen

print(f"\nOrpi NEW T2+: {len(orpi_new)}")

# ============= SQUARE HABITAT =============
print("\n=== SQUARE HABITAT ===")
with open('/tmp/havre/sqhab.html') as f:
    html = f.read()

sqhab_urls = re.findall(r'href="(/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/[0-9a-f-]+)"', html)
sqhab_new = []
for u in set(sqhab_urls):
    uid = u.split('/')[-1]
    pid = f'sqhab-{uid}'
    status = 'SEEN' if pid in seen else 'NEW'
    if status == 'NEW':
        sqhab_new.append((pid, u))
        print(f"  NEW: {pid} | {u}")
print(f"\nSqHab NEW: {len(sqhab_new)}")

# ============= JULLIEN & ALLIX =============
print("\n=== JULLIEN & ALLIX ===")
with open('/tmp/havre/ja.html') as f:
    html = f.read()

ja_urls = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/a-louer-appartement[^"]*?)"', html)
ja_f2plus = [u for u in set(ja_urls) if 'f2' in u or 'f3' in u or 'f4' in u or 'f5' in u or 'f6' in u]
ja_new = []
for u in ja_f2plus:
    # Generate ID from URL slug
    slug = u.split('/')[-1].replace('.html', '')
    pid = f'ja-{slug}'
    status = 'SEEN' if pid in seen else 'NEW'
    if status == 'NEW':
        ja_new.append((pid, u))
        print(f"  NEW: {pid} | {u}")
print(f"\nJA NEW T2+: {len(ja_new)}")

# ============= LH IMMO =============
print("\n=== LH IMMO ===")
with open('/tmp/havre/lhimmo_home.html') as f:
    html = f.read()

lh_urls = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]*)"', html)
lh_t2plus = [u for u in set(lh_urls) if 't2' in u or 't3' in u or 't4' in u or 't5' in u or 't6' in u]
lh_new = []
for u in lh_t2plus:
    slug = u.split('/')[-1].rstrip('/')
    pid = f'lhimmo-{slug}'
    status = 'SEEN' if pid in seen else 'NEW'
    if status == 'NEW':
        lh_new.append((pid, u))
        print(f"  NEW: {pid} | {u}")
print(f"\nLH Immo NEW T2+: {len(lh_new)}")

# ============= CENTURY 21 =============
print("\n=== CENTURY 21 ===")
with open('/tmp/havre/c21.html') as f:
    html = f.read()
c21_urls = re.findall(r'href="(/annonces/location[^"]*)"', html)
c21_full = [u for u in c21_urls if 'appartement' in u and 'le+havre' in u]
print(f"  C21 apt URLs: {len(c21_full)}")
for u in list(set(c21_full))[:10]:
    print(f"    {u}")

# ============= CITYA page 2/3 already checked =============
print("\n=== SUMMARY ===")
all_new = orpi_new + sqhab_new + ja_new + lh_new
print(f"Total NEW T2+ across all sources: {len(all_new)}")
for item in all_new:
    print(f"  {item}")