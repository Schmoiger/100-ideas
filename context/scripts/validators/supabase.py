#!/usr/bin/env python3
from __future__ import annotations

"""Validate Supabase invariants (context/rules/supabase.md).

Enforces:
1. Supabase client imports (Python and TypeScript) restricted to database service / stores.
2. SQL migrations must contain an audit row insert into schema_migrations table.
"""

import argparse
import re
import sys
from pathlib import Path

# Prohibited outside database-service or designated stores
PYTHON_IMPORT_PATTERN = re.compile(r"^\s*(import supabase\b|from supabase\b)", re.MULTILINE)
TS_IMPORT_PATTERN = re.compile(r"['\"]@supabase/supabase-js['\"]")

# Allowed directories for Supabase client imports
ALLOWED_IMPORT_DIRS = {"database_service", "database", "stores"}

# Migration audit insertion pattern
MIGRATION_AUDIT_PATTERN = re.compile(
    r"INSERT\s+INTO\s+schema_migrations\s*\(migration_file,\s*applied_at\)",
    re.IGNORECASE,
)


def is_allowed_supabase_location(path: Path) -> bool:
    """Check if file is in an allowed database or store directory."""
    parts = set(path.parts)
    return bool(parts & ALLOWED_IMPORT_DIRS)


def check_supabase_imports(files: list[Path]) -> list[str]:
    """Flag Supabase imports in unauthorised application code."""
    violations: list[str] = []
    for p in files:
        if is_allowed_supabase_location(p):
            continue
        try:
            text = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        if p.suffix in [".py", ""]:
            if PYTHON_IMPORT_PATTERN.search(text):
                violations.append(f"{p}: 'supabase' imported outside database service/stores")
        elif p.suffix in [".ts", ".tsx", ".js", ".jsx"] and TS_IMPORT_PATTERN.search(text):
            violations.append(f"{p}: '@supabase/supabase-js' imported outside database service/stores")

    return violations


def check_migration_audit(files: list[Path]) -> list[str]:
    """Flag SQL migration files missing the schema_migrations audit insert."""
    violations: list[str] = []
    for p in files:
        if p.suffix == ".sql" and "migrations" in p.parts:
            try:
                text = p.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            if not MIGRATION_AUDIT_PATTERN.search(text):
                violations.append(
                    f"{p}: missing required 'INSERT INTO schema_migrations (migration_file, applied_at)...' audit insert"
                )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Supabase invariants (context/rules/supabase.md)"
    )
    parser.add_argument("files", nargs="*", help="Files to inspect")
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file()]
        if not files:
            print("✅ Supabase invariants verified (no files to check)")
            return 0
    else:
        # Scan repo for python/ts files and migrations
        repo_root = Path(__file__).resolve().parents[3]
        ignored = {".git", ".venv", "venv", "node_modules"}
        files = []
        for ext in ("*.py", "*.ts", "*.tsx", "*.sql"):
            for p in repo_root.rglob(ext):
                if not (set(p.parts) & ignored):
                    files.append(p)

    import_violations = check_supabase_imports(files)
    migration_violations = check_migration_audit(files)

    all_violations = import_violations + migration_violations

    if all_violations:
        print("❌ Supabase invariant violations (context/rules/supabase.md):", file=sys.stderr)
        for v in all_violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("✅ Supabase invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
