import json, subprocess, sys, time

TAB = "400718c1-768b-46c4-ab9d-c74f757bfa58"

unique_links_str = """3245913837
3245819710
3114599423
3225885761
3245699657
3206014055
2978416071
3171888088
3245646772
3245645303
3236957272
3214369980
3020670214
3240426512
3213020854
3008426681
3245402762
3245333098
3166993605
3245020013
2932371645
3225853352
3223323830
3242301814
3244834386
3244831124
3244828763
3244825216
3244820840
3183706861
3229591468
3237764951
3229817725
3197373339
3244321696"""
unique_ids = unique_links_str.strip().split("\n")
unique_links = ["https://www.leboncoin.fr/ad/locations/"+x for x in unique_ids]

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

# Scroll the main content area to force lazy loading
# Leboncoin uses a scroll container. Let's scroll window and the scroll container
for scroll_step in range(20):
    evaluate(f"window.scrollBy(0,{(scroll_step+1)*500})")
    time.sleep(0.5)

# Now try extracting articles
all_texts = {}
for i in range(35):
    text = evaluate(f"document.querySelectorAll('article')[{i}]?.innerText?.replace(/\\n/g,' ')||''")
    if text and len(text) > 20:
        all_texts[i] = text
    else:
        # Try scrolling to this article
        evaluate(f"document.querySelectorAll('article')[{i}]?.scrollIntoView()")
        time.sleep(1)
        text = evaluate(f"document.querySelectorAll('article')[{i}]?.innerText?.replace(/\\n/g,' ')||''")
        if text and len(text) > 20:
            all_texts[i] = text

print(f"Extracted {len(all_texts)} articles with text", file=sys.stderr)

results = []
for i in range(35):
    results.append({
        "idx": i,
        "id": unique_ids[i] if i < len(unique_ids) else "",
        "link": unique_links[i] if i < len(unique_links) else "",
        "text": all_texts.get(i, "")
    })

with open("/opt/data/tmp/lbc_all_articles.json","w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

for r in results:
    if r["text"]:
        print(f"--- #{r['idx']} (id:{r['id']}) ---")
        print(f"Text: {r['text'][:400]}")
        print()