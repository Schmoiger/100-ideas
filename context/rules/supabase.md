---
description: Supabase invariants and strict constraints
globs: ["**/migrations/*.sql", "**/supabase/**", "**/database_service/**", "**/stores/**"]
alwaysApply: false
---

# Supabase Invariants

**Applies to**: All database operations against the Supabase project

---

## 1. Tooling Invariants

*   **Always use the Supabase MCP tools.**
*   **Never** use the Supabase CLI (`supabase` commands) or `psql`.
*   **Never** assume Docker is running.

---

## 2. Migration Auditing

*   After every `apply_migration`, you **MUST** insert an audit row into the `schema_migrations` table:

```sql
INSERT INTO schema_migrations (migration_file, applied_at)
VALUES ('<filename>.sql', now()) ON CONFLICT DO NOTHING;
```

---

## 3. Timestamp Bloat Prevention

*   **Timestamp bloat**: updating `fetched_at`/`computed_at` on every upsert creates dead tuples even when the payload is unchanged.
*   You **MUST ONLY** update timestamps when values actually change.
