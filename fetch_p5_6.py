#!/usr/bin/env python3
"""Check page 5 and 6 of le-partenaire rentals"""
import urllib.request
import re

for page in [5, 6]:
    url = f"https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?prix-max=500&page={page}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'fr-FR,fr;q=0.9'
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8')
        h2_count = len(re.findall(r'<h2', html))
        print(f"Page {page}: {h2_count} h2 elements, {len(html)} bytes")
        
        if h2_count == 0:
            print(f"  No listings on page {page} — end of results")
            break
        
        listing_blocks = re.split(r'<h2', html)
        for i, block in enumerate(listing_blocks[1:], 1):
            h2_match = re.search(r'>(.*?)</h2>', block, re.DOTALL)
            if not h2_match: continue
            h2_text = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
            link_match = re.search(r'href="(/immobilier/location/appartement/[^"]+)"', block)
            link = link_match.group(1) if link_match else "NO_LINK"
            block_text = re.sub(r'<[^>]+>', ' ', block[:5000])
            block_text = re.sub(r'\s+', ' ', block_text).strip()[:300]
            print(f"  P{page}-L{i}: {h2_text} | {link}")
            print(f"    Text: {block_text}")
    except Exception as e:
        print(f"Page {page} error: {e}")
        break