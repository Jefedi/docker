---
name: github-repo-reconnaissance
description: "Analyze GitHub repos without cloning. Use when given a URL."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, repo, reconnaissance, analysis, curl, web_extract]
    related_skills: [github, codebase-inspection]
---

# GitHub Repo Reconnaissance

Explore and summarize a GitHub repository's structure and contents without cloning it.
Use when the user shares a GitHub URL and wants a breakdown of what's inside —
topo, review, audit, or detailed analysis.

## Tool Selection (3-layer fallback)

| Layer | Tool | Rate limit | Best for |
|-------|------|-----------|----------|
| 1 | `web_extract` (Firecrawl) | ~10 req/min | Overview: README, file tree, stars, forks, commit count |
| 2 | GitHub Contents API (`curl`) | 60 req/hr (unauth) | Directory enumeration when web_extract rate-limits |
| 3 | `raw.githubusercontent.com` (`curl`) | Very generous | Bulk file content fetching |

**Key rule:** the moment `web_extract` returns a Firecrawl rate-limit error, switch
to `curl` immediately. Do NOT retry `web_extract` — it won't recover within the
session's useful window (~40-60s cooldown, and subsequent calls also fail).

## Workflow

### Step 1: Overview (web_extract)

```
web_extract(urls=["https://github.com/{owner}/{repo}"])
```

This gives you: README, file tree (top level), stars, forks, commit count,
last commit date, default branch name (master vs main).

Then fetch key files (README, configuration.yaml, package.json — whatever the
entry point is):

```
web_extract(urls=[
  "https://github.com/{owner}/{repo}/blob/{branch}/README.md",
  "https://github.com/{owner}/{repo}/blob/{branch}/configuration.yaml"
])
```

Limit: ~5-10 web_extract calls before Firecrawl rate-limits. Plan accordingly.

### Step 2: Enumerate directories (curl + GitHub API)

When web_extract rate-limits, switch to the GitHub Contents API:

```bash
# Single directory
curl -s "https://api.github.com/repos/{owner}/{repo}/contents/{path}" \
  | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f['name']) for f in data] if isinstance(data, list) else print(data.get('message','err'))"
```

**Batch multiple directories** in a single terminal call to avoid round-trips:

```bash
for pkg in dir1 dir2 dir3 dir4 dir5; do
  echo "=== $pkg ==="
  curl -s "https://api.github.com/repos/{owner}/{repo}/contents/{base_path}/$pkg" \
    | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f['name']) for f in data] if isinstance(data, list) else print(data.get('message','err'))" 2>/dev/null
done
```

The security scanner flags `curl | python3` — it's safe for GitHub's well-formed
JSON API. The command is auto-approved.

### Step 3: Fetch raw file contents (curl + raw.githubusercontent.com)

Use `raw.githubusercontent.com` to fetch file contents in bulk — no rate limits
for reasonable volumes:

```bash
for f in "path/to/file1.yaml" "path/to/file2.yaml" "path/to/file3.yaml" \
         "path/to/file4.yaml" "path/to/file5.yaml"; do
  echo "========== $f =========="
  curl -s "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/$f"
  echo
done
```

This can fetch 15+ files in a single terminal call with a 30s timeout.

**Truncate large files** with `head -N` if only the first section matters:

```bash
curl -s "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/automations.yaml" | head -300
```

## Analysis Tips

- **Start with the entry point** (configuration.yaml, package.json, docker-compose.yml) to understand the project structure
- **Look for `!secret` references** in YAML — actual secrets are in `.gitignore`d files, not in the repo. This is expected practice, not a gap.
- **Note `.disabled` file extensions** — these are intentionally inactive configurations
- **Check commit messages** from the overview — they reveal the project's evolution and the author's tools (e.g., "Claude Code" commits)
- **File naming conventions** reveal the author's language (French entity names, French comments)
- **Package/directory structure** reveals the project's modularity — `packages/` in HA configs is a strong signal of organized, modular config

## Pitfalls

1. **Firecrawl rate limits are per-minute and cumulative** — once you hit the limit, ALL subsequent `web_extract` calls fail until the window resets. Switch to `curl` immediately on first rate-limit error.
2. **GitHub API unauthenticated limit is 60 req/hr** — for large repos with many directories, prioritize the most interesting directories first. If you run out, you can still use `raw.githubusercontent.com` (no limit).
3. **Branch name matters** — use `master` or `main` depending on the repo's default branch. Check the overview from Step 1 to confirm.
4. **`curl | python3` security scanner warning** — the scanner flags pipe-to-interpreter as HIGH risk. It's safe for GitHub's well-formed JSON API. The command is auto-approved by smart approval.
5. **Large YAML files** — `automations.yaml` can have hundreds of lines. Use `head -300` to truncate if you only need the first section.
6. **`web_extract` on `raw.githubusercontent.com` URLs** — these also consume Firecrawl credits and can rate-limit. Prefer `curl` in terminal for raw file fetches.

## See Also

- `references/repo-reconnaissance.md` — detailed walkthrough of the 3-layer fallback technique with a real example