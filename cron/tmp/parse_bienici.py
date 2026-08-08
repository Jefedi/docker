import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

content = open('/tmp/bienici.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Bien'ici is JS-heavy. Check for data
print("=== BIEN'ICI ===")
print(f"Size: {len(content)}")

# Look for JSON data
json_blocks = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', content, re.S)
print(f"JSON blocks: {len(json_blocks)}")

# Look for __NEXT_DATA__ or similar
next_data = re.search(r'__NEXT_DATA__\s*=\s*({.*?})</script>', content, re.S)
if next_data:
    print("NEXT_DATA found!")

# Look for window.__ data
window_data = re.findall(r'window\.__(\w+)__', content)
print(f"Window data: {window_data}")

# Look for listing data in text
prices = re.findall(r'(\d{3,4})\s*€', text)
print(f"Prices: {prices[:30]}")

# Look for "location" or "à louer"
loc_mentions = text.count('location')
print(f"'location' mentions: {loc_mentions}")

# Find T2/T3 mentions
t_mentions = re.findall(r'(T[23456]|F[23456])', text)
print(f"T/F mentions: {t_mentions[:20]}")

# Check for specific JSON data patterns
# Bien'ici sometimes embeds data in a specific div
data_divs = re.findall(r'data-(\w+)="([^"]{50,})"', content)
print(f"Long data attrs: {len(data_divs)}")
for name, val in data_divs[:5]:
    print(f"  data-{name}: {val[:100]}...")