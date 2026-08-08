#!/usr/bin/env python3
import json, subprocess, sys

tab_id = open('/opt/data/cron/tmp/seloger_tab.txt').read().strip()
js = open('/opt/data/cron/tmp/seloger_eval.js').read().strip()
payload = json.dumps({'userId': 'hermes-veille', 'expression': js})

result = subprocess.run(
    ['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/evaluate',
     '-H', 'Content-Type: application/json', '-d', payload],
    capture_output=True, text=True
)

try:
    data = json.loads(result.stdout)
    if data.get('ok'):
        listings = json.loads(data['result'])
        for r in listings:
            print(f"seloger-{r['id']} | {r['price']}€ | {r['pieces']}pi | {r['surface']}m² | {r['url'][:80]}")
        print(f'Total: {len(listings)}')
    else:
        print('ERROR:', data)
except Exception as e:
    print(f'Parse error: {e}')
    print(result.stdout[:500])