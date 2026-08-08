import re, json, html

# Parse Orpi pages 3-6
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

all_new = []
for p in [3,4,5,6]:
    fname = f'/tmp/orpi{p}.html'
    s = open(fname).read()
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.DOTALL)
    if not ld: continue
    try:
        data = json.loads(ld.group(1))
    except: continue
    for item in data.get('itemListElement', []):
        url = item.get('url', '')
        price = item.get('item', {}).get('offers', {}).get('price', 0)
        type_m = re.search(r'appartement-(t\d)-', url)
        prop_type = type_m.group(1) if type_m else ''
        id_m = re.search(r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
        if not id_m:
            id_m = re.search(r'-(\d+-\d+)', url)
        listing_id = id_m.group(1) if id_m else ''
        if prop_type in ['t2','t3','t4','t5'] and price <= 500:
            seen_id = f"orpi-{listing_id}"
            status = "NEW" if seen_id not in seen else "SEEN"
            print(f"  p{p} {status}: {seen_id} | {prop_type} | {price}€ | {url}")
            if status == "NEW":
                all_new.append({'source': 'orpi', 'id': seen_id, 'type': prop_type, 'price': price, 'url': url, 'page': p})

# Parse DDG results for leboncoin
s = open('/tmp/ddg_lbc.html').read()
print("\n=== DDG results ===")
# DDG results have links
results = re.findall(r'class="result__url"[^>]*href="([^"]+)"', s)
if not results:
    results = re.findall(r'href="(https://www\.leboncoin\.fr/[^"]+)"', s)
print(f"LBC links found: {len(results)}")
for r in results[:10]:
    print(f"  {r}")
# Also try result links in DDG format
lbc_links = re.findall(r'leboncoin\.fr[^"<\s]*', s)
print(f"LBC mentions: {len(lbc_links)}")
for l in set(lbc_links[:15]):
    print(f"  {l}")