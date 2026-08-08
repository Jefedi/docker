---
name: github-awesome-list-exploration
description: "Find relevant datasets and tools in GitHub awesome-lists."
---

# GitHub Awesome-List Exploration

## When to use

- User shares a GitHub awesome-list URL and asks what's relevant to them
- User asks "what datasets/tools are available on GitHub for X domain"
- User wants to discover curated resource lists matching their interests
- Trigger words: awesome, curated list, github datasets, open data, public datasets

## Core workflow

1. **Extract the shared repo** — Use `web_extract` on the GitHub URL. The README is the primary content.
2. **Handle truncation** — Large awesome-list READMEs (100k–300k+ chars) truncate at ~15k chars. The full text is cached on disk at the path shown in the output footer. Use `read_file` with `offset`/`limit` to paginate through the complete content. Don't skip sections — relevant datasets can be anywhere.
3. **Match to user profile** — Filter entries against known user interests (see memory + user profile). Group by domain. Rank by relevance.
4. **Search beyond the shared repo** — Run `web_search` for complementary awesome-lists in matching domains (e.g., "awesome datasets github <domain> 2025"). The user expects exploration beyond the one repo they shared. This is the most important step — if the shared repo has nothing interesting, find repos that do BEFORE reporting "nothing interesting."
5. **Verify promising leads** — Use `web_extract` on 2–3 of the most promising complementary repos to confirm they contain real content, not just stubs.
6. **Present results** — Group by domain relevance, not by source repo. Include ⭐ counts and last-update dates as quality signals.

## Pitfalls

- **DO NOT only scan the repo the user shared.** They expect you to proactively search for complementary awesome-lists. If the first repo has nothing interesting in their domain, search for other awesome-lists that do — before reporting "nothing interesting." This happened in session 2026-08-01: user shared awesome-public-datasets, found nothing relevant in first pass, had to prompt twice ("rien d'interessant autre data", "toujours rien") before complementary searches were run. The complementary searches found awesome-french-open-data (DVF 20M transactions), awesome-hamradio, and awesome-RF — all highly relevant.
- **Large README truncation is silent.** `web_extract` returns only the head + tail of large pages. The middle (often the most relevant sections) is saved to disk. Always check the footer for a cache file path and paginate through it. For awesome-public-datasets (296k chars), the cache file was at `/opt/data/cache/web/github.com-<hash>.md` and required 3 `read_file` calls at offset 1, 453, 815 to cover all sections.
- **Star count ≠ quality.** A 30-star repo curated by domain experts (e.g., awesome-hamradio at 187 stars) can be more valuable than a 77k-star general list. Evaluate by relevance to the user's domains.
- **Check last update date.** Awesome-lists rot. A repo last updated 5 years ago likely has dead links. Prioritize repos updated within the last year.

## For this user specifically

- **Language**: Always respond in French, even if the user writes in English.
- **Profile domains**: Le Havre (immo buy-to-let), radio amateur (HAM/SDR/RF), Los Galactique (game hosting), homelab/infra, privacy/EU sovereignty, custom tools, CRM/business.
- **Filter aggressively**: Skip entries only relevant to US/China domestic contexts unless the technique is transferable.
- **Sovereignty matters**: Highlight EU/French sources. Flag US-only datasets as "modèle transférable" rather than directly useful.

## References

- `references/awesome-lists-by-domain.md` — catalog of awesome-lists discovered across sessions, with URLs, star counts, last-update dates, and domain tags