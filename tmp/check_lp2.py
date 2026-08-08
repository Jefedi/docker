import re
with open('/opt/data/tmp/lp_page2.html') as f:
    html = f.read()

# Find all occurrences of "Location Appartement" in the body
indices = [m.start() for m in re.finditer(r'Location Appartement', html)]
print(f"Found {len(indices)} occurrences")
for idx in indices[:5]:
    # Show surrounding context
    snippet = html[idx:idx+300]
    # Clean up HTML tags
    clean = re.sub(r'<[^>]+>', ' ', snippet)
    clean = re.sub(r'\s+', ' ', clean).strip()
    print(f"  [{idx}] {clean[:200]}")