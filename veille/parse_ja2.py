import re, html as h
import json

html = open('/tmp/veille/ja2.html').read()

# Find all "a-louer" slugs in the HTML
slugs = re.findall(r'/a-louer-([a-z0-9-]+)', html)
unique_slugs = list(dict.fromkeys(slugs))
print(f'JA a-louer slugs: {len(unique_slugs)}')

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

for slug in unique_slugs:
    lid = f'ja-a-louer-{slug}'
    status = 'SEEN' if lid in seen_ids else 'NEW'
    
    # Find context around this slug
    idx = html.find(f'/a-louer-{slug}')
    chunk = html[max(0,idx-1000):idx+2000]
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
    
    # Find price
    price_m = re.search(r'(\d+)\s*€', text)
    price = price_m.group(1) if price_m else '?'
    
    print(f'{status}: ja-a-louer-{slug} | price={price}€')
    print(f'  TEXT: {text[:300]}')
    print()