---
name: skill-builder
description: >
  Build structured Hermes Agent skills from git-sourced documentation. Clone
  repos shallow, extract markdown docs to references/, generate OpenAPI index
  files, write SKILL.md with routing table + gotchas + validation questions,
  and git-based sync.sh. Trigger words: build skill, create skill, skill from
  docs, skill from repo, documentation skill, sync.sh, openapi index.
---

# Skill Builder — From Git Repos to Structured Skills

## When to Use

When the user asks to build a Hermes Agent skill from one or more GitHub-hosted
documentation sources (wikis, docs folders, mkdocs sites, docusaurus sites).
This is the pattern used for `pangolin`, `servarr`, `torrent-vpn`, `jellyfin`,
`media-stack` skills.

## Mental Model

A skill = `SKILL.md` (mental model + routing table + behavior rule) + `references/`
(loaded on demand) + `scripts/sync.sh` (git-based sync). The agent reads SKILL.md
first, then loads the specific reference file for any given question. This keeps
context small and answers accurate.

## Step-by-Step

### 1. Reconnaissance (ALWAYS do this first, ask user to validate)

For each tool/source:
1. Check if repo exists: `curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/OWNER/REPO"`
2. Resolve 301 redirects (repo transfers) with `curl -sL`
3. Clone shallow: `git clone --depth 1 [--branch BRANCH] URL /tmp/NAME`
4. Find markdown docs: `find /tmp/NAME -name "*.md" -path "*/docs/*"`
5. Find openapi.json: `find /tmp/NAME -name "openapi.json"`
6. If no git repo exists → fall back to web scraping (like pangolin skill)
7. Delete clone: `rm -rf /tmp/NAME`
8. **List findings and WAIT for user validation**

### 2. Group into umbrella skills (class-level, not one-skill-per-tool)

User often wants N tools grouped into K skills (K < N). Example: 13 tools → 4
skills. Ask or follow user instructions for grouping.

### 3. Build references/

For each source repo:
```bash
git clone --depth 1 [--branch BRANCH] URL /tmp/SOURCE
# Copy markdown, flatten subdirs with __ separator
find /tmp/SOURCE/docs -name "*.md" | while IFS= read -r f; do
  rel="${f#docs/}"
  out="references/prefix__${rel//\//__}"
  cp "$f" "$out"
done
rm -rf /tmp/SOURCE
```

**Naming convention**: `<source-prefix>__<path>__<filename>` with `__` for directory
separators. Example: `sonarr__installation__docker.md`.

### 4. OpenAPI handling (for APIs)

- Clone the main repo (not docs repo), find `openapi.json`
- Save raw JSON as `references/<app>-openapi.json` (NEVER in SKILL.md — too large)
- Generate `references/<app>-api-index.md`:
  ```
  # <App> API Index

  ## METHOD /path
  <summary from openapi, 1 line>
  ```
- Use Python to parse JSON and generate the index:

```python
import json
with open(path) as f:
    spec = json.load(f)
paths = spec.get("paths", {})
index_lines = [f"# {app.capitalize()} API Index\n"]
for route in sorted(paths.keys()):
    for method in ("get", "post", "put", "delete", "patch"):
        if method in paths[route]:
            info = paths[route][method]
            summary = info.get("summary", "")
            index_lines.append(f"## {method.upper()} {route}")
            index_lines.append(summary[:120] if summary else "(no description)")
            index_lines.append("")
```

### 5. Gotchas file: `references/00-gotchas-jefe.md`

- `00` prefix = first alphabetically
- Compile from user's existing memory, prior sessions, and known infrastructure
- Mark unknowns as `TODO` — NEVER invent
- Key areas to check: Docker mounts, permissions, NFS, VPN, API keys, version migrations

### 6. SKILL.md (< 500 lines)

Structure:
```yaml
---
name: skill-name
description: >
  Description with trigger words for auto-loading.
---
```

Body:
1. **Mental Model**: What the tools are, how they relate, the core workflow
2. **Routing Table**: Markdown table mapping question domain → reference file
3. **Behavior Rule**: "Never answer from memory about config values. Always
   open the reference file. Do not invent."
4. **Validation Questions**: 3 questions (including 1 counter-intuitive),
   each with answer based on references

### 7. scripts/sync.sh

**Critical**: Use absolute `SCRIPT_DIR` (not `$(dirname "$0")` which breaks after `cd`):

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
```

Logic:
1. Clone repos to /tmp
2. Copy docs, compare with `cmp -s` against current references
3. Report `[CHANGED]` or `[OK]` per file
4. Clean up /tmp clones
5. Exit codes: 0=unchanged, 1=changed, 2=error

### 8. Parallel construction (for multi-skill batches)

Use `delegate_task` with up to 3 parallel leaf subagents. Each builds one skill
independently. The 4th skill can be built directly while subagents run. Check
live transcripts at `/opt/data/cache/delegation/live/<id>/task-0.log`.

### 9. Web-scraping pattern: `llms.txt` (Mintlify and similar)

When docs are NOT on GitHub but hosted on a docs platform (Mintlify, Docusaurus,
etc.), check for an `llms.txt` index file at the domain root. This file lists
all doc page URLs. Used for `pangolin` (132 pages) and `n8n` (1318 pages).

**Step 1 — Fetch the index:**
```
web_extract(urls=["https://docs.DOMAIN/llms.txt"], char_limit=50000)
```
If the file is very large (>100K chars), `web_extract` truncates it and saves
the full text to `/opt/data/cache/web/DOMAIN-<hash>.md`. Parse from that file
with a Python script to extract all URLs ending in `.md`.

**Step 2 — Extract URLs:**
```python
import re
with open("/opt/data/cache/web/DOMAIN-<hash>.md") as f:
    content = f.read()
urls = re.findall(r'https://docs\.DOMAIN/[^\s\)]+\.md', content)
# deduplicate preserving order
```

**Step 3 — Download pages (with resume support):**
- Save to `references/` with `/` → `__` in filenames (same convention as git)
- 200–300ms delay between requests (don't hammer the server)
- Skip files already downloaded (>100 bytes) so timeouts can resume
- For 1000+ pages, the download may exceed terminal timeout (600s). Run the
  script twice — the second run skips already-downloaded files.
- Use `urllib.request` in a Python script, NOT `web_extract` (too slow for
  hundreds of pages — one HTTP request per `web_extract` call)

**Step 4 — sync.sh (curl-based, NOT git-based):**
The sync script for web-scraped skills uses `curl` instead of `git clone`:
- Fetch `llms.txt` fresh
- Extract URLs with `grep -oP`
- Download each to `/tmp`, `diff` against existing
- Exit 1 if any file changed or is new
- Skip `00-gotchas-jefe.md` (not from upstream)

**Step 5 — cross_profile writes:**
When the user asks to install the skill on a DIFFERENT Hermes profile (not the
current one), `write_file` blocks with a cross-profile guard. Pass
`cross_profile=True` to bypass after explicit user direction. The skill will
be available on the target profile's sessions, not the current one.

## Pitfalls

- **`read -f` bug**: In `while read` loops, use `while IFS= read -r f` — the
  shorthand `read -f` is invalid bash syntax.
- **Relative REF_DIR**: `$(dirname "$0")/../references` breaks when the script
  does `cd` into a cloned repo. Always resolve to absolute with
  `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`.
- **gh CLI failures**: `gh api` may fail (401, missing binary). Fall back to
  `curl -sL "https://api.github.com/repos/OWNER/REPO"`.
- **301 redirects**: GitHub repo transfers return 301. Always use `curl -sL`
  to follow redirects.
- **Archived repos**: Check `archived: true` in repo metadata. Archived repos
  may have moved content elsewhere (e.g. jellyfin-docs → jellyfin.org).
- **GitHub wikis**: Clone with `.wiki.git` suffix: `git clone https://github.com/OWNER/REPO.wiki.git`
- **Subagent 401 on gh**: Subagents may not inherit gh auth. They should use
  `git clone` directly, not `gh api`.
- **Large openapi.json**: Never put openapi content in SKILL.md. Generate an
  index file and keep raw JSON separate.
- **llms.txt > 1000 pages**: Downloads will exceed terminal timeout (600s).
  Write the download script with resume support (skip files >100 bytes that
  already exist). Run it twice — second run finishes the remaining pages in
  ~300s. Use `urllib.request` in a Python script via `terminal`, NOT
  `web_extract` (one HTTP call per tool invocation is too slow for 1000+
  pages).
- **Cross-profile skill install**: `write_file` to another profile's
  `skills/` directory is blocked by default. The user must explicitly request
  the target profile. Pass `cross_profile=True` to `write_file` to bypass
  the guard. The skill is then invisible to `skills_list` on the current
  profile but loads correctly on the target profile.
- **SKILL.md not in skills_list**: A skill installed on another profile via
  `cross_profile=True` won't appear in `skills_list` on the current profile.
  Verify with `skill_view(name='X')` or `find /opt/data/profiles/<profile>/
  skills/` instead.

## Verification Checklist

- [ ] SKILL.md < 500 lines
- [ ] All reference files exist and are non-empty
- [ ] `00-gotchas-jefe.md` present with `00` prefix
- [ ] `sync.sh` executable, syntax valid (`bash -n`)
- [ ] `sync.sh` uses absolute `SCRIPT_DIR`
- [ ] Routing table lists ALL reference files
- [ ] 3 validation questions with answers (including 1 counter-intuitive)
- [ ] No openapi.json content in SKILL.md
- [ ] No invented content (TODOs for unknowns)