import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

all_new = []

for fname, label in [('/tmp/citya.html', 'p1'), ('/tmp/citya_p2.html', 'p2'), ('/tmp/citya_p3.html', 'p3')]:
    content = open(fname).read()
    text = re.sub(r'<[^>]+>', ' ', content)
    text = htmlmod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    link_pattern = re.findall(r'href="(https://www\.citya\.com/annonces/location/appartement/le-havre-76351/(GES[\w-]+))"', content)
    unique_links = list(dict.fromkeys(link_pattern))
    
    listings_text = re.findall(r'(Le Havre \(766\d\d\))\s+Appartement\s+(\d)\s*pièces\s+(\d+(?:\.\d+)?)m²\s+([^€]*?)\s+(\d+)\s*€', text)
    
    print(f"\n=== Citya {label}: {len(unique_links)} links, {len(listings_text)} text listings ===")
    
    for (full_url, ges_id), (city, pieces, surface, features, price) in zip(unique_links, listings_text):
        p = int(pieces)
        s = float(surface)
        pr = int(price)
        citya_id = f"citya-{ges_id}"
        
        if p >= 2 and s >= 28 and pr <= 500:
            is_new = citya_id not in seen_ids
            status = "NEW" if is_new else "SEEN"
            print(f"  [{status}] {citya_id} | T{p} {s}m² {pr}€ | {features.strip()}")
            if is_new:
                all_new.append({
                    'id': citya_id,
                    'pieces': p,
                    'surface': s,
                    'price': pr,
                    'features': features.strip(),
                    'url': full_url,
                    'source': 'citya'
                })

print(f"\n\nTotal NEW Citya candidates: {len(all_new)}")