---
name: github-actions-data-pipeline
description: "Build ETL-style data pipelines that run entirely on GitHub Actions runners — download external datasets, process/transform them, commit results back to the repo. Avoids consuming local VPS/workspace storage."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [github-actions, etl, data-pipeline, datasets, imdb, tmdb, sqlite]
    related_skills: [github]
---

# GitHub Actions Data Pipeline

Build data pipelines that process large datasets **on GitHub's runners** instead of your local machine. Perfect for:
- Downloading and transforming open datasets (IMDb, Kaggle, etc.)
- Enriching data with external APIs (TMDB, OMDB, etc.)
- Generating and committing processed data artifacts
- Running periodic data refreshes via cron triggers

## Core Architecture

```
.github/workflows/
├── sync-datasets.yml      # Main ETL workflow (cron + manual)
└── enrich-tmdb.yml        # API enrichment (manual trigger, depends on secrets)
scripts/
├── process-basics.py      # TSV → JSON conversion
├── enrich-api.py          # External API enrichment
└── generate-stats.py      # Stats aggregation
```

## Workflow Structure Template

```yaml
name: Sync Datasets

on:
  schedule:
    - cron: '0 3 * * 1'       # Weekly: Monday 3AM UTC
  workflow_dispatch:           # Manual trigger
  push:
    branches: [main]
    paths:
      - 'scripts/**'
      - '.github/workflows/**'

jobs:
  process-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true            # Enable Git LFS

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Download data
        run: |
          mkdir -p datasets/raw
          curl -sL "https://example.com/dataset.gz" -o datasets/raw/data.gz

      - name: Process
        run: python3 scripts/process.py

permissions:
  contents: write                   # REQUIRED — without this, push returns 403

jobs:
  process-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
          token: ${{ secrets.GITHUB_TOKEN }}  # Needed for push

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Download data
        run: |
          mkdir -p datasets/raw
          curl -sL "https://example.com/dataset.gz" -o datasets/raw/data.gz

      - name: Process
        run: python3 scripts/process.py

      - name: Commit & Push
        run: |
          git config user.name "Bot"
          git config user.email "bot@users.noreply.github.com"
          git remote set-url origin \
            https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
          git add datasets/processed/ scripts/ .gitattributes .gitignore
          git add -A
          if ! git diff --staged --quiet; then
            git commit -m "🔄 Sync datasets"
            git push
          else
            echo "✅ No changes"
          fi
```

## Key Patterns

### 1. Dataset Download on Runner

```yaml
- name: Download datasets
  run: |
    BASE="https://datasets.example.com"
    FILES=("file1.tsv.gz" "file2.tsv.gz")
    mkdir -p datasets/raw
    for FILE in "${FILES[@]}"; do
      curl -sL "$BASE/$FILE" -o "datasets/raw/$FILE"
    done
```

**Pitfalls:**
- Files over 100MB need Git LFS to commit to GitHub
- If the total dataset is >1-2 GB, consider GitHub Releases instead of commits
- GitHub Actions runners have ~7 GB RAM and ~14 GB SSD — plan accordingly

### 2. Memory-Constrained Processing with SQLite

When datasets are too large to fit in RAM (e.g., 769 MB compressed → 4-7 GB uncompressed), use SQLite as an intermediate store instead of loading everything in memory:

```python
import sqlite3, gzip, csv, json, os, tempfile

db_path = os.path.join(tempfile.gettempdir(), "data.db")
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=OFF")    # Speed up bulk inserts
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-80000")   # 80 MB page cache
cur = conn.cursor()

# 1. Load data in batches
cur.execute("CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT, ...)")
batch = []
with gzip.open("datasets/raw/data.tsv.gz", "rt") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        batch.append((row["id"], row["name"]))
        if len(batch) >= 50000:
            cur.executemany("INSERT OR IGNORE INTO items VALUES (?,?)", batch)
            conn.commit()
            batch = []
    if batch:
        cur.executemany("INSERT OR IGNORE INTO items VALUES (?,?)", batch)
        conn.commit()

# 2. Read back in chunks and write JSON files
cur.execute("SELECT * FROM items ORDER BY id")
chunk = 1
while True:
    rows = cur.fetchmany(20000)
    if not rows:
        break
    with open(f"datasets/processed/data_{chunk:04d}.json", "w") as f:
        json.dump([{"id": r[0], "name": r[1]} for r in rows], f)
    chunk += 1

conn.close()
os.remove(db_path)  # Clean up temp DB
```

### 3. Chunked JSON Output

GitHub has a 100 MB per-file hard limit (without LFS). Split large datasets:

```python
CHUNK_SIZE = 10000          # Items per file
MAX_FILE_SIZE = 45 * 1024 * 1024  # ~45 MB safety limit

items = load_all_items()
chunk = 1
while items:
    batch = items[:CHUNK_SIZE]
    items = items[CHUNK_SIZE:]

    # Check size — halve if too large
    while json.dumps(batch).encode("utf-8") > MAX_FILE_SIZE:
        mid = len(batch) // 2
        items = batch[mid:] + items
        batch = batch[:mid]

    with open(f"output_{chunk:04d}.json", "w") as f:
        json.dump(batch, f, ensure_ascii=False)
    chunk += 1

# Write index file
with open("output_index.json", "w") as f:
    json.dump({"chunks": chunk - 1, "files": [...]}, f)
```

### 4. External API Enrichment (Manual Workflow)

Some enrichment (posters, metadata) requires API keys. Keep these as GitHub secrets and use a separate manual-trigger workflow:

```yaml
name: Enrich with API
on:
  workflow_dispatch:    # Manual only — needs API key
    inputs:
      limit:
        description: 'Max items to enrich'
        default: '0'

jobs:
  enrich:
    runs-on: ubuntu-latest
    # ❌ DO NOT use: if: secrets.API_KEY != ''
    # → secrets context is NOT available in job-level if: conditions
    # → GitHub Actions returns: "Unrecognized named-value: 'secrets'"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: Check API Key
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: |
          if [ -z "$API_KEY" ]; then
            echo "API_KEY secret not set. Add it in Settings → Secrets → Actions"
            exit 1
          fi
          echo "API_KEY is set"
      - name: Enrich
        env:
          API_KEY: ${{ secrets.API_KEY }}
          LIMIT: ${{ inputs.limit }}
        run: python3 scripts/enrich.py
      - name: Commit
        run: |
          git add datasets/enriched/
          git commit -m "Enrich with API" && git push || echo "No changes"
```

Execute via:
```bash
gh secret set API_KEY -R owner/repo --body "your-key-here"
# Then trigger:
gh workflow run enrich.yml -R owner/repo
```

### 5. Git LFS — Only for files > 100MB

Files under 100MB (JSON chunks, small CSVs) track with regular Git — LFS adds upload overhead and can stall on large batches.

```bash
# .gitattributes — LFS only for binary/large formats
datasets/**/*.csv filter=lfs diff=lfs merge=lfs -text
datasets/**/*.tsv filter=lfs diff=lfs merge=lfs -text
datasets/**/*.parquet filter=lfs diff=lfs merge=lfs -text
# NOTE: JSON files under 100MB do NOT need LFS — regular git is faster
```

For raw compressed files that exceed GitHub's 100MB limit, add them to `.gitignore` (they're intermediates, re-downloadable):

```
datasets/raw/
datasets/**/*.tsv.gz
```

Enable LFS checkout in workflow:
```yaml
- uses: actions/checkout@v4
  with:
    lfs: true
    token: ${{ secrets.GITHUB_TOKEN }}
```

**Note:** LFS batch uploads on large file sets (400+ files) can time out. Prefer regular git for sub-100MB files.

### 6. GitHub Secrets for API Keys

```bash
# Set a secret
gh secret set MY_API_KEY -R owner/repo --body "value"

# Verify it exists
gh secret list -R owner/repo

# Use in workflow
env:
  API_KEY: ${{ secrets.MY_API_KEY }}
```

**Pitfalls**

- **`actions/setup-python` with `cache: 'pip'` fails** if there's no `requirements.txt` or `pyproject.toml` at the repo root. Omit the `cache` parameter when only using stdlib.
- **500 MB+ gzip files on standard runners**: Decompress to multiple GB. Use streaming or SQLite — don't `read()` into memory. GitHub standard runner has ~7 GB RAM and ~14 GB SSD.
- **Disk space fills up** with raw files + SQLite DB + JSON output. Strategy:
  a) Download → process → delete raw → commit (sequential, not parallel)
  b) Check disk with `df -h /` after each heavy step
  c) Clean up SQLite temp DBs (`os.remove(db_path)`) immediately after use  
  d) Use larger chunk sizes (25K credits, 100K people) to reduce file count → less git metadata overhead
- **`title.principals`-scale data**: The IMDb principals file (769 MB gz, 100M rows) takes ~20 minutes to stream even without SQLite. Plan accordingly. Split into separate workflow from lighter datasets.
- **Repo size limits**: GitHub repos recommend <5 GB. If your dataset is larger, use GitHub Releases or external storage.
- **`updatedAt` staleness**: The GitHub API's `updatedAt` field on workflow runs may not reflect per-step timing. Use `gh run view --json jobs` to get real step-level progress.
- **Logs hidden during run**: `gh run view --log` shows nothing until the run completes. Use `gh run view --json jobs` API for live progress.
- **Push fails with 403**: Missing `permissions: contents: write` at workflow level, or missing `token: ${{ secrets.GITHUB_TOKEN }}` on checkout/push URL.
- **`if: secrets.X != ''` is invalid at job level**: GitHub Actions does NOT expose the `secrets` context in job-level `if:` conditions. Using it returns `"422: Unrecognized named-value: 'secrets'"`. Fix: remove the job-level `if:` and add a step-level env var check instead (`if [ -z "$VAR" ]; then ...`). The secret IS accessible in step-level `env:` — validation belongs there.
- **TMDB v3 API key needs `api_key` query param, not Bearer auth**: TMDB gives you TWO credentials: v3 API key (short string) and v4 Bearer token (long JWT). Using a v3 key with `Authorization: Bearer` returns 401 on every request. Use `?api_key=KEY` in the URL instead. For IMDb lookup: `GET /find/{imdb_id}?external_source=imdb_id&api_key={KEY}`.
- **TMDB rate limits**: 50 req/s. Add `time.sleep(0.02)` between calls. Large datasets (millions of titles) can take hours.
- **Workflow YAML pushed via GitHub API**: Use `gh api repos/<owner>/<repo>/contents/<path>` to read SHA (`--jq '.sha'`), modify the file locally, then PUT with `-f message= -f content=$(base64 -w0 file) -f sha="$SHA" -f branch=main`. This bypasses needing a local clone when fixing workflow files from a CI runner or non-standard environment.
