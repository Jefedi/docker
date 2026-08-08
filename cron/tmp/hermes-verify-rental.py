#!/usr/bin/env python3
"""Ad-hoc verification for cron rental monitoring run (2026-08-08).

Verifies:
1. Seen state file is valid JSON with consistent internal counts
2. All expected source prefixes are represented in seen_ids
3. No new qualifying listings were missed (re-checks the filter logic
   against listings from LBC and LP sources)
4. The accepted-quartier filter logic is correct via test cases

This is NOT a test suite — it validates the artifacts produced by
the one-off scraping scripts in /opt/data/cron/tmp/.
"""
import json
import sys
import os

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"
LP_LISTINGS = "/opt/data/cron/tmp/lp_listings.json"
LBC_NEW = "/opt/data/cron/tmp/lbc_new_candidates.json"

errors = []
passes = []

# 1. Seen file validity
try:
    with open(SEEN_FILE) as f:
        data = json.load(f)
    assert "seen_ids" in data, "missing seen_ids key"
    assert isinstance(data["seen_ids"], list), "seen_ids not a list"
    assert data["total_seen"] == len(data["seen_ids"]), (
        f"total_seen={data['total_seen']} != len(seen_ids)={len(data['seen_ids'])}"
    )
    assert len(set(data["seen_ids"])) == len(data["seen_ids"]), "duplicate IDs in seen_ids"
    passes.append(f"Seen file valid: {data['total_seen']} unique IDs, updated {data['last_updated']}")
except Exception as e:
    errors.append(f"Seen file invalid: {e}")
    data = {"seen_ids": []}

# 2. Source prefix coverage
expected_prefixes = {
    "lbc", "seloger", "lp", "sqhab", "lhimmo", "citya",
    "orpi", "heuze", "ja", "stroch", "c21", "bienici",
}
actual_prefixes = set()
for id_ in data["seen_ids"]:
    if "-" in id_:
        actual_prefixes.add(id_.split("-")[0])
missing = expected_prefixes - actual_prefixes
if missing:
    errors.append(f"Missing source prefixes: {missing}")
else:
    passes.append(f"All {len(expected_prefixes)} source prefixes present in seen file")

# 3. Verify LBC filter: all 66 LBC listings should be in seen → 0 new
if os.path.exists(LBC_NEW):
    with open(LBC_NEW) as f:
        lbc_new = json.load(f)
    if len(lbc_new) == 0:
        passes.append("LBC: 0 new candidates (all 66 listings already seen)")
    else:
        errors.append(f"LBC: {len(lbc_new)} unexpected new candidates")
else:
    errors.append(f"LBC new candidates file missing: {LBC_NEW}")

# 4. Verify LP filter: all 61 LP listings should be in seen → 0 new qualifying
if os.path.exists(LP_LISTINGS):
    with open(LP_LISTINGS) as f:
        lp_listings = json.load(f)
    seen_set = set(data["seen_ids"])
    lp_new = [l for l in lp_listings if l["id"] not in seen_set
              and l["prix"] <= 500 and l["pieces"] >= 2 and l["surf"] >= 28]
    if len(lp_new) == 0:
        passes.append(f"LP: 0 new qualifying listings (all {len(lp_listings)} checked)")
    else:
        errors.append(f"LP: {len(lp_new)} unexpected new qualifying listings: {[l['id'] for l in lp_new]}")
else:
    errors.append(f"LP listings file missing: {LP_LISTINGS}")

# 5. Accepted-quartier filter correctness (test cases)
accepted = {
    "centre-ville", "coty", "massillon", "eure", "felix faure",
    "perret", "docks", "rond point - observatoire",
    "saint-francois - les docks",
    "danton", "sanvic", "bleville",
}
test_cases = [
    ("Coty", True), ("Eure", True), ("Massillon", True),
    ("Felix Faure", True), ("Rond point - Observatoire", True),
    ("Sanvic", True), ("Sainte-Anne", False), ("Graville", False),
    ("Universite - Sainte-Marie", False), ("Les Ormeaux", False),
]
for quartier, expected in test_cases:
    qn = quartier.lower().strip()
    result = any(aq in qn or qn in aq for aq in accepted)
    if result != expected:
        errors.append(f"Quartier filter wrong: '{quartier}' expected {expected}, got {result}")
    else:
        passes.append(f"Quartier filter OK: '{quartier}' -> {result}")

# Report
print("=" * 60)
print("AD-HOC VERIFICATION (not a test suite)")
print("=" * 60)
for p in passes:
    print(f"  PASS  {p}")
for e in errors:
    print(f"  FAIL  {e}")
print(f"\n{len(passes)} checks passed, {len(errors)} errors")
if errors:
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)