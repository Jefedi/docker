#!/usr/bin/env python3
"""Debug price extraction on lp2."""
import re

raw = open('/tmp/scrape/lp2.html','r',errors='replace').read()

# Find all class="prix" occurrences
prix_matches = re.findall(r'class="prix"[^>]*>([^<]{1,30})<', raw)
print(f'Total class="prix" matches on lp2: {len(prix_matches)}')
for m in prix_matches[:10]:
    print(f'  "{m}"')

# Let's look at a specific listing that's T2 and should have a price
# Find lp-23946724
pos = raw.find('23946724')
if pos > 0:
    chunk = raw[pos:pos+2000]
    # Find all class="prix" in this chunk
    prix_in_chunk = re.findall(r'class="prix"[^>]*>([^<]{1,30})<', chunk)
    print(f'\nPrix for 23946724: {prix_in_chunk}')
    # Also look for the full text
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = re.sub(r'\s+', ' ', text).strip()
    print(f'Text: {text[:300]}')