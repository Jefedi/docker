import re, html as h
import json

html = open('/tmp/veille/stroch2.html').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = h.unescape(re.sub(r'\s+', ' ', text)).strip()

# Find Saint Roch codes (LAxxxx)
codes = re.findall(r'\b(LA\d{3,4})\b', html)
unique_codes = list(dict.fromkeys(codes))
print(f'Stroch codes: {len(unique_codes)}')

# Find prices
prices = re.findall(r'(\d[\d.]*)\s*€', text)
print(f'Prices: {prices[:30]}')

# Find listing links
links = re.findall(r'href="([^"]*location[^"]*appartement[^"]*)"', html)
unique_links = list(dict.fromkeys(links))
print(f'Links: {len(unique_links)}')
for l in unique_links[:20]:
    print(f'  {l}')

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])
stroch_seen = [s for s in seen_ids if s.startswith('stroch-')]
print(f'\nStroch already seen: {len(stroch_seen)}')
for s in stroch_seen:
    print(f'  {s}')