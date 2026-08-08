#!/usr/bin/env python3
"""Ad-hoc verification: run parse_rentals.py and check output structure."""
import json, os, subprocess, sys

r = subprocess.run([sys.executable, "/opt/data/cron/tmp/parse_rentals.py"],
                   capture_output=True, text=True, timeout=30)
assert r.returncode == 0, f"exit code {r.returncode}\nstderr:\n{r.stderr}"

out = "/opt/data/cron/tmp/parsed_rentals.json"
assert os.path.exists(out), "output JSON missing"
with open(out) as f:
    data = json.load(f)

assert "all_filtered" in data and isinstance(data["all_filtered"], list)
assert "new_listings" in data and isinstance(data["new_listings"], list)
assert "all_ids_this_run" in data and isinstance(data["all_ids_this_run"], list)

for l in data["all_filtered"]:
    assert l["rooms"] >= 2, f"{l['id']} rooms={l['rooms']} <2"
    assert l["price"] <= 500, f"{l['id']} price={l['price']} >500"

new_ids = {l["id"] for l in data["new_listings"]}
filtered_ids = {l["id"] for l in data["all_filtered"]}
assert new_ids.issubset(filtered_ids), "new not subset of filtered"

assert len(data["new_listings"]) == 0
assert len(data["all_filtered"]) == 22

print("ALL ASSERTIONS PASSED")
print(f"filtered={len(data['all_filtered'])}, new={len(data['new_listings'])}, total_ids={len(data['all_ids_this_run'])}")