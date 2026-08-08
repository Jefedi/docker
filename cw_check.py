import httpx, json

cookie = "cw_auth=qtLymCxqhFylisH3i2Hr5sZRBzbrK3EX5jrW73QqZS0"
h = {"Cookie": cookie, "Content-Type": "application/json"}
b = "http://127.0.0.1:8787"

# Pairs
r = httpx.get(f"{b}/api/pairs", headers=h, timeout=10)
print(f"Pairs status: {r.status_code}")
try:
    data = r.json()
    if isinstance(data, list):
        for p in data:
            if isinstance(p, dict):
                src = p.get("source", "?")
                tgt = p.get("target", "?")
                mode = p.get("mode", "?")
                pid = p.get("id", "?")
                feats = p.get("features", {})
                wl = feats.get("watchlist", {})
                hist = feats.get("history", {})
                prog = feats.get("progress", {})
                wl_en = wl.get("enable", False) if isinstance(wl, dict) else bool(wl)
                h_en = hist.get("enable", False) if isinstance(hist, dict) else bool(hist)
                p_en = prog.get("enable", False) if isinstance(prog, dict) else bool(prog)
                print(f"  {pid}: {src} -> {tgt} | mode={mode} | WL={wl_en} HIST={h_en} PROG={p_en}")
            else:
                print(f"  (non-dict): {p}")
    elif isinstance(data, dict):
        pairs_key = data.get("pairs", data.get("data", []))
        if isinstance(pairs_key, list):
            for p in pairs_key:
                if isinstance(p, dict):
                    src = p.get("source", "?")
                    tgt = p.get("target", "?")
                    mode = p.get("mode", "?")
                    pid = p.get("id", "?")
                    feats = p.get("features", {})
                    wl = feats.get("watchlist", {})
                    hist = feats.get("history", {})
                    wl_en = wl.get("enable", False) if isinstance(wl, dict) else bool(wl)
                    h_en = hist.get("enable", False) if isinstance(hist, dict) else bool(hist)
                    print(f"  {pid}: {src} -> {tgt} | mode={mode} | WL={wl_en} HIST={h_en}")
        else:
            print(f"  Dict response: {json.dumps(data, indent=2)[:3000]}")
    else:
        print(f"  Type: {type(data)}, raw: {str(data)[:2000]}")
except Exception as e:
    print(f"  Parse error: {e}")
    print(f"  Raw text: {r.text[:2000]}")

# Config
r2 = httpx.get(f"{b}/api/config", headers=h, timeout=10)
print(f"\nConfig status: {r2.status_code}")
try:
    cfg = r2.json()
    if isinstance(cfg, dict):
        pairs_in_cfg = cfg.get("pairs", [])
        print(f"  Pairs in config: {len(pairs_in_cfg) if isinstance(pairs_in_cfg, list) else 'N/A'}")
        instances = cfg.get("provider_instances", cfg.get("instances", []))
        if isinstance(instances, list):
            print(f"  Provider instances: {len(instances)}")
            for inst in instances[:15]:
                if isinstance(inst, dict):
                    print(f"    {inst.get('provider','?')}: {inst.get('name','?')} (id={inst.get('id','?')})")
        watcher = cfg.get("watcher", cfg.get("scrobble", {}))
        if watcher:
            print(f"  Watcher config: {json.dumps(watcher, indent=2)[:500]}")
except Exception as e:
    print(f"  Config parse error: {e}")
    print(f"  Config raw: {r2.text[:1000]}")