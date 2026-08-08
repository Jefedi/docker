# Blogwatcher Pattern (Pattern A)

Full setup guide for standalone RSS monitoring using blogwatcher-cli,
without n8n. The agent both scans and translates (if needed).

## Prerequisites

- **blogwatcher-cli** installed and on `$PATH` (see the `blogwatcher` skill for
  installation details).

- If `/usr/local/bin` is not writable (common on managed Hermes hosts), install to
  `~/.local/bin`:
  ```bash
  mkdir -p ~/.local/bin
  curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz \
    | tar xz -C ~/.local/bin blogwatcher-cli
  chmod +x ~/.local/bin/blogwatcher-cli
  ```

## Setup Steps

### 1. Add RSS feeds

```bash
export PATH="$HOME/.local/bin:$PATH"
blogwatcher-cli add "Hacker News" https://news.ycombinator.com --feed-url https://news.ycombinator.com/rss
blogwatcher-cli add "Lobsters" https://lobste.rs --feed-url https://lobste.rs/rss
blogwatcher-cli add "The Verge" https://www.theverge.com --feed-url https://www.theverge.com/rss/index.xml
blogwatcher-cli add "Ars Technica" https://arstechnica.com --feed-url https://feeds.arstechnica.com/arstechnica/index
```

### 2. Mark initial backlog as read

```bash
blogwatcher-cli read-all --yes
```

### 3. Create the scan script

Place it at `~/.hermes/scripts/rss-scan.sh`. The cron `script` field only accepts
bare filenames in `~/.hermes/scripts/` — absolute paths are rejected.

The script is provided as `scripts/rss-scan.sh` in this skill.

### 4. Create the cron job(s)

Create one or two cron jobs (e.g. morning 8h, evening 20h) using the `cronjob` tool.
Key fields:

- `script`: `rss-scan.sh` (bare filename, NOT a path)
- `deliver`: `telegram` (or `discord`)
- `prompt`: the Pattern A filtering prompt (see `references/rss-filter-prompt.md`)
- `enabled_toolsets`: `["terminal"]`

### 5. Test manually before relying on cron

```bash
~/.hermes/scripts/rss-scan.sh
hermes cron run <job_id>
```

## Adding More Feeds Later

```bash
blogwatcher-cli add "Site Name" https://example.com --feed-url https://example.com/rss
blogwatcher-cli scan "Site Name"
blogwatcher-cli read-all --blog "Site Name" --yes
```

No need to touch the cron job — the script scans ALL tracked blogs automatically.

## Removing a Feed

```bash
blogwatcher-cli remove "Site Name" --yes
```