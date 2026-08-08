---
name: hermes-backup-github
description: "Use when Hermes backup to GitHub is stale or push fails."
category: devops
triggers:
  - backup notifications arrive but GitHub repo is stale or empty
  - git push to GitHub times out or silently fails
  - GitHub push protection blocks the backup
  - .git directory is unusually large (hundreds of MB)
  - user notices last successful backup is old despite regular notifications
tags: [hermes, backup, github, git, push-protection, gitignore, cron]
---

# Hermes Backup to GitHub — Troubleshooting & Maintenance

## System Overview

The backup system lives at `/opt/data/scripts/backup-to-github.sh`, runs via
cron job (every 720m = 12h), and pushes `/opt/data` to a private GitHub repo
(`Jefedi/docker`, branch `main`). Secrets and large files are excluded via
`/opt/data/.gitignore`.

The cron job prompt:
- Exit 0 = no changes → silent (no ntfy)
- Exit 1 = changes pushed → ntfy notification "N files backed up"
- Exit 2 = error → ntfy notification "ERREUR" (high priority)

## Diagnostic Workflow

### 1. Verify the cron job is running

```bash
# Check cron job status (use cronjob action=list in Hermes)

# Check local commits — are they accumulating?
cd /opt/data && git log --oneline -10
```

If commits accumulate locally but GitHub is stale, the **push is failing
silently**.

### 2. Check remote sync status

```bash
cd /opt/data
git fetch origin main
git status -sb | head -3
# If you see [gone], the remote branch was deleted
git log --oneline origin/main..HEAD  # commits not pushed
```

### 3. Check repo size

```bash
du -sh .git
git count-objects -vH
```

If `.git` > 100 MB, repo bloat is likely causing push timeouts. GitHub has
a ~1 GB soft limit and pushes of that size will hang indefinitely.

### 4. Find the largest objects in git history

```bash
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | sed -n 's/^blob //p' | sort -rnk2 | head -20
```

Common bloat sources on this system:
- `state.db.malformed-backup*` — SQLite malformed DB backups (~712 MB each)
- `core.*` — process core dumps (~39 MB each)
- `skills/.hub/index-cache/hermes-index.json` — skill index cache (~40 MB)
- Embedded git repos (`hermes-agent/`, `hermes-webui/`, `hermes-ios-build/`,
  `goxlr-utility-build/`) — hundreds of MB to GB each

### 5. Test push manually with timeout

```bash
cd /opt/data && timeout 30 git push origin main 2>&1
```

If this times out, the repo is too large. If it returns a GitHub error,
read the error message (push protection, auth, etc.).

## Repair: Cleaning Repo Bloat

When the repo is bloated with large files that shouldn't be tracked, the
cleanest fix (especially for repos with short history) is an **orphan branch**:

### Step 1: Update .gitignore

Add all bloat sources to `/opt/data/.gitignore`:

```
# State DB malformed backups — hundreds of MB each
state.db.malformed-backup*
state.db.malformed-backup*-shm
state.db.malformed-backup*-wal

# Core dumps
core.*

# Skills hub index cache — regenerable, ~40 MB
skills/.hub/index-cache/

# Embedded git repos — too large for backup
hermes-agent/
hermes-ios-build/
hermes-webui/
goxlr-utility-build/
```

### Step 2: Create orphan branch (clean slate, no history)

```bash
cd /opt/data
git checkout --orphan backup-fresh
git rm -rf --cached .
git add -A  # re-stages everything respecting new .gitignore
```

### Step 3: Verify no large files staged

```bash
git diff --cached --name-only | xargs -I{} du -sh {} 2>/dev/null | sort -rh | head -10
```

Largest staged file should be < 5 MB. If not, find and exclude the offender.

### Step 4: Commit and replace main

```bash
git commit -m "Fresh backup (cleaned: removed <what was removed>) $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
git branch -D main
git branch -m backup-fresh main
```

### Step 5: Force push

```bash
git push -u origin main --force
```

### Step 6: Garbage collect old .git objects

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
du -sh .git  # should drop dramatically (e.g. 954 MB → 7 MB)
```

## Repair: GitHub Push Protection (Secrets)

GitHub scans pushes for known secret patterns (API tokens, bot tokens, etc.).
If detected, the push is rejected with a message like:

```
remote: error: GH013: Repository rule violations found
remote: - GITHUB PUSH PROTECTION
remote:   —— Discord Bot Token ——
remote:     path: scripts/example.py:3
```

### Fix: Externalize the secret

1. Move the token to a file excluded by `.gitignore`:
   ```bash
   echo -n "TOKEN_VALUE" > /opt/data/scripts/.discord_token_example
   chmod 600 /opt/data/scripts/.discord_token_example
   ```

2. Update the script to read from the file:
   ```python
   # Python
   BOT_TOKEN = open("/opt/data/scripts/.discord_token_example").read().strip()
   ```
   ```bash
   # Bash
   TOKEN=$(cat /opt/data/scripts/.discord_token_example)
   ```

3. Ensure `.gitignore` covers the token file:
   ```
   scripts/.discord_token
   scripts/.discord_token_*
   ```

4. Re-commit and push.

**Note:** With an orphan branch (no parent commit), the commit only
contains the new clean content — GitHub won't see the old secret in a diff
because there is no parent to diff against.

## Backup Script Hardening

The original script had a critical flaw: it only checked for `rejected` or
`error` in push output. A **timeout** produces neither, so the script
reported success and sent notifications while nothing was pushed.

### Hardened script pattern

Key improvements:
1. **Timeout on push** (300s) — prevents indefinite hangs
2. **Exit code check** — not just grep on output
3. **Post-push verification** — fetch remote and compare commit hashes

```bash
# Push with timeout and proper error detection
PUSH_OUTPUT=$(timeout 300 git push origin main 2>&1) || PUSH_EXIT=$?
PUSH_EXIT=${PUSH_EXIT:-0}

if [ "$PUSH_EXIT" -eq 124 ]; then
    echo "ERROR: push timed out after 5 minutes" >&2
    exit 2
elif [ "$PUSH_EXIT" -ne 0 ]; then
    echo "ERROR: push failed (exit $PUSH_EXIT)" >&2
    echo "$PUSH_OUTPUT" >&2
    exit 2
fi

# Verify push actually succeeded
git fetch origin main 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "none")
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "ERROR: local and remote diverge after push" >&2
    exit 2
fi
```

See `references/backup-bloat-cleanup.md` for the detailed repair transcript
and additional context.

## Pitfalls

- **Silent push failure is the #1 risk** — the cron job reports "N files
  backed up" based on the local commit, not the push result. Always verify
  the push actually reached GitHub by comparing local and remote hashes.
- **`state.db.malformed-backup*` files appear spontaneously** — Hermes
  creates these when the state DB gets corrupted. Each is ~712 MB. They
  must be in `.gitignore` AND cleaned from git history when they appear.
- **Core dumps (`core.*`)** accumulate from crashed processes. Each is
  ~39 MB. Add `core.*` to `.gitignore` and clean periodically.
- **Embedded git repos** (directories with their own `.git/`) get added as
  submodules or embedded repos by `git add -A`, pulling in their entire
  history. Always exclude them in `.gitignore`.
- **GitHub push protection is retroactive** — even if you remove a secret
  from the current file, old commits containing it will still be blocked.
  Orphan branch approach sidesteps this.
- **`git gc --aggressive` is slow** but necessary after cleaning — without
  it, old objects stay in `.git` and the size doesn't drop.
- **The cron job's `deliver: local`** means it silently saves output to
  `/opt/data/cron/output/<job_id>/` — check these logs when diagnosing.
- **`*.txt` in .gitignore** already excludes many token files, but
  dotfiles (`.discord_token_*`) need their own pattern.