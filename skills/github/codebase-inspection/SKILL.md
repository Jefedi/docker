---
name: codebase-inspection
description: "Inspect and verify codebases — LOC metrics with pygount, plus post-implementation verification of TypeScript monorepos (typecheck, package coherence, schemas, exports)."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, TypeScript, Monorepo, Verification]
    related_skills: [github-repo-management, drizzle-orm-sqlite]
prerequisites:
  commands: [pygount]
---

# Codebase Inspection

Two modes of inspection: **LOC metrics** (pygount) and **post-implementation verification** (TypeScript monorepo quality gates).

---

## Mode 1: LOC Metrics with pygount

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios.

### When to Use

- User asks for LOC (lines of code) count
- User wants a language breakdown of a repo
- User asks about codebase size or composition
- User wants code-vs-comment ratios

### Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

### 1. Basic Summary

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories.

### 2. Common Folder Exclusions

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

### 3. Filter by Language

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

### 4. Output Formats

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .
```

### Pitfalls (LOC mode)

1. **Always exclude .git, node_modules, venv** — without `--folders-to-skip`, pygount crawls everything and may hang.
2. **Markdown shows 0 code lines** — pygount classifies all Markdown content as comments. Expected.
3. **Large monorepos** — use `--suffix` to target specific languages rather than scanning everything.

---

## Mode 2: Post-Implementation Verification (TypeScript Monorepo)

After implementing a phase or feature in a pnpm workspace monorepo, run this checklist before declaring done. This catches tsconfig gaps, missing exports, type errors, and coherence issues across packages.

### When to Use

- After completing a multi-package implementation phase
- User says "vérifie avant" (verify before proceeding) or similar
- Before marking a spec as complete
- Before moving to the next development phase

### Verification Checklist

#### 1. File Presence

```bash
# List all source files created/modified in the phase
find packages/*/src apps/*/src apps/*/app -type f \( -name '*.ts' -o -name '*.tsx' \) | grep -v node_modules | sort

# Check all expected files are present against the spec
```

**Check:** Every file referenced by the spec exists. No dangling `.gitkeep` files in non-empty directories.

#### 2. Package Configuration (package.json)

For each workspace package, verify:
- `"type": "module"` is set
- `"exports"` field includes all entry points (`.` and any subpath like `./middleware`, `./schema`)
- All `@cc/*` dependencies use `"workspace:*"` version
- External dependency versions are coherent across packages

**Common issues:**
- Missing export for a subpath that another package imports (e.g. `@cc/auth/middleware` imported but not exported)
- `jose`, `drizzle-orm`, or other transitive deps missing from a consumer package that imports a re-exported type

#### 3. TypeScript Configuration

```bash
# Check every package has a tsconfig.json
for pkg in packages/* apps/*; do
  [ -f "$pkg/tsconfig.json" ] && echo "✅ $pkg" || echo "❌ MISSING: $pkg"
done
```

**Key checks:**
- Every package that uses `.ts` extension imports must have `"allowImportingTsExtensions": true` in its tsconfig
- Every consumer package that imports from a workspace package must have path mappings in its tsconfig (e.g. `"@cc/db": ["../../packages/db/src/index.ts"]`)
- The root `tsconfig.base.json` must not need changes — extend it, don't duplicate
- `"verbatimModuleSyntax": true` in base config means type-only imports must use `import type { ... }`

#### 4. TypeScript Typecheck

```bash
# Install deps first
pnpm install

# Then typecheck each package individually
for pkg in packages/* apps/*; do
  if [ -f "$pkg/tsconfig.json" ]; then
    echo "=== $pkg ==="
    (cd "$pkg" && npx --no-install tsc --noEmit 2>&1)
    echo ""
  fi
done
```

**Note:** `apps/web/tsc` standalone may fail with `TS2307: Cannot find module 'drizzle-orm'` in pnpm workspaces because transitive deps are hoisted to root `node_modules`. This is expected — `next build`/`next dev` resolve correctly via webpack/turbopack. The important check is that packages/* typecheck cleanly.

#### 5. Migration ↔ Schema Match (if using Drizzle)

Verify the generated migration matches the schema definitions:

```bash
cat packages/db/migrations/0000_*.sql
```

Check:
- All tables from schema appear in migration
- Column types match (TEXT vs INTEGER vs REAL)
- Foreign keys are present with correct `ON DELETE` behavior
- Indexes match schema definitions
- UNIQUE constraints are present

#### 6. Runtime Behavior Spot-Check

For patterns where runtime behavior is uncertain (e.g. async vs sync drivers):

```bash
# Write a small test script, run it from the package directory so
# pnpm's node_modules symlinks resolve correctly
#
# Example: verifying drizzle query builders are thenable with better-sqlite3
# In drizzle-orm >= 0.38.x, query builders implement .then() so
# `await db.insert().values(x)` works without `.run()` or `.all()`.
# This was verified during Phase 0c review.
```

#### 7. Inter-Package Import Coherence

Trace each import chain:
- `apps/web` imports from `@cc/auth`, `@cc/audit`, `@cc/db`
- `@cc/auth` imports from `@cc/db`
- `@cc/audit` imports from `@cc/db`

**Check:** Each import target actually exports the symbol being imported. The chain is: consumer `package.json` exports → dependency exports → actual `src/index.ts` re-exports.

#### 8. Cross-Package Dependency Versions

```bash
# Check that shared deps (drizzle-orm, jose, etc.) are at compatible versions
pnpm ls --depth=0 -r 2>/dev/null | grep -E '(drizzle|jose|better-sqlite3)'
```

**Red flag:** One package on `drizzle-orm@0.38.0` and another on `0.39.0` — may cause subtle type mismatches on shared types.

### Pitfalls

1. **Missing tsconfig.json** — When a package directory is created (stub, Phase 0b), it may lack a tsconfig.json. The first real code in that package won't typecheck until it's created. Always check `packages/*/tsconfig.json` exists after adding files to a package.

2. **`allowImportingTsExtensions` must be in EVERY consumer** — If the dependent package (e.g. `@cc/db`) uses `.ts` extensions in its imports, every consumer must also set `allowImportingTsExtensions: true`. Without it, TypeScript rejects all imports with `TS5097: An import path can only end with a '.ts' extension when 'allowImportingTsExtensions' is enabled.`

3. **Path mappings in app-level tsconfig** — Next.js apps (`apps/web`) need explicit path mappings for all workspace packages they import. Without `@cc/db`, `@cc/auth`, etc. in `paths`, tsc can't resolve them.

4. **`await` on synchronous DB drivers** — Drizzle ORM 0.38+ with better-sqlite3 makes query builders thenable, so `await db.insert().values(x)` executes correctly without `.run()`. But this is a recent addition; older versions (pre-0.38) require explicit terminal methods. If the project pinned an older version, add `.run()`/`.all()`.

5. **pnpm hoisting and tsc** — `tsc` run from a sub-package can't resolve packages hoisted to the root `node_modules/.pnpm/` store. Use `npx --no-install tsc` from that package's directory, or add the transitive dependency to the consumer's `devDependencies`.

6. **Verification before sign-off** — When the user says "vérifie avant", they want a complete check before proceeding to the next phase. Present findings grouped by severity (blocking vs cosmetic) with fixes applied immediately.
