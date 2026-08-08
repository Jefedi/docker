import re, html as h
import json

html = open('/tmp/veille/heuze2.html').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = h.unescape(re.sub(r'\s+', ' ', text)).strip()

# Find HEUZE codes
codes = re.findall(r'\b([VL][AS]\d{3,4})\b', html)
unique_codes = list(dict.fromkeys(codes))
print(f'HEUZE codes on location page: {len(unique_codes)}')

# Find prices
prices = re.findall(r'(\d[\d.]*)\s*€', text)
print(f'Prices: {prices[:30]}')

# Find listing links with bien IDs
links = re.findall(r'href="([^"]*location/appartement/[^"]+)"', html)
unique_links = list(dict.fromkeys(links))
print(f'Links: {len(unique_links)}')
for l in unique_links[:20]:
    print(f'  {l}')

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Find listings with codes
for code in unique_codes:
    lid = f'heuze-{code}'
    status = 'SEEN' if lid in seen_ids else 'NEW'
    
    # Find context
    idx = html.find(code)
    chunk = html[max(0,idx-500):idx+2000]
    ctx = re.sub(r'<[^>]+>', ' ', chunk)
    ctx = h.unescape(re.sub(r'\s+', ' ', ctx)).strip()
    
    # Price
    price_m = re.search(r'(\d[\d.]*)\s*€', ctx)
    price = price_m.group(1) if price_m else '?'
    
    print(f'{status}: heuze-{code} | price={price}€')
    print(f'  TEXT: {ctx[:300]}')
    print()