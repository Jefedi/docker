# Radarr API — Key Fields for Library Inspection

## `movie` list response structure

Each movie object contains these fields relevant to cleanup:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Internal Radarr ID — used for DELETE |
| `title` | string | Movie title |
| `year` | int | Release year |
| `status` | string | `released`, `inCinemas`, `announced` |
| `monitored` | bool | Whether the movie is monitored |
| `hasFile` | bool | Whether a movie file exists on disk — **false = no file** |
| `sizeOnDisk` | int | Size in bytes (0 if no file) |
| `movieFile` | object\|null | Present when file exists, null otherwise |
| `genres[]` | array | Genre tags — used for grouping (Marvel, DC, etc.) |
| `studio` | string | Studio name — also used for grouping |
| `imdbId` | string | IMDB ID |
| `tmdbId` | int | TMDB ID |
| `rootFolderPath` | string | Path to media folder |

## DELETE endpoint

`DELETE /api/v3/movie/{id}` with empty body — removes the movie from Radarr without touching existing files. Items without `hasFile` have no files to delete.
