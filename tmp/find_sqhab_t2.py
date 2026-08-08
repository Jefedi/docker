#!/usr/bin/env python3
"""Find T2 under 500 on SquareHabitat."""
import re, html as h

raw = open('/tmp/scrape/sqhab.html','r',errors='replace').read()
text = re.sub(r'<[^>]+>', ' ', raw)
text = h.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

# Search for 395€ listing (T2 Docks 35m²) and check its details
idx = text.find('395 €')
if idx >= 0:
    print(f"395€ context: {text[max(0,idx-200):idx+400]}")

print()

# Search for 458€ listing (T3 Sanvic 70m²)
idx = text.find('458 €')
if idx >= 0:
    print(f"458€ context: {text[max(0,idx-200):idx+400]}")

# Also get the UUID for the 395€ listing
idx_raw = raw.find('395')
if idx_raw >= 0:
    chunk = raw[max(0,idx_raw-2000):idx_raw+500]
    uuids = re.findall(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', chunk)
    print(f"\nUUIDs near 395€: {uuids}")