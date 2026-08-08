import re, html as h

html_content = open('/tmp/veille/lhimmo_annonces.html').read()
# First strip HTML, then search
text = re.sub(r'<[^>]+>', ' ', html_content)
text = h.unescape(re.sub(r'\s+', ' ', text)).strip()

# Find all "XXX€ /mois" patterns
matches = re.finditer(r'(\d+)\s*€\s*/?\s*mois', text)
listings = []
for m in matches:
    price = int(m.group(1))
    start = max(0, m.start() - 500)
    end = min(len(text), m.end() + 500)
    context = text[start:end]
    listings.append((price, context))

print(f'LH Immo rental matches: {len(listings)}')
for price, ctx in listings:
    print(f'PRICE={price}€')
    print(f'  CONTEXT: {ctx[:300]}')
    print()