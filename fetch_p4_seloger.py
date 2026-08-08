#!/usr/bin/env python3
"""Fetch page 4 of le-partenaire rentals and also try SeLoger API"""
import urllib.request
import re
import json

# Page 4
url = "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?prix-max=500&page=4"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'fr-FR,fr;q=0.9'
})
try:
    with urllib.request.urlopen(req, timeout=20) as response:
        html = response.read().decode('utf-8')
    h2_count = len(re.findall(r'<h2', html))
    print(f"Page 4 h2 count: {h2_count}, size: {len(html)} bytes")
    
    if h2_count > 0:
        listing_blocks = re.split(r'<h2', html)
        for i, block in enumerate(listing_blocks[1:], 1):
            h2_match = re.search(r'>(.*?)</h2>', block, re.DOTALL)
            if not h2_match: continue
            h2_text = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
            link_match = re.search(r'href="(/immobilier/location/appartement/[^"]+)"', block)
            link = f"https://www.le-partenaire.fr{link_match.group(1)}" if link_match else "NO_LINK"
            block_text = re.sub(r'<[^>]+>', ' ', block[:5000])
            block_text = re.sub(r'\s+', ' ', block_text).strip()[:300]
            print(f"  P4-L{i}: {h2_text} | {link}")
            print(f"    Text: {block_text}")
    else:
        print("No listings on page 4 — end of results")
except Exception as e:
    print(f"Page 4 error: {e}")

print("\n=== Trying SeLoger API ===")
# SeLoger alternative API endpoint
seloger_urls = [
    "https://www.seloger.com/recherche/alm/results?adTypeCodes=1&propertyTypeCodes=1&cityCode=435120&districtCodes=nbh2fr6210&priceMax=500&roomsMin=2",
    "https://www.seloger.com/alter?projects=2&propertyTypeIds=1&cityCode=435120&districtCodes=nbh2fr6210&priceMax=500&roomsMin=2",
]
for sl_url in seloger_urls:
    print(f"\nTrying: {sl_url[:80]}...")
    req2 = urllib.request.Request(sl_url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json,text/html',
        'Accept-Language': 'fr-FR,fr;q=0.9',
        'Referer': 'https://www.seloger.com/',
    })
    try:
        with urllib.request.urlopen(req2, timeout=15) as response:
            data = response.read().decode('utf-8')
            print(f"  Response size: {len(data)} bytes")
            print(f"  First 300 chars: {data[:300]}")
            # Check if JSON
            try:
                j = json.loads(data)
                print(f"  JSON parsed! Keys: {list(j.keys()) if isinstance(j, dict) else 'array'}")
                print(json.dumps(j, indent=2, ensure_ascii=False)[:2000])
            except:
                # Check if HTML with DataDome
                if 'captcha-delivery' in data or 'datadome' in data.lower():
                    print("  BLOCKED by DataDome")
                else:
                    print("  HTML response (not JSON)")
    except Exception as e:
        print(f"  Error: {e}")