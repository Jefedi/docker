#!/bin/bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# SaintRoch and HEUZE use netty.immo platform - try fetching their API
# The netty.immo platform typically loads data from a JSON API endpoint
curl -s -L --max-time 30 -A "$UA" -H "Accept: application/json" \
  "https://www.saintrochimmo.com/api/annonces?departement=76&type=location&ville=Le+Havre" \
  -o /opt/data/cron/tmp/havre_rental/stroch_api.json 2>/dev/null
echo "SaintRoch API: $(wc -c < /opt/data/cron/tmp/havre_rental/stroch_api.json) bytes"

curl -s -L --max-time 30 -A "$UA" -H "Accept: application/json" \
  "https://www.heuze-immo.fr/api/annonces?departement=76&type=location&ville=Le+Havre" \
  -o /opt/data/cron/tmp/havre_rental/heuze_api.json 2>/dev/null
echo "HEUZE API: $(wc -c < /opt/data/cron/tmp/havre_rental/heuze_api.json) bytes"

# Try the netty.immo API directly
curl -s -L --max-time 30 -A "$UA" -H "Accept: application/json" \
  "https://cdn.netty.immo/api/v1/annonces?site=saintrochimmo&type=location&ville=Le+Havre" \
  -o /opt/data/cron/tmp/havre_rental/netty_stroch.json 2>/dev/null
echo "Netty SaintRoch: $(wc -c < /opt/data/cron/tmp/havre_rental/netty_stroch.json) bytes"

curl -s -L --max-time 30 -A "$UA" -H "Accept: application/json" \
  "https://cdn.netty.immo/api/v1/annonces?site=heuze-immo&type=location&ville=Le+Havre" \
  -o /opt/data/cron/tmp/havre_rental/netty_heuze.json 2>/dev/null
echo "Netty HEUZE: $(wc -c < /opt/data/cron/tmp/havre_rental/netty_heuze.json) bytes"

# Le-Partenaire page 2
curl -s -L --max-time 30 -A "$UA" \
  "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2&page=2" \
  -o /opt/data/cron/tmp/havre_rental/lp_page2.html 2>/dev/null
echo "LP page2: $(wc -c < /opt/data/cron/tmp/havre_rental/lp_page2.html) bytes"

# Try Leboncoin via Google search
curl -s -L --max-time 30 -A "$UA" \
  "https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-500&rooms=2-" \
  -o /opt/data/cron/tmp/havre_rental/lbc_page2.html 2>/dev/null
echo "Leboncoin retry: $(wc -c < /opt/data/cron/tmp/havre_rental/lbc_page2.html) bytes"

# Check if Leboncoin returned actual content
head -5 /opt/data/cron/tmp/havre_rental/lbc_page2.html 2>/dev/null

# Try SaintRoch and HEUZE direct location page with different paths
curl -s -L --max-time 30 -A "$UA" \
  "https://www.saintrochimmo.com/location" \
  -o /opt/data/cron/tmp/havre_rental/stroch_location.html 2>/dev/null
echo "SaintRoch /location: $(wc -c < /opt/data/cron/tmp/havre_rental/stroch_location.html) bytes"

curl -s -L --max-time 30 -A "$UA" \
  "https://www.heuze-immo.fr/location" \
  -o /opt/data/cron/tmp/havre_rental/heuze_location.html 2>/dev/null
echo "HEUZE /location: $(wc -c < /opt/data/cron/tmp/havre_rental/heuze_location.html) bytes"

# Look for the netty.immo API endpoint in the SaintRoch HTML
python3 -c "
import re
with open('/opt/data/cron/tmp/havre_rental/stroch_page.html', 'r', errors='replace') as f:
    html = f.read()
# Find API URLs or data endpoints
api_urls = re.findall(r'(?:api|ajax|fetch|endpoint|url)\s*[:=]\s*[\"\\']([^\"\\']+)[\"\\']', html, re.I)
print('=== SaintRoch API URLs ===')
for u in set(api_urls[:20]):
    print(f'  {u}')
# Find JSON data blocks
json_data = re.findall(r'window\.__INITIAL[_A-Z]*__\s*=\s*({.*?});', html, re.DOTALL)
if json_data:
    print(f'Found __INITIAL__ data: {len(json_data)} blocks')
    for d in json_data[:1]:
        print(d[:500])
# Also look for netty.immo CDN URLs
netty_urls = re.findall(r'(https?://[^\"\\']*netty[^\"\\']*)', html)
print('Netty URLs:', set(netty_urls[:10]))
# Find script src that might load listing data
script_srcs = re.findall(r'<script[^>]*src=\"([^\"]+)\"', html)
print('Script sources:')
for s in script_srcs[:20]:
    print(f'  {s}')
"