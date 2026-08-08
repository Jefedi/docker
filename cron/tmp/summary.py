#!/usr/bin/env python3
"""Parse Bien'ici T2 listings and Century21 from body text."""
import json, re

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# Bien'ici T2 listings (from the output)
# Looking at the data, we have these T2 listings:
# bienici-citya-immobilier-5002-GES60020012-78 | 495€ | 2p | 30m² | Danton - Rond point
# bienici-ag752345-539794229 | 449€ | 2p | 33m² | Sainte-Marie - Saint-Léon

# But we need to check the full Bien'ici page for ALL T2 listings, not just the first 15 links
# The body text showed "Appartement meublé 2 pièces 33 m²" near the end

# Let's check which Bien'ici IDs we already have
bienici_seen = [s for s in seen_ids if s.startswith('bienici-')]
print(f"Bien'ici seen IDs: {len(bienici_seen)}")
for s in sorted(bienici_seen):
    print(f"  {s}")

# The Bien'ici IDs from the listing:
# bienici-citya-immobilier-5002-GES60020012-78 -> check if seen
# bienici-ag752345-539794229 -> check if seen
print(f"\nbienici-citya-immobilier-5002-GES60020012-78 in seen: {'bienici-citya-immobilier-5002-GES60020012-78' in seen_ids}")
print(f"bienici-ag752345-539794229 in seen: {'bienici-ag752345-539794229' in seen_ids}")

# But wait - we have "bienici-GES60020012-78" in seen (without the citya prefix)
# And "bienici-ag752345-539794229" in seen
# So the IDs match with different prefix patterns
print(f"\nbienici-GES60020012-78 in seen: {'bienici-GES60020012-78' in seen_ids}")

# Let's also check the Bien'ici T2 listing from the body text:
# "Appartement meublé 2 pièces 33 m²" - this is ag752345-539794229

# Century21 - from body text:
print("\n=== Century21 ===")
# From the body text:
# 1. Ref 7371 - 26.89m², 2 pièces, 474€, Rue Felix Faure
# 2. Ref 15443 - 23.78m², 1 pièce, 450€
# 3. Ref 7201 - 29m², 1 pièce, 470€
# 4. Ref 15596 - 27.21m², 1 pièce, 475€

# Only ref 7371 is T2, but 26.89m² < 28m²
# Check seen
print(f"c21-7371 in seen: {'c21-7371' in seen_ids}")
print(f"c21-15443 in seen: {'c21-15443' in seen_ids}")
print(f"c21-7201 in seen: {'c21-7201' in seen_ids}")
print(f"c21-15596 in seen: {'c21-15596' in seen_ids}")

# Ref 7371: T2, 26.89m² (below 28m² threshold), 474€, Rue Felix Faure (Centre-ville)
# This doesn't qualify due to surface < 28m²

# Let's also check the Bien'ici T2 listing more carefully
# bienici-citya-immobilier-5002-GES60020012-78: 495€, 2p, 30m², Danton - Rond point
# This is in an accepted quartier (Danton - Rond point = Centre-ville/Danton area)
# But the ID in seen is "bienici-GES60020012-78" not "bienici-citya-immobilier-5002-GES60020012-78"
# However "citya-GES60020012-78" is in seen! So this is a cross-posted listing already tracked.

# The other Bien'ici T2: ag752345-539794229, 449€, 2p, 33m², Sainte-Marie - not in accepted quartier
print(f"\n=== Bien'ici T2 listings check ===")
# bienici-citya-immobilier-5002-GES60020012-78: 495€, 2p, 30m², Danton
# Check if equivalent ID is in seen
# "citya-GES60020012-78" is in seen, "bienici-GES60020012-78" is in seen
# So this is already tracked
print("bienici-citya-immobilier-5002-GES60020012-78: Already tracked as citya-GES60020012-78 / bienici-GES60020012-78")

# bienici-ag752345-539794229: 449€, 2p, 33m², Sainte-Marie - not accepted quartier
print("bienici-ag752345-539794229: Sainte-Marie - NOT accepted quartier")

# Summary
print("\n=== FINAL SUMMARY ===")
print("Leboncoin: 66 listings, ALL already seen")
print("SeLoger Centre-ville: 18 listings, no T2 <=500€")
print("SeLoger Sanvic: 16 listings, no new T2 <=500€ in accepted quartier")
print("SeLoger Bléville: 11 listings, no new T2 <=500€ in accepted quartier")
print("Le-Partenaire: 61 listings, ALL already seen")
print("SquareHabitat: 12 listings, ALL already seen")
print("Citya: 19 listings, ALL already seen")
print("Orpi: 10 new Le Havre listings, but all result in 404 pages (ads expired)")
print("LH Immo: 9 listings, ALL already seen")
print("HEUZE: 1 listing (T3 615€), already seen")
print("Jullien-Allix: 33 listings, need to check T2 <=500€ in accepted quartiers")
print("Saint Roch: 12 listings, ALL already seen")
print("Bien'ici: 26 listings, T2s already tracked via Citya cross-posting")
print("Century21: 4 listings, only 1 T2 (26.89m² < 28m² - doesn't qualify)")
print("PAP.fr: BLOCKED by Cloudflare")
print("Foncia: BLOCKED (403 Forbidden)")