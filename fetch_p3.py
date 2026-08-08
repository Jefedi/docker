#!/usr/bin/env python3
"""Fetch page 3 of le-partenaire rentals and parse it"""
import urllib.request
import re

url = "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?prix-max=500&page=3"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'fr-FR,fr;q=0.9'
})
try:
    with urllib.request.urlopen(req, timeout=20) as response:
        html = response.read().decode('utf-8')
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Save it
with open('/tmp/lp_p3.html', 'w') as f:
    f.write(html)

h2_count = len(re.findall(r'<h2', html))
print(f"Page 3 h2 count: {h2_count}")
print(f"Page 3 size: {len(html)} bytes")

if h2_count == 0:
    print("No listings on page 3 — end of results")
    exit(0)

# Parse listings
listing_blocks = re.split(r'<h2', html)
for i, block in enumerate(listing_blocks[1:], 1):
    h2_match = re.search(r'>(.*?)</h2>', block, re.DOTALL)
    if not h2_match:
        continue
    h2_text = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
    link_match = re.search(r'href="(/immobilier/location/appartement/[^"]+)"', block)
    link = f"https://www.le-partenaire.fr{link_match.group(1)}" if link_match else "NO_LINK"
    block_text = re.sub(r'<[^>]+>', ' ', block[:5000])
    block_text = re.sub(r'\s+', ' ', block_text).strip()[:400]
    print(f"--- P3-L{i} ---")
    print(f"  H2: {h2_text}")
    print(f"  Link: {link}")
    print(f"  Text: {block_text}")