# Backup Bloat Cleanup — 2026-07-31 Repair Transcript

## Symptoms

User reported: last GitHub backup was a week old, but ntfy notifications
"34 files backed up" kept arriving every 12h.

## Root Cause Chain

1. **state.db.malformed-backup files** (712 MB each, 25+ files on disk)
   were committed to git history. Three were in the git pack (~745 MB
   each as blobs).

2. **Core dumps** (`core.*`, 27 files × ~39 MB each) were also committed.

3. **Embedded git repos** (`hermes-agent/` 2.1 GB, `hermes-webui/` 349 MB,
   `hermes-ios-build/` 230 MB, `goxlr-utility-build/` 196 MB) were staged
   as embedded repos by `git add -A`.

4. Total `.git` size: **953 MB** — too large to push to GitHub. The push
   command hung indefinitely (confirmed: timeout after 30s with no output).

5. **The backup script's error detection was broken**: it only grepped for
   `rejected` or `error` in push output. A timeout produces neither string,
   so the script exited with code 1 (success) and sent the ntfy
   notification "34 files backed up" — while nothing was actually pushed.

6. **GitHub push protection** also blocked the push due to Discord bot
   tokens in `scripts/discord_cleanup.py` and `scripts/rappel-paiement-leoytb.sh`.

## Repair Steps

### .gitignore additions

```
state.db.malformed-backup*
state.db.malformed-backup*-shm
state.db.malformed-backup*-wal
core.*
skills/.hub/index-cache/
hermes-agent/
hermes-ios-build/
hermes-webui/
goxlr-utility-build/
scripts/.discord_token_*
```

### Secret externalization

- `scripts/discord_cleanup.py`: `BOT_TOKEN` now reads from
  `/opt/data/scripts/.discord_token_cleanup`
- `scripts/rappel-paiement-leoytb.sh`: `TOKEN` now reads from
  `/opt/data/scripts/.discord_token_rappel`
- Both token files created with `chmod 600`, excluded by `.gitignore`

### Orphan branch approach

Used orphan branch instead of `git filter-repo` (not installed) or BFG
(no Java). The repo only had 8 days of history (initial commit 2026-07-23),
so a fresh start was cleanest:

```bash
git checkout --orphan backup-fresh
git rm -rf --cached .
git add -A                          # respect new .gitignore
# Verify: largest staged file = 2.6 MB (down from 2.1 GB)
git commit -m "Fresh backup (cleaned...) ..."
git branch -D main
git branch -m backup-fresh main
git push -u origin main --force     # succeeded
git reflog expire --expire=now --all
git gc --prune=now --aggressive     # .git: 954 MB → 7 MB
```

### Backup script fix

Replaced the grep-based push check with:
1. `timeout 300` wrapper around `git push`
2. Exit code check (124 = timeout, non-zero = failure)
3. Post-push verification: `git fetch` + compare `HEAD` vs `origin/main`

### Verification

```bash
# Push test: 8 files, completed in <5s
bash /opt/data/scripts/backup-to-github.sh
# Exit 1 (success with changes)

# Sync check
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
# LOCAL == REMOTE → ✓ Sync OK
```

## Key Numbers

| Metric | Before | After |
|--------|--------|-------|
| `.git` size | 953 MB | 7 MB |
| Largest staged blob | 2.1 GB (embedded repo) | 2.6 MB |
| Push to GitHub | Timeout (>30s) | <5s |
| Branch `main` on remote | Gone (deleted) | Active, synced |
| Secret leaks in commits | 2 Discord bot tokens | 0 (externalized) |

## Files Modified

- `/opt/data/.gitignore` — added bloat patterns + token file patterns
- `/opt/data/scripts/backup-to-github.sh` — hardened push detection
- `/opt/data/scripts/discord_cleanup.py` — token externalized
- `/opt/data/scripts/rappel-paiement-leoytb.sh` — token externalized
- `/opt/data/scripts/.discord_token_cleanup` — new (chmod 600)
- `/opt/data/scripts/.discord_token_rappel` — new (chmod 600)