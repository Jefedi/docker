---
name: drizzle-orm-sqlite
title: Drizzle ORM + SQLite
description: Set up Drizzle ORM with SQLite (better-sqlite3), design schemas, generate migrations, and manage the DB client in a monorepo. Covers Docker dev container workflow and pnpm workspace integration.
tags: [drizzle, sqlite, orm, migration, database, pnpm, monorepo]
---

# Drizzle ORM + SQLite

Set up Drizzle ORM with SQLite (better-sqlite3), design schemas, generate and manage migrations.

## Quick Start

### 1. Add Dependencies

```bash
# In the target workspace package
pnpm add drizzle-orm better-sqlite3
pnpm add -D drizzle-kit @types/better-sqlite3
```

Expected `package.json` additions:

```json
{
  "dependencies": {
    "drizzle-orm": "^0.38.0",
    "better-sqlite3": "^11.7.0"
  },
  "devDependencies": {
    "drizzle-kit": "^0.30.0",
    "@types/better-sqlite3": "^7.6.12"
  },
  "scripts": {
    "generate": "drizzle-kit generate --config=./drizzle.config.ts",
    "migrate": "echo \"migrator pending\""
  }
}
```

### 2. Create Drizzle Config

`drizzle.config.ts` at the package root:

```ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "sqlite",
  schema: "./src/schema/index.ts",
  out: "./migrations",
});
```

### 3. Design Schemas

Each table in its own file under `src/schema/`. Re-export all from `src/schema/index.ts`.

**Table shapes from this project:**

- `users.ts` — `id TEXT PK`, `email TEXT UNIQUE NOT NULL`, `name TEXT NOT NULL`, optional `avatar_url TEXT`, `created_at TEXT DEFAULT (CURRENT_TIMESTAMP) NOT NULL`
- `sessions.ts` — `id TEXT PK`, `user_id TEXT FK→users(id) ON DELETE CASCADE`, `token_hash TEXT UNIQUE NOT NULL`, `expires_at INTEGER NOT NULL` (unix ts), `created_at TEXT DEFAULT (CURRENT_TIMESTAMP) NOT NULL`
- `service_flags.ts` — `id INTEGER PK AUTOINCREMENT`, `service_name TEXT UNIQUE NOT NULL`, `enabled INTEGER DEFAULT 1 NOT NULL`, `created_at/updated_at TEXT DEFAULT (CURRENT_TIMESTAMP) NOT NULL`
- `service_credentials.ts` — same shape as service_flags but with `credential_encrypted TEXT NOT NULL`
- `audit_log.ts` — `id INTEGER PK AUTOINCREMENT`, `correlation_id TEXT NOT NULL`, `user_id TEXT?`, `action TEXT NOT NULL`, `resource_type TEXT?`, `resource_id TEXT?`, `metadata TEXT?`, `ip_address TEXT?`, `created_at TEXT DEFAULT (CURRENT_TIMESTAMP) NOT NULL`

### 4. CRITICAL: SQLite Defaults Must Use `sql` Helper

**DO NOT** use a plain string for `DEFAULT` values in SQLite — it generates a string literal, not a SQL function call:

```ts
// ❌ WRONG — generates `DEFAULT 'current_timestamp'` (literal string!)
created_at: text("created_at").notNull().default("current_timestamp"),

// ✅ CORRECT — generates `DEFAULT (CURRENT_TIMESTAMP)` (SQL function)
import { sql } from "drizzle-orm";
created_at: text("created_at").notNull().default(sql`(CURRENT_TIMESTAMP)`),
```

The `sql` tagged template wraps the expression in parentheses, ensuring SQLite treats it as a function call.

### 5. Create DB Client Singleton

`src/index.ts`:

```ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema/index.ts";

const DB_PATH = process.env.CC_DB_PATH ?? "/data/central-control.db";
let dbInstance: ReturnType<typeof drizzle<typeof schema>> | null = null;

export function getDb() {
  if (!dbInstance) {
    const sqlite = new Database(DB_PATH);
    sqlite.pragma("journal_mode = WAL");
    sqlite.pragma("foreign_keys = ON");
    dbInstance = drizzle(sqlite, { schema });
  }
  return dbInstance;
}

export const db = getDb();
export * from "./schema/index.ts";
```

### 6. Generate Migration

```bash
# Run from inside the dev container
pnpm --filter @cc/db generate
```

This creates `.sql` files in the `migrations/` directory plus a `meta/` directory with snapshot and journal.

### 7. Indexing Pattern for SQLite

Use the third argument of `sqliteTable` for composite/compound indexes:

```ts
import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core";

export const auditLog = sqliteTable(
  "audit_log",
  { /* columns */ },
  (table) => ({
    correlationIdx: index("idx_audit_log_correlation_id").on(table.correlation_id),
    userIdIdx: index("idx_audit_log_user_id").on(table.user_id),
    resourceIdx: index("idx_audit_log_resource").on(table.resource_type, table.resource_id),
    createdAtIdx: index("idx_audit_log_created_at").on(table.created_at),
  }),
);
```

UNIQUE constraints are set inline: `text("email").unique().notNull()`

## Docker Dev Container Workflow

### Permission Issue with Bind Mounts

When the repo directory is owned by `root` on the host, but the Dockerfile uses `USER node`, pnpm install fails with EACCES. Fix: add `user: root` to the dev compose file:

```yaml
services:
  central-control-dev:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    user: root          # ← required when bind-mounting root-owned repo
```

This is standard practice for dev containers — root inside the container doesn't affect host security since the container is isolated.

### Running Commands Inside the Container

```bash
# Start container in background (CMD runs pnpm install && pnpm dev)
docker compose -f docker/compose.dev.yml up -d

# Run workspace-specific command
docker compose -f docker/compose.dev.yml exec central-control-dev \
  pnpm --filter @cc/db generate

# Interactive shell
docker compose -f docker/compose.dev.yml exec central-control-dev sh

# Check logs
docker compose -f docker/compose.dev.yml logs --tail=30
```

### Lockfile Management

When running `pnpm install` inside the container with a bind-mounted repo, `pnpm-lock.yaml` is written to the host filesystem automatically. This is the correct workflow: let the dev container generate the lockfile, then commit it.

### Typecheck Gotchas

Running `tsc --noEmit` from a workspace package's `scripts.typecheck` requires `typescript` as a **direct devDependency of that package**. The hoisted workspace copy is not in pnpm's execution PATH for the filtered package:

```json
{
  "devDependencies": {
    "typescript": "^5.5.0"
  }
}
```

After adding it: `pnpm install` then `pnpm --filter @cc/<package> run typecheck`.

If you see `sh: tsc: not found`, it means the package doesn't have `typescript` in its own `devDependencies`.

### Per-Package TypeScript Configuration

If a workspace package (like `@cc/db`) uses `.ts` extension imports internally:

```ts
import * as schema from "./schema/index.ts";  // ← requires allowImportingTsExtensions
```

Then **every consumer package** (like `@cc/auth` importing from `@cc/db`) needs its own `tsconfig.json` that extends the base and enables `.ts` import resolution:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "noEmit": true,
    "allowImportingTsExtensions": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Without this, TypeScript will reject all `.ts` import paths from the dependency with `TS2307: Cannot find module`.

## Migration Management

### Clean Regeneration (for initial migrations before first commit)

If you changed schema after generating the first migration (and haven't committed yet), delete old migration artifacts entirely:

```bash
rm -f packages/db/migrations/0000_*.sql
rm -rf packages/db/migrations/meta/
pnpm --filter @cc/db generate
```

This produces a single clean `0000_*.sql` with no incremental migration chain.

## Package Exports

Ensure `packages/db/package.json` exports the schema entry point:

```json
{
  "exports": {
    ".": "./src/index.ts",
    "./schema": "./src/schema/index.ts"
  }
}
```

This allows other packages to import schemas directly: `import { users } from "@cc/db/schema"`.

## Pitfalls

- **String DEFAULT vs SQL function**: Drizzle's `default("current_timestamp")` generates a string literal `'current_timestamp'` in SQLite, not the SQL function `CURRENT_TIMESTAMP`. Always use `sql\`(CURRENT_TIMESTAMP)\``.
- **Incremental migration on empty DB**: If you regenerate early migrations (before committing), delete the old `.sql` AND the whole `meta/` directory. Keeping `meta/` makes drizzle-kit think the old migration was already applied.
- **`table` parameter implicit 'any'**: The third argument callback in `sqliteTable` sometimes gets an implicit `any` for the `table` parameter in some TS configs. This is a Drizzle codegen pattern — it works correctly with `drizzle-kit` and at runtime.
- **bind mount + node user**: The `node` user (uid 1000) can't write to a root-owned bind mount. Always add `user: root` to the dev compose, or chmod the repo on the host.
- **`node_modules` in volume**: When bind-mounting the repo, the container's `node_modules` must be in a named volume (not the bind mount) to avoid host-side node_modules interfering. The compose file should have a dedicated volume for this.
- **pnpm workspaces + filter**: Always use `pnpm --filter <package-name>` (not `pnpm -C <dir>`) for workspace commands. The filter resolves by package name from `pnpm-workspace.yaml`.
- **Transitive type resolution in strict pnpm**: pnpm does NOT hoist transitive dependencies by default. If package B depends on `drizzle-orm` and exports its types, then package A (which depends on B) needs its own `drizzle-orm` dep to resolve those types. Fix: `pnpm add drizzle-orm --filter @cc/<consumer>` for the version used by the dependency. The import failure surfaces as `TS2307: Cannot find module 'drizzle-orm'` during typecheck even though the direct code doesn't import it.
