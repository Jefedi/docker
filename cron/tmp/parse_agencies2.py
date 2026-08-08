#!/usr/bin/env python3
"""Parse agency-specific pages for listings."""
import re, json, os

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&#039;', "'").replace('&amp;', '&')
    s = s.replace('&eacute;', 'é').replace('&egrave;', 'è').replace('&agrave;', 'à')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# --- Saint Roch Immobilier ---
print("=== SAINT ROCH IMMOBILIER ===")
with open('/tmp/stroch_loc.html', 'r', errors='replace') as f:
    html = f.read()

# Look for listing links
listing_links = re.findall(r'href="(/location/appartement/le-havre/76600/[^"]+)"', html)
print(f"Listing links: {len(listing_links)}")
for l in listing_links[:20]:
    print(f"  {l}")

# Look for prices
prices = re.findall(r'(\d[\d\s]{1,6})\s*€', html)
print(f"Prices: {prices[:15]}")

# Look for JSON data
json_blocks = re.findall(r'data-(?:bien|property|listing)="([^"]+)"', html)
print(f"Data blocks: {len(json_blocks)}")

# Try to find listing blocks with price + surface
blocks = re.split(r'/location/appartement/le-havre/76600/', html)
print(f"Blocks after listing URL split: {len(blocks)}")
for i, b in enumerate(blocks[1:6], 1):
    snippet = clean(b[:500])
    print(f"  Block {i}: {snippet[:200]}")

# --- HEUZE ---
print("\n=== HEUZE IMMOBILIER ===")
with open('/tmp/heuze_loc.html', 'r', errors='replace') as f:
    html = f.read()

listing_links = re.findall(r'href="(/location/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

prices = re.findall(r'(\d[\d\s]{1,6})\s*€', html)
print(f"Prices: {prices[:15]}")

# --- LH Immo ---
print("\n=== LH IMMO ===")
with open('/tmp/lhimmo_annonces.html', 'r', errors='replace') as f:
    html = f.read()

listing_links = re.findall(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

# --- SquareHabitat ---
print("\n=== SQUAREHABITAT ===")
with open('/tmp/sqhab_havre.html', 'r', errors='replace') as f:
    html = f.read()

# Look for listing URLs
listing_links = re.findall(r'href="(/annonces/location/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

# Look for JSON-LD data
ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f"JSON-LD blocks: {len(ld_blocks)}")
for b in ld_blocks[:3]:
    print(f"  {b[:300]}")

# Look for data attributes
data_attrs = re.findall(r'data-[a-z]+="[^"]*"', html)
print(f"Data attrs (first 20): {data_attrs[:20]}")

# --- Citya ---
print("\n=== CITYA ===")
with open('/tmp/citya_havre.html', 'r', errors='replace') as f:
    html = f.read()

listing_links = re.findall(r'href="(/annonces/location/appartement/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

# --- Orpi ---
print("\n=== ORPI ===")
with open('/tmp/orpi_havre.html', 'r', errors='replace') as f:
    html = f.read()

listing_links = re.findall(r'href="(/location-immobiliere-le-havre/louer-appartement/[^"]*annonce[^"]*|/annonce/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")

# --- Century21 ---
print("\n=== CENTURY21 ===")
with open('/tmp/c21_havre.html', 'r', errors='replace') as f:
    html = f.read()

listing_links = re.findall(r'href="(/annonces/[^"]+)"', html)
unique_links = list(dict.fromkeys(listing_links))
print(f"Listing links: {len(unique_links)}")
for l in unique_links[:20]:
    print(f"  {l}")