---
description: Secrets location constraints and forbidden handling patterns
globs: ["**/*.py", "**/*.ts", "**/*.js"]
alwaysApply: false
---

# Secrets Invariants

**Applies to**: All code handling credentials, API keys, or sensitive data

---

## 1. Location Matrix

Secrets MUST be placed in the designated locations:

| Secret Type | Location | Format |
|-------------|----------|--------|
| API credentials | `/secrets/*.json` | JSON file |
| Database passwords | Environment variable | `SUPABASE_DB_PASSWORD` |
| Service accounts | `/secrets/*.json` | JSON file |

---

## 2. Forbidden Actions

- **NEVER** create `.env` files with credentials
- **NEVER** hardcode secrets in source code
- **NEVER** copy secrets to multiple locations
- **NEVER** commit secrets to git (already in `.gitignore`)
