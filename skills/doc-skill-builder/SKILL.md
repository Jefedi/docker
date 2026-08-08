---
name: doc-skill-builder
description: >
  Build Hermes documentation skills from external git repos. Covers the full
  methodology: reconnaissance (find repos, verify they respond, identify doc
  folders), shallow clone, extract markdown, generate OpenAPI indexes, create
  SKILL.md with routing table, write gotchas from user notes, write sync.sh,
  and validate with test questions. Trigger words: build skill, documentation
  skill, skill from repo, doc skill, sync.sh, references, routing table,
  gotchas, openapi index, skill builder.
---

# Documentation Skill Builder

## When to Use

When the user asks to build a new documentation skill (or batch of skills) from
external sources — git repos, wikis, or API specs. The pattern: take a body of
upstream documentation, package it into a Hermes skill with a compact SKILL.md
(< 500 lines) and a `references/` directory loaded on demand.

## Mental Model

A documentation skill has 4 parts:
1. **SKILL.md** — mental model + routing table + behavior rule. < 500 lines.
   The routing table maps question domains to reference files. The behavior rule
   says "never answer from memory about a config value — always open the ref file."
2. **references/** — markdown files copied from upstream, flattened with `__`
   separator (e.g. `sonarr__installation__docker.md`). Loaded on demand, never
   all at once.
3. **references/00-gotchas-jefe.md** — field knowledge absent from upstream docs.
   Infrastructure-specific notes, known bugs, TODOs. `00` prefix = first
   alphabetically.
4. **scripts/sync.sh** — re-clones upstream repos, diffs against current
   references, exits 1 if changed (for cron detection).

## Step-by-Step Methodology

### Step 1: Reconnaissance (DO THIS BEFORE CODING)

For each tool/source, identify:
- The exact git repo URL (verify it responds — `curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/OWNER/REPO"`)
- The branch name (check `default_branch` via API or `gh`)
- The markdown folder inside the repo (clone shallow, `find . -name "*.md"`)
- If no repo exists, the fallback method (scraping, readthedocs, etc.)

**Present findings to user and WAIT for validation.** Do not guess repo URLs.

### Step 2: Check Existing Skills

- `skills_list` — check if a similar skill already exists (e.g. `media-center`)
- If yes: merge into it instead of duplicating. Tell the user what you merge.
- If no: create fresh.

### Step 3: Clone and Extract

```bash
# Shallow clone (saves time, avoids history)
git clone --depth 1 --branch <branch> https://github.com/<owner>/<repo>.git /tmp/<name>

# Copy markdown, flatten subdirs with __ separator
find /tmp/<name>/<docs-dir> -name "*.md" | while IFS= read -r f; do
  rel="${f#<docs-dir>/}"
  out="$REF_DIR/${prefix}__${rel//\//__}"
  cp "$f" "$out"
done

# Clean up
rm -rf /tmp/<name>
```

**Key**: only copy `.md` files. Skip images, binaries, `.git`, node_modules.

### Step 4: OpenAPI Indexes (when applicable)

If the source has an `openapi.json`:
- Keep the raw JSON as `references/<app>-openapi.json` (for targeted reads)
- Generate a compact index `references/<app>-api-index.md`:

```python
# For each path in openapi.json, output one block:
# ## METHOD /path
# <summary from openapi, 1 line, max 120 chars>
```

**NEVER put openapi.json content in SKILL.md.** It's enormous. The index is the
routing entry point; the JSON is read on demand for specific endpoints.

### Step 5: Write SKILL.md

Structure (follow the pangolin skill as template):
```yaml
---
name: <skill-name>
description: >
  <One paragraph with trigger words. Covers what tools, what domains.>
---
```

Body:
- **Mental Model**: 3-5 sentences explaining the system architecture and how
  components relate.
- **Routing Table**: markdown table, `| Question domain | Reference file |`.
  Include ALL reference files you created.
- **Behavior Rule**: "Never answer from memory about a configuration option,
  default value, or API field. Always open the corresponding reference file and
  cite the exact value. If the answer is not in the reference files or the
  gotchas file, say so explicitly. Do not invent."
- **Validation Questions**: 3 questions (including at least 1 counter-intuitive),
  with answers written from the reference files.

### Step 6: Write Gotchas (00-gotchas-jefe.md)

Source from:
- User's explicit "points à chercher en priorité" list
- Existing skills and memory entries
- Session history (past corrections, known bugs)

Format: `## <Topic>` sections. Mark unknowns as `TODO — ...`. Never invent.

### Step 7: Write sync.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
# Sync <skill> docs from GitHub repos
# Exit 0 if unchanged, 1 if changed, 2 on error.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
```

Key patterns:
- Use `SCRIPT_DIR` (absolute) not `$(dirname "$0")` (relative breaks after `cd`)
- Clone to `$TMP_BASE` with `mktemp -d`, `trap 'rm -rf' EXIT`
- Compare with `cmp -s` before copying (avoid false "changed" on identical files)
- Use `while IFS= read -r f` (NOT `while read -f` which is invalid bash)

### Step 8: Validate

- `bash -n scripts/sync.sh` — syntax check
- Run sync.sh — should exit 0 (no changes since just built)
- Count files: `find references -name "*.md" | wc -l`
- Count SKILL.md lines: `wc -l SKILL.md` (must be < 500)

## Parallelization with Subagents

For building multiple skills at once:
- `delegate_task` with `tasks` array (max 3 concurrent)
- Each subagent gets a self-contained goal with: repo URLs, branch names, doc
  folder paths, gotchas content, validation questions
- **Pitfall**: subagents using `gh` CLI may fail with 401 if gh isn't in PATH.
  Use `git clone` directly (no auth needed for public repos) or ensure
  `export PATH="$HOME/.local/bin:$PATH"` is in the subagent context.
- After parallel subagents finish, build remaining skills sequentially if > 3.

## Pitfalls

### .gitignore for sync.sh — use absolute REF_DIR
```bash
# WRONG (breaks after cd into clone dir):
REF_DIR="$(dirname "$0")/../references"

# RIGHT:
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references"
```

### `while read` syntax
```bash
# WRONG (invalid option):
find docs -name "*.md" | while read -f; do ...

# RIGHT:
find docs -name "*.md" | while IFS= read -r f; do ...
```

### OpenAPI JSON size
OpenAPI specs can be 200KB-2MB. NEVER inline in SKILL.md. Generate a compact
text index (`METHOD /path — 1-line summary`) and keep the JSON as a separate
file for on-demand reading.

### GitHub wiki repos
Some projects have their docs in a separate `.wiki.git` repo (e.g.
`qbittorrent/qBittorrent.wiki.git`), not in the main repo. Check:
- `has_wiki` field on the main repo API
- `git clone https://github.com/<owner>/<repo>.wiki.git`
- GitHub wikis are bare repos at root level (no subfolder)

### Redirected/moved repos
GitHub API returns 301 for moved repos. Use `curl -sL` (follow redirects) to
resolve the actual `full_name` and `default_branch` before cloning.

## Validation Checklist

- [ ] SKILL.md < 500 lines
- [ ] Routing table lists ALL reference files
- [ ] `00-gotchas-jefe.md` exists with user's specific gotchas
- [ ] `scripts/sync.sh` passes `bash -n` and exits 0 on first run
- [ ] OpenAPI JSON files are NOT in SKILL.md
- [ ] OpenAPI index files exist (one per API)
- [ ] 3 validation questions with answers, including 1 counter-intuitive
- [ ] No invented content — TODOs for unknowns