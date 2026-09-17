---
name: python-scripting
description: Procedural guidance and craft for authoring, running, and testing Python scripts with uv, PEP 723 inline metadata, and the --with pattern.
globs: ["**/*.py", "**/pyproject.toml", "context/scripts/**/*", "scripts/**/*"]
---

# Python Scripting Skill

---

## Overview
Procedural guidance for authoring reliable standalone scripts and internal tools. All commands executed under this skill are subject to the invariants defined in `context/rules/python-environment.md`.

---

## 1. Standalone Utility Scripts (PEP 723)
For self-contained automation scripts that require external libraries without modifying project dependencies, declare inline metadata:

```python
# /// script
# dependencies = [
#     "pyyaml>=6.0",
#     "rich>=13.0.0",
# ]
# ///
#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Execute via:
```bash
uv run python script.py
```

---

## 2. The Ephemeral `--with` Pattern
Use `uv run --with <pkg>` for temporary or ad-hoc tasks where declaring inline metadata or updating `pyproject.toml` is unnecessary:

- Ad-hoc single test run: `uv run --with pytest pytest <path>`
- Ad-hoc script execution: `uv run --with pyyaml python script.py`
- Ad-hoc formatting: `uv run --with ruff ruff format script.py`

*Note*: Ephemeral `--with` checks the local cache first, but requires network access on initial run to resolve from PyPI.

---

## 3. Verification Workflow
Verify authored scripts before handoff:
1. Syntax check: `uv run python -m py_compile <file>`
2. Lint check: `uv run --with ruff ruff check --fix <file>`
3. Test execution: `uv run --with pytest pytest <path> -v`

---

## 4. Script Authoring Standards
1. **Future annotations**: Always put `from __future__ import annotations` as the first import.
2. **Type hints**: Add explicit type annotations on all function signatures.
3. **CLI conventions**: Use `argparse` with standard operational flags (`--dry-run`, `--verbose`, `--quiet`).
4. **Path resolution**: Use `pathlib.Path` relative to `__file__`. Never use string concatenation or `os.path`.
5. **Deterministic exit**: Return exit code `0` on success and non-zero on failure.
6. **Execution boundaries**: Protect entry points with `if __name__ == "__main__": sys.exit(main())`.
7. **No multiline bash strings**: Write Python code to temporary files instead of passing complex scripts via `python -c "..."`.

---


## 6. Procedural Execution Commands

### Setup and Environment
```bash
# Sync project dependencies from lockfile
uv sync

# Add project dependencies
uv add package-name
uv add --dev package-name
```

### Database Migrations (Alembic)
```bash
# Initialize alembic
alembic init alembic

# Generate and run migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### Testing and Coverage
```bash
# Run pytest (always use uv run)
uv run pytest

# Run with coverage
uv run pytest --cov
```

---

## 7. Rationale
- **Why Fail-Fast on `uv`:** When `uv` fails (due to missing virtualenvs, path mismatches, or sandbox permissions), the failure is an environment defect to diagnose or escalate—never an invitation to bypass `uv`. Silent tool substitution (e.g. falling back to `pip`) masks defects, violates determinism, and produces untracked environment drift.
- **Why `--project`:** Without `--project` when running from the repo root, `uv` attempts to resolve `pyproject.toml` from the current working directory. If there is no `pyproject.toml`, it fails to resolve dependencies.
- **Why isolated dev dependencies:** Declaring `pytest`, plugins, and linters under `[dependency-groups] dev` guarantees that `uv sync` populates the local `.venv/` and `uv run pytest` runs deterministically and fully offline without sandbox/network friction.
