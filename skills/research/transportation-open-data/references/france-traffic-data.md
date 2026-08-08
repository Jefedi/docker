# French Traffic & Mobility Open Data — Detailed Reference

## National — DATEX II traffic state (Bison Futé)

**URL**: https://www.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede

**Producer**: Point d'Accès National transport.data.gouv.fr (ministère des Transports)

**Format**: XML, DATEX II (European standard for traffic data exchange)

**Refresh**: every 6 minutes (aggregated file)

**Content**:
- Average vehicle speed (km/h) per measurement station
- Traffic flow (vehicles/hour)
- Traffic status: fluide, dense, congestionné, impossible, inconnu
- Reference points for station identification

**Traficolor** — aggregated traffic state around 21 agglomerations:
Bordeaux, Brive, Caen, Calais, Clermont-Ferrand, Grenoble, Lille, Limoges, Lyon, Marseille, Metz, Montpellier, Mulhouse, Nancy, Nantes, Paris (Île-de-France), Rennes, Rouen, Saint-Étienne, Strasbourg, Toulouse.

**Note**: Le Havre is NOT covered by Traficolor.

**Related static reference data** (also on data.gouv.fr):
- Network geometry: https://www.data.gouv.fr/fr/datasets/liaisons-du-reseau-routier-national/
- Mileage markers: https://www.data.gouv.fr/fr/datasets/bornage-du-reseau-routier-national/
- Road managers: https://www.data.gouv.fr/fr/datasets/gestionnaires-du-reseau-routier-national/
- Road widths: https://www.data.gouv.fr/fr/datasets/largeur-de-routes-sur-le-reseau-routier-national/
- Road nature: https://www.data.gouv.fr/fr/datasets/nature-des-routes-du-reseau-routier-national/

**DATEX II documentation** by CEREMA:
- http://trafic-routier.data.cerema.fr/la-norme-europeenne-datex-ii-a58.html

---

## Bordeaux Métropole — DataHub (OpenDataSoft platform)

**Portal**: https://datahub.bordeaux-metropole.fr/

### 1. ci_trafi_l — État du trafic en temps réel

**URL**: https://datahub.bordeaux-metropole.fr/explore/dataset/ci_trafi_l/

**Refresh**: 1 minute

**Records**: 687 road segments

**Fields**:
| Field | Type | Description |
|---|---|---|
| `geo_point_2d` | geo_point_2d | Lat/lon coordinates |
| `geo_shape` | geo_shape | LineString geometry of segment |
| `gml_id` | text | GML identifier (e.g. CI_TRAFI_L.2151) |
| `gid` | text | Primary key |
| `ident` | text | Segment identifier (e.g. I83) |
| `typevoie` | text | Road type: BOULEVARDS, QUAIS, COURS, PENETRANTE, A62, A63, A631, A630, N230 |
| `etat` | text | Traffic state: FLUIDE, DENSE, EMBOUTEILLE, PARALYSE, INCONNU |
| `cdate` | datetime | Creation date |
| `mdate` | datetime | Modification date |
| `origine` | text | Data origin (e.g. PC_CIRCULATION) |
| `commune` | text | City name |
| `code_commune` | text | INSEE code |

**API**: Available via OpenDataSoft API (see "API" tab on dataset page)

### 2. ci_courb_a — Courbe de circulation en temps réel

**URL**: https://datahub.bordeaux-metropole.fr/explore/dataset/ci_courb_a/

**Refresh**: 10 minutes (source: 5 min)

**Records**: 193 measurement points

**Fields**:
| Field | Type | Description |
|---|---|---|
| `bm_gid` | int | Primary key |
| `bm_ident` | int | Sensor identifier |
| `bm_heure` | datetime | Timestamp of measurement |
| `bm_actuel` | int | Current traffic volume |
| `bm_reffluid` | int | Reference volume for "fluid" state |
| `bm_refdense` | int | Reference volume for "dense" state |
| `bm_refexcep` | int | Reference volume for "exceptional" state |
| `bm_prevision` | text | Forecast value |
| `bm_cdate` | date | Creation date |
| `bm_mdate` | datetime | Modification date |

### 3. ci_tpstj_a — Temps de parcours en temps réel

**URL**: https://datahub.bordeaux-metropole.fr/explore/dataset/ci_tpstj_a/

**Refresh**: real-time

### 4. pc_carf_p — Carrefour à feux (signalized intersection inventory)

**URL**: https://datahub.bordeaux-metropole.fr/explore/dataset/pc_carf_p/

**Records**: 1,326 intersections (1,023 existing, 303 removed)

**Key fields**:
| Field | Values | Count |
|---|---|---|
| `etat` | EXISTANT, DEPOSE | 1023 / 303 |
| `nature` | CENTRALISE, LOCAL, TETRA | 816 / 342 / 96 |
| `equipeme` | TRAFIC, TRAFIC_TRAM_A/B/C/D, TRAFIC_SAEIV, FEU_CLIGNOTANT, JALDYN, SIREDO, PMV | see below |
| `procedur` | PROCEDURE, CONFORMITE, HORS_PROCEDURE, SANS_FI | 647/294/168/129 |

**Equipment breakdown**:
- TRAFIC: 603 (standard traffic signals)
- TRAFIC_TRAM_A: 125 (tram line A priority)
- TRAFIC_SAEIV: 106 (with real-time traffic management + passenger info)
- TRAFIC_TRAM_B: 93
- FEU_CLIGNOTANT: 85 (flashing only)
- TRAFIC_TRAM_C: 77
- JALDYN: 73 (dynamic/adaptive signals)
- SIREDO: 43
- TRAFIC_TRAM_D: 29
- PMV: 24 (variable message panels)

**This inventory is the closest thing France has to signal infrastructure open data. But it contains NO timing/phase information.**

---

## Rennes Métropole — État du trafic en temps réel

**URL**: https://www.data.gouv.fr/datasets/etat-du-trafic-en-temps-reel

**Source**: Rennes Métropole / Autoroutes Trafic

**Delay**: ~3 minutes

**Fields**:
- `datetime`: ISO 8601 timestamp
- `averageVehicleSpeed`: km/h
- `travelTime`: seconds for segment
- `travelTimeReliability`: 0-100%
- `trafficStatus`: unknown, freeFlow, heavy, congested, impossible

**Downloads**: 576K+ (high reuse)

---

## Paris — Signalisation lumineuse tricolore

**URL**: https://www.data.gouv.fr/datasets/signalisation-lumineuse-tricolore

**Source**: Direction de la Voirie et des Déplacements, Ville de Paris

**Content**: Equipment inventory only — positions, lamp types, power ratings, support materials, supplier IDs. Extracted from GMAO (maintenance management system).

**NO timing, phase, or real-time state data.**

---

## Le Havre Seine Métropole — Open Data Portal

**URL**: https://data.lehavreseinemetropole.fr/

**Status**: Portal exists with general open data framework (Licence ODbL). However, as of July 2026, no datasets related to traffic, circulation, signalisation, or mobility are published.

**Implication**: The city likely operates centralized signal controllers internally (standard French métropole practice), but does not expose this data. A CADA (Commission d'Accès aux Documents Administratifs) request could be filed to force publication.

---

## Key standards reference

### SPaT (Signal Phase and Timing)
- SAE J2735 standard (US) / ETSI SPATEM (Europe)
- Contains: current phase, min/max time to change, sometimes predicted time
- Broadcast at 10 Hz in full deployments
- NOT deployed in open data anywhere in France as of 2026

### DATEX II
- European standard for traffic information exchange (CEN/TS 16157)
- XML-based
- Used by French government for national traffic data publication
- Covers: traffic state, speeds, flow, incidents, road conditions
- Does NOT cover individual signal phase/timing

### GTFS / GTFS-RT
- Transit schedule and real-time data standard
- Published by many French transit authorities via transport.data.gouv.fr
- Separate from road traffic data

### SIRI
- Service Interface for Real-time Information (EU standard for transit)
- Used by Bordeaux Métropole for bus/tram real-time
- Not applicable to traffic signals