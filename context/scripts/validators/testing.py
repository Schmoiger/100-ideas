#!/usr/bin/env python3
from __future__ import annotations

"""Validate testing invariants (context/rules/testing.md).

Enforces:
1. Assert on outcomes, not interactions (outcome-based assertions).
2. Prohibits interaction-based assertions (e.g. mock.assert_called_once_with)
   on internal collaborators in test files, allowing mocks only at explicit
   I/O boundaries (marked with # io-boundary or // io-boundary).
"""

import argparse
import re
import sys
from pathlib import Path

# Prohibited Python interaction assertion patterns
PY_INTERACTION_PATTERNS = [
    re.compile(r"\bassert_called_once_with\s*\("),
    re.compile(r"\bassert_called_with\s*\("),
    re.compile(r"\bassert_any_call\s*\("),
    re.compile(r"\bassert_has_calls\s*\("),
]

# Prohibited TypeScript / Jest / Vitest interaction assertion patterns
TS_INTERACTION_PATTERNS = [
    re.compile(r"\bexpect\s*\([^)]+\)\.toHaveBeenCalledWith\s*\("),
    re.compile(r"\bexpect\s*\([^)]+\)\.toHaveBeenLastCalledWith\s*\("),
    re.compile(r"\bexpect\s*\([^)]+\)\.toHaveBeenNthCalledWith\s*\("),
]

EXEMPT_MARKERS = ["io-boundary", "mock-allowed", "boundary-mock"]
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "site-packages", "fixtures"}


def is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    parts = set(path.parts)
    if parts & IGNORED_DIRS:
        return False
    if "context" in parts and "scripts" in parts and "tests" in parts:
        return False
    if "tests" in parts or "__tests__" in parts:
        return True
    name = path.name
    return any(marker in name for marker in [".test.", ".spec.", "_test."])


def check_forbidden_mocks(path: Path, content: str) -> list[tuple[int, str]]:
    """Flag interaction assertions on non-exempt lines in a test file."""
    violations: list[tuple[int, str]] = []
    lines = content.splitlines()

    is_py = path.suffix in [".py"]
    is_ts = path.suffix in [".ts", ".tsx", ".js", ".jsx"]

    patterns = PY_INTERACTION_PATTERNS if is_py else (TS_INTERACTION_PATTERNS if is_ts else [])
    if not patterns:
        return violations

    for i, line in enumerate(lines, 1):
        line_strip = line.strip()
        # Skip commented lines
        if line_strip.startswith(("#", "//")):
            continue

        # Check for boundary exemption comment
        if any(marker in line.lower() for marker in EXEMPT_MARKERS):
            continue

        for pat in patterns:
            if pat.search(line):
                violations.append(
                    (
                        i,
                        (
                            f"Line {i}: interaction-based assertion prohibited (context/rules/testing.md §2). "
                            "Assert on outcomes, not interactions. Use '# io-boundary' if mocking an external boundary."
                        ),
                    )
                )
                break

    return violations


def validate_test_files(files: list[Path]) -> list[str]:
    """Validate multiple test files."""
    all_violations: list[str] = []
    for f in files:
        if not is_test_file(f):
            continue
        try:
            content = f.read_text()
        except (OSError, UnicodeDecodeError) as e:
            all_violations.append(f"{f}: read error — {e}")
            continue

        for line_no, msg in check_forbidden_mocks(f, content):
            all_violations.append(f"{f}:{line_no}\n  {msg}")

    return all_violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate testing invariants (context/rules/testing.md)"
    )
    parser.add_argument("files", nargs="*", help="Test files to check")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]

    if args.files:
        files = [Path(f) for f in args.files if Path(f).is_file()]
    else:
        files = []
        for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx"):
            for p in repo_root.rglob(ext):
                if not (set(p.parts) & IGNORED_DIRS):
                    files.append(p)

    violations = validate_test_files(files)

    if violations:
        print("❌ Testing invariant violations (context/rules/testing.md):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("✅ Testing invariants verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
