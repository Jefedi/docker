import re, html, json

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# Final summary of all sources checked
print("=== VEILLE IMMOBILIÈRE LE HAVRE — RÉSUMÉ ===\n")

# 1. Le-Partenaire: All listings checked, all qualifying ones already seen
print("1. Le-Partenaire.fr: 8 pages scrutées, 112 annonces totales")
print("   T2+ ≤500€ ≥28m² trouvées: 8 (toutes déjà vues)")
print("   Sources: lp.html + lp_page2-7.html")
print()

# 2. Leboncoin: Blocked by DataDome
print("2. Leboncoin.fr: BLOQUÉ (DataDome CAPTCHA, 774 bytes)")
print()

# 3. SeLoger: Blocked
print("3. SeLoger.com: BLOQUÉ (3 pages quartiers, 771 bytes chacune)")
print()

# 4. SquareHabitat: Checked P1+P2
print("4. SquareHabitat: 2 pages scrutées, 18 listings (page 1) + listings page 2")
print("   Tous UUIDs déjà vus (0 nouveau)")
print()

# 5. LH Immo: Checked
print("5. LH Immo: Site scruté")
print("   - T2 Danton: VENTE (88k€, pas location)")
print("   - T2 Université: 590€/mois (au-dessus budget)")
print("   - T3 Brionne: 600€/mois + hors Le Havre (Brionne)")
print("   Aucun nouveau T2 location ≤500€")
print()

# 6. Citya: 3 pages scrutées, 64 listings
print("6. Citya Immobilier: 3 pages scrutées, 64 listings")
print("   T2+ ≤500€ ≥28m²: 4 trouvées (toutes déjà vues)")
print()

# 7. Foncia: Blocked
print("7. Foncia: BLOQUÉ (520 bytes, probablement JS)")
print()

# 8. Saint Roch Immobilier: JS-heavy, no listing data extractable
print("8. Saint Roch Immobilier: JS-only, aucune donnée extractible via curl")
print()

# 9. Century 21: 4 annonces
print("9. Century 21: 4 annonces sur Le Havre")
print("   - F2 26.89m² 474€: surface <28m² (éliminé)")
print("   - F1 23.78m² 450€: T1 (éliminé)")
print("   - Studio 29m² 470€: T1 (éliminé)")
print("   - F1 27.21m² 475€: T1 (éliminé)")
print("   Aucun T2+ ≤500€ ≥28m²")
print()

# 10. Orpi: Multiple pages checked
print("10. Orpi: 8 pages scrutées (main, centre-ville, coty, massillon, félix faure, eure, saint-françois, page 2)")
print("    T2 ≤500€ ≥28m²: AUCUN trouvé")
print("    T2 proches (>500€): 4 listings à Coty (520-575€, 29-36m²)")
print()

# 11. HEUZE Immobilier: JS-only
print("11. HEUZE Immobilier: JS-only, aucune donnée extractible via curl")
print()

# 12. Jullien & Allix: 33 annonces, toutes déjà vues
print("12. Jullien & Allix: 33 annonces scrutées, 0 nouvelle")
print()

# 13. PAP.fr: Blocked
print("13. PAP.fr: BLOQUÉ (Cloudflare)")
print()

# 14. Bien'ici: JS-only
print("14. Bien'ici: JS-only, aucune donnée extractible via curl")
print()

# 15. Google/DDG search: Both blocked
print("15. Recherche Google/DuckDuckGo: BLOQUÉES (JS/CAPTCHA)")
print()

print("=== CONCLUSION ===")
print("AUCUNE nouvelle annonce T2+ ≤500€ ≥28m² avec cuisine séparée et chambre fermée")
print("trouvée ce cycle. Toutes les sources accessibles ont été scrutées.")