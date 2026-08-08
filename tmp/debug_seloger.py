#!/usr/bin/env python3
"""Debug: check which SeLoger IDs are new and pass filters"""
import json

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"
with open(SEEN_FILE, "r") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))

# All SeLoger IDs from this run
sl_ids = [
    "276243197", "276243207", "180926433", "276185665", "276338655",
    "276408811", "26Z4GUXYNNCB", "267168127", "26I654XVFP3T", "276064257",
    "274667821", "276175525", "276243195", "275783129", "267698407",
    "275691613", "275691607", "276257925", "276255249", "276092941",
    "275691619", "276258183", "276182013", "276172833", "266005573",
    "275866055", "266054329", "262607053", "275675171", "275675201",
    # Sanvic
    "26Y63QXUDQGJ", "270704613", "275165711", "268MMPF498R2",
    "271834225", "275845193", "276140781",
    # Bléville
    "272270715", "26LIW2HARWHR", "276180117", "276068787",
    "276354903", "274271567", "273747587",
    # Additional from Bléville nearby
    "273920187", "271259701", "268717463", "276140781",
]

print("=== NEW SELOGER IDs NOT IN SEEN LIST ===")
new_sl = []
for sid in sl_ids:
    full_id = f"seloger-{sid}"
    if full_id not in seen_ids and sid not in seen_ids:
        new_sl.append(sid)
        print(f"  NEW: seloger-{sid}")

print(f"\nTotal new SeLoger: {len(new_sl)}")