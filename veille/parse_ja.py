import re, html as h
import json

# Parse JA (Jullien-Allix)
html = open('/tmp/veille/ja2.html').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = h.unescape(re.sub(r'\s+', ' ', text)).strip()

# Find listing patterns: "a-louer" in URLs
urls = re.findall(r'(https://www\.jullien-allix\.fr/a-louer-[^"\s<>]+)', html)
unique_urls = list(dict.fromkeys(urls))
print(f'JA a-louer URLs: {len(unique_urls)}')
for u in unique_urls[:30]:
    print(f'  {u}')

# Also look in the text for listing titles
titles = re.findall(r'a-louer-[\w-]+', text)
print(f'\nJA a-louer in text: {len(titles)}')
for t in list(dict.fromkeys(titles))[:30]:
    print(f'  {t}')

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])
ja_seen = [s for s in seen_ids if s.startswith('ja-')]
print(f'\nJA already seen: {len(ja_seen)}')
for s in ja_seen:
    print(f'  {s}')