import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

lbc = data['results'][0]['content']

# Strategy: Split on "Voir l'annonce" links to find listing blocks
# Each listing has a "Voir l'annonce" link, and the text before it (since previous link) is the listing info
lines = lbc.split('\n')

# Extract all ad URLs and their positions
ad_urls = []
for i, line in enumerate(lines):
    m = re.search(r'Voir l.annonce\]\((https://www\.leboncoin\.fr/ad/locations/\d+)\)', line)
    if m:
        ad_urls.append((i, m.group(1)))

print(f"Found {len(ad_urls)} ad URLs")
for idx, (line_num, url) in enumerate(ad_urls):
    print(f"  [{idx}] line {line_num}: {url}")