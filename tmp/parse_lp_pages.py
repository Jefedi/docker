import re, html as htmlmod

with open('/opt/data/tmp/lp_page2.html') as f:
    raw = f.read()

body_start = raw.find('<body')
body_html = raw[body_start:]

# Replace &nbsp; with space
body_html = body_html.replace('&nbsp;', ' ')

# Find all listing titles
titles = re.findall(r'à Le Havre (\d+) pièces\s*\|\s*(\d+) m²', body_html)
prices = re.findall(r'(\d[\d\s]*)€\s*/\s*mois', body_html)
links = re.findall(r'href="/immobilier/location/appartement/havre/76600/(\d+)pieces/(\d+)"', body_html)

# Dedupe links
seen = set()
unique_links = []
for rooms, id in links:
    if id not in seen:
        seen.add(id)
        unique_links.append((rooms, id))

print(f"Titles: {len(titles)}")
print(f"Prices: {len(prices)}")
print(f"Unique links: {len(unique_links)}")

# Load seen IDs
import json
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Parse and filter
for i, (rooms, surface) in enumerate(titles):
    price_str = prices[i].strip() if i < len(prices) else "?"
    price = int(re.sub(r'\s','',price_str)) if price_str != "?" else 0
    link_id = unique_links[i][1] if i < len(unique_links) else ""
    seen_id = f"lp-{link_id}"
    
    issues = []
    if price > 500: issues.append(f"prix {price}>500")
    if int(surface) < 28: issues.append(f"surface {surface}<28")
    if int(rooms) < 2: issues.append(f"T{rooms}<2")
    if seen_id in seen_ids: issues.append("DEJA VU")
    
    status = "❌" if issues else "✅"
    print(f"  {status} T{rooms} | {surface}m² | {price}€ | ID:{link_id} | {', '.join(issues) if issues else 'QUALIFIE'}")