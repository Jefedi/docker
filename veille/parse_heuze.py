import re, html as h
import json

# Parse HEUZE
html = open('/tmp/veille/heuze.html').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = h.unescape(re.sub(r'\s+', ' ', text)).strip()

# Find listing links/patterns
# HEUZE uses codes like VA3117, LA1928, LS082, etc.
codes = re.findall(r'\b([VL][AS]\d{3,4})\b', html)
unique_codes = list(dict.fromkeys(codes))
print(f'HEUZE codes: {len(unique_codes)}')
for c in unique_codes:
    print(f'  {c}')

# Find prices
prices = re.findall(r'(\d+)\s*€', text)
print(f'Prices: {prices[:30]}')

# Find links
links = re.findall(r'href="([^"]+)"', html)
prop_links = [l for l in links if any(k in l.lower() for k in ['bien', 'annonce', 'location', 'a-louer'])]
print(f'Prop links: {len(prop_links)}')
for l in list(dict.fromkeys(prop_links))[:20]:
    print(f'  {l}')

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])
heuze_seen = [s for s in seen_ids if s.startswith('heuze-')]
print(f'\nHEUZE already seen: {len(heuze_seen)}')
for s in heuze_seen:
    print(f'  {s}')