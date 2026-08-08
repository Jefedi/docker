---
name: firecrawl
description: "Web scraping with Firecrawl: scrape single URLs, crawl full sites, search + scrape, map, batch scrape, and LLM extraction. Python SDK, curl, and Hermes integration."
version: 1.0.0
author: Agent
tags: [scraping, crawling, firecrawl, web-extraction, data-collection]
---

# Firecrawl — Web Scraping for AI Agents

**Firecrawl** is a web scraping API that turns websites into clean Markdown, HTML, or structured data ready for LLMs. It handles JavaScript-rendered pages, supports full-site crawling, search-with-scrape, and LLM-based field extraction.

## Quick Start

```bash
pip install firecrawl-py
```

Get a free API key at https://firecrawl.dev (500 credits/mo, no credit card).

## Python SDK Basics

```python
from firecrawl import Firecrawl

# Auto-reads FIRECRAWL_API_KEY from env, or pass explicitly:
fc = Firecrawl(api_key="fc-YOUR-KEY")

# Scrape one page
doc = fc.scrape("https://example.com", formats=["markdown"])
print(doc.markdown)

# Crawl a full site
job = fc.crawl("https://example.com", limit=25)
for d in job.data:
    print(d.metadata.source_url)

# Search + auto-scrape results
results = fc.search("query", scrape_options={"formats": ["markdown"]})
```

## Key Endpoints

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/v2/scrape` | POST | Scrape one URL (markdown, html, extract, screenshot) |
| `/v2/crawl` | POST | Crawl a site; returns job ID, poll via `GET /v2/crawl/{id}` |
| `/v2/search` | POST | Web search with optional auto-scrape of results |
| `/v2/map` | POST | List all URLs on a site |
| `/v2/batch/scrape` | POST | Scrape multiple URLs at once |
| `/v2/parse` | POST | Parse uploaded files (PDF, DOCX, XLSX, HTML) |

## Hermes Integration

Firecrawl can be configured as a Hermes search/extract backend:

```bash
# In ~/.hermes/.env, uncomment:
FIRECRAWL_API_KEY=fc-your-key-here

# Then install the SDK (or let lazy deps auto-install):
pip install firecrawl-py

# Configure backends:
hermes config set web.backend firecrawl
hermes config set web.extract_backend firecrawl
# Optionally also for search:
hermes config set web.search_backend firecrawl
```

Once configured, Hermes agents can search and extract web content via `web_search` and `web_extract` tools using Firecrawl under the hood.

### ⚡ Credit-saving strategy (recommended for free/low-tier plans)

Firecrawl free tier gives 100–500 credits/month. To preserve credits while keeping search functionality:

```bash
# Keep DuckDuckGo for search (free, unlimited):
hermes config set web.search_backend ddgs

# Use Firecrawl only for content extraction:
hermes config set web.backend firecrawl
hermes config set web.extract_backend firecrawl
```

This way everyday web search queries use DDG (zero cost), and Firecrawl credits are spent only when you need to extract actual page content or crawl a site.

**Tip:** `web_extract` (extracting page content from a specific URL) uses Firecrawl credits. `web_search` (searching the web) uses DDG for free. If you set `web.search_backend: firecrawl`, every search query also costs a credit.

### Lazy dependency

The Hermes lazy_deps system defines `search.firecrawl` as `firecrawl-py==4.17.0`. Running `pip install firecrawl-py` may install a newer version (e.g. 4.28.0+); this is fine — the lazy check only verifies the package is importable, not the exact pinned version.

## Fallback When Credits Are Exhausted

When Firecrawl credits run out and `web_search` / `web_extract` return
"Payment Required" errors, use **curl to DuckDuckGo's HTML endpoint** as a
zero-cost terminal fallback. This also works when browser tools are down.

```bash
curl -s -L "https://html.duckduckgo.com/html/?q=YOUR+QUERY+HERE" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Referer: https://duckduckgo.com/" \
  | python3 -c "
import sys, re
html = sys.stdin.read()
results = re.findall(r'class=\"result__a\"[^>]*>(.*?)</a>', html, re.DOTALL)
snippets = re.findall(r'class=\"result__snippet\"[^>]*>(.*?)</div>', html, re.DOTALL)
for t, s in zip(results[:10], snippets[:10]):
    t = re.sub(r'<[^>]+>', '', t).strip()
    s = re.sub(r'<[^>]+>', '', s).strip()
    print(f'- {t}: {s}')
"
```

Key points:
- DDG HTML endpoint is free, unlimited, and returns parseable HTML
- **User-Agent and Referer headers are required** — without them DDG returns empty pages
- DDG rate-limits aggressively (1-2 queries then silence) — space requests
- For page content extraction without Firecrawl: `curl -s -L URL -H "User-Agent: ..."` then strip HTML tags with Python regex
- Google search via curl is blocked (returns 200 + empty or 410) — use DDG instead

## Reference

See `references/cheat-sheet.md` for the full reference including:
- All curl examples
- LLM extraction with schema
- Batch scrape
- Async usage
- Pricing tiers
- Workflow patterns
