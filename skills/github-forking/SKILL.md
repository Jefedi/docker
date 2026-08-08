---
name: github-forking
description: "Detailed guide to forking repositories and creating pull requests using gh CLI and curl fallback."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# GitHub Forking Guide

A fork creates a copy of a remote repository under your own GitHub account. This skill covers:
* Forking via `gh` CLI (recommended).
* Forking via REST API + Git clone.
* Verifying the fork, pushing changes, and opening a PR.
* Common pitfalls.

## Steps
1. **Fork & Clone**
   ```bash
   gh repo fork OWNER/REPO --clone
   ```
2. **Alternative (curl)**
   ```bash
   curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/OWNER/REPO/forks
   git clone https://github.com/YOUR-USERNAME/REPO.git
   ```
3. **Push changes**
   ```bash
   git push origin YOUR-branch
   ```
4. **Create PR**
   ```bash
   gh pr create --base main --head YOUR-USERNAME:YOUR-branch
   ```

## Exploring a Fork Without gh CLI

When `gh` is not installed and no `GITHUB_TOKEN` is available, you can
browse any **public** fork through the GitHub REST API using `web_extract`
against `api.github.com` endpoints (no auth needed for public repos).

### Workflow

1. **List user's repos** → find the fork:
   `GET https://api.github.com/users/{user}/repos?per_page=100&sort=updated`
   Filter for `"fork": true`; each repo object includes `"parent.full_name"`.

2. **List branches** → find feature/work branches:
   `GET https://api.github.com/repos/{owner}/{repo}/branches?per_page=100`
   Branch names like `claude/feature-name` reveal AI-assisted work branches.

3. **Get full recursive tree** (most efficient — one call for the whole repo):
   `GET https://api.github.com/repos/{owner}/{repo}/git/trees/{sha}?recursive=1`
   Use the branch HEAD sha from step 2. For large repos, `web_extract`
   truncates at `char_limit` and saves the full response to a cache file.
   Use `search_files` on the cache file to find paths by keyword
   (`ios`, `checklist`, `TODO`, `README`, etc.).

4. **Fetch raw file content**:
   `GET https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}`
   This is a `raw.githubusercontent.com` URL, NOT `api.github.com`.
   Pass directly to `web_extract` with an appropriate `char_limit`.

5. **Commit history for a specific branch**:
   `GET https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page=50`
   Each commit includes the full message, author login, and date.
   `author.login` reveals who/what made the commit (e.g. `claude` for
   Claude Code sessions).

### Tips

- The contents API (`/contents/`) lists one directory at a time; the trees
  API (`/git/trees/{sha}?recursive=1`) gives the whole repo in one shot —
  prefer trees for exploration.
- Use `web_extract` with `char_limit=30000+` for large tree responses.
- For private repos, use `terminal` with `curl` + `$GITHUB_TOKEN` header
  (`web_extract` doesn't support custom headers).

## Pitfalls
* Token scopes: need `repo` for private forks.
* `gh` may require authentication; run `gh auth login` first.
* Use `--clone` flag to get local copy.
* **Overlap with `github` skill**: The `github` umbrella skill covers the
  same fork/PR lifecycle with more detail. This skill remains useful as a
  quick-reference for fork-specific operations. Consider consolidating into
  `github` if the curator flags overlap.
