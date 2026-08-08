import re
with open('/opt/data/tmp/lp_page2.html') as f:
    html = f.read()

# Find occurrences in the body (skip head)
body_start = html.find('<body')
body_html = html[body_start:]

indices = [m.start() for m in re.finditer(r'Location Appartement', body_html)]
print(f"Found {len(indices)} occurrences in body")
for idx in indices[:5]:
    snippet = body_html[idx:idx+500]
    clean = re.sub(r'<[^>]+>', '|', snippet)
    clean = re.sub(r'\|+', '|', clean).strip()
    print(f"  [{idx}] {clean[:300]}")
    print()