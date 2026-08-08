#!/usr/bin/env python3
"""Create a private site resource in Pangolin for NAS SMB"""
import json, urllib.request, os

KEY = "e0411iyuhtammka.pftfyczb6jzlgyfszqrmmknq7xihlwlrwtt6upd3"
BASE = "https://api.jefe.ovh/v1"

# Try multiple body formats
formats = [
    # Format 1: flat siteResources fields
    {
        "name": "NAS SMB",
        "mode": "tcp",
        "destination": "192.168.1.92",
        "destinationPort": 445,
        "ssl": False,
        "enabled": True,
        "domainId": "ykx3vzina5zahuf",
        "subdomain": "nas",
        "authDaemonMode": "site",
        "disableIcmp": True,
        "tcpPortRangeString": "445"
    },
    # Format 2: wrapped in siteResources
    {
        "siteResources": {
            "name": "NAS SMB",
            "mode": "tcp",
            "destination": "192.168.1.92",
            "destinationPort": 445,
            "ssl": False,
            "enabled": True,
            "domainId": "ykx3vzina5zahuf",
            "subdomain": "nas"
        }
    },
    # Format 3: with siteNetworks wrapper
    {
        "siteNetworks": {"siteId": 18},
        "siteResources": {
            "name": "NAS SMB",
            "mode": "tcp",
            "destination": "192.168.1.92",
            "destinationPort": 445,
            "ssl": False,
            "enabled": True,
            "domainId": "ykx3vzina5zahuf",
            "subdomain": "nas"
        }
    }
]

for i, body in enumerate(formats, 1):
    req = urllib.request.Request(
        f"{BASE}/org/jorganisation/site/18/resource",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"Format {i}: SUCCESS")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
        break
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:500]
        print(f"Format {i}: {e.code} - {err_body}")
    print()
