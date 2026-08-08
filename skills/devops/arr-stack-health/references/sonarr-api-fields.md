# Sonarr API — Key Fields for Library Inspection

## `list_series` response structure

Each series object contains these fields relevant to cleanup:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Internal Sonarr ID — used for DELETE |
| `title` | string | Series title |
| `year` | int | First air year |
| `status` | string | `continuing`, `ended`, `upcoming`, `deleted` |
| `monitored` | bool | Whether the series is monitored |
| `seasons[]` | array | Array of season objects, each with `seasonNumber`, `monitored` |
| `statistics` | object | **Key field** — see below |

## `statistics` object

```json
{
  "seasonCount": 1,
  "episodeFileCount": 166,
  "episodeCount": 170,
  "totalEpisodeCount": 189,
  "sizeOnDisk": 388358709928,
  "releaseGroups": ["AMB3R"],
  "percentOfEpisodes": 97.6
}
```

| Field | Description |
|-------|-------------|
| `episodeFileCount` | Number of episode files on disk — **0 = no files** |
| `episodeCount` | Number of episodes available to download |
| `totalEpisodeCount` | Total episodes across all seasons |
| `sizeOnDisk` | Size in bytes |
| `percentOfEpisodes` | Percentage of available episodes that have files |

## DELETE endpoint

`DELETE /api/v3/series/{id}` with empty body — removes the series from Sonarr without touching existing files.
