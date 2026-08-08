import re, html as htmlmod

# Parse LH Immo
content = open('/tmp/lhimmo.html').read()
text = re.sub(r'<[^>]+>', ' ', content)
text = htmlmod.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Find links to listing pages
links = re.findall(r'href="([^"]*(?:location|annonce|appartement)[^"]*)"', content, re.I)
unique_links = list(dict.fromkeys(links))

# Find listing-related content
print("=== LH IMMO ===")
print(f"Size: {len(content)}")
print(f"Links found: {len(unique_links)}")
for l in unique_links[:30]:
    if 'immobilier' in l.lower() or 'location' in l.lower() or 'annonce' in l.lower() or 'appartement' in l.lower():
        print(f"  {l}")

# Look for T2/T3/appartement keywords
t_matches = re.findall(r'(T[23456]\s*\d+m²|F[23456]\s*\d+m²|\d+\s*pi[eè]ces?\s*\d+m²|appartement\s+T[23456])', text, re.I)
print(f"\nT/F matches in text: {t_matches[:20]}")

# Look for rent prices
prices = re.findall(r'(\d{2,4})\s*€', text)
print(f"Prices found: {prices[:30]}")

# Print relevant section of text
idx = text.lower().find('location')
if idx > 0:
    print(f"\nText around 'location': {text[idx:idx+1000]}")