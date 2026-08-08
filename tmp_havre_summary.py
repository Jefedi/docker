import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

# ============= ORPI page 2 - check new refs =============
print("=== ORPI Page 2 ===")
with open('/tmp/havre/orpi2.html') as f:
    html = f.read()

refs = set(re.findall(r'data-reference="([^"]+)"', html))
print(f"  Unique refs: {len(refs)}")

# Get all listing URLs with types
urls = re.findall(r'href="(/annonce-location-appartement-(t[2-9])[^"]*?)"', html, re.I)
le_havre_t2plus = []
for u, typ in set(urls):
    if '?contact=true' in u:
        continue
    if 'le-havre' in u:
        id_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', u)
        if id_match:
            uid = id_match.group(1)
        else:
            id_match2 = re.search(r'(\d+-\d+-\d+)\s*$', u.rstrip('/'))
            uid = id_match2.group(1) if id_match2 else u.rstrip('/').split('-')[-1]
        pid = f'orpi-{uid}'
        status = 'SEEN' if pid in seen else 'NEW'
        if status == 'NEW':
            le_havre_t2plus.append((pid, u, typ))
            print(f"  NEW: {pid} | {typ} | https://www.orpi.com{u}")

print(f"\nOrpi p2 NEW Le Havre T2+: {len(le_havre_t2plus)}")

# ============= LH IMMO - check the T3 Brionne listing =============
print("\n=== LH IMMO T3 Brionne ===")
# Brionne is NOT Le Havre - it's a different city (27410 Brionne in Eure dept)
# So this doesn't match our criteria
print("  Brionne is in Eure (27), NOT Le Havre - EXCLUDED")

# ============= Summary of all new candidates =============
print("\n=== ALL NEW CANDIDATES ===")
# Orpi: fe039240 (T3 Le Havre, 750€ from meta) - price too high
# Orpi: 77fa0976 (T2 Montivilliers, 657€ from meta) - not Le Havre + price too high
# C21: 15772891843 (F2 Le Havre, 474€, 26.89m²) - surface too small, coin cuisine not separated
# LH Immo T3 Brionne - wrong city

print("Candidates found:")
print("1. orpi-fe039240 - T3 Le Havre 750EUR - PRICE > 500EUR (EXCLUDED)")
print("2. orpi-77fa0976 - T2 Montivilliers 657EUR - NOT Le Havre + PRICE > 500EUR (EXCLUDED)")
print("3. c21-7371 - F2 Le Havre 474EUR 26.89m2 - SURFACE < 28m2 + coin cuisine (EXCLUDED)")
print("4. lhimmo-T3-Brionne - NOT Le Havre (EXCLUDED)")
print("\nNo NEW listings match ALL criteria.")