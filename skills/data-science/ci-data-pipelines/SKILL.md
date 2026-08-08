---
name: ci-data-pipelines
description: >-
  Process large external datasets using CI runners (GitHub Actions) instead of
  local infrastructure. Download, transform, chunk, and commit results back to
  the repo. Covers Git LFS, chunked JSON, multi-stage enrichment workflows, and
  GitHub secret management for API keys.
category: data-science
triggers:
  - user has a large external dataset to download and process
  - user says 'don't download to VPS' or 'avoid filling up disk space'
  - user wants to assemble or curate a data repository
  - user wants automatic periodic data refresh without local cron
---

# CI Data Pipelines

Process large external datasets using **GitHub Actions runners** — download, transform, and commit results back without touching local infrastructure.

## When to use

- Dataset is too large for local disk (ISOs, images, movie metadata, Common Crawl, ML datasets)
- Data needs periodic refresh (weekly/daily schedule)
- User wants to avoid local infrastructure burden
- Dataset will live in a Git repo (possibly with LFS)

## Architecture pattern

```
User repo → GitHub Actions runner → Download external data
                                   → Process/transform
                                   → Chunk into <50MB files
                                   → Git LFS for large files
                                   → Commit back to repo
```

## Step-by-step

### 1. Choose data source

Common open datasets that work well with this pattern:
- **IMDb non-commercial**: `https://datasets.imdbws.com/` (TSV.gz, ~1GB total)
- **TMDB daily exports**: Requires API key, JSON format
- **MovieLens**: `https://grouplens.org/datasets/movielens/` (CSV/JSON)
- **Kaggle**: Via Kaggle API or direct download
- **Wikipedia dumps**: Wikimedia database dumps
- **Common Crawl**: Columnar data

### 2. Structure the repository

```
repo/
├── .github/workflows/
│   ├── sync-primary.yml       ← Main data pipeline (scheduled + manual)
│   └── enrich-secondary.yml   ← Enrichment pipeline (manual only)
├── scripts/
│   ├── process-basics.py      ← Primary transform script
│   ├── process-more.py        ← Secondary processing
│   └── generate-stats.py      ← Statistics generation
├── datasets/processed/        ← Processed data output (Git LFS tracked)
├── datasets/raw/              ← Raw downloads (keep in .gitignore)
├── web/                       ← Optional: web interface for browsing
└── .gitattributes             ← Git LFS config
```

### 3. Workflow design

**Primary pipeline** (`sync-primary.yml`):
- Schedule + workflow_dispatch triggers
- Checkout with LFS: `actions/checkout@v4` with `lfs: true`
- Python setup without pip cache (no requirements.txt on runners)
- Download step: `curl -sL $URL -o datasets/raw/$FILE`
- Processing: Python scripts that read from raw, write to processed
- Commit & push: use `git add -A`, `git diff --staged --quiet` to skip empty

**Enrichment pipeline** (`enrich-secondary.yml`):
- `workflow_dispatch: {}` only (manual trigger)
- Guarded: `if: secrets.API_KEY != ''`
- API key passed via env: `TMDB_API_KEY: ${{ secrets.API_KEY }}`

### 4. File chunking strategy

GitHub repos have a soft limit of ~2GB and per-file limit of 100MB without LFS.

```python
CHUNK_SIZE = 10000        # items per file
MAX_FILE_SIZE = 45 * 1024 * 1024  # ~45 MB per chunk (well under 100MB)

def write_chunked(items, base_path):
    chunk = 1
    while items:
        batch = items[:CHUNK_SIZE]
        items = items[CHUNK_SIZE:]
        # Halve batch if too large
        while True:
            data = json.dumps(batch, ensure_ascii=False, indent=2)
            if len(data.encode()) < MAX_FILE_SIZE or len(batch) <= 1:
                break
            mid = len(batch) // 2
            items = batch[mid:] + items
            batch = batch[:mid]
        with open(f"{base_path}_{chunk:04d}.json", "w") as f:
            f.write(data)
        chunk += 1
```

Write a `_index.json` per directory with `{total_items, chunks, files: [...]}`.

### 5. Git LFS setup

```gitattributes
# .gitattributes
datasets/**/*.json filter=lfs diff=lfs merge=lfs -text
datasets/**/*.csv filter=lfs diff=lfs merge=lfs -text
datasets/**/*.tsv filter=lfs diff=lfs merge=lfs -text
datasets/**/*.parquet filter=lfs diff=lfs merge=lfs -text
```

Set LFS in workflow checkout: `actions/checkout@v4` with `lfs: true`.

### 6. GitHub secrets for API keys

```bash
gh secret set TMDB_API_KEY -R owner/repo
```

In the workflow:
```yaml
- name: Enrich
  env:
    TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}
  run: python3 scripts/enrich.py
```

Guard:
```yaml
if: secrets.TMDB_API_KEY != ''
```

## Pitfalls

- **pip cache**: Don't use `cache: 'pip'` in `setup-python@v5` without a requirements.txt — it hard-fails. Either add a requirements.txt or remove the cache option.
- **Workflow triggers**: Push trigger on paths can race with scheduled runs. Keep `workflow_dispatch: {}` for manual retry.
- **GitHub Actions timeout**: Default is 360min (6h). For massive datasets, consider `timeout-minutes: 60` explicitly.
- **Repo size**: GitHub warns at 2GB and blocks at 5GB. Use LFS or releases for truly large data. LFS gives 1GB free per repo on free plans.
- **Runner disk**: GitHub runners have ~70GB disk. Datasets larger than that need streaming or external storage (S3, GCS).
- **Split >100MB files**: GitHub blocks >100MB pushes without LFS. Use the chunking strategy above or enable LFS for those extensions.

## Verification

After pushing a workflow:
1. `gh workflow run <name> -R owner/repo` to trigger
2. `gh run list -R owner/repo --workflow=<name> --limit 1 --json status,conclusion`
3. `gh run view <run-id> -R owner/repo --log` to check progress
4. On completion, check repo has the new data files and `_index.json` per directory
