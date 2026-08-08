import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

# Parse Century21
content = open('/tmp/c21.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find listing links
links = re.findall(r'href="(https://www\.century21\.fr/annonces/[^"]*)"', content)
unique_links = list(dict.fromkeys(links))
print(f"=== CENTURY21 ===")
print(f"Links: {len(unique_links)}")
for l in unique_links[:15]:
    print(f"  {l}")

# Find prices
prices = re.findall(r'(\d{3,4})\s*€', text)
print(f"\nPrices: {prices[:30]}")

# Find T2/T3 with context
for t in ['T2', 'T3', 'T4', '2 pièces', '3 pièces', '4 pièces']:
    idx = 0
    count = 0
    while count < 3:
        pos = text.find(t, idx)
        if pos == -1:
            break
        context = text[max(0,pos-30):pos+200]
        print(f"  {t}: ...{context[:200]}...")
        idx = pos + 1
        count += 1