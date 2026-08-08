# Example: Cinema Datasets Pipeline

Full implementation at: https://github.com/Jefedi/cinema-datasets

## Repo structure

```
.github/workflows/
├── sync-datasets.yml     ← IMDb data pipeline (weekly + manual)
└── enrich-tmdb.yml       ← TMDB enrichment (manual, needs API key)
scripts/
├── process-basics.py     ← Movies (movie) vs Series (tvSeries/tvMiniSeries)
├── process-ratings.py    ← IMDb ratings, sorted by votes
├── process-episodes.py   ← Episodes with parent series mapping
├── process-people.py     ← Actors/crew names + credits per title
├── generate-stats.py     ← Global statistics aggregation
└── enrich-tmdb.py        ← TMDB poster URLs + synopsis + metadata
web/
└── index.html            ← Dark-theme dashboard
```

## Data sources

- **IMDb**: `https://datasets.imdbws.com/` — 7 datasets, TSV.gz, ~1GB compressed
- **TMDB**: API-based enrichment (posters, synopsis, popularity, production companies)

## Key decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | GitHub repo + LFS | Free, no infra to maintain |
| Processing | GitHub Actions | Runners do the work, no VPS disk used |
| File format | JSON chunks < 50MB | GitHub 100MB limit, easy to browse |
| Posters | Store URLs, not files | Images are terabytes, URLs are KB |
| TMDB key | GitHub secret | Prevents commit exposure |

## IMDb dataset mappings

| IMDb File | Size | Pipeline Output |
|-----------|------|-----------------|
| `title.basics.tsv.gz` | ~223 MB | `movies/*.json`, `series/*.json` |
| `title.ratings.tsv.gz` | ~8 MB | `ratings/*.json` |
| `title.episode.tsv.gz` | ~180 MB | `episodes/*.json` |
| `name.basics.tsv.gz` | ~280 MB | `people/people_*.json` |
| `title.principals.tsv.gz` | ~600 MB | `people/credits_*.json` |
| `title.akas.tsv.gz` | ~500 MB | Not processed yet |
| `title.crew.tsv.gz` | ~50 MB | Not processed yet |

## TMDB enrichment fields

From TMDB API, the script extracts:
- Poster URLs (original + w500)
- Backdrop URLs (original + w1280)
- Overview, tagline, status
- Popularity, TMDB vote average/count
- Production companies & countries
- Spoken languages
- Homepage

## GitHub secrets setup

```bash
gh secret set TMDB_API_KEY -R Jefedi/cinema-datasets
```

Then manually trigger:
```bash
gh workflow run enrich-tmdb.yml -R Jefedi/cinema-datasets
```
