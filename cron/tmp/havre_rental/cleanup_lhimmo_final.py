#!/usr/bin/env python3
"""Remove remaining garbage LH Immo entries from qualified and seen."""
import json

SEEN = "/opt/data/cron/output/havre-rental-seen.json"
QUAL = "/opt/data/cron/tmp/havre_rental/qualified_listings.json"

# All lhimmo-annonce/ entries are vente listings or non-location pages from the LH Immo homepage
# They were incorrectly captured because the LH Immo parser grabbed sale property links
GARBAGE = [
    "lhimmo-annonce/maison-avec-jardin-et-garage-bleville/",
    "lhimmo-annonce/appartement-t4-centre-ville/",
    "lhimmo-annonce/appartement-t3-brionne/",
    "lhimmo-annonce/colocation-meublee-3-chambres-disponibles-a-deux-pas-de-la-plage/",
    "lhimmo-annonce/hyper-centre-ville-appartement-t4/",
    "lhimmo-annonce/maison-a-vendre-sainte-adresse-95-m%c2%b2-4-chambres/",
    "lhimmo-annonce/appartement-t2-quartier-danton-2/",
    "lhimmo-annonce/appartement-t3-au-pied-de-lespace-coty/",
    "lhimmo-annonce/appartement-t2-quartier-universite-le-havre/",
]

# Clean seen
with open(SEEN) as f: sd = json.load(f)
before = len(sd["seen_ids"])
sd["seen_ids"] = [i for i in sd["seen_ids"] if i not in GARBAGE]
sd["total_seen"] = len(sd["seen_ids"])
with open(SEEN, "w") as f: json.dump(sd, f, indent=2, ensure_ascii=False)
print(f"Seen: {before} -> {len(sd['seen_ids'])} (removed {before - len(sd['seen_ids'])})")

# Clean qualified
with open(QUAL) as f: ql = json.load(f)
before_q = len(ql)
ql = [q for q in ql if q["id"] not in GARBAGE]
with open(QUAL, "w") as f: json.dump(ql, f, indent=2, ensure_ascii=False)
print(f"Qualified: {before_q} -> {len(ql)} (removed {before_q - len(ql)})")

# Show remaining new qualified
new_q = [q for q in ql if q.get("is_new")]
print(f"\nRemaining new qualified: {len(new_q)}")
for q in new_q:
    print(f"  {q['id']}: {q.get('price')}€ | {q.get('surface')}m² | {q.get('rooms')}p")