#!/usr/bin/env python3
"""Parse Saint Roch React SPA for listing data."""
import re, json

with open('/opt/data/tmp/havre/stroch_loc.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Look for script tags with JS code
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
for i, s in enumerate(scripts):
    if len(s.strip()) > 10:
        print(f"Script {i} ({len(s)} chars):")
        print(s[:300])
        # Look for API URLs
        api_urls = re.findall(r'https?://[^\s"\'`]+api[^\s"\'`]*', s, re.I)
        if api_urls:
            print(f"  API URLs: {api_urls[:5]}")
        # Look for fetch/axios calls
        fetch_calls = re.findall(r'fetch\(["\']([^"\']+)["\']', s)
        if fetch_calls:
            print(f"  Fetch calls: {fetch_calls[:5]}")
        # Look for JSON data structures
        json_data = re.findall(r'window\.\w+\s*=\s*({.+?});', s, re.DOTALL)
        if json_data:
            for j in json_data:
                print(f"  Window data: {j[:200]}")
        print()

# Also check for JSON-LD data
json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"JSON-LD blocks: {len(json_ld)}")
for j in json_ld[:3]:
    print(j[:300])
    print()

# Check for data-react-helmet or other data patterns
# The site claims 172 annonces - let's check if there's an API endpoint
# Look for any URL with 'biens' or 'annonces' or 'search'
urls = re.findall(r'https?://[^\s"\'`<>]+', content)
biens_urls = [u for u in urls if 'bien' in u.lower() or 'annonce' in u.lower() or 'search' in u.lower() or 'api' in u.lower()]
print(f"\nRelevant URLs: {len(biens_urls)}")
for u in biens_urls[:10]:
    print(f"  {u}")