#!/usr/bin/env python3
"""
Batch ingest URLs from a sitemap into the RAG knowledge base.
Fetches sitemap, filters URLs, POSTs each to the n8n auto-ingest webhook.

Usage:
    python3 batch-ingest-sitemap.py https://www.home-assistant.io/sitemap.xml /docs/ docs
    python3 batch-ingest-sitemap.py https://www.home-assistant.io/sitemap.xml /integrations/ integrations

Arguments:
    sitemap_url  — URL of the sitemap XML
    url_filter   — substring to filter URLs (e.g. /docs/ or /integrations/)
    category     — category label for all ingested docs
"""

import sys
import json
import urllib.request
import time
import re

def fetch_sitemap(sitemap_url):
    """Fetch and parse sitemap XML, return list of URLs."""
    resp = urllib.request.urlopen(sitemap_url, timeout=30)
    xml = resp.read().decode()
    urls = re.findall(r'<loc>([^<]+)</loc>', xml)
    return urls

def ingest_url(url, category, webhook_url="http://localhost:5678/webhook/rag-ha-ingest-url"):
    """POST a single URL to the n8n auto-ingest webhook."""
    payload = json.dumps({"url": url, "category": category}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=90)
    return json.loads(resp.read())

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <sitemap_url> <url_filter> <category>")
        sys.exit(1)

    sitemap_url = sys.argv[1]
    url_filter = sys.argv[2]
    category = sys.argv[3]

    print(f"Fetching sitemap: {sitemap_url}")
    all_urls = fetch_sitemap(sitemap_url)
    print(f"Total URLs in sitemap: {len(all_urls)}")

    filtered = [u for u in all_urls if url_filter in u]
    print(f"Filtered URLs ({url_filter}): {len(filtered)}")

    success = 0
    failed = 0
    errors = []

    for i, url in enumerate(filtered):
        try:
            result = ingest_url(url, category)
            chunks = result.get("chunks_stored", 0)
            success += 1
            if (i + 1) % 10 == 0:
                print(f"[{i+1}/{len(filtered)}] {success} OK, {failed} FAIL")
        except Exception as e:
            failed += 1
            errors.append({"url": url, "error": str(e)[:80]})

        time.sleep(0.3)

    print(f"\nFINAL: {success} success, {failed} failed out of {len(filtered)}")
    if errors:
        print("\nFailed URLs (first 10):")
        for e in errors[:10]:
            print(f"  {e['url']} - {e['error']}")

if __name__ == "__main__":
    main()