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

# SeLoger uses cards with class "card__content" or similar
# Let me first try to find listing articles
count = evaluate("document.querySelectorAll('article').length")
print(f"Articles: {count}")

# Get all the card data
text = evaluate("document.body.innerText")
print(f"Body text length: {len(text)}")

# SeLoger seems to use divs with data attributes. Let's get the full innerText
full_text = ""
for i in range(10):
    full_text += evaluate(f"document.body.innerText")
    # scroll down
    evaluate(f"window.scrollBy(0,{(i+1)*800})")
    time.sleep(1)

# Actually, let's get the text in one go - it might be long
# Let me try getting it in chunks
total_len = int(evaluate("document.body.innerText.length") or "0")
print(f"Total innerText length: {total_len}")

# Save the full text
full = ""
chunk_size = 3000
for start in range(0, min(total_len, 30000), chunk_size):
    chunk = evaluate(f"document.body.innerText.substring({start},{start+chunk_size})")
    if chunk:
        full += chunk

with open("/opt/data/tmp/seloger_centre.txt","w") as f:
    f.write(full)
print(f"Saved {len(full)} chars")
print(full[:3000])