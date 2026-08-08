#!/usr/bin/env python3
"""Process rental listings from scraped data, filter by criteria, deduplicate."""
import json
from datetime import datetime, timezone

# Load seen IDs
with open("/opt/data/cron/output/havre-rental-seen.json", "r") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))

print(f"Previously seen IDs: {len(seen_ids)}")

# All listings found this round (parsed from scraped data)
# Format: (id, price, rooms, surface, quartier, source, url)
all_listings = [
    # === LEBONCOIN ===
    ("lbc-3114599423", 455, 2, 31, "Coty", "leboncoin", "https://www.leboncoin.fr/ad/locations/3114599423"),
    ("lbc-3138529046", 460, 2, 18, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3138529046"),
    ("lbc-3138535281", 345, 2, 15, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3138535281"),
    ("lbc-3229817725", 449, 2, 33, "Centre-ville", "leboncoin", "https://www.leboncoin.fr/ad/locations/3229817725"),
    ("lbc-2978416071", 465, 2, 25, "Massillon", "leboncoin", "https://www.leboncoin.fr/ad/locations/2978416071"),
    ("lbc-3166993605", 470, 2, 34, "Les Ormeaux - Maréchal Joffre", "leboncoin", "https://www.leboncoin.fr/ad/locations/3166993605"),
    ("lbc-3213020854", 476, 2, 32, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/3213020854"),
    ("lbc-3241893358", 450, 2, 222, "Saint-Vincent - Plage", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241893358"),
    ("lbc-2932371645", 440, 2, 0, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/2932371645"),
    ("lbc-3197373339", 440, 2, 18, "Coty", "leboncoin", "https://www.leboncoin.fr/ad/locations/3197373339"),
    ("lbc-3229591468", 395, 2, 35, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3229591468"),
    ("lbc-3241786702", 490, 2, 30, "Rond point - Observatoire", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241786702"),
    ("lbc-3241640668", 500, 2, 30, "Sainte-Anne", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241640668"),
    ("lbc-3241474418", 470, 2, 30, "Coty", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241474418"),
    ("lbc-3219073825", 380, 2, 26, "Les Ormeaux - Maréchal Joffre", "leboncoin", "https://www.leboncoin.fr/ad/locations/3219073825"),
    ("lbc-3241348202", 430, 2, 28, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241348202"),
    ("lbc-3232584892", 450, 2, 19, "Les Ormeaux - Maréchal Joffre", "leboncoin", "https://www.leboncoin.fr/ad/locations/3232584892"),
    ("lbc-3237765019", 480, 2, 28, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/3237765019"),
    ("lbc-3229817723", 500, 2, 44, "Graville", "leboncoin", "https://www.leboncoin.fr/ad/locations/3229817723"),
    ("lbc-3224720197", 449, 2, 34, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/3224720197"),
    ("lbc-3209580923", 450, 2, 35, "Sainte-Anne", "leboncoin", "https://www.leboncoin.fr/ad/locations/3209580923"),
    ("lbc-3241059761", 499, 2, 31, "Université - Sainte-Marie", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241059761"),
    ("lbc-3241053474", 400, 2, 20, "Université - Sainte-Marie", "leboncoin", "https://www.leboncoin.fr/ad/locations/3241053474"),
    ("lbc-3196913879", 470, 2, 17, "Sainte-Anne", "leboncoin", "https://www.leboncoin.fr/ad/locations/3196913879"),
    ("lbc-3183706861", 470, 2, 41, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3183706861"),
    ("lbc-3195812292", 440, 2, 29, "Eure", "leboncoin", "https://www.leboncoin.fr/ad/locations/3195812292"),
    ("lbc-3221348340", 465, 2, 37, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/3221348340"),
    ("lbc-3235187047", 495, 2, 26, "Massillon", "leboncoin", "https://www.leboncoin.fr/ad/locations/3235187047"),
    ("lbc-3020670214", 476, 2, 32, "Non précisé", "leboncoin", "https://www.leboncoin.fr/ad/locations/3020670214"),
    ("lbc-3237765020", 495, 2, 35, "Centre-ville", "leboncoin", "https://www.leboncoin.fr/ad/locations/3237765020"),
    ("lbc-3240709047", 500, 2, 44, "Graville", "leboncoin", "https://www.leboncoin.fr/ad/locations/3240709047"),
    ("lbc-3235187051", 500, 2, 30, "Sainte-Anne", "leboncoin", "https://www.leboncoin.fr/ad/locations/3235187051"),
    ("lbc-3240546339", 500, 2, 44, "Graville", "leboncoin", "https://www.leboncoin.fr/ad/locations/3240546339"),
    ("lbc-3229022454", 490, 2, 50, "Sainte-Anne", "leboncoin", "https://www.leboncoin.fr/ad/locations/3229022454"),

    # === SELOGER CENTRE-VILLE ===
    ("seloger-266899095", 500, 1, 19, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/266899095.htm"),
    ("seloger-263624475", 500, 1, 20, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/263624475.htm"),
    ("seloger-276243207", 695, 2, 38, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276243207.htm"),
    ("seloger-276243197", 695, 2, 38, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276243197.htm"),
    ("seloger-276243195", 695, 2, 38, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276243195.htm"),
    ("seloger-276140311", 570, 2, 34, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276140311.htm"),
    ("seloger-276185665", 590, 2, 33, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276185665.htm"),
    ("seloger-26Z4GUXYNNCB", 880, 2, 50, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/26Z4GUXYNNCB.htm"),
    ("seloger-26I654XVFP3T", 475, 1, 22, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/26I654XVFP3T.htm"),
    ("seloger-267168127", 600, 3, 42, "Anatole France-Danton", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/anatole-france-danton/267168127.htm"),
    ("seloger-276064257", 750, 2, 40, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276064257.htm"),
    ("seloger-274667821", 690, 2, 47, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/274667821.htm"),
    ("seloger-276175525", 490, 1, 14, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276175525.htm"),
    ("seloger-276257925", 895, 3, 56, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276257925.htm"),
    ("seloger-275783129", 818, 2, 50, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/275783129.htm"),
    ("seloger-276182013", 670, 1, 35, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276182013.htm"),
    ("seloger-276172833", 445, 1, 13, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276172833.htm"),
    ("seloger-276255249", 590, 1, 39, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276255249.htm"),
    ("seloger-267698407", 1795, 6, 126, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/267698407.htm"),
    ("seloger-275691613", 650, 2, 36, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/275691613.htm"),
    ("seloger-275691607", 650, 2, 36, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275691607.htm"),
    ("seloger-276092941", 620, 2, 45, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276092941.htm"),
    ("seloger-275691619", 650, 2, 36, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275691619.htm"),
    ("seloger-276258183", 534, 2, 57, "Anatole France-Danton", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276258183.htm"),
    ("seloger-275866055", 650, 1, 24, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275866055.htm"),
    ("seloger-266005573", 500, 1, 26, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/266005573.htm"),
    ("seloger-266054329", 735, 2, 46, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/266054329.htm"),
    ("seloger-262607053", 730, 2, 40, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/262607053.htm"),
    ("seloger-275675171", 785, 2, 80, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275675171.htm"),
    ("seloger-275675201", 785, 2, 80, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275675201.htm"),
    ("seloger-275048601", 695, 1, 33, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275048601.htm"),
    ("seloger-275048603", 695, 1, 33, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/275048603.htm"),

    # === SELOGER SANVIC ===
    ("seloger-26Y63QXUDQGJ", 420, 2, 22, "Sanvic", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/sanvic/26Y63QXUDQGJ.htm"),
    ("seloger-270704613", 1080, 3, 80, "Sanvic", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/sanvic/270704613.htm"),
    ("seloger-268MMPF498R2", 670, 2, 40, "Sanvic", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/sanvic/268MMPF498R2.htm"),
    ("seloger-271834225", 476, 2, 32, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/271834225.htm"),
    ("seloger-275845193", 530, 1, 22, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/275845193.htm"),
    ("seloger-276140781", 490, 1, 20, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276140781.htm"),
    ("seloger-275083403", 930, 2, 48, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/275083403.htm"),

    # === SELOGER BLÉVILLE ===
    ("seloger-272270715", 480, 1, 22, "Bléville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/bleville/272270715.htm"),
    ("seloger-26LIW2HARWHR", 450, 0, 18, "Bléville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/bleville/26LIW2HARWHR.htm"),
    ("seloger-276180117", 895, 2, 51, "Saint-Vincent", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276180117.htm"),
    ("seloger-276068787", 435, 1, 20, "Centre-ville", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/276068787.htm"),
    ("seloger-274271567", 920, 4, 63, "Saint-Vincent", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/274271567.htm"),
    ("seloger-275689915", 820, 3, 58, "Points Cardinaux", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/points-cardinaux/275689915.htm"),
    ("seloger-273920187", 890, 3, 69, "Points Cardinaux", "seloger", "https://www.seloger.com/annonces/locations/appartement/le-havre-76/points-cardinaux/273920187.htm"),
]

# Criteria
ACCEPTED_QUARTIERS = {"Centre-ville", "Sanvic", "Bléville"}
MAX_PRICE = 500
MIN_ROOMS = 2

# Step 1: Filter by criteria
qualifying = []
for listing in all_listings:
    lid, price, rooms, surface, quartier, source, url = listing
    if rooms >= MIN_ROOMS and price <= MAX_PRICE and quartier in ACCEPTED_QUARTIERS:
        qualifying.append(listing)

print(f"\nTotal listings found this round: {len(all_listings)}")
print(f"Qualifying (T2+, <=500EUR, Centre-ville/Bléville/Sanvic): {len(qualifying)}")

for q in qualifying:
    print(f"  {q[0]}: {q[1]}EUR, {q[2]}p, {q[3]}m2, {q[4]}")

# Step 2: Deduplicate - find NEW qualifying listings
new_qualifying = []
for q in qualifying:
    if q[0] not in seen_ids:
        new_qualifying.append(q)

print(f"\nNEW qualifying listings: {len(new_qualifying)}")
for q in new_qualifying:
    print(f"  {q[0]}: {q[1]}EUR, {q[2]}p, {q[3]}m2, {q[4]}")

# Step 3: Find ALL new IDs (not just qualifying) for seen file update
all_new_ids = []
for listing in all_listings:
    if listing[0] not in seen_ids:
        all_new_ids.append(listing[0])

print(f"\nAll new IDs (any listing): {len(all_new_ids)}")
for nid in all_new_ids:
    print(f"  {nid}")

# Step 4: Update seen file
updated_seen_ids = sorted(list(seen_ids | set(l[0] for l in all_listings)))
now = datetime.now(timezone.utc).isoformat()

seen_data["seen_ids"] = updated_seen_ids
seen_data["last_updated"] = now
seen_data["last_run_count"] = len(all_listings)
seen_data["last_run_new"] = len(all_new_ids)
seen_data["last_run_new_qualifying"] = len(new_qualifying)

with open("/opt/data/cron/output/havre-rental-seen.json", "w") as f:
    json.dump(seen_data, f, indent=2, ensure_ascii=False)

print(f"\nSeen file updated: {len(updated_seen_ids)} total IDs")
print(f"Last run: {len(all_listings)} listings, {len(all_new_ids)} new, {len(new_qualifying)} new qualifying")

# Print new qualifying for notification
if new_qualifying:
    print("\n=== NOTIFICATION BODY ===")
    for q in new_qualifying:
        lid, price, rooms, surface, quartier, source, url = q
        print(f"🏠 T{rooms} {surface}m² — {quartier}")
        print(f"💰 {price}€/mois")
        print(f"🔗 {url}")
        print()