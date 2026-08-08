import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

for page in range(3, 7):
    with open(f'/opt/data/tmp/lp_page{page}.html') as f:
        raw = f.read()
    body_start = raw.find('<body')
    body_html = raw[body_start:].replace('&nbsp;', ' ')
    
    titles = re.findall(r'à Le Havre (\d+) pièces\s*\|\s*(\d+) m²', body_html)
    links = re.findall(r'href="/immobilier/location/appartement/havre/76600/(\d+)pieces/(\d+)"', body_html)
    seen = set()
    unique_links = []
    for rooms, id in links:
        if id not in seen:
            seen.add(id)
            unique_links.append((rooms, id))
    
    print(f"\n=== Page {page}: {len(titles)} titles, {len(unique_links)} links ===")
    for i, (rooms, surface) in enumerate(titles):
        link_id = unique_links[i][1] if i < len(unique_links) else ""
        seen_id = f"lp-{link_id}"
        is_seen = seen_id in seen_ids
        if int(rooms) >= 2 and int(surface) >= 28 and not is_seen:
            print(f"  ✅ NEW! T{rooms} | {surface}m² | ID:{link_id}")
        elif int(rooms) >= 2 and int(surface) >= 28 and is_seen:
            pass  # already seen, skip
        elif int(rooms) >= 2 and int(surface) >= 28:
            print(f"  ? T{rooms} | {surface}m² | ID:{link_id} | seen:{is_seen}")