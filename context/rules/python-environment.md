---
description: Python environment invariants, banned commands, and project configuration
globs: ["**/*.py", "**/pyproject.toml", "**/requirements.txt"]
alwaysApply: true
---

# Python Environment

**Applies to**: All Python execution and environment configurations

---

## Strict Invariants

1. **NEVER fall back to bare `python`, `python3`, `pip`, or ad-hoc `PYTHONPATH` hacks if `uv` fails.**
2. When executing from the repository root (or outside the service directory), **always pass `--project <path-to-service-or-tests>`** to `uv`.
3. Every Python project MUST have `pyproject.toml`, `.python-version`, and test dependencies under `[dependency-groups] dev`.
4. All functions MUST have explicit type hints (parameters, return types). Class attributes and module-level variables should be typed.

---

## Banned Commands & Tool Substitutions

| Action | Required | Forbidden |
|--------|----------|-----------|
| Run script / module | `uv run [--project <path>] python <target>` | `python ...`, `python3 ...` |
| Run test suite | `uv run [--project <path>] pytest` | `pytest ...`, `python3 -m pytest` |
| Install package | `uv add package` (or `--project <path>`) | `pip install ...` |
| Sync dependencies | `uv sync [--project <path>]` | `pip install -r ...` |
| Python REPL | `uv run [--project <path>] python` | `python`, `python3` |
| One-off CLI tool | `uvx <tool>` | `pipx ...`, global pip installs |
| Lint / Format | `uv run [--project <path>] ruff ...` | `.venv/bin/ruff ...` |
| Module search path | Managed `.venv` via `uv sync` | `PYTHONPATH=...`, `sys.path.append(...)` |
