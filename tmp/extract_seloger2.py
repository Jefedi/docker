import json, subprocess, sys, time, re

TAB = "400718c1-768b-46c4-ab9d-c74f757bfa58"

def evaluate(expr):
    r = subprocess.run(["curl", "-s", "-X", "POST", f"http://127.0.0.1:9377/tabs/{TAB}/evaluate",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"userId":"hermes-veille","expression":expr})
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        return d.get("result","")
    except:
        return ""

# Wait for page load
time.sleep(4)

# Scroll to load all listings
for i in range(15):
    evaluate(f"window.scrollBy(0,{(i+1)*1000})")
    time.sleep(0.8)

# Get all listing links
links_str = evaluate("Array.from(document.querySelectorAll('a')).filter(a=>a.href.includes('seloger.com/annonces/')).map(a=>a.href).join('\\n')")
# Also get the full inner text
total_len = int(evaluate("document.body.innerText.length") or "0")
print(f"Total innerText length: {total_len}")

full_text = ""
chunk_size = 4000
for start in range(0, total_len, chunk_size):
    chunk = evaluate(f"document.body.innerText.substring({start},{start+chunk_size})")
    if chunk:
        full_text += chunk

with open("/opt/data/tmp/seloger_centre_full.txt","w") as f:
    f.write(full_text)

# Parse the links
links = [l for l in links_str.split("\n") if l.strip()]
# dedupe
seen_links = set()
unique_links = []
for l in links:
    base = l.split("?")[0]
    if base not in seen_links:
        seen_links.add(base)
        unique_links.append(base)

with open("/opt/data/tmp/seloger_links.json","w") as f:
    json.dump(unique_links, f, indent=2)

print(f"Unique links: {len(unique_links)}")
for l in unique_links:
    print(l)

# Now parse the text into listings
# SeLoger text format:
# DPE letter (single char)  price € /mois charges comprises  ...  Type à louer  N pièces  ·  N chambre  ·  XX m²  ·  Étage X  Quartier, Le Havre (76600)  Agency

# Split by listing pattern - each starts with a photo count "1 / N" or DPE letter
lines = full_text.split("\n")
listings = []
current = []
in_listing = False

for line in lines:
    line = line.strip()
    if not line:
        continue
    # Detect start of new listing: "N / M" photo indicator or DPE letter
    if re.match(r'^\d+\s*/\s*\d+$', line):
        if current:
            listings.append(" | ".join(current))
        current = [line]
        in_listing = True
    elif in_listing:
        current.append(line)

if current:
    listings.append(" | ".join(current))

print(f"\nParsed {len(listings)} listings from text")
for i, l in enumerate(listings[:30]):
    print(f"--- Listing {i} ---")
    print(l[:300])
    print()