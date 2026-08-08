#!/usr/bin/env python3
"""Find the price element on lp2 for the first listing."""
import re

raw = open('/tmp/scrape/lp2.html','r',errors='replace').read()
pos = raw.find('24379617')
# Get 3000 chars after
chunk = raw[pos:pos+3000]
# Find all € mentions
prices = re.findall(r'(\d[\d\s\xa0]*)\s*€', chunk)
print('Prices found:', prices)

# Also look for the <span class="prix"> pattern
prix_matches = re.findall(r'class="prix"[^>]*>([^<]*)<', chunk)
print('Prix spans:', prix_matches)

# Look for "mois" near prices
mois_matches = re.findall(r'(\d[\d\s\xa0]*)\s*€[^<]*mois', chunk)
print('€/mois:', mois_matches)

# Also check full text around the price
text_chunk = re.sub(r'<[^>]+>', ' ', chunk)
text_chunk = re.sub(r'\s+', ' ', text_chunk).strip()
print('\nText around listing:')
print(text_chunk[:1000])