# IMDb Datasets Reference

Source: `https://datasets.imdbws.com/` — Non-commercial use only.

## Available files

| File | Size (gz) | Est. rows | Description |
|------|-----------|-----------|-------------|
| `title.basics.tsv.gz` | ~223 MB | 1M+ | Movies & series: id, title, year, genres, runtime, adult flag |
| `title.ratings.tsv.gz` | ~8.5 MB | 1M+ | Rating, numVotes per title |
| `title.episode.tsv.gz` | ~51 MB | 10M+ | Episode → parent series, season/episode number |
| `name.basics.tsv.gz` | ~200 MB | 12M+ | People: name, birth/death year, professions, known-for titles |
| `title.principals.tsv.gz` | ~769 MB | 100M | Credits: person → title, category, job, characters, ordering |
| `title.akas.tsv.gz` | ~500 MB | — | Alternative titles by country (akas) |
| `title.crew.tsv.gz` | small | — | Director/writer per title |

## Schema notes

- TSV, gzip compressed. Read with `gzip.open()` + `csv.DictReader(f, delimiter="\t")`
- Null values encoded as `\N`
- IDs: `tt0000001` (titles), `nm0000001` (people)
- `titleType` values: movie, tvSeries, tvMiniSeries, tvEpisode, tvMovie, video, videoGame, short, tvShort, tvSpecial
- `genres` : comma-separated, can be empty (use VALID_GENRES filter)
- `title.principals`: ~100M rows, ~4-5 GB uncompressed, DO NOT load entirely in memory
  - `category`: actor, actress, self, director, producer, writer, cinematographer, composer, editor, production_designer, archive_footage, archive_sound
  - `characters`: JSON array string or `\N`
  - `ordering`: 0-indexed per title

## Processing patterns

### Fast path (single-file chunking)
For title.basics, ratings, episodes:
- Read with csv.DictReader, write in chunks of 10K items
- Filter by titleType to separate movies vs series
- Chunk files < 50 MB to stay under GitHub's recommended limit

### Heavy path (principals)
- DON'T join with names in RAM (12M dict entries = ~3 GB)
- Stream row by row, group by tconst into dict
- Write credit chunks every 25K titles
- Store only nconst (not name) — consumers join with people files later

### People (names)
- 12M people → ~600 files at 20K/chunk or ~120 files at 100K/chunk
- SQLite bulk insert (50K batches, journal_mode=OFF) works well
- Clean up SQLite DB after writing to free disk space

## TMDB enrichment

- **v3 API key** (32-44 char string, looks like `abc123...`) — NOT a v4 Bearer token
- **Auth via `api_key` query param**, NOT `Authorization: Bearer` — using Bearer with a v3 key returns 401 on every request
  - Correct: `GET /find/{imdb_id}?external_source=imdb_id&api_key=YOUR_KEY`
  - Wrong: `curl -H "Authorization: Bearer YOUR_KEY" ...` → 401
- Set as GitHub secret: `gh secret set TMDB_API_KEY -R owner/repo --body "key-value"`
- Endpoints:
  - `GET /find/{imdb_id}?external_source=imdb_id&api_key=KEY` — find TMDB ID from IMDb ID
  - `GET /movie/{tmdb_id}?api_key=KEY&append_to_response=credits,external_ids` — full details
  - `GET /tv/{tmdb_id}?api_key=KEY&append_to_response=credits,external_ids,seasons` — TV details
- Poster URL: `https://image.tmdb.org/t/p/original{path}` or `w500` for smaller
- Rate limit: ~50 req/s (use `time.sleep(0.02)` between calls)
- Images are NOT downloadable for storage — store URLs only
