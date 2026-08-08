# Documentation Expert Skill — Build Pattern

Reference for building and maintaining "documentation expert" skills in the
Jefe skill library. Distilled from building `pangolin`, `servarr`,
`media-stack`, `torrent-vpn`, and `jellyfin` skills.

## Structure

```
skill-name/
├── SKILL.md              # < 500 lines: frontmatter, mental model, routing table, behavior rule, validation Qs
├── references/
│   ├── 00-gotchas-jefe.md # Field knowledge, infra-specific, TODOs, French
│   ├── 00-build-pattern.md # This file (optional, for maintenance)
│   └── <prefix>__<path>__<filename>.md  # Flattened from upstream repos
└── scripts/
    └── sync.sh            # Git-based sync: clone, copy, compare, clean, exit code
```

## SKILL.md Anatomy

1. **YAML frontmatter**: `name`, `description` with trigger words
2. **Mental Model**: 2-4 sentences explaining what the services are and how they relate
3. **Routing Table**: Markdown table mapping question domains → reference filenames
4. **Behavior Rule**: "Never answer from memory. Always open the reference file."
5. **Validation Questions**: 3 Q&As (1 normal, 1 counter-intuitive, 1 config)

## File Naming Convention

- Reference files: `<service-prefix>__<flattened-path>.md`
- Paths flattened with `__` (double underscore) replacing `/`
- `.mdx` extensions normalized to `.md`
- Bazarr wiki files: lowercase, spaces → dashes
- Gotchas: `00-gotchas-jefe.md` (zero-padded prefix for sort order)
- Build pattern: `00-build-pattern.md`

## sync.sh Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail
# Exit 0 = unchanged, 1 = changed, 2 = error
# 1. Clone repo(s) to tmpdir
# 2. Copy docs with find + flatten
# 3. cmp -s to detect changes (avoid unnecessary writes)
# 4. Clean up tmpdir
# 5. Exit with appropriate code
```

Key details:
- `trap 'rm -rf "$TMP_DIR"' EXIT` for cleanup
- `cmp -s "$src" "$dst"` to skip unchanged files
- `find ... -print0` + `while IFS= read -r -d ''` for safe filename handling
- Bash `${var,,}` for lowercase, `${var// /-}` for spaces to dashes

## Gotchas File Content

- Infrastructure map (services, containers, hosts, storage, reverse proxy)
- Per-service sections with TODO for unknowns
- French for user-facing text
- Cross-references to official reference files
- Never invent — use TODO for unknowns

## Overlap Notes

### bazarr skill overlap

The standalone `bazarr` skill (category: media) covers Bazarr as a single
service with a simple SKILL.md (Docker compose, features, providers, integration).
The `jellyfin` skill covers Bazarr with the full Bazarr wiki as references
(13 files from `morpheus65535/bazarr.wiki`) plus gotchas integration.

**Resolution**: Keep both for now. The `bazarr` skill is a quick-reference for
Docker compose and basic config. The `jellyfin` skill has the full wiki for
detailed troubleshooting, settings, FAQ, and reverse proxy. The background
curator can consolidate later if the overlap causes confusion.

### media-stack Bazarr references

The `media-stack` skill has TRaSH Guides Bazarr references
(`trash__Bazarr__Setup-Guide.md`, `trash__Bazarr__Bazarr-suggested-scoring.md`).
These are complementary — TRaSH Guides cover scoring/profile config, while
the `jellyfin` skill has the official Bazarr wiki for installation, settings,
FAQ, and troubleshooting.