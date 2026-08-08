import re, json, html

# Parse Jullien & Allix location page
s = open('/tmp/src_b82d1c6c.html').read()
print(f"=== Jullien & Allix ({len(s)} bytes) ===")
# JA has listing links with titles
links = re.findall(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/[^"]+)"', s)
print(f"Links: {len(links)}")
for l in links: print(f"  {l}")

# Find listing blocks with title, price, surface
# JA typically has article blocks
articles = re.findall(r'<article[^>]*>(.*?)</article>', s, re.DOTALL)
print(f"\nArticles: {len(articles)}")
for a in articles[:10]:
    title_m = re.search(r'<h[23456][^>]*>(.*?)</h[23456]>', a, re.DOTALL)
    title = html.unescape(re.sub('<[^>]+>','',title_m.group(1))).strip() if title_m else ''
    price_m = re.search(r'(\d[\d\s]*)\s*€', a)
    price = price_m.group(1).strip() if price_m else ''
    link_m = re.search(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/[^"]+)"', a)
    link = link_m.group(1) if link_m else ''
    print(f"  {title[:80]} | {price}€ | {link}")

# Also look for listing containers by link
print("\n=== Listings by link ===")
for link in set(links):
    idx = s.find(link)
    if idx >= 0:
        block = s[max(0,idx-500):idx+500]
        title_m = re.search(r'<h[23456][^>]*>(.*?)</h[23456]>', block, re.DOTALL)
        title = html.unescape(re.sub('<[^>]+>','',title_m.group(1))).strip() if title_m else ''
        price_m = re.search(r'(\d[\d\s]*)\s*€', block)
        price = price_m.group(1).replace(' ','').strip() if price_m else ''
        # Extract ID from URL
        id_m = re.search(r'/([a-z0-9-]+)\.html', link)
        lid = id_m.group(1) if id_m else ''
        print(f"  {lid[:60]} | {price}€ | {title[:60]}")