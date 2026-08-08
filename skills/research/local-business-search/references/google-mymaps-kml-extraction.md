# Extracting Location Data from Google My Maps KML Embeds

## When to use

OSM/Overpass doesn't always have niche business categories (e.g. self-service
dog wash stations, specialty franchise locations). Many chains and networks
publish their locations as an embedded Google My Maps on their website. You can
extract the full dataset as KML and parse it programmatically.

## Technique

### 1. Find the embed URL

Look at the page that shows the locations map (usually a "Nos emplacements" or
"Find a store" page). The map is typically an `<iframe>` pointing to:

```
https://www.google.com/maps/d/u/5/embed?mid=<MAP_ID>&...
```

Extract the `mid` parameter — that's the map ID.

### 2. Fetch the KML

```
https://www.google.com/maps/d/u/5/kml?mid=<MAP_ID>&forcekml=1
```

This returns a full KML XML document with all placemarks, addresses,
coordinates, and extended data.

### 3. Parse and filter

```python
import xml.etree.ElementTree as ET
import math

tree = ET.parse('data.kml')
root = tree.getroot()
ns = {'k': 'http://www.opengis.net/kml/2.2'}

ref_lat, ref_lng = 49.4944, 0.1076  # your reference point

for pm in root.findall('.//k:Placemark', ns):
    name = pm.find('k:name', ns).text
    ext = {}
    for d in pm.findall('.//k:Data', ns):
        key = d.get('name')
        val = d.find('k:value', ns)
        if val is not None:
            ext[key] = val.text or ''
    addr = ext.get('address', '')
    city = ext.get('city', '')
    zip_code = ext.get('zip', '')
    lat = float(ext.get('lat', '0') or '0')
    lng = float(ext.get('lng', '0') or '0')
    dist_km = math.sqrt((lat - ref_lat)**2 + (lng - ref_lng)**2) * 111
    if dist_km < 150:  # filter by radius
        print(f'{name} — {round(dist_km,1)} km — {addr}, {city} ({zip_code})')
```

### Real example: Dogwash.fr

Dogwash.fr (dogwash.fr/emplacements-dogwash-et-stations-lavage-canin/) embeds
a Google My Maps with 130+ stations. The KML URL is:

```
https://www.google.com/maps/d/u/5/kml?mid=19US-ejjnglFBewQgSbdpzVbBNpmL-5I&forcekml=1
```

Each placemark has: name, address, city, zip, lat, lng in ExtendedData.

Results near Le Havre (extracted 2026-08-03):
- **Desjardins Montivilliers** — 9.9 km — 1 Rue des Quatre Saisons, Montivilliers (76290)
- **Desjardins Trouville** — 55.4 km — 84 Route de Fauville, Trouville Alliquerville (76210)
- **Jardiland Dieppe** — 116.5 km — 55 Route de Paris, Saint-Aubin-sur-Scie (76550)

### Other networks using Google My Maps

Known franchise networks that publish locations this way:
- Dogwash (dogwash.fr) — 130+ dog wash stations across France
- Various garden centers (Jardiland, Truffaut, Tom&Co) host Dogwash stations
- Wash Dog Box (washdogbox.com) — separate network, check their site

## Pitfalls

- The KML URL uses `/kml?` not `/embed?` — just swap the path and add `forcekml=1`.
- Some maps may require the `u/5/` user context; others work without it. Try both.
- Coordinates in ExtendedData `lat`/`lng` fields may be strings — cast to float.
- The `address` field in `<address>` is separate from `ExtendedData/Data[@name="address"]` — check both.
- Google may rate-limit or require authentication for very large maps; for 130-200 placemarks it works fine with curl.
- Always cross-reference with a web search or the business's own page to confirm the location is still current.