---
name: supabase-operations
description: Procedural guidance for Supabase migrations, queries, and maintenance via MCP
globs: ["**/migrations/*.sql", "**/supabase/**", "**/database_service/**", "**/stores/**"]
---

# Supabase Operations Skill

---

## 1. Supabase MCP Tool Mapping

Use the following MCP tools for Supabase operations:

| Action | Correct | Wrong |
|--------|---------|-------|
| Query | `mcp__supabase__execute_sql` | `supabase db query`, `psql` |
| Migration | `mcp__supabase__apply_migration` + insert into `schema_migrations` | `supabase db push` |
| Logs | `mcp__supabase__get_logs` | CLI |
| Advisors | `mcp__supabase__get_advisors` | — |
| VACUUM | `mcp__supabase__execute_sql` | asyncpg in app code |

---

## 2. Migration Execution and Indexes

`apply_migration` runs inside a transaction — `CONCURRENTLY` DDL will silently create an invalid index or error. Use plain forms in migration files; use `execute_sql` for concurrent operations on live tables:

| | Migration file | `execute_sql` |
|-|---------------|---------------|
| Drop index | `DROP INDEX IF EXISTS idx` | `DROP INDEX CONCURRENTLY IF EXISTS idx` |
| Create index | `CREATE INDEX idx ON ...` | `CREATE INDEX CONCURRENTLY idx ON ...` |

---

## 3. Autovacuum Tuning

Default `scale_factor = 0.20` means vacuum triggers after 20% dead tuples — too late for large upsert-heavy tables. Tune per-table (Supabase blocks server-level GUC changes):

```sql
ALTER TABLE <table> SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_vacuum_threshold = 100,
    autovacuum_analyze_scale_factor = 0.005
);
```

Apply to any table > 1M rows with frequent upserts. Never add `VACUUM` to application code — run on demand via `execute_sql` after bulk loads only.

---

## 4. Diagnostics and Gotchas

### Replication Slots

Stale slots (consumer gone, slot not dropped) silently accumulate WAL until disk fills. Check when diagnosing disk growth:

```sql
SELECT slot_name, active,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_behind
FROM pg_replication_slots;
```

### PostgREST Transactions

All app queries run inside a transaction — VACUUM and `CONCURRENTLY` DDL require `execute_sql` or a direct connection.
