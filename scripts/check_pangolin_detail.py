#!/usr/bin/env python3
"""Check detailed resource info from Pangolin API"""
import json, os, urllib.request

KEY = "e0411iyuhtammka.pftfyczb6jzlgyfszqrmmknq7xihlwlrwtt6upd3"
BASE = "https://api.jefe.ovh/v1"

def api(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers={"Authorization": f"Bearer {KEY}"})
    return json.loads(urllib.request.urlopen(req).read())

# Get all resources first
data = api("org/jorganisation/resources")
resources = data['data']['resources']

# Check each resource detail
for r in resources:
    rid = r['resourceId']
    detail = api(f"resource/{rid}")
    res = detail.get('data', detail.get('resource', {}))
    name = res.get('name', r.get('name', '?'))
    domain = res.get('fullDomain', 'NONE') or 'NONE'
    
    # Find any field that's different
    print(f"=== {name} ({domain}) ===")
    for k, v in res.items():
        if k not in ['targets','sites']:
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
    print()
