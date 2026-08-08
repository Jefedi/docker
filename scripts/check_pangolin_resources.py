#!/usr/bin/env python3
import json, os, urllib.request

KEY = "e0411iyuhtammka.pftfyczb6jzlgyfszqrmmknq7xihlwlrwtt6upd3"
URL = "https://api.jefe.ovh/v1/org/jorganisation/resources"

req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {KEY}"})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

resources = data['data']['resources']
print(f"Total: {len(resources)}\n")

# All unique keys
keys = set()
for r in resources:
    keys.update(r.keys())
print("=== ALL FIELDS ===")
for k in sorted(keys):
    print(f"  {k}")
print()

# Each resource
for r in resources:
    name = r.get('name', '?')
    domain = r.get('fullDomain', 'NONE')
    print(f"--- {name} ({domain}) ---")
    for k, v in r.items():
        if k not in ['targets','sites']:
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
    print()
