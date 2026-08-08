import re, html as htmlmod

content = open('/tmp/c21.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Print all mentions of "Ref :" with context
refs = re.findall(r'Ref\s*:\s*(\w+)\s+(.{0,300})', text)
for ref, ctx in refs[:20]:
    print(f"Ref {ref}: {ctx[:200]}")
    print()

# Also find "par mois" patterns with more context
mois_matches = re.findall(r'(.{0,400}?)(\d{3,4})\s*€\s*par\s*mois', text)
for ctx, price in mois_matches[:10]:
    print(f"  {price}€: ...{ctx[-200:]}...")
    print()