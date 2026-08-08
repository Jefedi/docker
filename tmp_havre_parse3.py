import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# ============= ORPI - FIXED =============
print("=== ORPI (fixed) ===")
with open('/tmp/havre/orpi.html') as f:
    html = f.read()

# Get all unique listing URLs (not contact=true)
full_urls = set()
for m in re.finditer(r'href="(/annonce-location-appartement-t[2-9][^"]*?)"', html, re.I):
    u = m.group(1)
    if '?contact=true' not in u:
        full_urls.add(u)

orpi_new = []
for u in sorted(full_urls):
    u_clean = u.rstrip('/')
    # Try UUID first
    id_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', u)
    if id_match:
        uid = id_match.group(1)
    else:
        id_match2 = re.search(r'(\d+-\d+-\d+)\s*$', u_clean)
        uid = id_match2.group(1) if id_match2 else u_clean.split('-')[-1]
    pid = f'orpi-{uid}'
    status = 'SEEN' if pid in seen else 'NEW'

    # Get price from JSON-LD nearby
    idx = html.find(u)
    context = html[max(0,idx-5000):idx+1000] if idx >= 0 else ''
    # Try multiple price patterns
    price_m = re.search(r'"price":(\d+)', context)
    if not price_m:
        price_m = re.search(r'(\d[\d\s]*)\s*€', context[-1500:])
    price = price_m.group(1).strip() if price_m else '?'

    # City from URL
    city_m = re.search(r'(le-havre|harfleur|montivilliers|brionne|sainte-adresse)', u, re.I)
    city = city_m.group(1) if city_m else '?'
    type_m = re.search(r'(t[2-9])', u, re.I)
    typ = type_m.group(1) if type_m else '?'

    if status == 'NEW' and city == 'le-havre':
        orpi_new.append((pid, u, price, city, typ))
        print(f"  NEW: {pid} | {typ} | {price}EUR | {city} | https://www.orpi.com{u}")
    elif status == 'NEW':
        print(f"  NEW (not Le Havre): {pid} | {typ} | {price}EUR | {city}")

print(f"\nOrpi NEW T2+ Le Havre: {len(orpi_new)}")

# ============= LH IMMO - FIXED =============
print("\n=== LH IMMO (fixed) ===")
with open('/tmp/havre/lhimmo_home.html') as f:
    html = f.read()

lh_urls = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]*)"', html)
lh_t2plus = [u for u in set(lh_urls) if re.search(r't[2-6]', u)]
lh_new = []
for u in sorted(lh_t2plus):
    slug = u.rstrip('/').split('/')[-1]
    pid = f'lhimmo-{slug}'
    status = 'SEEN' if pid in seen else 'NEW'
    if status == 'NEW':
        lh_new.append((pid, u))
        print(f"  NEW: {pid} | {u}")
    else:
        print(f"  SEEN: {pid}")
print(f"\nLH Immo NEW T2+: {len(lh_new)}")

# ============= CENTURY 21 =============
print("\n=== CENTURY 21 ===")
with open('/tmp/havre/c21.html') as f:
    html = f.read()
c21_urls = set(re.findall(r'href="(/annonces/location[^"]*)"', html))
c21_full = [u for u in c21_urls if 'appartement' in u]
print(f"  C21 apt URLs: {len(c21_full)}")
for u in sorted(c21_full)[:20]:
    print(f"    {u}")

# ============= PAP.fr - empty file =============
print("\n=== PAP.fr ===")
import os
if os.path.getsize('/tmp/havre/pap.html') == 0:
    print("  PAP file is empty (curl failed)")

# ============= FONCIA - empty file =============
print("\n=== FONCIA ===")
if os.path.getsize('/tmp/havre/foncia.html') == 0:
    print("  Foncia file is empty (curl failed)")

# ============= HEUZE - 26 lines =============
print("\n=== HEUZE ===")
with open('/tmp/havre/heuze_home.html') as f:
    html = f.read()
print(f"  {len(html)} chars")
heuze_links = re.findall(r'href="([^"]*location[^"]*)"', html, re.I)
print(f"  Location links: {heuze_links[:10]}")

# ============= SAINT ROCH - 26 lines =============
print("\n=== SAINT ROCH ===")
with open('/tmp/havre/stroch_home.html') as f:
    html = f.read()
print(f"  {len(html)} chars")
stroch_links = re.findall(r'href="([^"]*(?:location|annonce)[^"]*)"', html, re.I)
print(f"  Links: {stroch_links[:10]}")