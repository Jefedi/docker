# GitHub Actions Workflow Authoring Reference

## Workflow Basics

```yaml
name: My Workflow

on:
  schedule:
    - cron: '0 3 * * 1'  # cron syntax
  workflow_dispatch:        # manual trigger via UI or gh CLI

permissions:
  contents: write           # REQUIRED for push-back (default is read-only)

jobs:
  job-name:
    name: Human-Readable Name
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
          token: ${{ secrets.GITHUB_TOKEN }}  # ensures write access
      - uses: actions/setup-python@v5
```

## Permissions: The #1 Pitfall

**Default GITHUB_TOKEN is read-only** on pushed triggers (schedule, workflow_dispatch, push).

To write back to the repo (commit + push), add:

```yaml
permissions:
  contents: write
```

AND use the token when checking out AND when pushing:

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

## Push-Back Pattern

After generating data in a workflow, commit and push:

```yaml
- name: Commit & Push
  run: |
    git config user.name "Bot Name"
    git config user.email "user+noreply@users.noreply.github.com"
    git remote set-url origin https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
    git add -A
    if ! git diff --staged --quiet; then
      git commit -m "🔄 Auto-update data"
      git push
    else
      echo "No changes"
    fi
```

The `git remote set-url origin ...` line is critical — the default token from `actions/checkout` may not have push permissions.

## Git LFS for Large Files

GitHub has a **100 MB per-file limit** (even for LFS). Files > 100 MB will be rejected.

### .gitattributes (LFS patterns)
```gitattributes
datasets/**/*.json filter=lfs diff=lfs merge=lfs -text
datasets/**/*.csv filter=lfs diff=lfs merge=lfs -text
```

### .gitignore for raw download files
```gitignore
datasets/raw/
datasets/**/*.tsv.gz
datasets/**/*.tsv
```

Keep raw download files (.tsv.gz, .csv.gz) in `.gitignore` — they're too large for git and can be re-downloaded.

## Splitting Heavy Jobs

When a dataset is too large for a single workflow run (timeout / RAM limits):

1. **Core datasets** in main workflow (finishes in minutes)
2. **Heavy processing** in a separate workflow (can run for 30-60+ min independently)

```yaml
# sync-people.yml — Separate workflow for heavy data
on:
  workflow_dispatch:
  schedule:
    - cron: '0 5 * * 1'  # runs after core
```

Standard GitHub runners have 7 GB RAM. Python in-memory processing of 100M+ rows will swap. Use SQLite streaming instead.

## LFS Storage & GitHub Actions

LFS objects uploaded via workflow are billed to the repo owner's LFS storage quota (free accounts get 1 GB, enough for pointers only — actual data counts toward quota). The LFS upload happens automatically when `git lfs` is installed and `.gitattributes` patterns match.

When `actions/checkout@v4` has `lfs: true`, it fetches LFS objects on checkout. Raw.githubusercontent.com does NOT serve LFS files — use the GitHub API or web UI for browsing.

## Triggering Workflows

```bash
# List workflows
gh workflow list -R owner/repo

# Run manually
gh workflow run workflow-name.yml -R owner/repo

# Watch a run
gh run watch <run-id> -R owner/repo

# View run status
gh run view <run-id> -R owner/repo --json status,conclusion,jobs

# Cancel hung run
gh run cancel <run-id> -R owner/repo

# Get job steps status
gh api repos/owner/repo/actions/runs/<run-id>/jobs \
  --jq '.jobs[0].steps[] | "\(.number): \(.name) — \(.status)"'

# View run logs
gh run view <run-id> -R owner/repo --log

# Set repo secrets
gh secret set MY_SECRET -R owner/repo --body "value"
```

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| 403 on push | Add `permissions: contents: write` + explicit token URL |
| File > 100 MB | Add to `.gitignore`, don't commit raw downloads |
| LFS not pushing | Add `datasets/**/*.json filter=lfs ...` to `.gitattributes` |
| Workflow hangs on step | Split heavy jobs into separate workflows |
| Pip cache error | Remove `cache: 'pip'` from `setup-python` if no requirements.txt |
| Logs not available | Wait until run completes, then `gh run view --log` |
