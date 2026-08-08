import re, html as htmlmod, json

content = open('/tmp/citya.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find listing IDs and details
# Pattern: "Le Havre (XXXXX) Appartement N pièces XXm² [features] XXX €"
# Also find links
listings_raw = re.findall(r'(Le Havre \(766\d\d\))\s+Appartement\s+(\d)\s*pièces\s+(\d+(?:\.\d+)?)m²\s+([^€]*?)\s+(\d+)\s*€', text)

# Also find the links from the HTML
# Citya links pattern: /annonces/location/appartement/le-havre-76351/ID
link_pattern = re.findall(r'href="(/annonces/location/appartement/le-havre-76351/[^"]+)"', content)
unique_links = list(dict.fromkeys(link_pattern))

print(f"Listings from text: {len(listings_raw)}")
print(f"Links: {len(unique_links)}")
for l in unique_links[:30]:
    print(f"  {l}")

# Filter T2+ with surface >= 28 and price <= 500
candidates = []
for (city, pieces, surface, features, price) in listings_raw:
    p = int(pieces)
    s = float(surface)
    pr = int(price)
    if p >= 2 and s >= 28 and pr <= 500:
        candidates.append({
            'city': city,
            'pieces': p,
            'surface': s,
            'features': features.strip(),
            'price': pr
        })

print(f"\nCandidates (T2+, >=28m², <=500€): {len(candidates)}")
for c in candidates:
    print(f"  T{c['pieces']} {c['surface']}m² {c['price']}€ | {c['city']} | Features: {c['features']}")