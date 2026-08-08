import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

with open('/tmp/veille/ja.html', encoding='utf-8', errors='replace') as f:
    raw = f.read()
ja_urls = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/a-louer-[^"]+\.html)"', raw)
ja_urls = list(dict.fromkeys(ja_urls))

new_ja = []
for u in ja_urls:
    slug = u.split('/')[-1].replace('.html', '')
    listing_id = f'ja-{slug}'
    if listing_id not in seen_ids:
        new_ja.append((listing_id, u))

print(f'JA total: {len(ja_urls)}, NEW: {len(new_ja)}')
for lid, url in new_ja:
    print(f'  {lid}')
    print(f'    {url}')