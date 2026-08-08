#!/usr/bin/env python3
"""Aspire toutes les pages de la doc Pangolin depuis llms.txt"""
import re, time, os, sys, urllib.request

URL = "https://docs.pangolin.net/llms.txt"
REF_DIR = os.path.expanduser("~/skills/pangolin/references")
os.makedirs(REF_DIR, exist_ok=True)

# Fetch index
req = urllib.request.Request(URL, headers={"User-Agent": "Hermes-Agent/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    content = resp.read().decode("utf-8")

# Extract all .md URLs
url_pattern = re.compile(r'https://docs\.pangolin\.net/[^\s\)]+\.md')
urls = url_pattern.findall(content)
seen = set()
unique = []
for u in urls:
    if u not in seen:
        seen.add(u)
        unique.append(u)

print(f"Total URLs: {len(unique)}")

failures = []
successes = 0
total_bytes = 0

for i, page_url in enumerate(unique):
    path = page_url.replace("https://docs.pangolin.net/", "")
    filename = path.replace("/", "__")
    filepath = os.path.join(REF_DIR, filename)

    try:
        req = urllib.request.Request(page_url, headers={"User-Agent": "Hermes-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            text = body.decode("utf-8", errors="replace")

            if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
                failures.append((page_url, "HTML instead of markdown"))
                print(f"  [FAIL-HTML] {page_url}")
            else:
                with open(filepath, "w") as f:
                    f.write(text)
                total_bytes += len(body)
                successes += 1
                if (i+1) % 20 == 0:
                    print(f"  [{i+1}/{len(unique)}] {successes} OK, {len(failures)} failed, {total_bytes//1024}KB")
    except Exception as e:
        failures.append((page_url, str(e)[:100]))
        print(f"  [FAIL] {page_url}: {e}")

    if i < len(unique) - 1:
        time.sleep(0.3)

print(f"\n=== DONE ===")
print(f"Success: {successes}/{len(unique)}")
print(f"Failures: {len(failures)}")
print(f"Total: {total_bytes} bytes ({total_bytes/1024/1024:.1f} MB)")
if failures:
    print("Failed pages:")
    for url, reason in failures:
        print(f"  - {url}: {reason}")