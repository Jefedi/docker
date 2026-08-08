import re, html as htmlmod, json

content = open('/tmp/citya.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Get all listing links with IDs
link_pattern = re.findall(r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/(GES[\w-]+))"', content)
unique_links = list(dict.fromkeys(link_pattern))

# Parse text for listings - more precise pattern
# "Le Havre (766XX) Appartement N pièces XX.XXm² [features] XXX €"
listings_text = re.findall(r'(Le Havre \(766\d\d\))\s+Appartement\s+(\d)\s*pièces\s+(\d+(?:\.\d+)?)m²\s+([^€]*?)\s+(\d+)\s*€', text)

# Match links to text listings by order
# Citya lists are in order - links match text listings
print(f"Links: {len(unique_links)}")
print(f"Text listings: {len(listings_text)}")

# Pair them up
for i, ((full_url, ges_id), (city, pieces, surface, features, price)) in enumerate(zip(unique_links, listings_text)):
    p = int(pieces)
    s = float(surface)
    pr = int(price)
    
    if p >= 2 and s >= 28 and pr <= 500:
        citya_id = f"citya-{ges_id}"
        print(f"\n  NEW CANDIDATE: {citya_id}")
        print(f"  T{p} {s}m² {pr}€ | {city} | Features: {features.strip()}")
        print(f"  URL: {full_url}")

# Also check if there are more listings on page 2 and 3
print(f"\n\nAll T2+ <=500€ from Citya:")
for (full_url, ges_id), (city, pieces, surface, features, price) in zip(unique_links, listings_text):
    p = int(pieces)
    s = float(surface)
    pr = int(price)
    if p >= 2 and s >= 28 and pr <= 500:
        print(f"  citya-{ges_id} | T{p} {s}m² {pr}€ | {features.strip()}")