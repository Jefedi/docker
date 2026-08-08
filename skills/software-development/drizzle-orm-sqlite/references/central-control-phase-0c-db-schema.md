# Central Control Phase 0c — DB Schema Implementation Reference

This file captures the exact code, commands, and decisions from implementing T1 (Drizzle ORM schema + migration) for the Central Control project. Refer to this when revisiting or extending Phase 0c.

## Schema Files

### `packages/db/src/schema/users.ts`
```ts
import { sqliteTable, text } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),               // UUID
  email: text("email").unique().notNull(),
  name: text("name").notNull(),
  avatar_url: text("avatar_url"),             // nullable
  created_at: text("created_at")
    .notNull()
    .default(sql`(CURRENT_TIMESTAMP)`),
});
```

### `packages/db/src/schema/sessions.ts`
```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
import { users } from "./users";

export const sessions = sqliteTable("sessions", {
  id: text("id").primaryKey(),
  user_id: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  token_hash: text("token_hash").unique().notNull(),
  expires_at: integer("expires_at").notNull(),  // unix timestamp
  created_at: text("created_at")
    .notNull()
    .default(sql`(CURRENT_TIMESTAMP)`),
});
```

### `packages/db/src/schema/service-flags.ts`
```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const serviceFlags = sqliteTable("service_flags", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  service_name: text("service_name").unique().notNull(),
  enabled: integer("enabled").notNull().default(1),
  created_at: text("created_at")
    .notNull()
    .default(sql`(CURRENT_TIMESTAMP)`),
  updated_at: text("updated_at")
    .notNull()
    .default(sql`(CURRENT_TIMESTAMP)`),
});
```

### `packages/db/src/schema/service-credentials.ts`
Same shape as service-flags, but with `credential_encrypted: text("credential_encrypted").notNull()` instead of `enabled`.

### `packages/db/src/schema/audit-log.ts`
```ts
import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const auditLog = sqliteTable(
  "audit_log",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    correlation_id: text("correlation_id").notNull(),
    user_id: text("user_id"),
    action: text("action").notNull(),
    resource_type: text("resource_type"),
    resource_id: text("resource_id"),
    metadata: text("metadata"),     // JSON string
    ip_address: text("ip_address"),
    created_at: text("created_at")
      .notNull()
      .default(sql`(CURRENT_TIMESTAMP)`),
  },
  (table) => ({
    correlationIdx: index("idx_audit_log_correlation_id").on(table.correlation_id),
    userIdIdx: index("idx_audit_log_user_id").on(table.user_id),
    resourceIdx: index("idx_audit_log_resource").on(table.resource_type, table.resource_id),
    createdAtIdx: index("idx_audit_log_created_at").on(table.created_at),
  }),
);
```

### `packages/db/src/schema/index.ts`
```ts
export { users } from "./users";
export { sessions } from "./sessions";
export { serviceFlags } from "./service-flags";
export { serviceCredentials } from "./service-credentials";
export { auditLog } from "./audit-log";
```

## Drizzle Config

### `packages/db/drizzle.config.ts`
```ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "sqlite",
  schema: "./src/schema/index.ts",
  out: "./migrations",
});
```

## DB Client Singleton

### `packages/db/src/index.ts`
```ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema/index.ts";

const DB_PATH = process.env.CC_DB_PATH ?? "/data/central-control.db";
let dbInstance: ReturnType<typeof drizzle<typeof schema>> | null = null;

export function getDb(): ReturnType<typeof drizzle<typeof schema>> {
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

## Commands Used (inside Docker dev container)

```bash
# Add deps
pnpm add drizzle-orm better-sqlite3 --filter @cc/db
pnpm add -D drizzle-kit @types/better-sqlite3 --filter @cc/db

# Generate migration
pnpm --filter @cc/db generate

# Clean regenerate (early phase)
rm -f packages/db/migrations/0000_*.sql
rm -rf packages/db/migrations/meta/
pnpm --filter @cc/db generate
```

## Docker Compose Fix

The repo on the host is owned by `root`, but Dockerfile.dev uses `USER node`. pnpm install failed with EACCES. Fix in `docker/compose.dev.yml`:

```yaml
services:
  central-control-dev:
    # ... existing build config
    user: root        # ← added
```

## Commit

`be1a63f` — `feat(db): drizzle schema and initial migration`
- 15 files changed, 5348 insertions, 4 deletions
- Includes: 5 schema files, drizzle.config.ts, migration SQL, DB singleton, pnpm-lock.yaml, compose.dev.yml fix
