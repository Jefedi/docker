---
name: transportation-open-data
description: "Traffic light timing and mobility open data research."
---

# Transportation & Mobility Open Data Research

## When to use

- User asks about traffic light prediction, green wave optimization, or route planning that accounts for signal timing
- User wants to know what transportation/traffic data is available as open data in France or Europe
- User asks about real-time traffic conditions data from government sources
- User wants to build an app that uses traffic signal or road condition data
- Trigger words: feux, traffic light, SPaT, DATEX, trafic temps réel, circulation, mobilité, transport open data, green wave, onde verte, GLOSA, carrefour à feux, signalisation lumineuse

## Key distinction: Traffic STATE vs Signal TIMING

The most common confusion is between two completely different data types:

| Data type | Standard | What it tells you | Update freq | France availability |
|---|---|---|---|---|
| **Traffic state** | DATEX II | "This road segment is congested, avg speed 12 km/h" | 1–6 min | ✅ Published (national + some cities) |
| **Signal phase & timing (SPaT)** | SAE J2735 / ETSI SPATEM | "This light is green, turns red in 23 seconds" | 1–10 sec | ❌ Not published anywhere in France |

**Users almost always want SPaT. France only publishes traffic state. This gap is the core finding to communicate.**

## French government data sources

### National — transport.data.gouv.fr / Bison Futé
- **Dataset**: "État de circulation en temps réel sur le réseau national routier non concédé"
- **URL**: https://www.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede
- **Format**: DATEX II (XML), speeds + flow + traffic state
- **Refresh**: every 6 minutes
- **Coverage**: national non-conceded network + Traficolor for 21 large agglomérations
- **Traficolor cities**: Bordeaux, Brive, Caen, Calais, Clermont-Ferrand, Grenoble, Lille, Limoges, Lyon, Marseille, Metz, Montpellier, Mulhouse, Nancy, Nantes, Paris, Rennes, Rouen, Saint-Étienne, Strasbourg, Toulouse
- **Le Havre is NOT in Traficolor**

### City-level — Bordeaux Métropole (most advanced in France)
- **Portal**: https://datahub.bordeaux-metropole.fr/
- **Datasets** (see references/france-traffic-data.md for full details):
  - `ci_trafi_l` — traffic state per segment, refresh 1 min, 687 segments
  - `ci_courb_a` — traffic volume curves, refresh 10 min
  - `ci_tpstj_a` — travel times, real-time
  - `pc_carf_p` — inventory of 1,326 signalized intersections (816 centralized, 342 local, 96 TETRA, 106 SAEIV, 73 JALDYN adaptive)
- All have API endpoints (OpenDataSoft platform)

### City-level — Rennes Métropole
- **URL**: https://www.data.gouv.fr/datasets/etat-du-trafic-en-temps-reel
- Speed, travel time, traffic status per segment, ~3 min delay

### City-level — Paris
- Signal inventory only (positions, luminaire types, power) — NO timing data
- https://www.data.gouv.fr/datasets/signalisation-lumineuse-tricolore

### Le Havre Seine Métropole
- Portal exists: https://data.lehavreseinemetropole.fr/
- **169 datasets** total, but **zero real-time traffic data**
- 17 "Voirie transport" datasets exist but all are static (semestrielle/annuelle): stationnement, réseau cyclable, règlement circulation, zones apaisées, etc.
- No signal inventory, no traffic state, no SPaT
- API is undocumented but discoverable (see references/le-havre-catalog.md for full catalog + API extraction method)

## European SPaT deployments (where it actually works)

### Germany — Signal2X (Yunex Traffic / ex-Siemens)
- App (iOS + Android) deployed in Darmstadt and other cities
- All city traffic lights equipped with forecast service
- Gives speed recommendation to catch green, or countdown if red unavoidable
- Proprietary but demonstrates the concept at scale

### Belgium — Open Traffic Lights (Antwerp) — OPEN SOURCE
- **Project**: https://opentrafficlights.org/
- Intersection in Antwerp publishes SPaT as Linked Open Data (RDF)
- Prediction research: median-based frequency distribution achieves ~5s MAE for phases <1 min
- **Data repo**: https://github.com/kridhaen/OpenTrafficLightsData
- **Demo code**: https://codepen.io/kridhaen/pen/VJrezO/
- Prediction degrades linearly for phases >1 min (unusable without detector data)

### Netherlands — most advanced
- Dutch SPaT profile MANDATES server-side predicted duration calculation
- Client receives "light turns red in 23s" directly — no client-side prediction needed

### European C-ITS program (C-ROADS)
- France participates with 13 beneficiaries but SPaT broadcast not yet operational in open data
- ITS-G5 standard for vehicle-to-infrastructure communication
- Report: https://www.c-roads.eu/ (annual deployment overview)

## Open source building blocks

| Component | Project | License |
|---|---|---|
| SPaT publication spec | Open Traffic Lights ontology | Open |
| Historical data + prediction | github.com/kridhaen/OpenTrafficLightsData | Open |
| GLOSA mobile app | github.com/EastpointSoftware/glosa-mobile | Open |
| Client-side routing | Planner.js (planner.js.org) | MIT |
| AI traffic light controller | Reddit r/selfhosted Jetson project | Open |

## Pitfalls

- **DO NOT answer "no" without checking government portals first.** The user expects thorough exploration before any negative answer. Always search data.gouv.fr, transport.data.gouv.fr, and city-specific open data portals before concluding data is unavailable.
- **Traffic state ≠ signal timing.** Users asking about "predicting traffic lights" want SPaT, not DATEX II traffic state. Don't conflate the two.
- **Adaptive signals are harder to predict.** Feux adaptatifs (tram priority, detector-driven) have variable phase durations. Prediction error grows linearly for phases >1 min without detector data access.
- **Le Havre has no traffic open data.** The portal exists but is empty on circulation. A CADA request could force publication since the infrastructure (centralized controllers) likely exists internally.

## CADA request approach

If user wants to push a French city to publish traffic/signal data:
1. **CADA** (Commission d'Accès aux Documents Administratifs) — formal request
2. Cities with centralized signal controllers (like Bordeaux's 816 centralized intersections) already have the data internally
3. The LOM law (Loi d'Orientation des Mobilités, 2019) mandates opening mobility data — traffic signal data arguably falls under this
4. Reference: transport.data.gouv.fr as the existing national platform for publication

## Reverse-engineering French open data portals

Many French city portals are custom jQuery SPAs (not OpenDataSoft/CKAN) with no visible API docs. To extract the full catalog:

1. Open the portal in browser, inspect pagination links — they often call a JS function like `afficheData(query, theme, offset, limit)`
2. Find the function definition in the minified JS (`/js/script.min.js` or similar)
3. Extract the API URL pattern (usually `api/v1/datas/search/{q}/theme/{t}/?offset={n}&limit={n}`)
4. Call the API directly via `curl` — response may be **XML** even if the JS uses `$.getJSON` (jQuery auto-parses based on Content-Type)
5. Use `%20` for spaces in path segments
6. Parse with `xml.etree.ElementTree` in Python

**Pitfall**: `browser_console` expression evaluation may fail with 500 errors when processing large JSON/XML responses (size limit). Fall back to `terminal` with `curl` + file output + Python parsing.

**Pitfall**: `execute_code` may be blocked in cron-like contexts. Use `terminal` with `curl -s -o /tmp/file` then separate Python parse command.

## References

- `references/france-traffic-data.md` — detailed dataset schemas, API endpoints, field descriptions for Bordeaux and national datasets
- `references/le-havre-catalog.md` — full 169-dataset catalog of Le Havre Seine Métropole, including API discovery technique