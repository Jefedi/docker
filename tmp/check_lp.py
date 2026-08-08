import re
with open('/opt/data/tmp/lp_page2.html') as f:
    html = f.read()
# Look for the actual pattern
matches = re.findall(r'à Le Havre\s*(\d+)\s*pièces.*?(\d+)\s*m²', html)
print(f'Pattern matches: {len(matches)}')
# Try different pattern
matches2 = re.findall(r'Location Appartement', html)
print(f'Location Appartement count: {len(matches2)}')
# Show context around first occurrence
idx = html.find('Location Appartement')
if idx >= 0:
    print(repr(html[idx:idx+200]))
else:
    print("'Location Appartement' not found in HTML")
    # Try to find any heading with "Le Havre" and "pièce"
    idx2 = html.find('pièce')
    if idx2 >= 0:
        print(repr(html[max(0,idx2-100):idx2+100]))