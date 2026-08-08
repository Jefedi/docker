import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

content = open('/tmp/c21.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find listing blocks: "LE HAVRE 76 XX,XX m 2, N pièces Ref : XXXX Appartement FX ... XXX € par mois"
listings = re.findall(
    r'LE HAVRE 76\s+(\d+(?:,\d+)?)\s*m\s*2\s*,\s*(\d)\s*pièces?\s+Ref\s*:\s*(\w+)\s+(.*?)(?=\d{3,4}\s*€\s*par\s*mois)',
    text
)

# Find prices near these listings
price_listings = re.findall(
    r'LE HAVRE 76\s+(\d+(?:,\d+)?)\s*m\s*2\s*,\s*(\d)\s*pièces?\s+Ref\s*:\s*(\w+)\s+(.*?)\s+(\d{3,4})\s*€\s*par\s*mois',
    text
)

print(f"Price listings: {len(price_listings)}")

# Also find links with Ref
ref_links = re.findall(r'href="(https://www\.century21\.fr/annonces/location/[^"]+)"', content)
unique_links = list(dict.fromkeys(ref_links))
print(f"Links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

# Find all listings with price
for surface, pieces, ref, desc, price in price_listings:
    p = int(pieces)
    s = float(surface.replace(',', '.'))
    pr = int(price)
    c21_id = f"c21-{ref}"
    is_new = c21_id not in seen_ids
    
    if p >= 2 and s >= 28 and pr <= 500:
        status = "NEW" if is_new else "SEEN"
        print(f"\n  [{status}] {c21_id} | T{p} {s}m² {pr}€/mois")
        print(f"  Desc: {desc[:200]}")