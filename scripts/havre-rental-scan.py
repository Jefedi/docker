#!/usr/bin/env python3
"""Scrape Leboncoin + SeLoger for Le Havre T2+ rentals in Centre-ville, Bléville, Saint-Vincent.
Filters: T2 minimum, target neighbourhoods only, cheapest first.
Outputs JSON to stdout. Stays silent (empty output) when no new matches found.
"""
import json, re, sys, urllib.request, urllib.parse, os
from datetime import datetime

# --- Config ---
TARGET_AREAS = [
    "centre-ville", "centre ville", "arcole", "brindeau", "anatole france",
    "saint-vincent", "saint vincent", "st vincent",
    "bleville", "bléville", "nautick",
]
MIN_ROOMS = 2
MAX_PRICE = 800  # soft cap, we want cheapest

# Previously seen IDs (stored in /tmp)
SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(ids):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)

def matches_area(text):
    text_lower = text.lower()
    return any(area in text_lower for area in TARGET_AREAS)

def extract_leboncoin():
    """Extract listings from Leboncoin search results page."""
    url = "https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-800&rooms=2-"
    results = []
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        # Extract ad links and surrounding text
        # Pattern: /ad/locations/XXXXX
        ad_ids = re.findall(r'/ad/locations/(\d+)', html)
        
        # Extract price patterns like "575 €" or "575€"
        prices = re.findall(r'(?:Prix:\s*)?(\d{3,4})\s*€', html)
        
        # Extract room/surface patterns
        rooms = re.findall(r'(\d+)\s*pièces', html)
        surfaces = re.findall(r'(\d+(?:,\d+)?)\s*m²', html)
        
        # Extract neighbourhoods
        areas = re.findall(r'Le Havre 76600\s+([^\n<]+?)(?:\n|<)', html)
        
        # Also look for "Centre-ville", "Saint-Vincent", "Bléville" directly
        area_matches = re.findall(r'(?:Le Havre 76600|Le Havre \(76600\))\s+([A-Za-zÀ-ÿ\s\-]+)', html)
        
        for i, ad_id in enumerate(ad_ids):
            price = int(prices[i]) if i < len(prices) else 0
            room_count = int(rooms[i]) if i < len(rooms) else 0
            surface = surfaces[i] if i < len(surfaces) else "?"
            area = areas[i].strip() if i < len(areas) else ""
            
            if room_count < MIN_ROOMS or price > MAX_PRICE:
                continue
            if not matches_area(area):
                continue
            
            results.append({
                "id": f"lbc_{ad_id}",
                "source": "leboncoin",
                "url": f"https://www.leboncoin.fr/ad/locations/{ad_id}",
                "price": price,
                "rooms": room_count,
                "surface": surface,
                "area": area,
                "title": f"T{room_count} {surface}m² — {area}"
            })
    except Exception as e:
        print(f"[leboncoin error: {e}]", file=sys.stderr)
    
    return results

def extract_seloger():
    """Extract from SeLoger search URLs for target neighbourhoods."""
    urls = {
        "centre-ville": "https://www.seloger.com/recherche/location/appartement/le-havre-76600/centre-ville-76600/nbh2fr6210",
        "saint-vincent": "https://www.seloger.com/recherche/location/appartement/le-havre-76600/saint-vincent-76600/nbh2fr6211",
        "bleville": "https://www.seloger.com/recherche/location/appartement/le-havre-76600/bleville-76620/nbh2fr6221",
    }
    results = []
    
    for area_name, url in urls.items():
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            
            # Extract listing IDs from seloger URLs
            ids = re.findall(r'/annonces/locations/appartement/le-havre-76/[^/]+/(\d+)\.htm', html)
            prices = re.findall(r'(\d{3,4})\s*€/mois', html)
            rooms = re.findall(r'(\d+)\s*pièces', html)
            surfaces = re.findall(r'(\d+(?:[.,]\d+)?)\s*m²', html)
            
            seen_ids = set()
            for i, listing_id in enumerate(ids):
                if listing_id in seen_ids:
                    continue
                seen_ids.add(listing_id)
                
                price = int(prices[i]) if i < len(prices) else 0
                room_count = int(rooms[i]) if i < len(rooms) else 0
                surface = surfaces[i] if i < len(surfaces) else "?"
                
                if room_count < MIN_ROOMS or price > MAX_PRICE:
                    continue
                
                results.append({
                    "id": f"slg_{listing_id}",
                    "source": "seloger",
                    "url": f"https://www.seloger.com/annonces/locations/appartement/le-havre-76/{listing_id}.htm",
                    "price": price,
                    "rooms": room_count,
                    "surface": surface,
                    "area": area_name,
                    "title": f"T{room_count} {surface}m² — {area_name}"
                })
        except Exception as e:
            print(f"[seloger {area_name} error: {e}]", file=sys.stderr)
    
    return results

def main():
    all_results = extract_leboncoin() + extract_seloger()
    
    # Sort by price (cheapest first)
    all_results.sort(key=lambda x: x["price"])
    
    seen = load_seen()
    new_results = [r for r in all_results if r["id"] not in seen]
    
    if not new_results:
        # Stay silent — nothing to report
        print("")
        return
    
    # Output new results as JSON
    print(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "new_count": len(new_results),
        "total_count": len(all_results),
        "new_listings": new_results
    }, ensure_ascii=False, indent=2))
    
    # Update seen
    all_ids = set(r["id"] for r in all_results) | seen
    save_seen(all_ids)

if __name__ == "__main__":
    main()