#!/usr/bin/env python3
import re

# JA - look at actual link patterns
with open('/opt/data/cron/tmp/havre_rental/ja_page.html', 'r', errors='replace') as f:
    html = f.read()
hrefs = re.findall(r'href="([^"]+)"', html)
listing_hrefs = [h for h in hrefs if any(kw in h.lower() for kw in ['annonce', 'location', 'louer', 'a-louer'])]
print('=== JA HREFS (first 30) ===')
seen = set()
for h in listing_hrefs:
    if h not in seen:
        seen.add(h)
        print(f'  {h}')
print()

# SaintRoch
with open('/opt/data/cron/tmp/havre_rental/stroch_page.html', 'r', errors='replace') as f:
    html = f.read()
hrefs = re.findall(r'href="([^"]+)"', html)
print('=== SaintRoch HREFS (first 20) ===')
for h in hrefs[:20]:
    print(f'  {h}')
la_ids = re.findall(r'LA\d+', html)
va_ids = re.findall(r'VA\d+', html)
print(f'  LA IDs: {la_ids[:10]}')
print(f'  VA IDs: {va_ids[:10]}')
# Check for card patterns
cards = re.findall(r'data-(?:ref|id|listing)="([^"]+)"', html)
print(f'  data-ref/ids: {cards[:10]}')

# Look for listing blocks with 'louer' in text
louer_blocks = re.findall(r'(?:louer|location|Loyer).{0,200}', html[:50000])
print(f'  Louer/location blocks (first 5): ')
for b in louer_blocks[:5]:
    clean = re.sub(r'<[^>]+>', ' ', b)
    clean = re.sub(r'\s+', ' ', clean)
    print(f'    {clean[:150]}')
print()

# HEUZE
with open('/opt/data/cron/tmp/havre_rental/heuze_page.html', 'r', errors='replace') as f:
    html = f.read()
hrefs = re.findall(r'href="([^"]+)"', html)
print('=== HEUZE HREFS (first 20) ===')
for h in hrefs[:20]:
    print(f'  {h}')
la_ids = re.findall(r'LA\d+', html)
va_ids = re.findall(r'VA\d+', html)
print(f'  LA IDs: {la_ids[:10]}')
print(f'  VA IDs: {va_ids[:10]}')

# Orpi - check actual listing URL pattern
with open('/opt/data/cron/tmp/havre_rental/orpi_page.html', 'r', errors='replace') as f:
    html = f.read()
orpi_hrefs = re.findall(r'href="(/annonce-location[^"]+)"', html)
print('=== ORPI listing hrefs (first 10) ===')
seen = set()
for h in orpi_hrefs:
    if h not in seen:
        seen.add(h)
        print(f'  {h}')
print()

# C21 - check listing pattern
with open('/opt/data/cron/tmp/havre_rental/c21_page.html', 'r', errors='replace') as f:
    html = f.read()
c21_hrefs = re.findall(r'href="([^"]*annonce[^"]*)"', html)
print('=== C21 listing hrefs (first 10) ===')
seen = set()
for h in c21_hrefs:
    if h not in seen:
        seen.add(h)
        print(f'  {h}')