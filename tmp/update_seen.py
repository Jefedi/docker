#!/usr/bin/env python3
"""Update seen file with current run's IDs and timestamp"""
import json

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"
with open(SEEN_FILE, "r") as f:
    seen_data = json.load(f)

# All IDs from this run (LBC + SeLoger) - already all in seen
this_run_ids = [
    "lbc-3243119818", "lbc-3243118723", "lbc-3114599423", "lbc-3240426512",
    "lbc-2978416071", "lbc-3206014055", "lbc-3225885761", "lbc-3242915625",
    "lbc-3171888088", "lbc-3242893363", "lbc-3236957272", "lbc-3183706861",
    "lbc-3242751208", "lbc-3008426681", "lbc-3225853352", "lbc-3138529046",
    "lbc-3222895244", "lbc-3020670214", "lbc-3230697352", "lbc-3242316355",
    "lbc-3242315235", "lbc-3242301814", "lbc-3223323830", "lbc-3197074083",
    "lbc-3229817725", "lbc-3166993605", "lbc-3213020854", "lbc-3241893358",
    "lbc-3197373339", "lbc-3229591468", "lbc-3241786702", "lbc-3241640668",
    "lbc-3241474418",
    "seloger-276243197", "seloger-276243207", "seloger-180926433",
    "seloger-276185665", "seloger-276338655", "seloger-276408811",
    "seloger-26Z4GUXYNNCB", "seloger-267168127", "seloger-26I654XVFP3T",
    "seloger-276064257", "seloger-274667821", "seloger-276175525",
    "seloger-276243195", "seloger-275783129", "seloger-267698407",
    "seloger-275691613", "seloger-275691607", "seloger-276257925",
    "seloger-276255249", "seloger-276092941", "seloger-275691619",
    "seloger-276258183", "seloger-276182013", "seloger-276172833",
    "seloger-266005573", "seloger-275866055", "seloger-266054329",
    "seloger-262607053", "seloger-275675171", "seloger-275675201",
    "seloger-26Y63QXUDQGJ", "seloger-270704613", "seloger-275165711",
    "seloger-268MMPF498R2", "seloger-271834225", "seloger-275845193",
    "seloger-276140781", "seloger-272270715", "seloger-26LIW2HARWHR",
    "seloger-276180117", "seloger-276068787", "seloger-276354903",
    "seloger-274271567", "seloger-273747587", "seloger-273920187",
    "seloger-271259701", "seloger-268717463",
]

# Add any new IDs not already in seen
existing = set(seen_data.get("seen_ids", []))
added = 0
for rid in this_run_ids:
    if rid not in existing:
        seen_data["seen_ids"].append(rid)
        existing.add(rid)
        added += 1

seen_data["last_updated"] = "2026-08-02"
seen_data["total_seen"] = len(existing)

with open(SEEN_FILE, "w") as f:
    json.dump(seen_data, f, indent=2)

print(f"Added {added} new IDs to seen file")
print(f"Total seen: {len(existing)}")
print(f"Last updated: 2026-08-02")