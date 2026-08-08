# Open Data Property Research (via data.gouv.fr & APIs gouvernementales)

## Overview

Research a specific French property/address from GPS coordinates or address using government open data sources — no authentication required. This is complementary to listing scraping: instead of finding *deals*, you investigate a **specific location** (property type, transaction history, businesses on site, legal structure).

## Sources

| Source | URL | Purpose |
|--------|-----|---------|
| **BAN (Base Adresse Nationale)** | `https://api-adresse.data.gouv.fr/reverse/` | Reverse geocode GPS → address |
| **MCP data.gouv.fr** | `https://mcp.data.gouv.fr/mcp` | Search datasets, DVF metadata |
| **Geo-DVF (fichiers CSV)** | `https://files.data.gouv.fr/geo-dvf/latest/csv/` | Per-commune transaction history |
| **Annuaire des Entreprises** | `https://annuaire-entreprises.data.gouv.fr/` | Businesses at an address |
| **Pappers** | `https://www.pappers.fr/` | Company leadership & SCI info |
| **Societe.com** | `https://www.societe.com/` | Company registry & financials |
| **Historique Adresses** | `https://www.historiqueadresses.com/` | Timeline of businesses at an address |
| **BODACC** | `https://www.bodacc.fr/pages/annonces-commerciales/` | Legal announcements (creations, modifications, comptes) |
| **Pappers** | `https://www.pappers.fr/` | Company leadership, subsidiaries, SCI pyramid tracing |
| **MeilleursAgents** | `https://www.meilleursagents.com/` | Per-address price estimates |

## Workflow

### Step 1: Reverse Geocode GPS → Address

```bash
curl -s "https://api-adresse.data.gouv.fr/reverse/?lon=LONGITUDE&lat=LATITUDE"
```

Returns a `FeatureCollection` with closest addresses sorted by distance. Key fields:
- `properties.label` — Full address string
- `properties.housenumber`, `properties.street`, `properties.city`, `properties.postcode`
- `properties.citycode` — INSEE commune code (e.g., 95252 for Franconville)
- `properties.context` — "95, Val-d'Oise, Île-de-France"
- `properties.distance` — Meters from GPS pin

**Pitfall:** The closest match may be across a commune boundary. Always check the `city` field — the GPS pin (48.990029, 2.205266) initially looked like Conflans-Sainte-Honorine but resolved to Franconville.

### Step 2: Search DVF Datasets (via MCP data.gouv.fr)

The MCP server uses **Streamable HTTP** transport. Connect with:

```bash
curl -s -X POST "https://mcp.data.gouv.fr/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Required Accept header:** `application/json, text/event-stream` — the server rejects requests that only accept one of the two.

**Key tools (read-only, no auth):**
- `search_datasets(query, page_size)` — Search datasets by keyword
- `get_dataset_info(dataset_id)` — Full metadata for a dataset
- `list_dataset_resources(dataset_id)` — List files in a dataset
- `query_resource_data(resource_id, page, page_size, filter_column, filter_value)` — Query tabular data via Tabular API

**Key dataset IDs for real estate:**
- `5c4ae55a634f4117716d5656` — Demandes de valeurs foncières (raw DVF, DGFiP)
- `5cc1b94a634f4165e96436c1` — Demandes de valeurs foncières **géolocalisées** (enriched, with geo data)
- `62e9bbe102256eedbd0505d1` — Données valeurs foncières à la commune par période (Caisse des Dépôts)

### Step 3: Query Per-Commune DVF+ CSV Files

The enriched geo-DVF dataset publishes **per-commune CSV files** by year:

```
https://files.data.gouv.fr/geo-dvf/latest/csv/{YEAR}/communes/{DEP}/ {COMMUNE_CODE}.csv
```

Example for Franconville (95, code 95252):
```
https://files.data.gouv.fr/geo-dvf/latest/csv/2025/communes/95/95252.csv
```

**CSV columns (key ones):**
```
id_mutation,date_mutation,numero_disposition,nature_mutation,valeur_fonciere,
adresse_numero,adresse_suffixe,adresse_nom_voie,adresse_code_voie,
code_postal,code_commune,nom_commune,code_departement,
id_parcelle,lot1_numero,lot1_surface_carrez,...nombre_lots,
code_type_local,type_local,surface_reelle_bati,
nombre_pieces_principales,surface_terrain,longitude,latitude
```

**Search patterns:**
```bash
# All transactions on a specific street
grep -i "LECLERC" 95252.csv

# All transactions at a specific house number
grep "LECLERC" 95252.csv | awk -F',' '$6 == "368"'

# Transactions near GPS coordinates (within ~50m box)
awk -F',' '{lon=$NF-1; lat=$NF; if(lon>=2.203&&lon<=2.208&&lat>=48.987&&lat<=48.992) print}'
```

**Pitfall:** Street names use abbreviations in DVF (e.g., "RUE DU GAL LECLERC" not "Rue du Général Leclerc"). Search with partial matches.

**Pitfall:** No transactions at an address between 2021-2025 means either (a) the property hasn't changed hands, (b) it was sold before 2021 (check earlier years if available), or (c) the building doesn't have a separate cadastre registration at that number.

### Step 4: Look Up Businesses at the Address

```bash
# Via Annuaire des Entreprises (search by address)
https://annuaire-entreprises.data.gouv.fr/etablissement/{SIRET}
# Or search by address: https://annuaire-entreprises.data.gouv.fr/rechercher?terme=368+Rue+du+General+Leclerc

# Via Historique Adresses
https://www.historiqueadresses.com/{ADDRESS_SLUG}
```

This reveals:
- What businesses are/were registered at the address
- Their legal form (SAS, SARL, SCI...)
- When they started/stopped
- SIRET, NAF/APE code (activity type)
- Contact info (phone, website)

**NAF codes for property research:**
- `68.20B` — Location de terrains et biens immobiliers
- `68.10Z` — Activités des marchands de biens immobiliers
- `41.10D` — Supports juridiques de programmes (SCI de construction)
- `56.10A` — Restauration traditionnelle (commercial tenant)

### Step 5: Check Company Leadership

```bash
# Pappers — free company details
https://www.pappers.fr/entreprise/{SIREN}
https://www.pappers.fr/dirigeant/{NAME}_{BIRTH_YEAR-MONTH}

# Societe.com — registry info
https://www.societe.com/societe/{NAME}-{SIREN}.html
```

Reveals:
- Legal form (SCI, SAS...)
- Directors/partners
- Creation date
- Share capital
- Address (may differ from the property address — SCI often domiciled elsewhere)

### Step 6: Cross-Reference with Transaction Data

Compare:
- **No recent DVF transaction** → property likely long-held or never sold recently
- **Massive nearby transactions** (e.g., 16M€ commercial sale at adjacent number) → the zone is commercial/industrial, not residential
- **Multi-tenant building with diverse businesses** → likely a commercial retail park or centre commercial

### Step 6a: Check BODACC Legal Announcements

The **BODACC** (Bulletin Officiel des Annonces Civiles et Commerciales) publishes legal announcements for French companies — address changes, director changes, creations, liquidations.

**Search by SIREN:**
```
https://www.bodacc.fr/pages/annonces-commerciales/?q.registre=registre:{SIREN}
```

**Direct announcement links** (from Pappers or Annuaire-entreprises):
```
https://www.bodacc.fr/annonce/detail-annonce/{TYPE}/{YEAR}{NUMBER}/{ANNOUNCE_ID}
```
Where TYPE = A (creations), B (modifications), C (comptes annuels)

**What BODACC reveals that other sources may miss:**
- Date the company actually started activity (often months after creation)
- Address changes (J&F COMPANY moved from Le Blanc-Mesnil → Villemomble in 2019)
- "Société n'exerce aucune activité" — confirms a dormant period
- Director change dates with precision (day-level accuracy)
- Radiation (deregistration)

**Pitfall:** BODACC announcements have confidentiality declarations for financial accounts — don't expect to see revenue/profit data there for most SAS/SARL.

### Step 7: Trace the Corporate Pyramid

Docker-compose-style corporate tree. A restaurant at an address may be operated by:

```
BENEFICIAL OWNER (individual, e.g., Jun CHEN)
    ↓ Président / associé
HOLDING (e.g., J&F COMPANY, often at a different address)
    ↓ Président
OPERATING COMPANY (e.g., GROUPE PACIFIC, at the restaurant address)
    ↓ exploite
RESTAURANT (enseigne, e.g., RESTAURANT PACIFIC)
```

**How to trace:**
1. Find the operating company via `annuaire-entreprises` (step 4)
2. Get its SIREN, check the "Président" field — it's often another company (the holding)
3. Look up the holding on Pappers (step 5) to find:
   - Its own directors (the actual people)
   - Other companies it controls (sister companies, other restaurants)
   - Its address (usually *not* at the property address — prove separation)
4. Check the holding's SIREN on Pappers for "Entreprises dirigées" (subsidiaries section)

**Signal for tenant vs. owner:** If the holding/operating company is registered at a *different* address than the property, and doesn't have real estate in its NAF code, it's almost certainly renting. If CZ IMMO or 6 PSM exist as sister companies (real-estate vehicles), they may own the property — check their address.

### Step 7a: Social Media & Web Cross-Reference

Cross-check the address and business name on social media to verify active operations:
- TikTok videos geotagged or mentioning the address
- Google Maps reviews
- Delivery platforms (Uber Eats, Deliveroo)

This confirms the business is actually operating and not just registered at the address.

### Step 8: Cross-Reference with Other Tenants at Same Address

Check ALL businesses at the address (via historiqueadresses.com or annuaire-entreprises). Multiple unrelated businesses at one address → commercial rental building (centre commercial / retail park). Each business is independently renting from a landlord.

**Key questions:**
- Do any of the other tenants share the same corporate umbrella? (→ owner-occupied)
- Are they all independent? (→ rental with a third-party landlord)
- Are any in financial difficulty? (liquidation/redressement judiciaire → the lease may be available)

### Determining Rental vs. Ownership

A multi-signal assessment:

| Signal | Renting | Owning |
|--------|---------|--------|
| Multi-tenant building (4+ businesses) | ✅ Strong | ❌ Unlikely |
| Capital < 100K€ | ✅ | ❌ |
| Président/holding at different address | ✅ | ❌ |
| No DVF transaction for the address | Neutral | Neutral |
| Sister real-estate company (CZ IMMO, SCI, etc.) | — | ✅ Possible |
| Operating company NAF ≠ real estate | ✅ | ❌ |
| Bilan shows no immobilier corporel | ✅ | ❌ |

### Step 9: MeilleursAgents Price Estimate

```
https://www.meilleursagents.com/prix-immobilier/{CITY}-{POSTCODE}/rue-du-{STREET}-{ID}/{NUMBER}/
```

Example:
```
https://www.meilleursagents.com/prix-immobilier/franconville-95130/rue-du-general-leclerc-2124895/368/
```

Provides estimated price per m² for the specific address where available.

## Limitations

1. **Propriétaires non disponibles en open data.** Les fichiers fonciers MAJIC (qui listent les noms des propriétaires) sont en accès restreint aux services publics (État, collectivités, EPF, SAFER, ADIL, etc.). Impossible d'identifier le propriétaire d'un bien via les APIs ouvertes.

2. **DVF only covers transactions from 2014+** (when the open data mandate started). No pre-2014 history.

3. **Alsace, Moselle, Mayotte** — DVF data does NOT cover these areas (specific cadastre regimes).

4. **Per-commune CSVs are large** (500MB+ full file for all of France). Only query per-commune files for your target commune.

5. **DVF does not include rental data** — only property *sales* transactions. No rental prices, lease info, or owner contact.

## Tools vs Data Sources Summary

| Data you want | Source | Access |
|--------------|--------|--------|
| Address from GPS | BAN API (`api-adresse.data.gouv.fr/reverse/`) | ✅ Free, open |
| Sales transactions (type, price, date, surface) | Geo-DVF CSV per commune | ✅ Free, open |
| Businesses at address | Annuaire des Entreprises | ✅ Free, open |
| Company directors & SCI info | Pappers / Societe.com | ✅ Free (basic info) |
| Property owner name | MAJIC / Fichiers fonciers | 🔒 Restricted (public service only) |
| Cadastre parcel boundaries | PCI Vecteur (data.gouv.fr) | ✅ Free, open |
| Current rental listings | Le-Partenaire, PAP, seloger | ✅ Scrapable |
| Current market value estimate | MeilleursAgents, DVF comparables | ✅ Partial (web scrape) |
