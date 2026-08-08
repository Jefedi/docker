import re, json

# Parse Le-Partenaire HTML pages to extract listing URLs in order
# The URLs are in href attributes within the page

all_urls = []
for p in range(1,7):
    try:
        html = open(f'/opt/data/tmp/lp_page{p}.html').read()
    except:
        continue
    
    # Find all listing URLs - pattern: /immobilier/location/appartement/havre/76600/Npieces/ID
    url_pattern = r'href="(/immobilier/location/appartement/havre/76600/\d+pieces/\d+)"'
    urls = re.findall(url_pattern, html)
    
    # Deduplicate while preserving order
    seen = set()
    page_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            page_urls.append(u)
    
    # Also find h2 headings in order
    h2_pattern = r'<h2[^>]*>(.*?)</h2>'
    h2s_raw = re.findall(h2_pattern, html, re.DOTALL)
    
    clean_h2s = []
    for h in h2s_raw:
        h = re.sub(r'<[^>]+>', '', h)
        h = h.replace('&nbsp;', ' ').strip()
        h = ' '.join(h.split())
        if 'pièce' in h and 'm' in h:
            clean_h2s.append(h)
    
    # The h2s and urls should be in the same order
    # But URLs appear twice (image link + title link), so deduped URLs = half the count
    # Let's try matching them
    
    print(f"Page {p}: {len(clean_h2s)} h2s, {len(page_urls)} unique URLs")
    
    for i, h2 in enumerate(clean_h2s):
        if i < len(page_urls):
            url = f'https://www.le-partenaire.fr{page_urls[i]}'
            # Extract ID from URL
            id_match = re.search(r'/(\d+)$', page_urls[i])
            list_id = id_match.group(1) if id_match else 'N/A'
            
            # Extract rooms and surface from h2
            rooms_match = re.search(r'(\d+)\s*pi[èe]ce', h2)
            surf_match = re.search(r'(\d+)\s*m', h2)
            rooms = int(rooms_match.group(1)) if rooms_match else 0
            surface = int(surf_match.group(1)) if surf_match else 0
            
            all_urls.append({
                'page': p,
                'idx': i,
                'id': list_id,
                'url': url,
                'rooms': rooms,
                'surface': surface,
                'title': h2
            })

# Now match with the body text listings (which have prices)
# The body text has 112 listings, the HTML has the URLs
# They should be in the same order (page by page)

# Save all URL mappings
with open('/opt/data/tmp/lp_url_map.json', 'w') as f:
    json.dump(all_urls, f)

print(f"\nTotal URL mappings: {len(all_urls)}")

# Show T2+ with surface >= 28
t2_plus = [u for u in all_urls if u['rooms'] >= 2 and u['surface'] >= 28]
print(f"T2+ >= 28m²: {len(t2_plus)}")
for u in t2_plus:
    print(f"  lp-{u['id']} | T{u['rooms']} | {u['surface']}m² | {u['url']}")