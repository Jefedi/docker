---
name: github
description: "Unified GitHub workflow skill — authentication, repo management, PR lifecycle, code review, and issues. Covers gh CLI and git+curl fallback for every operation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, git, PR, CI, issues, code-review, authentication]
    related_skills: [hermes-agent, claude-code, codex]
---

# GitHub — Unified Workflow Skill

A single class-level skill covering everything you need to work with GitHub from the terminal: authentication, repository management, pull requests, code review, and issue triage. Each major section provides `gh` CLI commands first, then `git+curl` fallbacks for machines without `gh`.

## Installation

Install `gh` if not present. The `scripts/gh-install.sh` script auto-detects
your platform and runs the right command (apt-get, brew, winget, dnf, etc.)
with a manual-tarball fallback:

```bash
source skills/github/scripts/gh-install.sh   # or just bash it
```

Or manually:

```bash
# Debian/Ubuntu
apt-get install gh -y

# macOS
brew install gh

# Verify
gh --version
```

### Authentication

After install, authenticate:

```bash
# Interactive browser flow (recommended for desktop)
gh auth login

# Token-based (headless VPS/server) — create a PAT at https://github.com/settings/tokens
# with scopes: repo, workflow, read:org, gist
gh auth login --with-token <<< "ghp_xxxxxxxxxxxxxxxxxxxx"

# Verify
gh auth status
```

## Auth Detection

Run this at the start of any GitHub workflow:

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
  GH_USER=$(gh api user --jq '.login')
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

### Auth Methods

**HTTPS with PAT:** Use `git config --global credential.helper store` + test with `git ls-remote`. Create token at https://github.com/settings/tokens with `repo` + `workflow` scopes.

**SSH keys:** `ssh-keygen -t ed25519`, add to https://github.com/settings/keys, test with `ssh -T git@github.com`.

**gh CLI:** `gh auth login` (interactive or `gh auth login --with-token`).

See full details in `references/authentication.md`.

---

## Repo Management (clone/create/fork/releases/settings)

### Cloning
```bash
git clone https://github.com/owner/repo.git
gh repo clone owner/repo
```

### Creating Repos
```bash
gh repo create name --public --clone
# Or via API:
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name": "name", "private": false}'
```

### Forking + Keeping in Sync
```bash
gh repo fork owner/repo --clone
git remote add upstream https://github.com/owner/repo.git
git fetch upstream && git merge upstream/main
```

### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
# API:
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{"tag_name": "v1.0.0", "name": "v1.0.0"}'
```

### Branch Protection & Secrets
```bash
# Branch protection via API
curl -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{"required_status_checks": {"strict": true, "contexts": ["ci/test"]}}'

# Secrets (gh is simpler)
gh secret set API_KEY --body "value"
```

See full details in `references/repo-management.md`.

---

## Pull Request Lifecycle

### Branch + Commit
```bash
git checkout -b feat/add-auth
# ... make changes, use file tools
git add -A && git commit -m "feat: add JWT authentication"
git push -u origin HEAD
```

Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`

### Create PR
```bash
gh pr create --title "feat: ..." --body "Summary" --label "enhancement"
# API:
BRANCH=$(git branch --show-current)
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\": \"feat: ...\", \"head\": \"$BRANCH\", \"base\": \"main\"}"
```

### Monitor CI
```bash
gh pr checks --watch
# API polling:
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status
```

### Merge
```bash
gh pr merge --squash --delete-branch
# API:
curl -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$NUM/merge \
  -d '{"merge_method": "squash"}'
```

See full details in `references/pr-lifecycle.md`, `templates/pr-body-bugfix.md`, `templates/pr-body-feature.md`.

---

## Code Review

### Local Changes Review
```bash
git diff main...HEAD --stat
git diff main...HEAD
# Check for red flags:
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|password\|secret"
```

### PR Review
```bash
gh pr view 123
gh pr diff 123
gh pr checkout 123

# Post review
gh pr review 123 --approve --body "LGTM"
gh pr review 123 --request-changes --body "Issues found"
```

Output format: `Critical → Warnings → Suggestions → Looks Good`.

See full details in `references/code-review.md`, `references/review-output-template.md`.

---

## Issues Management

### List/Create/Edit Issues
```bash
gh issue list --label "bug" --state open
gh issue create --title "Bug: ..." --body "Steps..." --label "bug"
gh issue edit 42 --add-label "priority:high"
gh issue close 42 --reason "completed"
```

### Templates
See `templates/bug-report.md`, `templates/feature-request.md`.

---

## GitHub Actions Workflow Authoring

Writing workflows that process data and push results back to the repo.

### Minimal Write-Back Workflow

```yaml
name: Process & Push
on:
  workflow_dispatch:
permissions:
  contents: write       # ← CRITICAL: read-only by default
jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
          token: ${{ secrets.GITHUB_TOKEN }}
      - name: Generate data
        run: python3 scripts/generate.py
      - name: Commit & Push
        run: |
          git config user.name "Bot"
          git config user.email "bot@users.noreply.github.com"
          git remote set-url origin https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
          git add -A
          git diff --staged --quiet || (git commit -m "Auto-update" && git push)
```

### Large Dataset Workflows

When processing datasets that are hundreds of MB / millions of rows:
- **Keep raw compressed files in `.gitignore`** (they exceed GitHub's 100 MB limit)
- **Use `.gitattributes` with LFS patterns** for output .json files
- **Split heavy processing into separate workflows** (one fast workflow for core data, another for heavy joins/cross-references)
- **Use SQLite for streaming** instead of loading 100M+ rows in RAM (GitHub runner: 7 GB)

See `references/github-actions-workflows.md` for: permissions troubleshooting, LFS setup, push-back pattern, triggering/monitoring commands, and a pitfall table.

## Quick Reference Table

| Action | gh | curl/git |
|--------|-----|----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create n --public` | `curl POST /user/repos` |
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| Create issue | `gh issue create ...` | `POST /repos/{o}/{r}/issues` |
| Create PR | `gh pr create ...` | `POST /repos/{o}/{r}/pulls` |
| Check CI | `gh pr checks` | `GET /repos/{o}/{r}/commits/{sha}/status` |
| Merge PR | `gh pr merge --squash` | `PUT /repos/{o}/{r}/pulls/{n}/merge` |
| Post review | `gh pr review N --approve` | `POST /repos/{o}/{r}/pulls/{n}/reviews` |
| Release | `gh release create v1.0` | `POST /repos/{o}/{r}/releases` |
| Secrets | `gh secret set K V` | `PUT /repos/{o}/{r}/actions/secrets/K` |
| Workflow | `gh workflow list` | `GET /repos/{o}/{r}/actions/workflows` |

## Pitfalls

- **Token scopes**: Missing `repo` scope = push failures. Missing `workflow` scope = can't push to `.github/workflows/`.
- **SSH key permissions**: `~/.ssh/id_*.pub` files must be `600`. GitHub requires keys added via Settings → SSH and GPG keys.
- **Multiple accounts**: Use SSH config with different `Host` aliases per account.
- **Token in remote URL**: Embedding token in URL avoids prompts but exposes it in `git remote -v`. Use credential helper for persistent sessions.
- **PR merge conflicts**: Resolve locally with `git merge main`, fix conflicts, commit, push.
- **gh not installed**: All operations have `git+curl` fallbacks — never a hard blocker.
