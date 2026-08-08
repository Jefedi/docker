#!/usr/bin/env python3
"""Examine Le-Partenaire HTML structure around listings."""
import re

with open('/tmp/lp_havre.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find a 2p listing block and print raw HTML around it
# Let's find ID 24395043 (2p 54m²)
pos = html.find('/immobilier/location/appartement/havre/76600/2pieces/24395043')
if pos == -1:
    pos = html.find('/immobilier/location/appartement/le-havre/76600/2pieces/24395043')

if pos != -1:
    # Get 3000 chars around this position
    start = max(0, pos - 1500)
    end = min(len(html), pos + 1500)
    snippet = html[start:end]
    print(f"=== Around listing 24395043 (pos {pos}) ===")
    print(snippet)
else:
    print("Listing 24395043 not found")

print("\n\n=== Looking for price patterns ===")
# Find all € signs with context
euro_positions = [m.start() for m in re.finditer('€', html)]
print(f"Total € signs: {len(euro_positions)}")
for i, pos in enumerate(euro_positions[:30]):
    start = max(0, pos - 100)
    end = min(len(html), pos + 50)
    snippet = html[start:end]
    clean = re.sub(r'<[^>]+>', ' ', snippet)
    clean = re.sub(r'\s+', ' ', clean).strip()
    print(f"  {i}: ...{clean}...")