import json, subprocess, sys, time

TAB = "400718c1-768b-46c4-ab9d-c74f757bfa58"

# Use the known unique links from the previous extraction
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
unique_links = ["https://www.leboncoin.fr/ad/locations/"+x for x in unique_links_str.strip().split("\n")]

print(f"Total unique ad links: {len(unique_links)}", file=sys.stderr)

results = []
for i in range(35):
    expr = f"document.querySelectorAll('article')[{i}].innerText.replace(/\\n/g,' ')"
    r = subprocess.run(["curl", "-s", "-X", "POST", f"http://127.0.0.1:9377/tabs/{TAB}/evaluate",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"userId":"hermes-veille","expression":expr})
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        if "result" in d:
            results.append({"idx": i, "link": unique_links[i] if i < len(unique_links) else "", "text": d["result"]})
        else:
            results.append({"idx": i, "link": unique_links[i] if i < len(unique_links) else "", "text": "ERROR:" + r.stdout[:200]})
    except:
        results.append({"idx": i, "link": unique_links[i] if i < len(unique_links) else "", "text": "PARSE_ERROR"})

# Save to file
with open("/opt/data/tmp/lbc_all_articles.json","w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print summary
for r in results:
    print(f"--- #{r['idx']} ---")
    print(f"Link: {r['link']}")
    print(f"Text: {r['text'][:400]}")
    print()